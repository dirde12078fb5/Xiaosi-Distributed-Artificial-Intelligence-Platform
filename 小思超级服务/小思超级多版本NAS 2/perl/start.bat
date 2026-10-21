@echo off
REM 小思超级多版本NAS服务 - Perl版本启动脚本
REM 默认端口: 8095

echo ============================================================
echo 小思超级多版本NAS服务 - Perl版本
echo ============================================================
echo.

REM 检查Perl是否安装
where perl >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Perl未安装或未添加到PATH环境变量
    echo 请安装Perl后重试
    echo 下载地址: https://www.perl.org/get.html
    echo Windows推荐: Strawberry Perl 或 ActivePerl
    pause
    exit /b 1
)

echo [信息] Perl版本信息:
perl -v | findstr "This is perl"
echo.

REM 检查必要的Perl模块
echo [检查] 正在检查必要的Perl模块...
perl -e "use HTTP::Daemon;" 2>nul
if %errorlevel% neq 0 (
    echo [警告] HTTP::Daemon模块未安装
    echo [提示] 请安装: cpan HTTP::Daemon
)

perl -e "use JSON::PP;" 2>nul
if %errorlevel% neq 0 (
    echo [警告] JSON::PP模块未安装
    echo [提示] 请安装: cpan JSON::PP
)

perl -e "use Digest::SHA;" 2>nul
if %errorlevel% neq 0 (
    echo [警告] Digest::SHA模块未安装
    echo [提示] 请安装: cpan Digest::SHA
)

echo.
echo ============================================================
echo [启动] 正在启动NAS服务器...
echo [端口] 8095
echo [访问] http://localhost:8095/
echo ============================================================
echo.

REM 启动服务器
cd /d "%~dp0"
perl server.pl

pause