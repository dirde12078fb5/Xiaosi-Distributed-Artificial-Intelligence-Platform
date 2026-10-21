@echo off
chcp 65001 > nul
echo ============================================================
echo   小思NAS服务启动器 (Crystal版)
echo ============================================================
echo   Ruby语法 · C性能
echo ============================================================

cd /d "%~dp0"

REM 检查Crystal是否安装
where crystal >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] Crystal未安装！
    echo 请访问: https://crystal-lang.org/install/ 安装Crystal
    pause
    exit /b 1
)

REM 检查依赖是否安装
if not exist "lib\kemal" (
    echo [信息] 正在安装依赖...
    shards install
)

echo [信息] 启动NAS服务...
echo [端口] 8096 (可通过config.json修改)
echo ============================================================

crystal run src/server.cr

pause