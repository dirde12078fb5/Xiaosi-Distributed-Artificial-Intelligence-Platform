# 小思超级NAS

智能存储管理平台 - 多语言版本

## 📋 项目简介

小思超级NAS是一个智能网络存储管理平台，支持多种编程语言实现，让您可以根据自己的技术栈选择最适合的版本。

## 🏗️ 系统架构

### 整体架构图

```mermaid
graph TB
    User[用户<br>浏览器/客户端]
    subgraph "前端层"
        Frontend[前端应用<br>index.html + styles.css + app.js]
    end
    subgraph "后端服务层"
        Backend[后端服务<br>多语言实现]
        Auth[认证模块<br>JWT/Bcrypt]
        FileAPI[文件API<br>上传/下载/列表]
        StatsAPI[统计API<br>存储/用户]
        SettingsAPI[设置API<br>系统配置]
    end
    subgraph "数据存储层"
        Storage[文件存储<br>./storage目录]
        Config[配置文件<br>./config目录]
        Temp[临时文件<br>./temp目录]
    end
    
    User -->|HTTP访问| Frontend
    Frontend -->|REST API| Backend
    Backend --> Auth
    Backend --> FileAPI
    Backend --> StatsAPI
    Backend --> SettingsAPI
    FileAPI --> Storage
    Auth --> Config
    Backend --> Temp
    
    style Frontend fill:#e1f5ff
    style Backend fill:#f0f9ff
    style Storage fill:#e6f7ff
```

### 目录架构图

```mermaid
graph LR
    Root[小思超级NAS/]
    Root --> P1[01_python_version/]
    Root --> P2[02_nodejs_version/]
    Root --> P3[03_java_version/]
    Root --> P4[04_php_version/]
    Root --> P5[05_c_version/]
    Root --> P6[06_shell_version/]
    Root --> Public[public/]
    
    P1 --> S1[src/app.py]
    P1 --> C1[config/.env<br>requirements.txt]
    P1 --> Sc1[scripts/启动.bat]
    
    P2 --> S2[src/server.js]
    P2 --> C2[config/.env<br>package.json]
    P2 --> Sc2[scripts/启动.bat]
    
    P3 --> S3[src/XiaosiNAS.java]
    P3 --> C3[config/config.properties]
    P3 --> Sc3[scripts/启动.bat]
    
    P4 --> S4[src/server.php]
    P4 --> C4[config/.env]
    P4 --> Sc4[scripts/启动.bat]
    
    P5 --> S5[src/main.c]
    P5 --> C5[config/config.h]
    P5 --> Sc5[scripts/启动.bat<br>编译.bat]
    
    P6 --> S6[src/nas-server.sh]
    P6 --> C6[config/config.sh]
    P6 --> Sc6[scripts/启动.sh]
    
    Public --> H[index.html]
    Public --> C[styles.css]
    Public --> J[app.js]
    
    style Public fill:#d4f7dc
    style C1 fill:#fce8e6
    style C2 fill:#fce8e6
    style C3 fill:#fce8e6
    style C4 fill:#fce8e6
    style C5 fill:#fce8e6
    style C6 fill:#fce8e6
    style Sc1 fill:#fff4e6
    style Sc2 fill:#fff4e6
    style Sc3 fill:#fff4e6
    style Sc4 fill:#fff4e6
    style Sc5 fill:#fff4e6
    style Sc6 fill:#fff4e6
```

### 技术栈架构图

```mermaid
mindmap
  root((小思超级NAS))
    前端
      HTML5
      CSS3
      Vanilla JavaScript
      JWT认证
    后端实现
      Python
        Flask框架
        JWT
        bcrypt
      Node.js
        Express框架
        JWT
        bcryptjs
      Java
        JDK内置HttpServer
      PHP
        内置服务器
      C语言
        Socket API
        Winsock2
      Shell/Bash
        Python HTTP
    数据存储
      文件系统存储
      内存用户会话
      配置文件
    安全
      JWT Token
      密码加密
      CORS跨域
```

### API架构图

