@echo off
chcp 65001 > nul
title 小思超级多版本NAS - Nim版本

echo ==========================================
echo 小思超级多版本NAS系统 v2.0 (Nim)
echo ==========================================
echo.

REM 检查Nim是否安装
where nim > nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Nim编译器未安装，请先安装Nim
    echo.
    echo 安装方法:
    echo   1. 访问 https://nim-lang.org/install.html
    echo   2. 下载并安装Nim编译器
    echo   3. 运行 nim -v 验证安装
    echo.
    pause
    exit /b 1
)

REM 显示Nim版本
echo [信息] Nim编译器版本:
nim -v | findstr /C:"Nim Compiler"
echo.

REM 检查是否需要安装依赖
echo [信息] 检查项目依赖...
if not exist "nas_server.nimble" (
    echo [警告] nimble配置文件不存在，将创建默认配置
)

REM 安装必要的依赖包
echo [信息] 安装必要的依赖包...
nimble install jester -y
nimble install asyncdispatch -y
nimble install json -y
nimble install base64 -y
nimble install sha1 -y
nimble install mimetypes -y

echo.
echo [信息] 编译服务器程序...
nim c -d:release -d:ssl server.nim

if %errorlevel% neq 0 (
    echo [错误] 编译失败，请检查代码
    pause
    exit /b 1
)

echo [信息] 编译成功!
echo.

REM 检查配置文件
if not exist "..\config\config.json" (
    echo [警告] 配置文件不存在: ..\config\config.json
    echo [信息] 将使用默认配置运行
)

echo ==========================================
echo 启动NAS服务器...
echo ==========================================
echo.
echo [提示] 按 Ctrl+C 停止服务器
echo.

REM 运行服务器
server.exe

pause