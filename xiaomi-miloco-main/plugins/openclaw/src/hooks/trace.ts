// agent turn trace —— 全 turn buffer,turn 结束时:
//   1. debug 模式 → gzip 写 $MILOCO_HOME/trace/agent/YYYYMMDD/<runId>__<query>.jsonl.gz
//   2. meta 留在 turns Map(状态置 done),backend 通过 get_trace webhook 主动来取
//
// turn 结束信号同时监听 agent_end 与 subagent_ended:
//   miloco 走 webhooks/agent.ts → api.runtime.subagent.run(...) 派生子 agent,SDK
//   2026.5.20 在该路径上 fire 的是 subagent_ended(subagent-registry.js),不是
//   agent_end(后者只在主 agent selection 主循环 fire)。两个都监听 + finalize 幂等
//   去重,既覆盖子 agent 主路径,又保留主 agent 路径作 fallback,适配未来 SDK 调整。
//
// debug 标志:每 turn 现读 $MILOCO_HOME/.debug_observability,运行时切换立即生效。
// 单日 cap:每天 trace/agent/YYYYMMDD/ 下 ≤300 个 jsonl.gz,超出 warn 跳过(防撑爆磁盘)。
// backend 关联通过 webhooks/agent.ts 调用 registerTraceLink(runId, traceId)。
// 反向通信:backend → webhooks/get_trace.ts(本文件 popDoneTurn 提供)。
import { existsSync, mkdirSync, readdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { gzipSync } from "node:zlib";
import { milocoHome } from "../miloco/paths.js";
import { toLocalParts } from "../utils/time.js";
import type { HookRegister } from "./index.js";

type RecordedEvent = {
  ts: string;
  local_time: string;
  hook: string;
  runId: string;
  traceId?: string;
  sessionId?: string;
  sessionKey?: string;
  callId?: string;
  toolCallId?: string;
  // biome-ignore lint/suspicious/noExplicitAny: hook payload shape varies
  payload: any;
};

function nowTimestamp(): { ts: string; local_time: string } {
  const d = new Date();
  const pad = (n: number, w = 2) => String(n).padStart(w, "0");
  const yyyy = d.getFullYear();
  const mm = pad(d.getMonth() + 1);
  const dd = pad(d.getDate());
  const HH = pad(d.getHours());
  const MM = pad(d.getMinutes());
  const SS = pad(d.getSeconds());
  const mmm = pad(d.getMilliseconds(), 3);
  const offsetMin = -d.getTimezoneOffset();
  const sign = offsetMin >= 0 ? "+" : "-";
  const oh = pad(Math.floor(Math.abs(offsetMin) / 60));
  const om = pad(Math.abs(offsetMin) % 60);
  return {
    ts: d.toISOString(),
    local_time: `${yyyy}-${mm}-${dd} ${HH}:${MM}:${SS}.${mmm}${sign}${oh}${om}`,
  };
}

type AgentMetaPayload = {
  traceId: string;
  runId: string;
  query: string;
  durationMs: number;
  success: boolean;
  jsonlPath: string | null;
  llmCallCount: number;
  toolCallCount: number;
  llmTotalMs: number;
  toolTotalMs: number;
  toolMaxMs: number;
  slowestToolName: string | null;
  errorCount: number;
  errorMsg: string | null;
};

type TurnState = {
  buffer: RecordedEvent[];
  query?: string;
  startedAt: number;
  done?: AgentMetaPayload;
  doneAt?: number;
};

const BUFFER_MAX = 500;
const QUERY_LEN_MAX = 30;
const DONE_TTL_MS = 120_000; // turn 结束后 meta 保留 2 分钟,够 backend 来取
const STUCK_TTL_MS = 900_000; // 未结束 turn 15 分钟强制 evict
const TURNS_HARD_CAP = 20; // turns Map 大小硬上限
const DAILY_DUMP_MAX = 300; // 当日 jsonl.gz 文件数硬上限,超出跳过不落盘
const turns = new Map<string, TurnState>();
const traceLinks = new Map<string, string>();

/** 给 webhooks/get_trace.ts 用:返回已结束 turn 的 meta 并清除,未结束返 undefined。 */
export function popDoneTurn(runId: string): AgentMetaPayload | undefined {
  const state = turns.get(runId);
  if (!state || !state.done) return undefined;
  const meta = state.done;
  turns.delete(runId);
  return meta;
}

/** 非破坏性读取已结束 turn 的 meta（不 pop），供 webhooks/agent.ts 溢出自愈检测用。
 *  刻意不清除,避免与 backend poller 的 popDoneTurn 争用(poll 在 webhook 返回后才开始)。 */
export function peekTurnMeta(runId: string): AgentMetaPayload | undefined {
  return turns.get(runId)?.done;
}

/** 已结束 turn 状态查询:done / in_progress / unknown。 */
export function getTurnStatus(
  runId: string,
): "done" | "in_progress" | "unknown" {
  const state = turns.get(runId);
  if (!state) return "unknown";
  return state.done ? "done" : "in_progress";
}

function gcExpiredTurns() {
  const now = Date.now();
  const doneCutoff = now - DONE_TTL_MS;
  const stuckCutoff = now - STUCK_TTL_MS;
  let evictedDone = 0;
  let evictedStuck = 0;
  for (const [runId, state] of turns.entries()) {
    if (state.doneAt && state.doneAt < doneCutoff) {
      turns.delete(runId);
      evictedDone++;
    } else if (!state.done && state.startedAt < stuckCutoff) {
      turns.delete(runId);
      evictedStuck++;
      console.error(
        `[miloco-trace] stuck turn evicted: runId=${runId} ` +
          `age=${Math.round((now - state.startedAt) / 1000)}s`,
      );
    }
  }
  // 硬上限兜底:按 startedAt 升序删最老的
  if (turns.size > TURNS_HARD_CAP) {
    const sorted = Array.from(turns.entries()).sort(
      (a, b) => a[1].startedAt - b[1].startedAt,
    );
    const drop = sorted.slice(0, turns.size - TURNS_HARD_CAP);
    for (const [runId] of drop) {
      turns.delete(runId);
    }
    console.error(
      `[miloco-trace] turns over hard cap ${TURNS_HARD_CAP}, evicted ${drop.length}`,
    );
  }
  if (evictedStuck > 0) {
    console.warn(
      `[miloco-trace] gc: done=${evictedDone} stuck=${evictedStuck} size=${turns.size}`,
    );
  }
}

function isDebugEnabled(): boolean {
  return existsSync(join(milocoHome(), ".debug_observability"));
}

export function registerTraceLink(runId: string, traceId: string): void {
  traceLinks.set(runId, traceId);
  // 种入 turn 占位条目,避免 backend 第一次 get_trace poll 在 llm_input 之前到达时
  // turns.get(runId) 为空 → getTurnStatus 返 "unknown" → poller 立即放弃。
  // llm_input 的 getOrInit 会复用同一条目,不影响 buffer 累积。
  if (!turns.has(runId)) {
    turns.set(runId, { buffer: [], startedAt: Date.now() });
  }
}

export function popTraceLink(runId: string): string | undefined {
  const v = traceLinks.get(runId);
  traceLinks.delete(runId);
  return v;
}

function traceRoot(): string {
  return join(milocoHome(), "trace", "agent");
}

function todayDir(): string {
  const p = toLocalParts(new Date().toISOString());
  if (!p) throw new Error("todayDir: failed to parse current Date");
  const pad2 = (n: number) => String(n).padStart(2, "0");
  return join(traceRoot(), `${p.y}${pad2(p.m)}${pad2(p.d)}`);
}

function extractUserQuery(prompt: string | undefined): string {
  if (!prompt) return "";
  const re = /\[(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s[^\]]*\]\s*/g;
  let cut = -1;
  let m: RegExpExecArray | null;
  while ((m = re.exec(prompt)) !== null) cut = m.index + m[0].length;
  return (cut >= 0 ? prompt.slice(cut) : prompt).trim();
}

function sanitizeQueryForFilename(q: string | undefined): string {
  if (!q) return "system";
  return (
    q
      .replace(/[\r\n\t]+/g, " ")
      .replace(/[/\\:*?"<>|`]/g, "_")
      .replace(/\s+/g, " ")
      .trim()
      .slice(0, QUERY_LEN_MAX) || "system"
  );
}

function getOrInit(runId: string): TurnState {
  let s = turns.get(runId);
  if (!s) {
    s = { buffer: [], startedAt: Date.now() };
    turns.set(runId, s);
  }
  return s;
}

function push(state: TurnState, ev: RecordedEvent): void {
  if (state.buffer.length < BUFFER_MAX) {
    state.buffer.push(ev);
  } else if (state.buffer.length === BUFFER_MAX) {
    state.buffer.push({
      ...nowTimestamp(),
      hook: "_truncated",
      runId: ev.runId,
      payload: { droppedAfter: BUFFER_MAX },
    });
  }
}

type ReducedMeta = {
  llmCallCount: number;
  toolCallCount: number;
  llmTotalMs: number;
  toolTotalMs: number;
  toolMaxMs: number;
  slowestToolName: string | null;
  errorCount: number;
  errorMsg: string | null;
};

function reduceMeta(buffer: RecordedEvent[]): ReducedMeta {
  let llmCallCount = 0;
  let toolCallCount = 0;
  let llmTotalMs = 0;
  let toolTotalMs = 0;
  let toolMaxMs = 0;
  let slowestToolName: string | null = null;
  let errorCount = 0;
  let errorMsg: string | null = null;

  for (const ev of buffer) {
    if (ev.hook === "llm_output") {
      llmCallCount++;
    }
    if (ev.hook === "model_call_ended") {
      const d = ev.payload?.durationMs;
      if (typeof d === "number") llmTotalMs += d;
    }
    if (ev.hook === "after_tool_call") {
      toolCallCount++;
      const d = ev.payload?.durationMs;
      if (typeof d === "number") {
        toolTotalMs += d;
        if (d > toolMaxMs) {
          toolMaxMs = d;
          slowestToolName = ev.payload?.toolName ?? null;
        }
      }
      if (ev.payload?.error) {
        errorCount++;
        errorMsg = String(ev.payload.error).slice(0, 1024);
      }
    }
  }
  return {
    llmCallCount,
    toolCallCount,
    llmTotalMs,
    toolTotalMs,
    toolMaxMs,
    slowestToolName,
    errorCount,
    errorMsg,
  };
}

export const registerTraceHooks: HookRegister = (api) => {
  console.log(
    "[miloco-trace] agent turn trace registered (debug flag checked per turn)",
  );

  api.on("llm_input", (event, ctx) => {
    const runId = event.runId || ctx.runId;
    if (!runId) return;
    const state = getOrInit(runId);
    if (!state.query) state.query = extractUserQuery(event.prompt);
    push(state, {
      ...nowTimestamp(),
      hook: "llm_input",
      runId,
      traceId: traceLinks.get(runId),
      sessionId: event.sessionId || ctx.sessionId,
      sessionKey: ctx.sessionKey,
      payload: {
        provider: event.provider,
        model: event.model,
        systemPrompt: event.systemPrompt,
        prompt: event.prompt,
        historyMessages: event.historyMessages,
        imagesCount: event.imagesCount,
      },
    });
  });

  api.on("before_tool_call", (event, ctx) => {
    const runId = event.runId || ctx.runId;
    if (!runId) return;
    const state = getOrInit(runId);
    push(state, {
      ...nowTimestamp(),
      hook: "before_tool_call",
      runId,
      traceId: traceLinks.get(runId),
      sessionId: ctx.sessionId,
      sessionKey: ctx.sessionKey,
      toolCallId: event.toolCallId,
      payload: { toolName: event.toolName, params: event.params },
    });
  });

  api.on("after_tool_call", (event, ctx) => {
    const runId = event.runId || ctx.runId;
    if (!runId) return;
    const state = turns.get(runId);
    if (!state) return;
    push(state, {
      ...nowTimestamp(),
      hook: "after_tool_call",
      runId,
      traceId: traceLinks.get(runId),
      sessionId: ctx.sessionId,
      sessionKey: ctx.sessionKey,
      toolCallId: event.toolCallId,
      payload: {
        toolName: event.toolName,
        result: event.result,
        error: event.error,
        durationMs: event.durationMs,
      },
    });
  });

  api.on("llm_output", (event, ctx) => {
    const runId = event.runId || ctx.runId;
    if (!runId) return;
    const state = turns.get(runId);
    if (!state) return;
    push(state, {
      ...nowTimestamp(),
      hook: "llm_output",
      runId,
      traceId: traceLinks.get(runId),
      sessionId: event.sessionId || ctx.sessionId,
      sessionKey: ctx.sessionKey,
      payload: {
        provider: event.provider,
        model: event.model,
        resolvedRef: event.resolvedRef,
        assistantTexts: event.assistantTexts,
        usage: event.usage,
      },
    });
  });

  api.on("model_call_ended", (event, ctx) => {
    const runId = event.runId || ctx.runId;
    if (!runId) return;
    const state = turns.get(runId);
    if (!state) return;
    push(state, {
      ...nowTimestamp(),
      hook: "model_call_ended",
      runId,
      traceId: traceLinks.get(runId),
      sessionId: event.sessionId || ctx.sessionId,
      sessionKey: ctx.sessionKey,
      callId: event.callId,
      payload: {
        provider: event.provider,
        model: event.model,
        durationMs: event.durationMs,
        outcome: event.outcome,
        errorCategory: event.errorCategory,
      },
    });
  });

  // agent_end 与 subagent_ended 的归一化 finalize:reduceMeta + 落盘 + 写 state.done。
  // 两个 hook 都可能对同一 runId fire(主 agent 路径走 agent_end,子 agent 路径走
  // subagent_ended,边界场景下偶尔两个都到),靠 state.done 幂等去重。
  async function finalizeTurn(end: {
    hookName: "agent_end" | "subagent_ended";
    runId: string;
    success: boolean;
    error?: string;
    durationMs?: number;
    endedAt?: number;
    messageCount?: number;
    sessionId?: string;
    sessionKey?: string;
  }) {
    // 早期去重:省掉无意义的 setImmediate 排队。
    let state = turns.get(end.runId);
    if (!state || state.done) return;

    // selection.js 的 fire 顺序是 agent_end (15000) → llm_output (15062),且本 handler
    // 整段无 await,如果立即 reduceMeta + 落盘,llm_output handler 还没排到执行,
    // 结果 buffer 缺 llm_output 事件、llm_call_count=0。等一个 event loop tick 让
    // llm_output 的同步 push 完成后再 finalize。subagent_ended 通常在 turn 全部
    // 收尾后才 fire(子 agent registry 路径),无此竞态,但统一走 setImmediate 不影响。
    await new Promise<void>((resolve) => setImmediate(resolve));

    // setImmediate 后再去重:另一个 end hook 已经 fire 过则跳过。
    state = turns.get(end.runId);
    if (!state || state.done) return;

    const traceId = popTraceLink(end.runId);

    push(state, {
      ...nowTimestamp(),
      hook: end.hookName,
      runId: end.runId,
      traceId,
      sessionId: end.sessionId,
      sessionKey: end.sessionKey,
      payload: {
        success: end.success,
        error: end.error,
        durationMs: end.durationMs,
        messageCount: end.messageCount,
      },
    });

    // 无 traceId 的(openclaw cron / dreaming / setup / 其他非 miloco webhook 路径)
    // 跟 miloco 业务无关,直接 GC,不落盘也不留 meta。
    if (!traceId) {
      turns.delete(end.runId);
      gcExpiredTurns();
      return;
    }

    const meta = reduceMeta(state.buffer);
    const durationMs =
      end.durationMs ??
      (end.endedAt
        ? end.endedAt - state.startedAt
        : Date.now() - state.startedAt);
    const finalSuccess = end.success;
    // turn 整体失败但 tool 都正常时,errorMsg 会是空 — 用 SDK end.error 兜底
    if (!finalSuccess && end.error && !meta.errorMsg) {
      meta.errorCount += 1;
      meta.errorMsg = String(end.error).slice(0, 1024);
    }

    let jsonlPath: string | null = null;
    if (isDebugEnabled()) {
      try {
        const dir = todayDir();
        mkdirSync(dir, { recursive: true });
        const existing = readdirSync(dir).filter((f) =>
          f.endsWith(".jsonl.gz"),
        ).length;
        if (existing >= DAILY_DUMP_MAX) {
          console.warn(
            `[miloco-trace] daily cap reached: ${existing}/${DAILY_DUMP_MAX}, ` +
              `skip dump runId=${end.runId}`,
          );
        } else {
          const filename = `${end.runId}__${sanitizeQueryForFilename(state.query)}.jsonl.gz`;
          const fullPath = join(dir, filename);
          const text = `${state.buffer.map((e) => JSON.stringify(e)).join("\n")}\n`;
          writeFileSync(fullPath, gzipSync(Buffer.from(text, "utf-8")));
          const dayName = dir.split("/").pop();
          jsonlPath = `trace/agent/${dayName}/${filename}`;
        }
      } catch (err) {
        console.error(`[miloco-trace] gzip write failed: ${err}`);
      }
    }

    // 把 meta 留在 turns Map,等 backend 通过 get_trace webhook 来取
    state.done = {
      traceId,
      runId: end.runId,
      query: state.query || "",
      durationMs,
      success: finalSuccess,
      ...meta,
      jsonlPath,
    };
    state.doneAt = Date.now();
    gcExpiredTurns();
  }

  api.on("agent_end", async (event, ctx) => {
    const runId = event.runId || ctx.runId;
    if (!runId) return;
    await finalizeTurn({
      hookName: "agent_end",
      runId,
      success: event.success ?? true,
      error: event.error,
      durationMs: event.durationMs,
      messageCount: Array.isArray(event.messages)
        ? event.messages.length
        : undefined,
      sessionId: ctx.sessionId,
      sessionKey: ctx.sessionKey,
    });
  });

  api.on("subagent_ended", async (event, ctx) => {
    // miloco 主路径:webhooks/agent.ts 走 subagent.run 派生子 agent,turn 结束 SDK
    // 在 subagent-registry.js 的 emitSubagentEndedHookOnce 里 fire 本事件。
    // outcome 缺省或 "ok" 算成功;"error" / "timeout" / "killed" / "reset" / "deleted" 算失败。
    const runId = event.runId || ctx.runId;
    if (!runId) return;
    await finalizeTurn({
      hookName: "subagent_ended",
      runId,
      success: event.outcome ? event.outcome === "ok" : !event.error,
      error: event.error,
      endedAt: event.endedAt,
      sessionKey: event.targetSessionKey,
    });
  });
};
