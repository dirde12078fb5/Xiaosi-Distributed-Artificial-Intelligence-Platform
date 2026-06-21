@echo off
rem =====================================================================
rem ConfigGUI · 启动本地服务
rem 功能：
rem   1) 自动寻找 Python 解释器（优先 py，其次 python）
rem   2) 启动 server.py（默认端口 8765，工作流目录 ./workflows）
rem   3) 自动在默认浏览器中打开 http://127.0.0.1:8765/
rem
rem 用法：
rem   start-server.bat                 # 默认端口 8765
rem   start-server.bat 8080            # 自定义端口
rem   start-server.bat 8080 --no-browser    # 指定端口且不打开浏览器
rem =====================================================================

setlocal
pushd "%~dp0"

rem 查找可用的 Python
set "PYCMD="
where py >nul 2>&1 && (set "PYCMD=py -3")
if not defined PYCMD (
    where python >nul 2>&1 && set "PYCMD=python"
)
if not defined PYCMD (
    echo [错误] 未检测到 Python，请先安装 Python 3.x 并添加到 PATH。
    echo        下载地址：https://www.python.org/downloads/
    pause
    popd
    exit /b 1
)

rem 解析参数
set "PORT="
set "EXTRA_ARGS="
:parse_args
if "%~1"=="" goto done_parse
for /f "delims=0123456789" %%a in ("%~1") do set "not_a_number=1"
if not "%not_a_number%"=="1" (
    set "PORT=%~1"
    shift
    goto parse_args
)
rem 其它参数（如 --no-browser）透传给 server.py
set EXTRA_ARGS=%EXTRA_ARGS% %~1
set "not_a_number="
shift
goto parse_args
:done_parse

if "%PORT%"=="" set "PORT=8765"

echo.
echo ==============================================================
echo   ConfigGUI · 正在启动服务
echo   Python : %PYCMD%
echo   地址   : http://127.0.0.1:%PORT%/
echo   目录   : %cd%
echo   (按 Ctrl+C 可停止服务)
echo ==============================================================
echo.

%PYCMD% server.py --port %PORT% %EXTRA_ARGS%

set "EXITCODE=%ERRORLEVEL%"
popd
if %EXITCODE% NEQ 0 (
    echo.
    echo [提示] 服务异常退出，码 %EXITCODE%
    pause
)
exit /b %EXITCODE%
