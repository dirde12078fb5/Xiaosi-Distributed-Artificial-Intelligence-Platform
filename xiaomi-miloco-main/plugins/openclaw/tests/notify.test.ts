import { describe, expect, it, vi } from "vitest";

const getRuntimeConfigMock = vi.fn();
const getPluginConfigMock = vi.fn();

vi.mock("../src/config.js", () => ({
  getRuntimeConfig: (...args: unknown[]) => getRuntimeConfigMock(...args),
  getPluginConfig: (...args: unknown[]) => getPluginConfigMock(...args),
}));

import {
  notifyOwner,
  resolveNotifyTarget,
  toTimestamp,
} from "../src/tools/notify.js";

type SubagentMock = {
  run: ReturnType<typeof vi.fn>;
  waitForRun: ReturnType<typeof vi.fn>;
};

function makeApi(
  store: Record<string, Record<string, unknown>>,
  subagent?: SubagentMock,
) {
  return {
    runtime: {
      agent: {
        session: {
          resolveStorePath: vi.fn(() => "/fake/store"),
          loadSessionStore: vi.fn(() => store),
        },
      },
      subagent,
    },
  } as any;
}

function makeSubagent(
  waitResult: Record<string, unknown> = { status: "ok" },
): SubagentMock {
  return {
    run: vi.fn(async () => ({ runId: "run-1" })),
    waitForRun: vi.fn(async () => waitResult),
  };
}

// ─── toTimestamp ─────────────────────────────────────────────────────────────

describe("toTimestamp", () => {
  it("number → passthrough", () => {
    expect(toTimestamp(1716700000000)).toBe(1716700000000);
  });

  it("valid ISO string → epoch ms", () => {
    const iso = "2026-05-14T10:00:00Z";
    expect(toTimestamp(iso)).toBe(Date.parse(iso));
  });

  it("invalid string → 0", () => {
    expect(toTimestamp("not-a-date")).toBe(0);
  });

  it("undefined → 0", () => {
    expect(toTimestamp(undefined)).toBe(0);
  });

  it("null → 0", () => {
    expect(toTimestamp(null)).toBe(0);
  });

  it("object → 0", () => {
    expect(toTimestamp({})).toBe(0);
  });
});

// ─── resolveNotifyTarget ────────────────────────────────────────────────────

