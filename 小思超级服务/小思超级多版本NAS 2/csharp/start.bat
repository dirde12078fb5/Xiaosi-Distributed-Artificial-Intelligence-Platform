@echo off
echo ================================
echo 小思超级NAS服务 - C#版本
echo ================================
echo.

cd /d "%~dp0"

echo 正在检查.NET环境...
dotnet --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未检测到.NET Core环境
    echo 请安装.NET Core 8.0或更高版本
    echo 下载地址: https://dotnet.microsoft.com/download
    pause
    exit /b 1
)

echo 正在启动NAS服务...
echo 服务地址: http://localhost:8085
echo.

dotnet run

pause