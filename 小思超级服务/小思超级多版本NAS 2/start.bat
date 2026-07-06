@echo off
chcp 65001 >nul
title NAS Service - Lua Server

echo ========================================
echo    NAS Service - Lua Implementation
echo    Version: 2.0
echo    Port: 8094
echo ========================================
echo.

REM 检查Lua是否安装
where lua >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Lua未安装，请先安装Lua 5.3+
    echo 下载地址: https://www.lua.org/download.html
    pause
    exit /b 1
)

REM 进入lua目录
cd /d "%~dp0lua"

REM 检查server.lua是否存在
if not exist "server.lua" (
    echo [ERROR] server.lua 文件不存在
    pause
    exit /b 1
)

REM 创建storage目录
if not exist "..\storage" mkdir "..\storage"

echo [INFO] 正在启动NAS服务...
echo [INFO] 访问地址: http://localhost:8094
echo [INFO] 按 Ctrl+C 停止服务
echo.

REM 启动Lua服务器
lua server.lua

pause