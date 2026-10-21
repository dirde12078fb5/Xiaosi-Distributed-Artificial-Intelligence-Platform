@echo off
chcp 65001 >nul
title 小思超级NAS服务 (第二代) - Python版本
color 0A

echo ==========================================
echo   小思超级NAS服务启动脚本
echo   第二代 · Python实现 · 零依赖
echo ==========================================
echo.

REM 检查Python是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.6+
    echo.
    pause
    exit /b 1
)

REM 显示Python版本
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
echo [信息] Python版本: %PYTHON_VER%
echo.

REM 设置端口（默认8080）
set NAS_PORT=8080
if not "%1"=="" set NAS_PORT=%1

REM 切换到脚本所在目录
cd /d "%~dp0"

echo [信息] 启动NAS服务...
echo [信息] 服务端口: %NAS_PORT%
echo.
echo ==========================================
echo   按 Ctrl+C 可停止服务
echo ==========================================
echo.

REM 启动服务器
python nas_server.py %NAS_PORT%

pause