@echo off
chcp 65001 >nul
title 小思NAS服务 - Ruby版

echo ============================================================
echo 小思NAS服务 (Ruby版) v2.0.0
echo ============================================================

cd /d "%~dp0"

echo 正在检查Ruby环境...
where ruby >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未找到Ruby，请先安装Ruby
    echo 下载地址: https://www.ruby-lang.org/zh_cn/downloads/
    pause
    exit /b 1
)

echo Ruby版本:
ruby --version
echo.

echo 正在安装依赖...
if exist Gemfile (
    gem install bundler --quiet 2>nul
    bundle install --quiet 2>nul
)
echo.

echo 正在启动服务...
echo 服务地址: http://localhost:8087
echo 按 Ctrl+C 停止服务
echo ============================================================
echo.

ruby server.rb

pause