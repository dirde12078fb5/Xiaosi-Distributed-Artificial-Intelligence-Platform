#!/bin/bash
#
# 小思超级NAS - Shell版本启动脚本
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 添加执行权限
chmod +x "$PROJECT_DIR/src/nas-server.sh"

# 运行服务器
"$PROJECT_DIR/src/nas-server.sh"
