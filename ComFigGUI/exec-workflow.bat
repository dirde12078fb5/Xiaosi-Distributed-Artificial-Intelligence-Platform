@echo off
rem =====================================================================
rem ConfigGUI · 执行工作流 JSON
rem 功能：
rem   1) 自动寻找 Python 解释器
rem   2) 调用 run-workflow.py 解析并模拟执行工作流
rem   3) 输出执行顺序与耗时报告
rem
rem 用法：
rem   exec-workflow.bat my_workflow.json
rem   exec-workflow.bat my_workflow.json --out report.json
rem   exec-workflow.bat --gen-demo demo_workflow.json
rem =====================================================================

setlocal
pushd "%~dp0"

set "PYCMD="
where py >nul 2>&1 && (set "PYCMD=py -3")
if not defined PYCMD (
    where python >nul 2>&1 && set "PYCMD=python"
)
if not defined PYCMD (
    echo [错误] 未检测到 Python，请先安装 Python 3.x 并添加到 PATH。
    pause
    popd
    exit /b 1
)

if "%~1"=="" (
    echo 用法: %~nx0 ^<工作流文件.json^> [参数...]
    echo.
    echo 示例:
    echo   %~nx0 workflows\demo.json
    echo   %~nx0 workflows\demo.json --out report.json
    echo   %~nx0 --gen-demo demo_workflow.json
    echo.
    %PYCMD% run-workflow.py
    popd
    exit /b 2
)

%PYCMD% run-workflow.py %*

set "EXITCODE=%ERRORLEVEL%"
popd
exit /b %EXITCODE%
