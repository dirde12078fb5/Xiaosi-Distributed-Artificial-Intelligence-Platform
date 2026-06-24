/**
 * 习惯建议状态库 + `miloco_habit_suggest` 工具。
 *
 * 背景：每日 10 点的 isolated cron（扫描 agent）从家庭档案识别"值得建成任务的习惯"，
 * 主动 IM 推荐；用户在主 IM session（回应 agent，与扫描 agent 不共享上下文）认可后
 * 加载 miloco-create-task 建任务。两个 agent 通过本库的持久状态衔接。
 *
 * 设计核心：**让工具成为防骚扰的权威**——"同一时刻至多 1 条待回应 / 每天至多 1 条新推 /
 * 拒绝永不再问 / 超 7 天没回应作废" 这些闸门都由工具裁定并拒绝越界写入，不依赖
 * 扫描 agent 自觉。`asked` 严格等价"已确认送达"：扫描 agent 必须先 record(pending)，
 * miloco_im_push 返回 ok:true 之后才能 mark_asked，杜绝"通知超时却把状态翻成
 * asked → 静默死锁 7 天"或"未送达却次日重复打扰"。
 *
 * 身份（key）由扫描 agent 自己起的稳定语义 slug 决定——"是不是同一个习惯"交给 agent 判断
 * （任意语言皆可），工具不做规则匹配，只按 exact key 幂等 upsert + 拒绝复活终态条目。agent
 * 每次先 list 看已有条目，复用既有 key、跳过已拒绝/已建过的。所有读改写经进程内互斥串行化 +
 * 原子写（temp→rename），消除扫描 session 与回应同进程并发的竞态。
 */

import type { OpenClawPluginApi } from "openclaw/plugin-sdk/core";
import {
  jsonResult,
  type OpenClawPluginToolFactory,
} from "openclaw/plugin-sdk/core";
import { Type } from "typebox";
import { nowLocalIso, toLocalParts } from "../utils/time.js";
import { readJsonFileSync, writeJsonFileSync } from "../utils/io.js";
import { habitSuggestionsPath } from "./helpers.js";

// ─── 常量（节奏=克制，硬编码） ────────────────────────────────────────────

const STORE_VERSION = 1;
/** 同一时刻最多几条待回应（占用"待回应位"）。 */
const MAX_OPEN_QUESTIONS = 1;
/** 每个 Asia/Shanghai 日历日最多新推几条。 */
const MAX_NEW_ASK_PER_DAY = 1;
/** asked 超过这么多天没回应 → 过期（释放待回应位；未达 MAX_ASKS 则下次扫描复活重推）。 */
const STALE_DAYS = 7;
const STALE_MS = STALE_DAYS * 86_400_000;
/** 同一条建议累计最多主动询问几次；问满仍无果（无回应 / 未建成）即永久放弃、不再复活重推。 */
const MAX_ASKS = 3;

// ─── 类型 ──────────────────────────────────────────────────────────────────

export type SuggestionStatus =
  | "pending" // 已识别入库、尚未询问
  | "asked" // 已确认送达、等回应（占待回应位）
  | "accepted" // 用户同意、建任务中
  | "created" // 任务已建（永久终态，不再推荐）
  | "rejected" // 用户明确拒绝（永久终态，不再推荐）
  | "expired"; // 无明确回应而过期（asked 超时 / accepted 未建成）——非永久，下次 record 同 key 复活为 pending 重推；累计问满 MAX_ASKS(3) 次仍无果则永久放弃、不再复活

export type Suggestion = {
  key: string;
  title: string;
  subject: string;
  habit: string;
  suggestion: string;
  evidence?: string;
  status: SuggestionStatus;
  ask_count: number;
  created_at: string;
  updated_at: string;
  asked_at?: string;
  resolved_at?: string;
  task_id?: string;
  /** 源家庭档案条目 id（ProfileEntry.id）：追踪建议来源；建成任务后据此从档案渲染中剔除。 */
  item_id?: string;
  reason?: string;
};

export type SuggestionStore = { version: number; entries: Suggestion[] };

type ActionResult = { ok: boolean; [k: string]: unknown };
type Dispatch = { res: ActionResult; dirty: boolean };

// ─── 纯函数（便于测试） ─────────────────────────────────────────────────────

