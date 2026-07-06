@echo off
chcp 65001 >nul
echo ========================================
echo NAS 服务启动脚本 (Elixir版本)
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] 检查 Elixir 环境...
where mix >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Elixir 环境，请先安装 Elixir
    echo 下载地址: https://elixir-lang.org/install.html
    pause
    exit /b 1
)
echo [成功] Elixir 环境已就绪

echo.
echo [2/3] 安装依赖...
call mix deps.get
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)
echo [成功] 依赖已安装

echo.
echo [3/3] 启动 NAS 服务...
echo 服务地址: http://localhost:8098
echo 按 Ctrl+C 可停止服务
echo.
call mix run --no-halt