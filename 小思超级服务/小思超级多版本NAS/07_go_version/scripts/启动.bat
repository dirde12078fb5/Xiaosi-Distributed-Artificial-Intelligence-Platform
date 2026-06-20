@echo off
chcp 65001 >nul
echo.
echo  ╔═══════════════════════════════════════════════════════════╗
echo  ║                                                           ║
echo  ║         💾 小思超级NAS - Go语言版本                       ║
echo  ║         智能存储管理平台                                ║
echo  ║                                                           ║
echo  ╚═══════════════════════════════════════════════════════════╝
echo.

REM 检查Go环境
echo [1/4] 检查Go环境...
go version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ❌ 错误：未找到Go！
    echo.
    echo 请先安装Go：
    echo   • 访问: https://golang.org/dl/
    echo   • 或使用: https://go.dev/doc/install
    echo.
    pause
    exit /b 1
)

go version
echo ✅ Go已安装
echo.

REM 获取当前目录
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..

REM 准备目录
echo [2/4] 准备目录...
if not exist "%PROJECT_DIR%\public" mkdir "%PROJECT_DIR%\public"
if not exist "%PROJECT_DIR%\storage" mkdir "%PROJECT_DIR%\storage"
echo ✅ 目录已创建

REM 移动前端文件
echo [3/4] 准备前端文件...
for %%f in (index.html styles.css app.js) do (
    if exist "%PROJECT_DIR%\%%f" (
        move /Y "%PROJECT_DIR%\%%f" "%PROJECT_DIR%\public\%%f" >nul 2>&1
        echo    ✓ %%f
    )
)
echo ✅ 前端文件已准备
echo.

REM 安装依赖并运行
echo [4/4] 安装依赖并运行...
cd /d "%SCRIPT_DIR%..\config"
if not exist "vendor" (
    echo 首次运行，正在下载依赖...
    go mod download
)

cd /d "%SCRIPT_DIR%..\src"
if exist "xiaosi-nas.exe" del xiaosi-nas.exe

go build -o xiaosi-nas.exe main.go
if %errorlevel% equ 0 (
    echo ✅ 编译成功！
) else (
    echo ❌ 编译失败！
    pause
    exit /b 1
)
echo.

echo ════════════════════════════════════════════════════════════
echo.
echo   🚀 小思超级NAS 正在启动...
echo.
echo   📡 访问地址：
echo      本地访问: http://localhost:8080
echo.
echo   👤 登录信息：
echo      用户名: admin
echo      密码: admin123
echo.
echo   💡 提示：按 Ctrl+C 可以停止服务器
echo.
echo ════════════════════════════════════════════════════════════
echo.

xiaosi-nas.exe

pause