/** 部署时区视角的日历日 key（YYYY-MM-DD），用于"今天是否已问过"。 */
export function localDateKey(iso: string): string {
  const p = toLocalParts(iso);
  if (!p) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${p.y}-${pad(p.m)}-${pad(p.d)}`;
}

function elapsedMs(fromIso: string, nowIso: string): number {
  const a = Date.parse(fromIso);
  const b = Date.parse(nowIso);
  if (Number.isNaN(a) || Number.isNaN(b)) return 0;
  return b - a;
}

/**
 * 惰性过期：无明确回应的在途条目超 7 天 → expired。返回是否有变更。
 * - `asked` 超 7 天：用户始终没回应（按 asked_at 判龄）。
 * - `accepted` 超 7 天：用户答应了但任务始终没建成（create-task 当轮反问/中断/拒绝、
 *   未返回 task_id；按 resolved_at=接受时刻判龄）。
 * expired **非永久终态**：释放待回应位，且下次扫描 record 同 key 会复活为 pending 重新推荐
 * （只有用户明确 rejected / 已 created 才永久不再提）。
 */
export function applyExpiry(store: SuggestionStore, nowIso: string): boolean {
  let changed = false;
  for (const e of store.entries) {
    const stamp =
      e.status === "asked"
        ? e.asked_at
        : e.status === "accepted"
          ? e.resolved_at
          : undefined;
    if (stamp && elapsedMs(stamp, nowIso) > STALE_MS) {
      e.status = "expired";
      e.resolved_at = nowIso;
      e.reason = `${STALE_DAYS} 天无明确回应自动过期（可重新推荐）`;
      e.updated_at = nowIso;
      changed = true;
    }
  }
  return changed;
}

function askedToday(store: SuggestionStore, nowIso: string): boolean {
  const today = localDateKey(nowIso);
  return store.entries.some(
    (e) => e.asked_at && localDateKey(e.asked_at) === today,
  );
}

function openCount(store: SuggestionStore): number {
  return store.entries.filter((e) => e.status === "asked").length;
}

/** 此刻是否还能发起新询问（待回应位未满 + 今天还没问过）。 */
export function canAskNow(
  store: SuggestionStore,
  nowIso: string,
): {
  can: boolean;
  reason?: string;
} {
  if (openCount(store) >= MAX_OPEN_QUESTIONS) {
    return { can: false, reason: "已有待回应的建议，本次不再打扰" };
  }
  if (MAX_NEW_ASK_PER_DAY > 0 && askedToday(store, nowIso)) {
    return { can: false, reason: "今天已经推荐过一条，明天再说" };
  }
  return { can: true };
}

// ─── 存取 ──────────────────────────────────────────────────────────────────

function loadStore(): SuggestionStore {
  const raw = readJsonFileSync<SuggestionStore>(habitSuggestionsPath());
  if (raw && Array.isArray(raw.entries)) {
    return { version: raw.version ?? STORE_VERSION, entries: raw.entries };
  }
  return { version: STORE_VERSION, entries: [] };
}

function saveStore(store: SuggestionStore): void {
  writeJsonFileSync(habitSuggestionsPath(), store, { pretty: true });
}

/** injection.ts 用：未作废的待回应条目（不写盘，作废留给下次工具调用持久化）。 */
export function loadOpenQuestions(nowIso = nowLocalIso()): Suggestion[] {
  const store = loadStore();
  return store.entries.filter(
    (e) =>
      e.status === "asked" &&
      e.asked_at &&
      elapsedMs(e.asked_at, nowIso) <= STALE_MS,
  );
}

// ─── 进程内互斥 ────────────────────────────────────────────────────────────

let writeLock: Promise<unknown> = Promise.resolve();

function withLock<T>(fn: () => T): Promise<T> {
  const run = writeLock.then(() => fn());
  // 串成链：无论成败都让后续排队任务继续。
  writeLock = run.then(
    () => undefined,
    () => undefined,
  );
  return run;
}

// ─── action 实现 ───────────────────────────────────────────────────────────

function str(v: unknown): string {
  return typeof v === "string" ? v.trim() : "";
}

function view(e: Suggestion) {
  return {
    key: e.key,
    title: e.title,
    subject: e.subject,
    habit: e.habit,
    suggestion: e.suggestion,
    status: e.status,
    asked_at: e.asked_at,
    task_id: e.task_id,
    item_id: e.item_id,
  };
}

function doList(store: SuggestionStore, now: string): Dispatch {
  const gate = canAskNow(store, now);
  const open = store.entries.filter((e) => e.status === "asked");
  const pending = store.entries.filter((e) => e.status === "pending");
  const counts: Record<string, number> = {};
  for (const e of store.entries) counts[e.status] = (counts[e.status] ?? 0) + 1;
  return {
    dirty: false,
    res: {
      ok: true,
      can_ask_now: gate.can,
      blocked_reason: gate.reason,
      open_questions: open.map(view), // 回应 agent 用：用户在回应哪条
      askable_pending: pending.map(view), // 扫描 agent 用：可挑 1 条去询问
      // 全量条目（含已拒绝/已建/已作废）——你据此判断"是不是同一个习惯"、复用既有 key、跳过终态
      entries: store.entries.map(view),
      counts,
    },
  };
}

function doRecord(
  store: SuggestionStore,
  now: string,
  p: Record<string, unknown>,
): Dispatch {
  const key = str(p.key);
  const subject = str(p.subject) || "shared";
  const habit = str(p.habit);
  const suggestion = str(p.suggestion);
  const title = str(p.title) || habit.slice(0, 24);
  if (!key || !habit || !suggestion) {
    return {
      dirty: false,
      res: { ok: false, error: "record 需要 key / habit / suggestion" },
    };
  }
  const existing = store.entries.find((e) => e.key === key);
  if (existing) {
    // 命中既有 key（由 agent 判断为同一习惯），按状态分三类处理，永不新建副本：
    // 1) rejected / created：永久抑制——用户明确拒绝过、或已建成任务，绝不重提。
    if (existing.status === "rejected" || existing.status === "created") {
      return {
        dirty: false,
        res: {
          ok: true,
          key,
          status: existing.status,
          deduped: true,
          note: `已存在且状态为 ${existing.status}，永久不再推荐`,
        },
      };
    }
    // 2) expired：无明确回应而过期。累计问满 MAX_ASKS 次仍无果 → 永久放弃、不再复活；
    //    否则复活为 pending 重新纳入推荐（保留 ask_count 作再推计数）。
    if (existing.status === "expired") {
      if (existing.ask_count >= MAX_ASKS) {
        return {
          dirty: false,
          res: {
            ok: true,
            key,
            status: "expired",
            deduped: true,
            note: `已主动询问 ${existing.ask_count} 次仍无果，放弃、不再推荐`,
          },
        };
      }
      existing.status = "pending";
      existing.asked_at = undefined;
      existing.resolved_at = undefined;
      existing.reason = undefined;
      existing.title = title;
      existing.subject = subject;
      existing.habit = habit;
      existing.suggestion = suggestion;
      existing.evidence = str(p.evidence) || existing.evidence;
      existing.item_id = str(p.item_id) || existing.item_id;
      existing.updated_at = now;
      return {
        dirty: true,
        res: {
          ok: true,
          key,
          status: "pending",
          deduped: true,
          revived: true,
          note: `过期未答复，已重新纳入推荐候选（将是第 ${existing.ask_count + 1} 次询问，上限 ${MAX_ASKS}）`,
        },
      };
    }
    // 3) pending / asked / accepted：在途，不打扰；仅 pending 刷新展示字段。
    let dirty = false;
    if (existing.status === "pending") {
      existing.title = title;
      existing.subject = subject;
      existing.habit = habit;
      existing.suggestion = suggestion;
      existing.evidence = str(p.evidence) || existing.evidence;
      existing.item_id = str(p.item_id) || existing.item_id;
      existing.updated_at = now;
      dirty = true;
    }
    return {
      dirty,
      res: {
        ok: true,
        key,
        status: existing.status,
        deduped: true,
        note:
          existing.status === "pending"
            ? "已存在待处理候选（已刷新）"
            : `已存在且状态为 ${existing.status}`,
      },
    };
  }
  const entry: Suggestion = {
    key,
    title,
    subject,
    habit,
    suggestion,
    evidence: str(p.evidence) || undefined,
    item_id: str(p.item_id) || undefined,
    status: "pending",
    ask_count: 0,
    created_at: now,
    updated_at: now,
  };
  store.entries.push(entry);
  return {
    dirty: true,
    res: { ok: true, key, status: "pending", deduped: false },
  };
}

function doMarkAsked(
  store: SuggestionStore,
  now: string,
  p: Record<string, unknown>,
): Dispatch {
  const key = str(p.key);
  const e = store.entries.find((x) => x.key === key);
  if (!e)
    return { dirty: false, res: { ok: false, error: "找不到该建议 key" } };
  if (e.status !== "pending") {
    return {
      dirty: false,
      res: {
        ok: false,
        status: e.status,
        error: `状态为 ${e.status}，不能标记为已询问`,
      },
    };
  }
  const gate = canAskNow(store, now);
  if (!gate.can) {
    return {
      dirty: false,
      res: { ok: false, blocked_reason: gate.reason, error: gate.reason },
    };
  }
  e.status = "asked";
  e.asked_at = now;
  e.updated_at = now;
  e.ask_count += 1;
  return { dirty: true, res: { ok: true, key, status: "asked" } };
}

function doResolve(
  store: SuggestionStore,
  now: string,
  p: Record<string, unknown>,
): Dispatch {
  const key = str(p.key);
  const outcome = str(p.outcome);
  const e = store.entries.find((x) => x.key === key);
  if (!e)
    return { dirty: false, res: { ok: false, error: "找不到该建议 key" } };
  const from = e.status;

  if (outcome === "rejected") {
    if (from === "created" || from === "expired") {
      return {
        dirty: false,
        res: { ok: false, status: from, error: `状态为 ${from}，不能拒绝` },
      };
    }
    e.status = "rejected";
    e.reason = str(p.reason) || undefined;
    e.resolved_at = now;
    e.updated_at = now;
    return { dirty: true, res: { ok: true, key, status: "rejected" } };
  }

  if (outcome === "accepted") {
    // accepted 仅从 asked 流转（注入只暴露 asked，pending→accepted 不可达；显式收紧与文档对齐）。
    if (from !== "asked") {
      return {
        dirty: false,
        res: {
          ok: false,
          status: from,
          error: `状态为 ${from}，不能接受（需处于 asked）`,
        },
      };
    }
    e.status = "accepted";
    e.resolved_at = now;
    e.updated_at = now;
    return {
      dirty: true,
      res: {
        ok: true,
        key,
        status: "accepted",
        suggestion: e.suggestion,
        next: "加载 miloco-create-task 据此建任务；建成后再次 resolve outcome=created 并回填 task_id",
      },
    };
  }

  if (outcome === "created") {
    // created 仅从 accepted（标准路径）或 asked（用户当轮接受并直接建好的快捷路径）流转。
    // 用白名单而非黑名单：显式排除 pending→created（从未询问过的条目不该凭空变成已建任务）及一切终态，
    // 与文档状态机 pending → asked →（accepted → created）保持一致。
    if (from !== "accepted" && from !== "asked") {
      return {
        dirty: false,
        res: {
          ok: false,
          status: from,
          error: `状态为 ${from}，不能标记为已建（需先 accepted，或处于 asked）`,
        },
      };
    }
    e.status = "created";
    e.task_id = str(p.task_id) || e.task_id;
    e.resolved_at = now;
    e.updated_at = now;
    return {
      dirty: true,
      res: { ok: true, key, status: "created", task_id: e.task_id },
    };
  }

  return {
    dirty: false,
    res: { ok: false, error: `未知 outcome：${outcome}` },
  };
}

/**
 * 核心调度（load → 惰性作废 → dispatch → 按需写盘），全程持锁串行化。
 * 导出供工具 execute 与测试共用；`nowOverride` 仅测试注入。
 */
export function applyHabitAction(
  input: Record<string, unknown>,
  nowOverride?: string,
): Promise<ActionResult> {
  return withLock(() => {
    const now = nowOverride ?? nowLocalIso();
    const store = loadStore();
    const expired = applyExpiry(store, now);
    const action = str(input.action);
    let out: Dispatch;
    switch (action) {
      case "list":
        out = doList(store, now);
        break;
      case "record":
        out = doRecord(store, now, input);
        break;
      case "mark_asked":
        out = doMarkAsked(store, now, input);
        break;
      case "resolve":
        out = doResolve(store, now, input);
        break;
      default:
        out = {
          dirty: false,
          res: { ok: false, error: `未知 action：${action}` },
        };
    }
    if (expired || out.dirty) saveStore(store);
    return out.res;
  });
}

// ─── 工具注册 ──────────────────────────────────────────────────────────────

const TOOL_DESCRIPTION = [
  "习惯建议候选库的读写入口（防骚扰状态机）。配合 miloco-habit-suggest skill 使用。",
  "状态流转：pending → asked →（accepted → created）| rejected | expired。",
  "",
  "action 取值：",
  "- list：读候选库现状。返回 can_ask_now（此刻能否发起新询问，工具裁定）、open_questions（正在等用户回应的条目）、",
  "  askable_pending（可挑去询问的候选）、entries（全量条目含已拒绝/已建/已作废——你据此判断是不是同一个习惯、复用既有 key、跳过终态）。",
  "- record：把识别到的一条习惯登记为候选（status=pending）。传你起的稳定语义 key + subject/habit/suggestion(/title/evidence/item_id)；item_id 填该习惯所依据的家庭档案条目 id，用于追踪来源 + 建成任务后从档案渲染中剔除。",
  "  同一 key 幂等：已 rejected/created 的只返回既有、永久不再推；过期（expired，无明确回应）的会复活为 pending 重新推荐，但累计问满 3 次仍无果即永久放弃；在途（pending/asked/accepted）的原样返回。是否同一习惯由你判断——务必先 list 复用既有 key。",
  "- mark_asked：把某条 pending 翻成 asked。**必须在 miloco_im_push 返回 ok:true（确认送达）之后才调**；",
  "  工具会再次校验防骚扰闸门，越界（已有待回应 / 今天已问过 / 状态不对）直接返回 ok:false。",
  "- resolve：用户回应后落地。outcome=created（任务建成、回填 task_id，终态）/ rejected（拒绝，终态永不再问）/",
  "  accepted（可选中间态：仅当需跨轮分步建任务时先标「已同意」；正常流程应**先建成再 resolve(created)**，未完成的 accepted 会自动作废、不永久滞留）。",
].join("\n");

export function registerHabitSuggestTool(api: OpenClawPluginApi): void {
  const factory: OpenClawPluginToolFactory = (_ctx) => ({
    name: "miloco_habit_suggest",
    label: "Habit suggestion store",
    description: TOOL_DESCRIPTION,
    parameters: Type.Object({
      action: Type.Union(
        [
          Type.Literal("list"),
          Type.Literal("record"),
          Type.Literal("mark_asked"),
          Type.Literal("resolve"),
        ],
        { description: "操作类型：list / record / mark_asked / resolve" },
      ),
      key: Type.Optional(
        Type.String({
          description:
            "建议的稳定语义 key，由你自己起（如 wanglei_sleep_dim_light）。record/mark_asked/resolve 都用它定位；同一习惯务必复用 list 里已有的 key，避免重复或复活已拒绝项",
        }),
      ),
      subject: Type.Optional(
        Type.String({
          description:
            "习惯主体：成员名（如 王磊）；全家公共填 shared。record 用",
        }),
      ),
      habit: Type.Optional(
        Type.String({
          description:
            "观察到的习惯（规范短句，如『王磊 傍晚约19点健身约30分钟』）。record 用，作为条目展示与你日后判断是否同一习惯的依据",
        }),
      ),
      suggestion: Type.Optional(
        Type.String({
          description:
            "要推荐给用户的任务点子（自然语言，认可后即据此建任务）。record 用",
        }),
      ),
      title: Type.Optional(
        Type.String({
          description: "一句话标题（可选，缺省截取 habit）。record 用",
        }),
      ),
      evidence: Type.Optional(
        Type.String({
          description: "依据（档案条目/出现频率，可选）。record 用",
        }),
      ),
      item_id: Type.Optional(
        Type.String({
          description:
            "该习惯所依据的家庭档案条目 id（来自 home-profile list 的 id 字段）。record 用：追踪建议来源，建成任务后据此把该条目从家庭档案渲染中剔除",
        }),
      ),
      outcome: Type.Optional(
        Type.Union(
          [
            Type.Literal("accepted"),
            Type.Literal("rejected"),
            Type.Literal("created"),
          ],
          {
            description: "resolve 的结果：accepted / rejected / created",
          },
        ),
      ),
      task_id: Type.Optional(
        Type.String({ description: "outcome=created 时回填的任务 id" }),
      ),
      reason: Type.Optional(
        Type.String({ description: "outcome=rejected 时的简短原因（可选）" }),
      ),
    }),
    async execute(_toolCallId, params) {
      const input =
        typeof params === "object" && params !== null && !Array.isArray(params)
          ? (params as Record<string, unknown>)
          : {};
      const result = await applyHabitAction(input);
      return jsonResult(result);
    },
  });

  api.registerTool(factory, { name: "miloco_habit_suggest" });
}
