@echo off
chcp 65001 >nul
echo.
echo  ╔═══════════════════════════════════════════════════════════╗
echo  ║                                                           ║
echo  ║         💾 小思超级NAS - Python版本                       ║
echo  ║         智能存储管理平台                                ║
echo  ║                                                           ║
echo  ╚═══════════════════════════════════════════════════════════╝
echo.

REM 检查Python环境
echo [1/4] 检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    python3 --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo.
        echo ❌ 错误：未找到Python！
        echo.
        echo 请先安装Python：
        echo   • Windows: 从 Microsoft Store 搜索 "Python" 安装
        echo   • 或访问: https://www.python.org/downloads/
        echo.
        pause
        exit /b 1
    )
    set PYTHON=python3
) else (
    set PYTHON=python
)

%PYTHON% --version
echo ✅ Python已安装
echo.

REM 获取当前目录
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..

REM 准备目录
echo [2/4] 准备目录...
if not exist "%PROJECT_DIR%\public" mkdir "%PROJECT_DIR%\public"
if not exist "%PROJECT_DIR%\storage" mkdir "%PROJECT_DIR%\storage"
if not exist "%PROJECT_DIR%\temp" mkdir "%PROJECT_DIR%\temp"
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

REM 检查依赖
echo [4/4] 检查依赖包...
%PYTHON% -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo 首次运行，正在安装依赖...
    cd /d "%SCRIPT_DIR%..\config"
    %PYTHON% -m pip install -r requirements.txt -q
    if %errorlevel% neq 0 (
        echo.
        echo ⚠️  自动安装失败，尝试使用国内镜像...
        %PYTHON% -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple -q
    )
    cd /d "%SCRIPT_DIR%"
)
echo ✅ 依赖检查完成
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
%PYTHON% app.py

pause
