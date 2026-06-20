@echo off
chcp 65001 >nul
echo.
echo  ╔═══════════════════════════════════════════════════════════╗
echo  ║                                                           ║
echo  ║         💾 小思超级NAS - PHP版本                           ║
echo  ║         智能存储管理平台                                ║
echo  ║                                                           ║
echo  ╚═══════════════════════════════════════════════════════════╝
echo.

REM 检查PHP环境
echo [1/4] 检查PHP环境...
php --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ❌ 错误：未找到PHP！
    echo.
    echo 请先安装PHP：
    echo   • Windows: https://windows.php.net/download/
    echo   • 或使用XAMPP/WAMP: https://www.apachefriends.org/
    echo.
    pause
    exit /b 1
)

php --version | findstr "PHP"
echo ✅ PHP已安装
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

REM 检查PHP版本
echo [4/4] 检查PHP版本...
php -r "echo PHP_VERSION;" >nul 2>&1
php -r "if (version_compare(PHP_VERSION, '7.4.0', '<')) { exit(1); }" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  建议使用PHP 7.4或更高版本
)
echo ✅ PHP版本检查完成
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

cd /d "%SCRIPT_DIR%..\src"
php -S 0.0.0.0:8080 server.php

pause
