import type { OpenClawPluginApi } from "openclaw/plugin-sdk";

/**
 * 日志工具类：转发到 OpenClaw 宿主 logger。
 * 不再独立写文件——宿主已统一管理 plugin 日志落盘 / rotate。
 */
class Logger {
  private api?: OpenClawPluginApi;

  init(api: OpenClawPluginApi) {
    this.api = api;
  }

  debug = (message: string): void => {
    this._log("DEBUG", message);
  };

  info = (message: string): void => {
    this._log("INFO", message);
  };

  warn = (message: string): void => {
    this._log("WARN", message);
  };

  error = (message: string): void => {
    this._log("ERROR", message);
  };

  private _log(level: string, message: string): void {
    if (!this.api) {
      return;
    }
    const logLevel = level.toLowerCase() as keyof typeof this.api.logger;
    this.api.logger[logLevel]?.(`miloco [${level}]: ${message}`);
  }
}

export const logger = new Logger();
