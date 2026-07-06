@echo off
title Xiaosi NAS Service - Build

echo ============================================
echo    Xiaosi NAS Service - Building...
echo ============================================
echo.

REM 设置Java环境（如果需要）
REM set JAVA_HOME=C:\Program Files\Java\jdk-17
REM set PATH=%JAVA_HOME%\bin;%PATH%

REM 检查Maven
where mvn >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Maven not found.
    pause
    exit /b 1
)

cd /d "%~dp0"

echo [INFO] Cleaning and building project...
call mvn clean package -DskipTests

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Build completed successfully!
    echo [INFO] Output: target\xiaosi-nas-1.0.0.jar
) else (
    echo.
    echo [ERROR] Build failed!
)

pause