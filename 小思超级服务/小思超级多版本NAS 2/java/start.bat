@echo off
title Xiaosi NAS Service

echo ============================================
echo    Xiaosi NAS Service - Starting...
echo ============================================
echo.

REM 设置Java环境（如果需要）
REM set JAVA_HOME=C:\Program Files\Java\jdk-17
REM set PATH=%JAVA_HOME%\bin;%PATH%

REM 检查Maven是否安装
where mvn >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Maven not found. Please install Maven first.
    echo Download from: https://maven.apache.org/download.cgi
    pause
    exit /b 1
)

REM 检查Java是否安装
where java >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Java not found. Please install Java 17+ first.
    echo Download from: https://www.oracle.com/java/technologies/downloads/
    pause
    exit /b 1
)

echo [INFO] Java version:
java -version
echo.

echo [INFO] Maven version:
mvn -version
echo.

REM 进入项目目录
cd /d "%~dp0"

REM 检查pom.xml是否存在
if not exist pom.xml (
    echo [ERROR] pom.xml not found in current directory.
    pause
    exit /b 1
)

REM 检查是否已经编译
if not exist target\xiaosi-nas-1.0.0.jar (
    echo [INFO] Building project first...
    call mvn clean package -DskipTests
    if %errorlevel% neq 0 (
        echo [ERROR] Build failed. Please check the error messages above.
        pause
        exit /b 1
    )
)

echo.
echo [INFO] Starting Xiaosi NAS Service on port 8083...
echo [INFO] Access the service at: http://localhost:8083
echo [INFO] Health check: http://localhost:8083/api/public/health
echo [INFO] API documentation: http://localhost:8083/api/public/info
echo.

REM 启动Spring Boot应用
java -jar target\xiaosi-nas-1.0.0.jar

pause