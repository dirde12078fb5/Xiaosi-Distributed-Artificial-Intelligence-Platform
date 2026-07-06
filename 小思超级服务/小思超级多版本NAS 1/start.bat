@echo off
echo ========================================
echo    Xiaosi Super NAS Server
echo ========================================
echo.
python nas_server.py
if errorlevel 1 (
    echo.
    echo Failed to start. Please make sure Python is installed.
    pause
)
