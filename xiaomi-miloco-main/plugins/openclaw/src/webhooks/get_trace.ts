import { getTurnStatus, popDoneTurn } from "../hooks/trace.js";
import type { WebhookEntry } from "./index.js";

interface IRequestBody {
	runId: string;
}

// backend 反向 poll:已结束 → 返回 {status:"done", ...meta} 并清除内存
//                     未结束 → 返回 {status:"in_progress"}
//                     unknown → 返回 {status:"unknown"}
export const kGetTraceWebhook: WebhookEntry<IRequestBody> = {
	name: "get_trace",
	action: ({ payload }) => {
		const { runId } = payload;
		if (!runId) return { status: "error", message: "runId required" };

		const status = getTurnStatus(runId);
		if (status !== "done") return { status };

		const meta = popDoneTurn(runId);
		if (!meta) return { status: "unknown" };
		return { status: "done", ...meta };
	},
};
