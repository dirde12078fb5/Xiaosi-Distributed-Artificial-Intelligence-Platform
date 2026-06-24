import { logger } from "../utils/logger.js";
import { runShell } from "../utils/shell.js";
import type { ServiceBuilder } from "./index.js";

export const createBackendService: ServiceBuilder = () => {
  return {
    id: "miloco-backend",
    start: async () => {
      const result = await runShell("miloco-cli", ["service", "restart"]);
      if (result.error || result.status !== 0) {
        logger.error(
          `❌ start miloco-backend, details:${JSON.stringify(result)}`,
        );
      } else {
        logger.info(
          `✅ start miloco-backend, details:${JSON.stringify(result)}`,
        );
      }
    },
    stop: async () => {
      const result = await runShell("miloco-cli", ["service", "stop"]);
      if (result.error || result.status !== 0) {
        logger.error(
          `❌ stop miloco-backend, details:${JSON.stringify(result)}`,
        );
      } else {
        logger.info(
          `✅ stop miloco-backend, details:${JSON.stringify(result)}`,
        );
      }
    },
  };
};
