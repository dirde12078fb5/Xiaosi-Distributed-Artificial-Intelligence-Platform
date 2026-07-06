@echo off
chcp 65001 >nul
echo ====================================
echo 小思超级多版本NAS服务 - Dart实现
echo ====================================
echo.

cd /d "%~dp0"

REM 检查Dart是否安装
where dart >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Dart SDK
    echo 请安装Dart SDK: https://dart.dev/get-dart
    pause
    exit /b 1
)

REM 检查依赖是否已安装
if not exist ".dart_tool" (
    echo [信息] 正在安装依赖...
    dart pub get
    if %errorlevel% neq 0 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
    echo [信息] 依赖安装完成
)

echo [信息] 正在启动NAS服务...
echo.

dart run bin/server.dart

pause