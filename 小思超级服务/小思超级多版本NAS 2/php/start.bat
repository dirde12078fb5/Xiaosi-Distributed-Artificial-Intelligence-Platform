@echo off
title 小思超级NAS服务 - PHP版本
echo ========================================
echo    小思超级NAS服务 - PHP版本
echo    默认端口: 8088
echo ========================================
echo.
echo 正在启动服务器...
echo.

REM 切换到php目录
cd /d "%~dp0"

REM 启动PHP内置服务器
php -S 0.0.0.0:8088 server.php

echo.
echo 服务器已启动，访问地址：
echo http://localhost:8088
echo http://127.0.0.1:8088
echo.
echo 按Ctrl+C停止服务器
pause