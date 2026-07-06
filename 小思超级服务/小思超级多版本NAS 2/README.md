# 小思超级多版本NAS服务 - 第二代

<p align="center">
  <img src="https://img.shields.io/badge/Version-2.0-brightgreen.svg" alt="Version">
  <img src="https://img.shields.io/badge/Languages-20-orange.svg" alt="Languages">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Mac-lightgrey.svg" alt="Platform">
  <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License">
</p>

一款功能强大的跨平台NAS管理服务，支持**20种编程语言**实现，提供局域网文件推送、存储管理、用户管理、SMB共享等核心功能。

**第二代全新升级：**
- 🚀 支持20种编程语言实现（第一代仅3种）
- 🌍 支持28种界面语言
- 🔧 统一API接口，跨语言兼容
- 📦 每个版本独立可运行
- 🎯 配置文件互通，数据共享

---

## 📋 目录

- [支持的语言版本](#支持的语言版本)
- [快速开始](#快速开始)
- [功能特性](#功能特性)
- [API接口](#api接口)
- [配置说明](#配置说明)
- [开发指南](#开发指南)

---

## 🎯 支持的语言版本

### 第一梯队（高性能）⭐⭐⭐

| 语言 | 目录 | 默认端口 | 启动方式 | 特色 |
|------|------|----------|----------|------|
| 🐍 **Python** | `python/` | 8080 | `python nas_server.py` | 零依赖，开箱即用 |
| 🟢 **Node.js** | `nodejs/` | 8081 | `npm start` | Express框架，前端友好 |
| 🐹 **Go** | `go/` | 8082 | `go run main.go` | 高性能编译版 |
| ☕ **Java** | `java/` | 8083 | `mvn spring-boot:run` | Spring Boot生态 |
| 🦀 **Rust** | `rust/` | 8084 | `cargo run` | 内存安全，极致性能 |

### 第二梯队（企业级）⭐⭐

| 语言 | 目录 | 默认端口 | 启动方式 | 特色 |
|------|------|----------|----------|------|
| 💜 **C#** | `csharp/` | 8085 | `dotnet run` | .NET Core跨平台 |
| ⚡ **C++** | `cpp/` | 8086 | `./nas_server` | 原生性能 |
| 💎 **Ruby** | `ruby/` | 8087 | `ruby server.rb` | Sinatra简洁 |
| 🐘 **PHP** | `php/` | 8088 | `php -S localhost:8088` | 原生PHP内置服务器 |
| 🍎 **Swift** | `swift/` | 8089 | `swift run` | Apple生态原生支持 |

### 第三梯队（现代语言）⭐

| 语言 | 目录 | 默认端口 | 启动方式 | 特色 |
|------|------|----------|----------|------|
| 🎯 **Kotlin** | `kotlin/` | 8090 | `java -jar nas.jar` | JetBrains官方语言 |
| 📘 **TypeScript** | `typescript/` | 8091 | `npm start` | 类型安全的JavaScript |
| 🎯 **Dart** | `dart/` | 8092 | `dart run bin/server.dart` | Flutter生态 |
| 🔴 **Scala** | `scala/` | 8093 | `sbt run` | JVM函数式编程 |
| 🌙 **Lua** | `lua/` | 8094 | `lua server.lua` | 轻量级脚本 |

### 第四梯队（小众精品）✨

| 语言 | 目录 | 默认端口 | 启动方式 | 特色 |
|------|------|----------|----------|------|
| 🐪 **Perl** | `perl/` | 8095 | `perl server.pl` | 文本处理强大 |
| 💎 **Crystal** | `crystal/` | 8096 | `crystal run src/server.cr` | Ruby语法C性能 |
| 🎯 **Nim** | `nim/` | 8097 | `nim c -r server.nim` | Python语法C性能 |
| 💧 **Elixir** | `elixir/` | 8098 | `mix phx.server` | Erlang VM并发 |
| 🔷 **F#** | `fsharp/` | 8099 | `dotnet run` | .NET函数式编程 |

---

## 🚀 快速开始

### 方式一：选择你熟悉的语言

```bash
# Python版本（推荐新手）
cd python
python nas_server.py

# Node.js版本（前端开发者）
cd nodejs
npm install && npm start

# Go版本（追求性能）
cd go
go run main.go

# Rust版本（追求极致性能和内存安全）
cd rust
cargo run
```

### 方式二：统一启动脚本

**Windows:**
```bash
# 启动Python版本
start_python.bat

# 启动Node.js版本
start_nodejs.bat

# 启动Go版本
start_go.bat
```

**Linux/macOS:**
```bash
# 启动Python版本
./start_python.sh

# 启动Node.js版本
./start_nodejs.sh

# 启动Go版本
./start_go.sh
```

### 访问服务

- Python版本：**http://localhost:8080**
- Node.js版本：**http://localhost:8081**
- Go版本：**http://localhost:8082**
- 其他版本：根据上表端口号访问

---

## ✨ 功能特性

### 核心功能

- **存储卷管理** - 创建、删除、查询存储卷，支持配额设置
- **用户管理** - 用户CRUD操作，密码加密存储
- **SMB共享** - 创建文件共享，设置读写权限
- **文件夹推送** - 局域网内一键推送文件夹到其他NAS设备
- **IP检测** - 自动检测本机所有网卡IP地址
- **设备发现** - 局域网设备扫描发现

### 多语言支持

支持 **28种界面语言**：

| 区域 | 语言 |
|------|------|
| 中文 | 🇨🇳 简体中文、🇹🇼 繁体中文 |
| 英语 | 🇺🇸 美式英语、🇬🇧 英式英语 |
| 东亚 | 🇯🇵 日语、🇰🇷 韩语 |
| 欧洲 | 🇩🇪 德语、🇫🇷 法语、🇪🇸 西班牙语、🇮🇹 意大利语、🇵🇹 葡萄牙语 |
| 东欧 | 🇷🇺 俄语、🇺🇦 乌克兰语、🇵🇱 波兰语、🇨🇿 捷克语 |
| 中东 | 🇸🇦 阿拉伯语、🇮🇱 希伯来语、🇹🇷 土耳其语 |
| 亚洲其他 | 🇮🇳 印地语、🇹🇭 泰语、🇻🇳 越南语、🇮🇩 印尼语 |
| 北欧 | 🇳🇱 荷兰语、🇸🇪 瑞典语、🇩🇰 丹麦语、🇫🇮 芬兰语 |
| 其他 | 🇭🇺 匈牙利语、🇷🇴 罗马尼亚语 |

### 跨语言特性

- ✅ 统一配置文件格式（JSON）
- ✅ 统一API接口规范
- ✅ 数据共享（所有版本使用相同数据目录）
- ✅ 文件推送协议兼容
- ✅ 多语言界面切换

---

## 📚 API接口

所有语言版本提供统一的REST API：

### 存储管理

```
GET    /api/storage/volumes          # 获取存储卷列表
POST   /api/storage/volumes          # 创建存储卷
POST   /api/storage/volumes/delete   # 删除存储卷
```

### 用户管理

```
GET    /api/users                    # 获取用户列表
POST   /api/users                    # 创建用户
POST   /api/users/delete              # 删除用户
```

### SMB共享

```
GET    /api/smb/shares               # 获取共享列表
POST   /api/smb/shares                # 创建共享
POST   /api/smb/shares/delete         # 删除共享
```

### IP与推送

```
GET    /api/ip/local                 # 获取本机IP列表
GET    /api/ip/scan?port=8080        # 扫描局域网设备
GET    /api/push/targets             # 获取推送目标
POST   /api/push/targets             # 添加推送目标
POST   /api/push/folder               # 推送文件夹
GET    /api/push/status               # 推送状态/历史
POST   /api/push/receive              # 接收文件
```

### 多语言

```
GET    /api/i18n/?lang=zh_CN          # 获取翻译
```

---

## ⚙️ 配置说明

### config.json

所有版本共享同一配置文件格式：

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "language": "zh_CN"
  },
  "storage": {
    "volumes": [
      {
        "name": "data",
        "path": "/mnt/data",
        "quota_gb": 1000
      }
    ]
  },
  "smb": {
    "enabled": true,
    "port": 445,
    "workgroup": "WORKGROUP"
  },
  "push": {
    "targets": []
  },
  "data_dir": "nas_data",
  "receive_dir": "nas_data/received"
}
```

### 推送协议

使用HTTP multipart/form-data协议：

```
POST /api/push/receive
Content-Type: multipart/form-data; boundary=----XiaosiNASPush

------XiaosiNASPush
Content-Disposition: form-data; name="folder"

文件夹名称
------XiaosiNASPush
Content-Disposition: form-data; name="filepath"

子目录/文件名.txt
------XiaosiNASPush
Content-Disposition: form-data; name="file"; filename="example.txt"
Content-Type: application/octet-stream

[文件二进制内容]
------XiaosiNASPush--
```

---

## 👨‍💻 开发指南

### 目录结构

```
小思超级多版本NAS 2/
├── python/                    # Python版本
│   ├── nas_server.py
│   ├── start.bat
│   └── start.sh
├── nodejs/                    # Node.js版本
│   ├── server.js
│   ├── package.json
│   └── start.bat
├── go/                        # Go版本
│   ├── main.go
│   ├── go.mod
│   └── go.sum
├── java/                      # Java版本
│   ├── src/main/java/
│   ├── pom.xml
│   └── start.bat
├── rust/                      # Rust版本
│   ├── src/main.rs
│   └── Cargo.toml
├── csharp/                    # C#版本
│   ├── Program.cs
│   └── nas.csproj
├── cpp/                       # C++版本
│   ├── main.cpp
│   └── CMakeLists.txt
├── ruby/                      # Ruby版本
│   ├── server.rb
│   └── Gemfile
├── php/                       # PHP版本
│   ├── server.php
│   └── start.bat
├── swift/                     # Swift版本
│   ├── main.swift
│   └── Package.swift
├── kotlin/                    # Kotlin版本
│   ├── src/main/kotlin/
│   └── build.gradle.kts
├── typescript/                # TypeScript版本
│   ├── src/server.ts
│   └── package.json
├── dart/                      # Dart版本
│   ├── bin/server.dart
│   └── pubspec.yaml
├── scala/                     # Scala版本
│   ├── src/main/scala/
│   └── build.sbt
├── lua/                       # Lua版本
│   ├── server.lua
│   └── start.bat
├── perl/                      # Perl版本
│   ├── server.pl
│   └── start.bat
├── crystal/                   # Crystal版本
│   ├── src/server.cr
│   └── shard.yml
├── nim/                       # Nim版本
│   ├── server.nim
│   └── start.bat
├── elixir/                    # Elixir版本
│   ├── lib/nas.ex
│   └── mix.exs
├── fsharp/                    # F#版本
│   ├── Program.fs
│   └── nas.fsproj
├── config/                    # 共享配置
│   ├── config.json
│   └── i18n/
├── web/                       # 共享Web资源
│   ├── index.html
│   ├── css/
│   └── js/
├── nas_data/                  # 共享数据目录
│   └── received/
├── start_python.bat           # Python启动脚本
├── start_python.sh
├── start_nodejs.bat           # Node.js启动脚本
├── start_nodejs.sh
├── README.md                  # 本文档
└── LICENSE                    # MIT许可证
```

### 添加新语言版本

1. 在项目根目录创建语言目录
2. 实现核心API接口
3. 支持config.json配置
4. 添加启动脚本
5. 更新README.md

### 代码规范

- 遵循各语言的最佳实践
- 统一API接口格式
- 错误处理完整
- 日志输出清晰
- 支持配置文件

---

## 🔧 系统要求

| 语言 | 最低版本 | 推荐版本 |
|------|----------|----------|
| Python | 3.7+ | 3.11+ |
| Node.js | 16+ | 20+ |
| Go | 1.19+ | 1.21+ |
| Java | 11+ | 17+ |
| Rust | 1.65+ | 1.75+ |
| C# | .NET 6+ | .NET 8+ |
| Ruby | 2.7+ | 3.2+ |
| PHP | 7.4+ | 8.2+ |
| Swift | 5.5+ | 5.9+ |
| Kotlin | 1.7+ | 1.9+ |

---

## 📝 更新日志

### v2.0.0 (2026-07-06)

**重大更新：**
- ✨ 新增17种编程语言支持（共20种）
- 🎨 统一项目目录结构
- 📦 统一配置文件格式
- 🔧 统一API接口规范
- 📚 完善开发文档
- 🌍 支持28种界面语言

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

---

## 📧 联系方式

- 问题反馈: GitHub Issues
- 功能建议: GitHub Discussions

---

<p align="center">
  用 ❤️ 和 ☕ 构建 | 小思超级NAS服务 v2.0
</p>