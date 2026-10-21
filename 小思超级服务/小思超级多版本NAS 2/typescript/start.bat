@echo off
chcp 65001 >nul
title 小思超级NAS服务 - TypeScript版

echo ================================================
echo   小思超级NAS服务启动 (TypeScript)
echo ================================================
echo.

cd /d "%~dp0"

echo [1] 检查Node.js环境...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Node.js，请先安装Node.js
    pause
    exit /b 1
)

echo [2] 检查npm...
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到npm，请先安装Node.js
    pause
    exit /b 1
)

echo [√] Node.js环境正常

echo.
echo [3] 检查项目依赖...
if not exist "node_modules" (
    echo [!] 未检测到依赖包，正在安装...
    npm install
    if %errorlevel% neq 0 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

echo [√] 依赖包已安装

echo.
echo [4] 编译TypeScript代码...
npm run build
if %errorlevel% neq 0 (
    echo [错误] TypeScript编译失败
    pause
    exit /b 1
)

echo [√] 编译成功

echo.
echo [5] 启动NAS服务...
echo.
echo ================================================
echo   服务正在启动，端口: 8091
echo   请在浏览器中访问: http://localhost:8091
echo ================================================
echo.

node dist/server.js

pause