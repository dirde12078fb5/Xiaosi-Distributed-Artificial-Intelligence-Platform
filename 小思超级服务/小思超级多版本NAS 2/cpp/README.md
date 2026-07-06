# 小思超级多版本NAS服务 - C++版本

基于现代C++ (C++17) 实现的高性能NAS服务。

## 功能特性

- ✅ 完整的文件管理API（上传、下载、删除、复制、移动）
- ✅ 目录操作（列表、创建、搜索）
- ✅ 28种语言国际化支持
- ✅ RESTful API设计
- ✅ CORS跨域支持
- ✅ 配置文件支持
- ✅ 轻量高效

## 快速开始

### 前置要求

- C++17兼容编译器 (GCC 8+, Clang 7+, MSVC 2017+)
- CMake 3.15+

### 依赖库

本项目使用以下header-only库：

1. **cpp-httplib** - 轻量级HTTP服务器
2. **nlohmann/json** - JSON处理库

### 安装依赖

#### 方式1: 手动下载

```bash
# 创建第三方库目录
mkdir -p third_party

# 下载cpp-httplib
cd third_party
wget https://raw.githubusercontent.com/yhirose/cpp-httplib/master/httplib.h

# 下载nlohmann/json
wget https://raw.githubusercontent.com/nlohmann/json/v3.11.2/single_include/nlohmann/json.hpp -O json.hpp
cd ..
```

#### 方式2: 使用vcpkg

```bash
vcpkg install httplib nlohmann-json
```

### 构建项目

#### Windows (Visual Studio)

```cmd
mkdir build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release
```

或者直接运行:

```cmd
build.bat
```

#### Linux/macOS

```bash
mkdir build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
```

或使用Makefile:

```bash
make
```

### 运行服务

#### Windows

```cmd
start.bat
```

#### Linux/macOS

```bash
./nas_server
# 或
make run
```

## API文档

### 基础API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/ | 欢迎信息 |
| GET | /api/health | 健康检查 |
| GET | /api/config | 获取配置 |

### 文件操作

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/files | 列出文件 |
| POST | /api/files/upload | 上传文件 |
| GET | /api/files/download | 下载文件 |
| DELETE | /api/files | 删除文件 |
| POST | /api/files/mkdir | 创建目录 |
| POST | /api/files/copy | 复制文件 |
| POST | /api/files/move | 移动文件 |

### 搜索

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/search | 搜索文件 |

### 系统信息

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/system/info | 系统信息 |
| GET | /api/system/storage | 存储统计 |

### 国际化

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/i18n/languages | 支持的语言列表 |
| GET | /api/i18n/translations | 获取翻译 |

## 使用示例

### 获取欢迎信息

```bash
curl http://localhost:8086/api/
```

### 上传文件

```bash
curl -X POST -F "file=@test.txt" http://localhost:8086/api/files/upload
```

### 列出文件

```bash
curl http://localhost:8086/api/files?path=./data
```

### 下载文件

```bash
curl -O http://localhost:8086/api/files/download?path=./data/test.txt
```

### 搜索文件

```bash
curl "http://localhost:8086/api/search?q=test"
```

### 多语言支持

```bash
# 获取英文翻译
curl http://localhost:8086/api/?lang=en

# 使用Header指定语言
curl -H "Accept-Language: ja" http://localhost:8086/api/
```

## 支持的语言 (28种)

| 代码 | 语言 | 代码 | 语言 |
|------|------|------|------|
| zh-CN | 简体中文 | zh-TW | 繁体中文 |
| en | 英语 | ja | 日语 |
| ko | 韩语 | fr | 法语 |
| de | 德语 | es | 西班牙语 |
| it | 意大利语 | pt | 葡萄牙语 |
| ru | 俄语 | ar | 阿拉伯语 |
| hi | 印地语 | th | 泰语 |
| vi | 越南语 | id | 印尼语 |
| ms | 马来语 | tr | 土耳其语 |
| pl | 波兰语 | nl | 荷兰语 |
| sv | 瑞典语 | no | 挪威语 |
| da | 丹麦语 | fi | 芬兰语 |
| cs | 捷克语 | hu | 匈牙利语 |
| ro | 罗马尼亚语 | uk | 乌克兰语 |
| el | 希腊语 | | |

## 配置文件

配置文件路径: `../config/config.json`

```json
{
  "port": 8086,
  "host": "0.0.0.0",
  "data_dir": "./data",
  "upload_dir": "./uploads",
  "log_level": "info",
  "max_upload_size": 104857600
}
```

## 项目结构

```
cpp/
├── main.cpp              # 主程序源码
├── CMakeLists.txt        # CMake配置
├── Makefile             # Make构建文件
├── start.bat            # Windows启动脚本
├── build.bat            # Windows构建脚本
├── README.md            # 项目文档
└── third_party/         # 第三方库
    ├── httplib.h        # cpp-httplib库
    └── json.hpp         # nlohmann/json库
```

## 技术栈

- **C++17** - 现代C++标准
- **cpp-httplib** - 轻量级HTTP服务器库
- **nlohmann/json** - JSON处理库
- **CMake** - 构建系统

## 许可证

MIT License

## 作者

小思超级多版本NAS服务团队