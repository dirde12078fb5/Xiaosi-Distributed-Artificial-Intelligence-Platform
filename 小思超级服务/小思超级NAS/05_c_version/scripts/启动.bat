@echo off
chcp 65001 >nul
echo.
echo  ╔═══════════════════════════════════════════════════════════╗
echo  ║                                                           ║
echo  ║         💾 小思超级NAS - C语言版本                        ║
echo  ║         智能存储管理平台                                ║
echo  ║                                                           ║
echo  ╚═══════════════════════════════════════════════════════════╝
echo.

REM 获取当前目录
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..

REM 检查可执行文件
if not exist "%PROJECT_DIR%\src\xiaosi-nas-c.exe" (
    echo ❌ 错误：找不到 xiaosi-nas-c.exe
    echo.
    echo 请先运行 "scripts\编译.bat" 编译程序
    echo.
    pause
    exit /b 1
)

echo ✅ 找到程序文件
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

cd /d "%PROJECT_DIR%\src"
xiaosi-nas-c.exe

pause
