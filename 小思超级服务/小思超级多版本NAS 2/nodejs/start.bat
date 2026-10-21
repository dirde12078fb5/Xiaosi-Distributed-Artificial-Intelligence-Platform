@echo off
title 小思超级NAS服务 - Node.js版本
echo ==================================================
echo   小思超级NAS服务启动
echo ==================================================
echo.

cd /d "%~dp0"

echo 正在检查Node.js环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Node.js环境，请先安装Node.js
    echo 下载地址: https://nodejs.org/
    pause
    exit /b 1
)

echo Node.js版本:
node --version

echo.
echo 正在检查依赖...
if not exist "node_modules" (
    echo 未安装依赖，正在安装express...
    npm install express --production
)

echo.
echo 启动NAS服务...
echo 服务端口: 8081
echo 访问地址: http://localhost:8081
echo.
node server.js

pause