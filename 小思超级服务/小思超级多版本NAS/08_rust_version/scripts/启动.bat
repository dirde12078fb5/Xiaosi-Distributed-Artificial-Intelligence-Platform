@echo off
chcp 65001 >nul
echo.
echo  ╔═══════════════════════════════════════════════════════════╗
echo  ║                                                           ║
echo  ║         💾 小思超级NAS - Rust语言版本                     ║
echo  ║         智能存储管理平台                                ║
echo  ║                                                           ║
echo  ╚═══════════════════════════════════════════════════════════╝
echo.

REM 检查Rust环境
echo [1/4] 检查Rust环境...
rustc --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ❌ 错误：未找到Rust！
    echo.
    echo 请先安装Rust：
    echo   • 访问: https://rustup.rs/
    echo   • 或运行: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
    echo.
    pause
    exit /b 1
)

rustc --version
cargo --version
echo ✅ Rust已安装
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

REM 编译并运行Rust程序
echo [4/4] 编译并运行Rust程序...
cd /d "%SCRIPT_DIR%..\config"

if not exist "Cargo.lock" (
    echo 首次运行，正在下载依赖...
    cargo fetch
)

cd /d "%SCRIPT_DIR%..\src"

echo 正在编译（这可能需要几分钟）...
cargo build --release

if %errorlevel% equ 0 (
    echo.
    echo ✅ 编译成功！
) else (
    echo.
    echo ❌ 编译失败！请检查代码是否有错误
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

cargo run --release

pause