describe("resolveNotifyTarget", () => {
  it("已配置 notifySessionKey 且有效 → needsBind: false", () => {
    const store = {
      "wechat:abc": {
        lastChannel: "wechat",
        lastTo: "user123",
        lastAccountId: "acc1",
        lastThreadId: "t1",
      },
    };
    const api = makeApi(store);
    getRuntimeConfigMock.mockReturnValue({ session: {} });
    getPluginConfigMock.mockReturnValue({ notifySessionKey: "wechat:abc" });

    const result = resolveNotifyTarget(api);
    expect(result.needsBind).toBe(false);
    expect(result.target).toEqual({
      channel: "wechat",
      to: "user123",
      accountId: "acc1",
      threadId: "t1",
      sessionKey: "wechat:abc",
    });
    expect(result.bindReason).toBeUndefined();
  });

  it("已配置但 session 无 lastTo → fallback + bindReason: configured_but_invalid", () => {
    const store = {
      "wechat:abc": { lastChannel: "wechat" },
      "telegram:xyz": {
        lastChannel: "telegram",
        lastTo: "tg_user",
        lastInteractionAt: 1000,
      },
    };
    const api = makeApi(store);
    getRuntimeConfigMock.mockReturnValue({ session: {} });
    getPluginConfigMock.mockReturnValue({ notifySessionKey: "wechat:abc" });

    const result = resolveNotifyTarget(api);
    expect(result.needsBind).toBe(true);
    expect(result.bindReason).toBe("configured_but_invalid");
    expect(result.target?.channel).toBe("telegram");
    expect(result.target?.sessionKey).toBe("telegram:xyz");
  });

  it("已配置但 session 不存在 → fallback + bindReason: configured_but_invalid", () => {
    const store = {
      "telegram:xyz": {
        lastChannel: "telegram",
        lastTo: "tg_user",
        lastInteractionAt: 2000,
      },
    };
    const api = makeApi(store);
    getRuntimeConfigMock.mockReturnValue({ session: {} });
    getPluginConfigMock.mockReturnValue({
      notifySessionKey: "wechat:nonexist",
    });

    const result = resolveNotifyTarget(api);
    expect(result.needsBind).toBe(true);
    expect(result.bindReason).toBe("configured_but_invalid");
    expect(result.target?.sessionKey).toBe("telegram:xyz");
  });

  it("未配置 → fallback 到最近活跃 + bindReason: not_configured", () => {
    const store = {
      "wechat:old": {
        lastChannel: "wechat",
        lastTo: "user_old",
        lastInteractionAt: 1000,
      },
      "telegram:new": {
        lastChannel: "telegram",
        lastTo: "user_new",
        lastInteractionAt: 5000,
      },
    };
    const api = makeApi(store);
    getRuntimeConfigMock.mockReturnValue({ session: {} });
    getPluginConfigMock.mockReturnValue({});

    const result = resolveNotifyTarget(api);
    expect(result.needsBind).toBe(true);
    expect(result.bindReason).toBe("not_configured");
    expect(result.target?.channel).toBe("telegram");
    expect(result.target?.sessionKey).toBe("telegram:new");
  });

  it("未配置 + 用 updatedAt 作为 fallback 排序依据", () => {
    const store = {
      "a:1": {
        lastChannel: "a",
        lastTo: "u1",
        updatedAt: "2026-05-10T10:00:00Z",
      },
      "b:2": {
        lastChannel: "b",
        lastTo: "u2",
        updatedAt: "2026-05-14T10:00:00Z",
      },
    };
    const api = makeApi(store);
    getRuntimeConfigMock.mockReturnValue({ session: {} });
    getPluginConfigMock.mockReturnValue({});

    const result = resolveNotifyTarget(api);
    expect(result.target?.sessionKey).toBe("b:2");
  });

  it("store 为空 → target: null", () => {
    const api = makeApi({});
    getRuntimeConfigMock.mockReturnValue({ session: {} });
    getPluginConfigMock.mockReturnValue({});

    const result = resolveNotifyTarget(api);
    expect(result.target).toBeNull();
    expect(result.needsBind).toBe(true);
    expect(result.bindReason).toBe("not_configured");
  });

  it("store 中所有 entry 无 lastTo → target: null", () => {
    const store = {
      "a:1": { lastChannel: "wechat" },
      "b:2": { lastChannel: "telegram", lastInteractionAt: 9999 },
    };
    const api = makeApi(store);
    getRuntimeConfigMock.mockReturnValue({ session: {} });
    getPluginConfigMock.mockReturnValue({});

    const result = resolveNotifyTarget(api);
    expect(result.target).toBeNull();
  });

  it("多 session 同 lastInteractionAt → 取最后遍历的（稳定性）", () => {
    const store = {
      "a:1": {
        lastChannel: "a",
        lastTo: "u1",
        lastInteractionAt: 3000,
      },
      "b:2": {
        lastChannel: "b",
        lastTo: "u2",
        lastInteractionAt: 3000,
      },
    };
    const api = makeApi(store);
    getRuntimeConfigMock.mockReturnValue({ session: {} });
    getPluginConfigMock.mockReturnValue({});

    const result = resolveNotifyTarget(api);
    // >= means later entry wins when equal
    expect(result.target?.sessionKey).toBe("b:2");
  });
});

// ─── notifyOwner ─────────────────────────────────────────────────────────────

