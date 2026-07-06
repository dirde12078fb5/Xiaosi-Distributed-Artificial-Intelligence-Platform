@echo off
chcp 65001 >nul
title 下载第三方依赖库

echo ====================================
echo 下载NAS服务所需第三方库
echo ====================================
echo.

REM 创建第三方库目录
if not exist third_party (
    echo 创建第三方库目录...
    mkdir third_party
)

cd third_party

REM 检查是否已存在
if exist httplib.h (
    echo httplib.h 已存在，跳过下载
) else (
    echo 下载 cpp-httplib...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/yhirose/cpp-httplib/master/httplib.h' -OutFile 'httplib.h'}"
    if %errorlevel% neq 0 (
        echo 下载 httplib.h 失败！
        echo 请手动下载: https://raw.githubusercontent.com/yhirose/cpp-httplib/master/httplib.h
    )
)

if exist json.hpp (
    echo json.hpp 已存在，跳过下载
) else (
    echo 下载 nlohmann/json...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/nlohmann/json/v3.11.2/single_include/nlohmann/json.hpp' -OutFile 'json.hpp'}"
    if %errorlevel% neq 0 (
        echo 下载 json.hpp 失败！
        echo 请手动下载: https://raw.githubusercontent.com/nlohmann/json/v3.11.2/single_include/nlohmann/json.hpp
    )
)

cd ..

echo.
echo ====================================
echo 第三方库下载完成
echo ====================================
echo.

pause