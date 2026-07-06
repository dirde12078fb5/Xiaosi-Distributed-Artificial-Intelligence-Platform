@echo off
chcp 65001 >nul
echo ========================================
echo NAS服务 - F#实现
echo ========================================
echo.

REM 检查.NET SDK
dotnet --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到.NET SDK，请先安装.NET 8.0 SDK
    echo 下载地址: https://dotnet.microsoft.com/download/dotnet/8.0
    pause
    exit /b 1
)

REM 恢复依赖
echo [1/3] 恢复项目依赖...
dotnet restore
if %errorlevel% neq 0 (
    echo [错误] 依赖恢复失败
    pause
    exit /b 1
)

REM 构建项目
echo [2/3] 构建项目...
dotnet build -c Release
if %errorlevel% neq 0 (
    echo [错误] 项目构建失败
    pause
    exit /b 1
)

REM 运行项目
echo [3/3] 启动服务...
echo.
echo ========================================
echo 服务即将启动，默认端口: 8099
echo API文档:
echo   GET  /api/info       - 获取服务信息
echo   GET  /api/files      - 列出文件列表
echo   POST /api/upload     - 上传文件
echo   GET  /api/download   - 下载文件
echo   DELETE /api/delete   - 删除文件
echo   POST /api/mkdir      - 创建目录
echo   GET  /api/languages  - 获取支持的语言列表
echo ========================================
echo.

dotnet run -c Release

pause