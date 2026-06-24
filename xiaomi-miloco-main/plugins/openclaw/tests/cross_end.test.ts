import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import type { OpenClawPluginApi } from "openclaw/plugin-sdk";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

const FIXTURE = path.resolve(
  __dirname,
  "../../..",
  "backend",
  "miloco",
  "tests",
  "fixtures",
  "config.sample.json",
);

async function makeApi(
  pluginConfig: Record<string, unknown> = {},
): Promise<OpenClawPluginApi> {
  const { kPluginId } = await import("../src/config.js");
  return {
    runtime: {
      config: {
        current: () => ({
          plugins: { entries: { [kPluginId]: { config: pluginConfig } } },
        }),
      },
    },
    config: {},
  } as unknown as OpenClawPluginApi;
}

/**
 * 与 cli/tests/test_cross_end_alignment.py、backend/miloco/tests/test_cross_end_alignment.py
 * 配对：同一份 fixture 在三端加载后字段语义完全一致。
 *
 * 这里用空 plugin 配置调用 loadSharedConfig(api)，确保插件侧不覆盖 fixture；
 * fixture 的 agent.webhook_url 与默认 gateway URL 一致，auth_bearer 已预置，因此
 * ensureAgentEssentials 的写入结果与 fixture 相同。
 */
describe("cross-end alignment", () => {
  let origHome: string | undefined;
  let origGatewayToken: string | undefined;
  let tmpHome: string;

  beforeEach(() => {
    origHome = process.env.MILOCO_HOME;
    origGatewayToken = process.env.OPENCLAW_GATEWAY_TOKEN;
    tmpHome = mkdtempSync(path.join(tmpdir(), "miloco-home-"));
    writeFileSync(
      path.join(tmpHome, "config.json"),
      readFileSync(FIXTURE, "utf-8"),
    );
    process.env.MILOCO_HOME = tmpHome;
    // ensureAgentEssentials resolves auth from env — match the fixture value
    process.env.OPENCLAW_GATEWAY_TOKEN = "fixture-gateway-token";
  });

  afterEach(() => {
    if (origHome === undefined) delete process.env.MILOCO_HOME;
    else process.env.MILOCO_HOME = origHome;
    if (origGatewayToken === undefined)
      delete process.env.OPENCLAW_GATEWAY_TOKEN;
    else process.env.OPENCLAW_GATEWAY_TOKEN = origGatewayToken;
    rmSync(tmpHome, { recursive: true, force: true });
  });

  it("loadSharedConfig 加载 fixture 后字段与 Python 侧一致", async () => {
    const { loadSharedConfig } = await import("../src/miloco/config.js");
    const expected = JSON.parse(readFileSync(FIXTURE, "utf-8"));
    const api = await makeApi();
    const cfg = loadSharedConfig(api);

    expect(cfg.debug).toBe(expected.debug);
    expect(cfg.server.url).toBe(expected.server.url);
    expect(cfg.server.token).toBe(expected.server.token);
    expect(cfg.server.tls_verify).toBe(expected.server.tls_verify);
    expect(cfg.server.python_bin).toBe(expected.server.python_bin);
    expect(cfg.agent.webhook_url).toBe(expected.agent.webhook_url);
    expect(cfg.agent.auth_bearer).toBe(expected.agent.auth_bearer);
    expect(cfg.model.omni.model).toBe(expected.model.omni.model);
    expect(cfg.model.omni.base_url).toBe(expected.model.omni.base_url);
    expect(cfg.model.omni.api_key).toBe(expected.model.omni.api_key);
  });
});