```mermaid
sequenceDiagram
    participant U as 用户
    participant F as 前端
    participant B as 后端
    participant A as 认证
    participant S as 存储
    
    U->>F: 访问首页
    F->>B: GET /
    B-->>F: 200 OK (index.html)
    
    U->>F: 登录 (username/password)
    F->>B: POST /api/auth/login
    B->>A: 验证凭据
    A-->>B: 验证成功
    B-->>F: 200 OK (JWT Token)
    
    F->>B: GET /api/stats (Token)
    B-->>F: 200 OK (统计数据)
    
    F->>B: GET /api/files (Token)
    B->>S: 读取文件列表
    S-->>B: 文件列表
    B-->>F: 200 OK (文件列表)
    
    F->>B: POST /api/files/upload (Token + 文件)
    B->>S: 保存文件
    S-->>B: 保存成功
    B-->>F: 200 OK (上传成功)
```

## 🚀 快速开始

### 选择您的语言版本

本项目提供6种语言实现：

1. **Python版本** - 易于部署，无需编译
   - 路径: [01_python_version](01_python_version/)
   - 启动: 双击 `scripts\启动.bat`

2. **Node.js版本** - 高性能JavaScript运行时
   - 路径: [02_nodejs_version](02_nodejs_version/)
   - 启动: 双击 `scripts\启动.bat`

3. **Java版本** - 企业级可靠性
   - 路径: [03_java_version](03_java_version/)
   - 启动: 双击 `scripts\启动.bat`

4. **PHP版本** - 广泛兼容，易于部署
   - 路径: [04_php_version](04_php_version/)
   - 启动: 双击 `scripts\启动.bat`

5. **C语言版本** - 最高性能，需要编译
   - 路径: [05_c_version](05_c_version/)
   - 编译: 双击 `scripts\编译.bat`
   - 启动: 双击 `scripts\启动.bat`

6. **Shell版本** - Linux/Unix专用
   - 路径: [06_shell_version](06_shell_version/)
   - 启动: 运行 `scripts/启动.sh`

## 📁 项目结构

```
小思超级NAS/
├── 01_python_version/          # Python版本
│   ├── src/                    # 源代码
│   ├── config/                 # 配置文件
│   └── scripts/                # 启动脚本
├── 02_nodejs_version/          # Node.js版本
│   ├── src/                    # 源代码
│   ├── config/                 # 配置文件
│   └── scripts/                # 启动脚本
├── 03_java_version/            # Java版本
│   ├── src/                    # 源代码
│   ├── config/                 # 配置文件
│   └── scripts/                # 启动脚本
├── 04_php_version/            # PHP版本
│   ├── src/                    # 源代码
│   ├── config/                 # 配置文件
│   └── scripts/                # 启动脚本
├── 05_c_version/               # C语言版本
│   ├── src/                    # 源代码
│   ├── config/                 # 配置文件
│   └── scripts/                # 编译和启动脚本
├── 06_shell_version/          # Shell版本
│   ├── src/                    # 源代码
│   ├── config/                 # 配置文件
│   └── scripts/                # 启动脚本
└── public/                     # 公共前端文件
    ├── index.html
    ├── styles.css
    └── app.js
```

## 🌟 主要功能

- **文件管理**: 上传、下载、创建文件夹
- **用户管理**: 用户注册、权限控制
- **存储统计**: 实时存储使用情况
- **系统设置**: 灵活的配置选项
- **跨平台**: 支持Windows、Linux、macOS

## 🔐 默认登录

- 用户名: `admin`
- 密码: `admin123`

## 📡 访问地址

启动后访问：
- 本地访问: `http://localhost:8080`
- 局域网访问: `http://<您的IP地址>:8080`

## 🛠️ 技术栈

### Python版本
- Flask
- Flask-CORS
- JWT认证
- bcrypt密码加密

### Node.js版本
- Express
- CORS
- JSON Web Token
- bcryptjs

### Java版本
- JDK内置HttpServer
- 无需额外依赖

### PHP版本
- PHP内置服务器
- JSON处理

### C语言版本
- POSIX Socket API
- Windows Winsock2
- 多线程支持

### Shell版本
- Python HTTP服务器
- Bash脚本

## 📝 详细文档

- [多语言版本指南](多语言版本指南.md) - 各版本详细说明和对比

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 👨‍💻 作者

小思AI团队

## 🙏 致谢

感谢所有开源项目的贡献者！
