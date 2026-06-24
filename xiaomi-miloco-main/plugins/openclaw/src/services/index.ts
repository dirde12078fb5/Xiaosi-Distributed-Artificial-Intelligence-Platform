import type { OpenClawPluginApi } from "openclaw/plugin-sdk";
import { getPluginConfig, type MilocoPluginConfig } from "../config.js";
import { createBackendService } from "./backend.js";

type OpenClawPluginService = Parameters<
  OpenClawPluginApi["registerService"]
>[0];

export type ServiceBuilder = (
  api: OpenClawPluginApi,
  config: MilocoPluginConfig,
) => OpenClawPluginService | undefined;

const kBuilders: ServiceBuilder[] = [
  createBackendService, // 启动 Python 后端
];

export function registerServices(api: OpenClawPluginApi) {
  const config = getPluginConfig(api);
  for (const builder of kBuilders) {
    const service = builder(api, config);
    if (service) {
      api.registerService(service);
    }
  }
}
