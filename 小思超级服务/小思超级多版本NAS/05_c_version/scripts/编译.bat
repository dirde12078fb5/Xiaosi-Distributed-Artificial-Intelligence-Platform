@echo off
chcp 65001 >nul
echo.
echo  ╔═══════════════════════════════════════════════════════════╗
echo  ║                                                           ║
echo  ║         💾 小思超级NAS - C语言版本                        ║
echo  ║         编译脚本                                        ║
echo  ║                                                           ║
echo  ╚═══════════════════════════════════════════════════════════╝
echo.

REM 获取当前目录
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..

REM 检查GCC编译器
echo [1/3] 检查GCC编译器...
gcc --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ❌ 错误：未找到GCC编译器！
    echo.
    echo 请先安装MinGW-w64：
    echo   • 访问: https://www.mingw-w64.org/
    echo   • 或使用MSYS2: https://www.msys2.org/
    echo.
    pause
    exit /b 1
)

gcc --version | findstr "gcc"
echo ✅ GCC已安装
echo.

REM 准备目录
echo [2/3] 准备目录...
if not exist "%PROJECT_DIR%\public" mkdir "%PROJECT_DIR%\public"
if not exist "%PROJECT_DIR%\storage" mkdir "%PROJECT_DIR%\storage"
echo ✅ 目录已创建

REM 移动前端文件
echo     准备前端文件...
for %%f in (index.html styles.css app.js) do (
    if exist "%PROJECT_DIR%\%%f" (
        move /Y "%PROJECT_DIR%\%%f" "%PROJECT_DIR%\public\%%f" >nul 2>&1
    )
)
echo ✅ 前端文件已准备
echo.

REM 编译程序
echo [3/3] 编译C程序...
cd /d "%SCRIPT_DIR%..\src"
if exist "xiaosi-nas-c.exe" (
    del xiaosi-nas-c.exe
)

gcc main.c -o xiaosi-nas-c.exe -lws2_32 -Wall -O2

if %errorlevel% equ 0 (
    echo.
    echo ✅ 编译成功！
    echo.
    echo 可执行文件已生成：xiaosi-nas-c.exe
    echo.
    echo 接下来运行 "scripts\启动.bat" 来启动服务器
    echo.
) else (
    echo.
    echo ❌ 编译失败！
    echo.
    echo 请检查代码是否有语法错误
    echo.
)

pause
