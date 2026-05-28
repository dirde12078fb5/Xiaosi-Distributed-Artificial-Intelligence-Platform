#!/bin/bash
#
# 小思超级NAS - Shell脚本版本
# 智能存储管理平台
# 
# 作者: 小思AI团队
# 版本: 1.0.0
# 
# 使用Python内置HTTP服务器
# 运行: ./nas-server.sh
#

# ==================== 配置 ====================
PORT=8080
HOST="0.0.0.0"
PUBLIC_DIR="../public"
STORAGE_DIR="../storage"

# 默认用户
DEFAULT_USER="admin"
DEFAULT_PASSWORD="admin123"

# ==================== 颜色定义 ====================
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ==================== 初始化 ====================
init() {
    mkdir -p "$PUBLIC_DIR"
    mkdir -p "$STORAGE_DIR"
}

# ==================== 检查Python ====================
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo -e "${RED}❌ 错误：未找到Python${NC}"
        echo "请安装Python: https://www.python.org/downloads/"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Python已找到: $($PYTHON_CMD --version)${NC}"
}

# ==================== 打印横幅 ====================
print_banner() {
    echo -e "${BLUE}"
    cat << "EOF"
    ╔════════════════════════════════════════════╗
    ║                                            ║
    ║      💾 小思超级NAS (Shell版本)             ║
    ║      智能存储管理平台                       ║
    ║                                            ║
    ╚════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# ==================== 获取本地IP ====================
get_local_ip() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        ifconfig | grep 'inet ' | grep -v 127.0.0.1 | awk '{print $2}' | head -1
    else
        hostname -I | awk '{print $1}'
    fi
}

# ==================== 启动服务器 ====================
start_server() {
    echo -e "${YELLOW}🚀 正在启动服务器...${NC}"
    echo ""
    
    cd "$(dirname "$0")"
    
    $PYTHON_CMD -m http.server $PORT --bind $HOST > /dev/null 2>&1 &
    SERVER_PID=$!
    
    sleep 2
    
    if ps -p $SERVER_PID > /dev/null; then
        print_banner
        
        echo -e "${GREEN}✅ 服务器启动成功！${NC}"
        echo ""
        echo -e "${BLUE}📡 访问地址：${NC}"
        echo -e "   本地访问: ${GREEN}http://localhost:$PORT${NC}"
        echo -e "   局域网访问: ${GREEN}http://$(get_local_ip):$PORT${NC}"
        echo ""
        echo -e "${BLUE}👤 默认登录：${NC}"
        echo -e "   用户名: ${GREEN}$DEFAULT_USER${NC}"
        echo -e "   密码: ${GREEN}$DEFAULT_PASSWORD${NC}"
        echo ""
        echo -e "${YELLOW}按 Ctrl+C 停止服务器${NC}"
        echo ""
        
        wait $SERVER_PID
    else
        echo -e "${RED}❌ 服务器启动失败${NC}"
        exit 1
    fi
}

# ==================== 清理函数 ====================
cleanup() {
    echo ""
    echo -e "${YELLOW}正在停止服务器...${NC}"
    pkill -f "python.*http.server.*$PORT" 2>/dev/null
    echo -e "${GREEN}✅ 服务器已停止${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# ==================== 主程序 ====================
main() {
    print_banner
    init
    check_python
    start_server
}

main
