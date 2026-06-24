import { loadOpenQuestions } from "./suggestions.js";

/**
 * 待回应习惯建议的注入块。仅在确有未作废 `asked` 条目时返回，否则空串（正常日子完全静默）。
 *
 * 由 hooks/prompt.ts 在 full profile 的 append 段调用（habit-suggest cron 推到用户 bind 的 IM
 * 会话，回应落在同一 full 会话；本块补齐"用户这条『好』在回应什么"的指代，并把它路由到
 * miloco_habit_suggest(resolve)，避免肯定语被当成无意图消息丢弃）。
 */
export function buildPendingSuggestionBlock(): string {
  let open: ReturnType<typeof loadOpenQuestions>;
  try {
    open = loadOpenQuestions();
  } catch {
    return "";
  }
  if (open.length === 0) return "";

  const items = open
    .map((e) => `- [${e.key}] ${e.title}：${e.suggestion}`)
    .join("\n");

  return `## 等用户回应的习惯建议

你此前主动向用户推荐过把下面的习惯设成任务，正在等用户回应（**请勿重复推送同一条**）：

${items}

**如何处理用户这条消息：**
- 若是肯定/选择/否定语气（"好/可以/行/就第一个/不用了/不要"等）且**没有**其它明确意图 → 这就是对上面建议的答复：
  - 同意 → **先用一句话复述命中的是哪条**，再加载 miloco-create-task skill 据该 suggestion 建任务；**建成、拿到 task_id 后** \`miloco_habit_suggest(action="resolve", key, outcome="created", task_id="<新任务id>")\`。若 create-task 当轮以反问/中断结束、未建成 → 先不 resolve，条目留待用户补答后再落地（勿凭空 resolve）。
  - 拒绝 → \`miloco_habit_suggest(action="resolve", key="<对应 key>", outcome="rejected")\`，简短回应即可，**之后不再就这条打扰**。
- 多条待回应时按用户指代（"第一个/那个喝水的"）定位对应 key。
- 若用户这条消息**与这些建议无关**（在说别的事）→ **忽略本段，照常处理，不要调用 resolve**。`;
}
