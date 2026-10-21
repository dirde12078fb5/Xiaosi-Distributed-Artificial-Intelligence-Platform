@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0.."

echo ============================================================
echo   小思分布式人工智能平台 - 一键安装依赖 (Windows)
echo ============================================================
echo.

echo [1/4] 检查 Python ...
where python >nul 2>nul
if errorlevel 1 (
    echo [X] 未检测到 python，请先安装 Python 3.10+ 并加入 PATH。
    echo     下载：https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version

echo.
echo [2/4] 升级 pip ...
python -m pip install --upgrade pip

echo.
echo [3/4] 安装各模块依赖 ...
if exist "requirements.txt"            pip install -r "requirements.txt"
if exist "requirements 视觉模块.txt"   pip install -r "requirements 视觉模块.txt"
if exist "requirements 服务管理.txt"   pip install -r "requirements 服务管理.txt"

echo.
echo [4/4] 完成！下一步双击「一键启动.bat」选择要运行的模块。
echo.
pause
endlocal
