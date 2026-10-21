@echo off
chcp 65001 >nul
title 构建NAS服务

echo ====================================
echo 构建小思超级多版本NAS服务
echo ====================================
echo.

REM 创建构建目录
if not exist build (
    echo 创建构建目录...
    mkdir build
)

cd build

REM 配置项目
echo.
echo 配置CMake项目...
cmake .. -DCMAKE_BUILD_TYPE=Release
if %errorlevel% neq 0 (
    echo.
    echo CMake配置失败！
    cd ..
    pause
    exit /b 1
)

REM 构建项目
echo.
echo 构建项目...
cmake --build . --config Release
if %errorlevel% neq 0 (
    echo.
    echo 构建失败！
    cd ..
    pause
    exit /b 1
)

cd ..

echo.
echo ====================================
echo 构建完成！
echo ====================================
echo.
echo 可执行文件位于: build\Release\nas_server.exe
echo.
echo 运行 start.bat 启动服务
echo.

pause