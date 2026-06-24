import type { OpenClawPluginApi } from "openclaw/plugin-sdk";
import { registerHomeProfileScheduler } from "./scheduler.js";
import { registerHabitSuggestTool } from "./suggestions.js";

export function registerHomeProfile(api: OpenClawPluginApi): void {
  registerHomeProfileScheduler(api);
  registerHabitSuggestTool(api);
}
