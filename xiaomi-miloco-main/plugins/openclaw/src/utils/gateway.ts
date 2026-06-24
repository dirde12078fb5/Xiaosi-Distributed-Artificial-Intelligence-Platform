import type { OpenClawPluginApi } from "openclaw/plugin-sdk";

export function resolveGatewayUrl(api: OpenClawPluginApi) {
  const cfg = api.config;
  const scheme = cfg.gateway?.tls?.enabled ? "https" : "http";
  const port =
    Number(process.env.OPENCLAW_GATEWAY_PORT) ||
    api.config.gateway?.port ||
    18789;
  const customHost = cfg.gateway?.customBindHost?.trim();
  const host =
    cfg.gateway?.bind === "custom" && customHost ? customHost : "127.0.0.1";
  const url = `${scheme}://${host}:${port}`;
  return url;
}
