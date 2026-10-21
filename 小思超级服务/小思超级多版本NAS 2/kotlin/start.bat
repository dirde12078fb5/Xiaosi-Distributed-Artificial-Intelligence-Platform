@echo off
chcp 65001 >nul
title 小思NAS服务

echo ╔════════════════════════════════════════════╗
echo ║         小思NAS服务启动脚本                  ║
echo ╚════════════════════════════════════════════╝
echo.

REM 检查Java环境
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Java环境，请安装JDK 17或更高版本
    pause
    exit /b 1
)

REM 设置工作目录
cd /d "%~dp0"

REM 检查是否已构建
if not exist "build\libs\xiaosi-nas-1.0.0.jar" (
    echo [信息] 首次运行，正在构建项目...
    echo.
    
    REM 检查Gradle Wrapper
    if not exist "gradlew.bat" (
        echo [信息] 正在下载Gradle Wrapper...
        gradle wrapper
    )
    
    echo [信息] 正在构建项目，请稍候...
    call gradlew.bat build -x test
    
    if %errorlevel% neq 0 (
        echo [错误] 项目构建失败
        pause
        exit /b 1
    )
    echo.
    echo [成功] 项目构建完成
    echo.
)

echo [信息] 正在启动小思NAS服务...
echo.

REM 启动服务
java -jar build\libs\xiaosi-nas-1.0.0.jar

pause