describe("notifyOwner", () => {
  const boundStore = {
    "wechat:abc": { lastChannel: "wechat", lastTo: "user123" },
  };
  const unboundStore = {
    "telegram:xyz": {
      lastChannel: "telegram",
      lastTo: "tg_user",
      lastInteractionAt: 1000,
    },
  };

  it("无任何可用 channel → ok:false，不调用 subagent", async () => {
    const subagent = makeSubagent();
    const api = makeApi({}, subagent);
    getRuntimeConfigMock.mockReturnValue({ session: {} });
    getPluginConfigMock.mockReturnValue({});

    const result = await notifyOwner(api, "hello");
    expect(result.ok).toBe(false);
    expect(result.error).toContain("no available IM channel");
    expect(subagent.run).not.toHaveBeenCalled();
  });

  it("未绑定且未提供 bindHint → 不发送，返回 needsBind 交回 agent", async () => {
    const subagent = makeSubagent();
    const api = makeApi(unboundStore, subagent);
    getRuntimeConfigMock.mockReturnValue({ session: {} });
    getPluginConfigMock.mockReturnValue({});

    const result = await notifyOwner(api, "提醒该吃药了");
    expect(result.ok).toBe(false);
    expect(result.needsBind).toBe(true);
    expect(result.bindReason).toBe("not_configured");
    expect(result.fallbackChannel).toBe("telegram");
    // 返回里自带可翻译的 bindHint 范例 + 明确的下一步指令（不依赖 agent 去加载 skill）
    expect(result.bindHintExample).toContain("Miloco 通知频道");
    expect(result.nextAction).toContain("bindHint");
    expect(subagent.run).not.toHaveBeenCalled();
  });

  it("配置失效且未提供 bindHint → bindReason: configured_but_invalid，不发送", async () => {
    const subagent = makeSubagent();
    const api = makeApi(unboundStore, subagent);
    getRuntimeConfigMock.mockReturnValue({ session: {} });
    getPluginConfigMock.mockReturnValue({ notifySessionKey: "gone:404" });

    const result = await notifyOwner(api, "msg");
    expect(result.ok).toBe(false);
    expect(result.needsBind).toBe(true);
    expect(result.bindReason).toBe("configured_but_invalid");
    expect(subagent.run).not.toHaveBeenCalled();
  });

  it("未绑定 + 提供 bindHint → 投递到 fallback，fallback:true，正文拼接 bindHint", async () => {
    const subagent = makeSubagent({ status: "ok" });
    const api = makeApi(unboundStore, subagent);
    getRuntimeConfigMock.mockReturnValue({ session: {} });
    getPluginConfigMock.mockReturnValue({});

    const result = await notifyOwner(api, "该吃药了", {
      bindHint: "回复「绑定通知频道」可固定到此",
    });
    expect(result.ok).toBe(true);
    expect(result.channel).toBe("telegram");
    expect(result.fallback).toBe(true);
    expect(subagent.run).toHaveBeenCalledTimes(1);

    const arg = subagent.run.mock.calls[0][0] as { message: string };
    expect(arg.message).toBe(
      "<miloco-notification>该吃药了\n---\n回复「绑定通知频道」可固定到此</miloco-notification>",
    );
  });

  it("空白 bindHint 视为未提供 → 不发送", async () => {
    const subagent = makeSubagent();
    const api = makeApi(unboundStore, subagent);
    getRuntimeConfigMock.mockReturnValue({ session: {} });
    getPluginConfigMock.mockReturnValue({});

    const result = await notifyOwner(api, "msg", { bindHint: "   " });
    expect(result.ok).toBe(false);
    expect(result.needsBind).toBe(true);
    expect(subagent.run).not.toHaveBeenCalled();
  });

  it("已绑定且有效 → 正常发送、无 fallback，且忽略 bindHint", async () => {
    const subagent = makeSubagent({ status: "ok" });
    const api = makeApi(boundStore, subagent);
    getRuntimeConfigMock.mockReturnValue({ session: {} });
    getPluginConfigMock.mockReturnValue({ notifySessionKey: "wechat:abc" });

    const result = await notifyOwner(api, "正文", {
      bindHint: "不应出现的引导语",
    });
    expect(result.ok).toBe(true);
    expect(result.channel).toBe("wechat");
    expect(result.fallback).toBeUndefined();

    const arg = subagent.run.mock.calls[0][0] as { message: string };
    expect(arg.message).toBe("<miloco-notification>正文</miloco-notification>");
    expect(arg.message).not.toContain("不应出现的引导语");
    // 回归保护：工具不再注入任何写死的中文提示
    expect(arg.message).not.toContain("提示：");
  });

  it("subagent 投递失败 → ok:false 带 error", async () => {
    const subagent = makeSubagent({ status: "error", error: "boom" });
    const api = makeApi(boundStore, subagent);
    getRuntimeConfigMock.mockReturnValue({ session: {} });
    getPluginConfigMock.mockReturnValue({ notifySessionKey: "wechat:abc" });

    const result = await notifyOwner(api, "正文");
    expect(result.ok).toBe(false);
    expect(result.error).toContain("subagent delivery failed");
    expect(result.error).toContain("boom");
  });
});
