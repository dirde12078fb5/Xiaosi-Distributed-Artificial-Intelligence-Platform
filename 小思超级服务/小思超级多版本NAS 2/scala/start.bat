@echo off
chcp 65001
echo ====================================
echo 小思超级NAS服务 - Scala版本
echo ====================================
echo 正在启动服务...
echo 默认端口: 8093
echo 支持config.json配置文件
echo 支持28种语言翻译
echo ====================================

cd /d "%~dp0"

REM 检查SBT是否安装
where sbt >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到SBT，请先安装SBT
    echo 安装方法: 
    echo 1. 访问 https://www.scala-sbt.org/download.html
    echo 2. 或使用 scoop install sbt (Windows)
    pause
    exit /b 1
)

REM 检查Java是否安装
where java >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Java，请先安装JDK 11+
    pause
    exit /b 1
)

echo [启动] 使用SBT编译并运行服务...
sbt run

pause