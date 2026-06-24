#!/usr/bin/env bash
# .ci/run-opengrep.sh
#
# 用 .ci/opengrep-rules.yml 跑 OpenGrep 扫描，CI 与本地共用同一组路径和排除项
# （排除项见仓库根的 .semgrepignore）。
#
# 用法：
#   .ci/run-opengrep.sh                # 全量扫描，人读输出
#   .ci/run-opengrep.sh --sarif        # 额外写 SARIF 供上传
#   .ci/run-opengrep.sh --changed      # 仅扫本次改动的一方源码路径
#   .ci/run-opengrep.sh --error        # 有发现时以非零码退出
#
# 退出码：扫描出错非零；传 --error 且有发现时非零。

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG="$REPO_ROOT/.ci/opengrep-rules.yml"

if [[ ! -f "$CONFIG" ]]; then
  echo "error: 规则文件不存在：$CONFIG" >&2
  exit 66
fi
if ! command -v opengrep >/dev/null 2>&1; then
  echo "error: 未找到 opengrep。安装：curl -fsSL https://raw.githubusercontent.com/opengrep/opengrep/v1.22.0/install.sh | bash -s -- -v v1.22.0" >&2
  exit 127
fi

EXTRA_ARGS=()
CHANGED_ONLY=0
while (( $# > 0 )); do
  case "$1" in
    --sarif) mkdir -p "$REPO_ROOT/.opengrep-out"; EXTRA_ARGS+=( "--sarif-output=$REPO_ROOT/.opengrep-out/precise.sarif" ); shift ;;
    --json)  mkdir -p "$REPO_ROOT/.opengrep-out"; EXTRA_ARGS+=( "--json" "--output=$REPO_ROOT/.opengrep-out/precise.json" ); shift ;;
    --changed) CHANGED_ONLY=1; shift ;;
    --error) EXTRA_ARGS+=( "--error" ); shift ;;
    *) EXTRA_ARGS+=( "$1" ); shift ;;
  esac
done

cd "$REPO_ROOT"

# 第一方源码目录（与 CI paths 一致）
FIRST_PARTY_RE='^(backend|cli|plugins/openclaw/src|web/src|scripts)/'

if (( CHANGED_ONLY )); then
  DIFF_REF="${MILOCO_OPENGREP_BASE_REF:-origin/main...HEAD}"
  SCAN_PATHS=()
  while IFS= read -r p; do
    [[ -L "$p" ]] && continue
    [[ -f "$p" || -d "$p" ]] || continue
    SCAN_PATHS+=( "$p" )
  done < <(
    {
      git diff --name-only --diff-filter=ACMRTUXB "$DIFF_REF" 2>/dev/null || true
      git ls-files --others --exclude-standard
    } | grep -E "$FIRST_PARTY_RE" | sort -u
  )
  if (( ${#SCAN_PATHS[@]} == 0 )); then
    echo "→ 本次无改动的第一方源码，跳过 opengrep。" >&2
    exit 0
  fi
else
  SCAN_PATHS=( backend cli plugins/openclaw/src web/src scripts )
fi

echo "→ opengrep 扫描：${SCAN_PATHS[*]}（排除项见 .semgrepignore）" >&2
exec opengrep scan --no-strict --config "$CONFIG" --no-git-ignore "${EXTRA_ARGS[@]}" "${SCAN_PATHS[@]}"
