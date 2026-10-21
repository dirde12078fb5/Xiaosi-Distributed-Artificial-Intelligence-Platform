@echo off
chcp 65001 >nul
title 小思超级多版本NAS服务 - C++版本

echo ====================================
echo 小思超级多版本NAS服务 - C++版本
echo ====================================
echo.

REM 检查是否存在可执行文件
if exist "nas_server.exe" (
    echo 启动服务...
    nas_server.exe
) else if exist "build\Release\nas_server.exe" (
    echo 启动服务（从build目录）...
    cd build\Release
    nas_server.exe
    cd ..\..
) else if exist "build\nas_server.exe" (
    echo 启动服务（从build目录）...
    cd build
    nas_server.exe
    cd ..
) else (
    echo 错误：未找到可执行文件 nas_server.exe
    echo.
    echo 请先构建项目：
    echo   mkdir build
    echo   cd build
    echo   cmake ..
    echo   cmake --build . --config Release
    echo.
    echo 或者运行 build.bat 进行自动构建
    pause
    exit /b 1
)

pause