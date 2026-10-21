@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0.."

:menu
cls
echo ============================================================
echo   小思分布式人工智能平台 - 启动选单 (Windows)
echo ============================================================
echo.
echo   1. 网络管理模块   (WiFi 扫描 / 网络工具 GUI)
echo   2. 视觉管理模块   (摄像头 / 图像处理 GUI)
echo   3. 服务管理 - 内网通服
echo   4. 服务管理 - 外网通服
echo   5. 小思超级 PXE    (网络安装系统 GUI)
echo   0. 退出
echo.
set /p c=请输入编号后回车:
if "%c%"=="1" goto run1
if "%c%"=="2" goto run2
if "%c%"=="3" goto run3
if "%c%"=="4" goto run4
if "%c%"=="5" goto run5
if "%c%"=="0" exit /b 0
goto menu

:run1
python "小思分布式人工智能网络模块.py"
goto end
:run2
python "小思分布式视觉管理模块.py"
goto end
:run3
python "内网通服.py"
goto end
:run4
python "外网通服.py"
goto end
:run5
pushd "小思超级服务\小思超级PXE"
python gui.py
popd
goto end

:end
echo.
echo 已退出该模块。按任意键返回选单 ...
pause >nul
goto menu
endlocal
