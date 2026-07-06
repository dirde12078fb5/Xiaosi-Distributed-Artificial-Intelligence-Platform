@echo off
title Xiaosi NAS Service - Stop

echo ============================================
echo    Xiaosi NAS Service - Stopping...
echo ============================================
echo.

REM 查找并停止Java进程
echo [INFO] Looking for running Xiaosi NAS processes...

for /f "tokens=2" %%i in ('tasklist ^| findstr /i "java.exe"') do (
    wmic process where "processid=%%i and commandline like '%xiaosi-nas%'" get processid,commandline 2>nul | findstr xiaosi-nas >nul
    if !errorlevel! equ 0 (
        echo [INFO] Stopping process %%i...
        taskkill /F /PID %%i
    )
)

echo.
echo [INFO] Xiaosi NAS Service stopped.

pause