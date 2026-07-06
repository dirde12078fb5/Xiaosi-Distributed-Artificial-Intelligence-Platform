@echo off
chcp 65001 >nul
echo ========================================
echo    小思超级多版本NAS - 第二代
echo    支持20种编程语言
echo ========================================
echo.
echo 请选择要启动的语言版本：
echo.
echo 第一梯队（高性能）：
echo  1. Python   (端口8080) - 零依赖，开箱即用
echo  2. Node.js  (端口8081) - Express框架，前端友好
echo  3. Go       (端口8082) - 高性能编译版
echo  4. Java     (端口8083) - Spring Boot生态
echo  5. Rust     (端口8084) - 内存安全，极致性能
echo.
echo 第二梯队（企业级）：
echo  6. C#       (端口8085) - .NET Core跨平台
echo  7. C++      (端口8086) - 原生性能
echo  8. Ruby     (端口8087) - Sinatra简洁
echo  9. PHP      (端口8088) - 原生PHP内置服务器
echo  10. Swift   (端口8089) - Apple生态原生支持
echo.
echo 第三梯队（现代语言）：
echo  11. Kotlin     (端口8090) - JetBrains官方语言
echo  12. TypeScript (端口8091) - 类型安全的JavaScript
echo  13. Dart       (端口8092) - Flutter生态
echo  14. Scala      (端口8093) - JVM函数式编程
echo  15. Lua        (端口8094) - 轻量级脚本
echo.
echo 第四梯队（小众精品）：
echo  16. Perl     (端口8095) - 文本处理强大
echo  17. Crystal  (端口8096) - Ruby语法C性能
echo  18. Nim      (端口8097) - Python语法C性能
echo  19. Elixir   (端口8098) - Erlang VM并发
echo  20. F#       (端口8099) - .NET函数式编程
echo.
echo  0. 退出
echo.
set /p choice="请输入选项编号 (0-20): "

if "%choice%"=="0" exit
if "%choice%"=="1" cd python && start.bat
if "%choice%"=="2" cd nodejs && start.bat
if "%choice%"=="3" cd go && start.bat
if "%choice%"=="4" cd java && start.bat
if "%choice%"=="5" cd rust && start.bat
if "%choice%"=="6" cd csharp && start.bat
if "%choice%"=="7" cd cpp && start.bat
if "%choice%"=="8" cd ruby && start.bat
if "%choice%"=="9" cd php && start.bat
if "%choice%"=="10" cd swift && start.sh
if "%choice%"=="11" cd kotlin && start.bat
if "%choice%"=="12" cd typescript && start.bat
if "%choice%"=="13" cd dart && start.bat
if "%choice%"=="14" cd scala && start.bat
if "%choice%"=="15" cd lua && start.bat
if "%choice%"=="16" cd perl && start.bat
if "%choice%"=="17" cd crystal && start.bat
if "%choice%"=="18" cd nim && start.bat
if "%choice%"=="19" cd elixir && start.bat
if "%choice%"=="20" cd fsharp && start.bat

echo.
echo 启动失败或选项无效，请检查输入。
pause