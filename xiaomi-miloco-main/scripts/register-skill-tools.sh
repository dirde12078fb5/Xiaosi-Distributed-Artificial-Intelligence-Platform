#!/usr/bin/env bash
# 把 plugins/skills/*/SKILL.md frontmatter 里声明的所有 miloco_* tool
# append 到 openclaw 用户 config 的 tools.alsoAllow。
#
# 该脚本只处理"安装后"那一层 gate（user config 白名单），需要远端有
# openclaw CLI 可用。另一层 gate 是 plugin manifest 的 contracts.tools
# （plugins/openclaw/openclaw.plugin.json）—— 那是编译前就写死在源码里
# 的，由 skill 作者人工维护，本脚本不动。
#
# 用法：
#   ./scripts/register-skill-tools.sh                 # 写盘
#   ./scripts/register-skill-tools.sh --dry-run       # 只校验不写盘
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/plugins/skills"
CONFIG_TOOL="$SCRIPT_DIR/openclaw_config_tool.py"

DRY_RUN=()
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=("--dry-run")

[[ -d "$SKILLS_DIR" ]] || { echo "[register-skill-tools] 缺 $SKILLS_DIR" >&2; exit 1; }
[[ -f "$CONFIG_TOOL" ]] || { echo "[register-skill-tools] 缺 $CONFIG_TOOL" >&2; exit 1; }

# 扫 SKILL.md frontmatter 的 requires.tools，输出按行排序去重
# 用 while-read 收集（mapfile/readarray 是 bash 4+，macOS 自带 bash 3.2 没有此命令）
TOOLS=()
while IFS= read -r _tool; do
    if [[ -n "$_tool" ]]; then TOOLS+=("$_tool"); fi
done < <(python3 - "$SKILLS_DIR" <<'PYEOF'
import os, re, sys
skills_dir = sys.argv[1]
tools = set()
for root, _, files in os.walk(skills_dir):
    for fn in files:
        if fn != "SKILL.md":
            continue
        text = open(os.path.join(root, fn), encoding="utf-8").read()
        m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        if not m:
            continue
        in_tools = False
        for line in m.group(1).splitlines():
            if re.match(r"^\s+tools:\s*$", line):
                in_tools = True
                continue
            if not in_tools:
                continue
            item = re.match(r"^\s+-\s+([A-Za-z_][\w]*)\s*$", line)
            if item:
                tools.add(item.group(1))
                continue
            if line.strip() and not line.lstrip().startswith("-"):
                in_tools = False
for t in sorted(tools):
    print(t)
PYEOF
)

if [[ ${#TOOLS[@]} -eq 0 ]]; then
    echo "[register-skill-tools] frontmatter 未声明任何 tool，跳过" >&2
    exit 0
fi

echo "[register-skill-tools] 扫到 ${#TOOLS[@]} 个 tool，append 到 tools.alsoAllow:"
for t in "${TOOLS[@]}"; do echo "  - $t"; done

# 空数组在 bash 3.2 + set -u 下展开 "${DRY_RUN[@]}" 会报 unbound variable（4.4+ 才修）,
# 故按长度守卫:空就不展开。
if [[ ${#DRY_RUN[@]} -gt 0 ]]; then
    exec python3 "$CONFIG_TOOL" "${DRY_RUN[@]}" append tools.alsoAllow "${TOOLS[@]}"
else
    exec python3 "$CONFIG_TOOL" append tools.alsoAllow "${TOOLS[@]}"
fi
