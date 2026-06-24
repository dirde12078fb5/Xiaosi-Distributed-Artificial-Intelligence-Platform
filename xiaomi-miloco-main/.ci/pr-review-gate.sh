#!/usr/bin/env bash
# PR 审查 + 严重度门禁的单一实现，供 pr-review.yml / pr-review-command.yml 共用。
# 两个 workflow 都以 `git show origin/main:.ci/pr-review-gate.sh | bash -s -- <pr> <repo>` 方式调用，
# 即始终跑 base 分支(main)上的本脚本——fork PR 改不动它，也保证严重度正则等只有一处。
#
# 安全模型：调用方 checkout 的代码树可能是不可信的 fork PR。审查 CLI 启动时会自动加载工作目录的
# CLAUDE.md（项目指令）、.claude/settings.json（hooks=RCE）、.mcp.json（MCP server=RCE），拷进
# .claude/commands/ 的 review-pr.md 又会被当命令直接执行。故启动前先清掉这些会被自动加载/执行的文件，
# 再只从 base 分支(fork 改不到)取回可信版本。调用前需保证 origin/main 已 fetch。
#
# 用法: pr-review-gate.sh <pr-number> <repo-slug>
# 退出码: 0=放行（无严重/重要问题，或 infra 故障放行不阻塞）, 1=发现严重或重要问题
set -uo pipefail

PR_NUMBER="$1"
REPO="$2"

# 下面取可信文件依赖 origin/main。经 `git show origin/main:gate.sh | bash` 调用时调用方必然已 fetch
# （否则连本脚本都取不出来），这里再保底一次，使脚本也能独立运行（如本地 `bash pr-review-gate.sh` 测试）
git fetch --no-tags origin main 2>/dev/null || true

# ANTHROPIC_BASE_URL 未配置时 CI 注入成空串，会被 SDK 当成无效 base URL；清掉空值回退默认端点
if [ -z "${ANTHROPIC_BASE_URL:-}" ]; then unset ANTHROPIC_BASE_URL; fi

# 清不可信配置，从 base 取回可信版本（见顶部安全模型）
find . \( -name 'CLAUDE.md' -o -name 'CLAUDE.local.md' \) -print0 | xargs -0 -r rm -f
rm -rf .claude .mcp.json
git show origin/main:CLAUDE.md > CLAUDE.md 2>/dev/null || true
mkdir -p .claude/commands
git show "origin/main:.agents/commands/review-pr.md" \
  | sed "s#XiaoMi/xiaomi-miloco#${REPO}#g" \
  > .claude/commands/review-pr.md

# 跑审查：infra 故障（API 宕机/超时/限流）直接放行，避免 infra 问题阻塞 merge。
# < /dev/null 必须：本脚本以 `git show ...:pr-review-gate.sh | bash` 方式（脚本走 bash stdin）调用，
# 而审查 CLI 的 -p 模式在非 TTY 下会读 stdin 当输入，会把 bash 尚未读完的后续脚本（含下面的门禁逻辑）吞掉，
# 导致 pr-agent 后整段门禁被静默跳过、门禁恒放行。隔到 /dev/null 杜绝它消费脚本流。
if ! /usr/local/bin/pr-agent "/review-pr $PR_NUMBER --ci" < /dev/null; then
  echo "[WARN] 审查执行失败，跳过严重度检查"
  exit 0
fi

# 拉刚发布的 review-pr-ci 评论；gh api 瞬断时 || 回退空串，交给下方空值分支放行
NOTE_BODY=$(gh api "/repos/$REPO/issues/$PR_NUMBER/comments" --paginate \
  | jq -rs 'add | .[] | select((.body // "") | startswith("<!-- review-pr-ci -->")) | .body') || NOTE_BODY=""
if [ -z "$NOTE_BODY" ]; then
  echo "[WARN] 未找到 review-pr-ci 评论，跳过严重度检查"
  exit 0
fi

# 锚定到 Markdown 小节标题（review-pr 约定 #### 开头，留 1~4 个 # 余量），避免概述里的提法被误判
if echo "$NOTE_BODY" | grep -qE '^#{1,4} .*(🔴 严重|🟡 重要)'; then
  echo "[FAIL] Review 发现严重或重要问题"
  exit 1
fi
echo "[PASS] 未发现严重或重要问题"
exit 0
