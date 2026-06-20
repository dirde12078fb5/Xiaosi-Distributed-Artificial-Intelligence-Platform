# 小思超级NAS - C语言版本配置文件

# 服务器配置
PORT=8080
HOST=0.0.0.0

# 路径配置
ROOT_DIR=../public
STORAGE_DIR=../storage

# 用户配置
DEFAULT_USER=admin
DEFAULT_PASSWORD=admin123

# 编译配置
CC=gcc
CFLAGS=-Wall -O2
LDFLAGS=-lws2_32  # Windows
#LDFLAGS=-lpthread  # Linux

# 目标文件
TARGET=xiaosi-nas-c.exe  # Windows
#TARGET=xiaosi-nas-c      # Linux
