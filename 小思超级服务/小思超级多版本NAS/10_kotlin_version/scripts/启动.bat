@echo off
chcp 65001 >nul
title 小思超级NAS - Kotlin版本

echo.
echo ========================================
echo   🚀 小思超级NAS (Kotlin/Ktor版本)
echo ========================================
echo.

cd /d "%~dp0.."

if not exist "config\.env" (
    echo [错误] 未找到配置文件 config/.env
    echo 请确保配置文件存在
    pause
    exit /b 1
)

echo [信息] 加载配置文件...
for /f "tokens=1,* delims==" %%a in (config\.env) do (
    set "%%a=%%b"
)

echo [信息] 检查Gradle环境...

where gradlew >nul 2>nul
if %errorlevel% neq 0 (
    echo [提示] 未找到gradlew，尝试使用系统Gradle...
    
    where gradle >nul 2>nul
    if %errorlevel% neq 0 (
        echo [错误] 未找到Gradle，请安装Gradle或使用Gradle Wrapper
        pause
        exit /b 1
    )
    
    echo [信息] 使用系统Gradle构建项目...
    call gradle build -x test
    
    if %errorlevel% neq 0 (
        echo [错误] 构建失败！
        pause
        exit /b 1
    )
    
    echo [信息] 启动服务器...
    call gradle run
) else (
    echo [信息] 使用Gradle Wrapper构建项目...
    call gradlew build -x test
    
    if %errorlevel% neq 0 (
        echo [错误] 构建失败！
        pause
        exit /b 1
    )
    
    echo [信息] 启动服务器...
    call gradlew run
)

pause
