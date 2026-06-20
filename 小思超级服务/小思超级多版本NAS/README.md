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

    style FileManager fill:#ffb3d9
    style UserManager fill:#ffe6b3
    style StatsCollector fill:#b3ffff
    style SettingsMgr fill:#d9ffb3
```

### 组件架构图（后端详细结构）

```mermaid
graph TB
    subgraph "API网关层"
        Router[路由分发<br/>统一入口]
        Middleware[中间件<br/>日志/跨域/限流]
    end
    
    subgraph "认证授权层"
        Login[用户登录<br/>POST /api/auth/login]
        Token[JWT生成<br/>Token验证]
        Session[会话管理<br/>用户状态]
    end
    
    subgraph "业务逻辑层"
        FileManager[文件管理<br/>上传/下载/删除/列表]
        UserManager[用户管理<br/>CRUD/权限]
        StatsCollector[数据统计<br/>存储/访问统计]
        SettingsMgr[系统设置<br/>配置管理]
    end
    
    subgraph "数据访问层"
        FileStorage[文件存储<br/>文件系统操作]
        UserDB[用户数据<br/>内存存储]
        ConfigReader[配置读取<br/>环境变量/文件]
    end
    
    Router --> Middleware
    Middleware --> Login
    Middleware --> FileManager
    Middleware --> UserManager
    Middleware --> StatsCollector
    Middleware --> SettingsMgr
    
    Login --> Token
    Login --> Session
    Token --> UserDB
    Session --> UserDB
    
    FileManager --> FileStorage
    UserManager --> UserDB
    StatsCollector --> FileStorage
    SettingsMgr --> ConfigReader
    
    style Router fill:#ffcccc
    style Middleware fill:#ffd9b3
    style Login fill:#b3ffb3
    style Token fill:#b3e6ff
    style Session fill:#e6b3ff
    style FileManager fill:#ffb3d9
    style UserManager fill:#ffe6b3
    style StatsCollector fill:#b3ffff
    style SettingsMgr fill:#d9ffb3
```

### 数据流架构图

```mermaid
flowchart LR
    subgraph Request[客户端请求]
        R1[文件列表请求]
        R2[文件上传请求]
        R3[用户登录请求]
        R4[统计数据请求]
    end
    
    subgraph Process[处理流程]
        P1[请求验证]
        P2[参数解析]
        P3[业务处理]
        P4[数据存储]
        P5[响应封装]
    end
    
    subgraph Storage[存储系统]
        S1[文件存储<br/>./storage]
        S2[配置存储<br/>./config]
        S3[临时存储<br/>./temp]
        S4[内存存储<br/>会话/缓存]
    end
    
    subgraph Response[响应数据]
        Resp1[JSON响应]
        Resp2[文件流]
        Resp3[错误信息]
    end
    
    R1 & R2 & R3 & R4 --> P1
    P1 --> P2
    P2 --> P3
    P3 --> P4
    P4 --> P5
    P5 --> Response
    
    P3 -->|文件操作| S1
    P3 -->|配置读写| S2
    P3 -->|临时文件| S3
    P3 -->|用户会话| S4
    
    style Request fill:#e6f3ff
    style Process fill:#fff5e6
    style Storage fill:#e6ffe6
    style Response fill:#ffe6f0
```

### 安全架构图

```mermaid
graph TB
    subgraph Client[客户端安全]
        C1[浏览器安全<br/>HTTPS加密]
        C2[Cookie安全<br/>HttpOnly/Secure]
        C3[XSS防护<br/>输入过滤]
    end
    
    subgraph Transport[传输安全]
        T1[TLS/SSL<br/>传输层加密]
        T2[CORS策略<br/>跨域控制]
        T3[请求限流<br/>防DDoS]
    end
    
    subgraph ServerAuth[服务端认证]
        A1[用户认证<br/>密码验证]
        A2[Token认证<br/>JWT验证]
        A3[权限控制<br/>RBAC角色]
    end
    
    subgraph DataSecurity[数据安全]
        D1[密码加密<br/>bcrypt/盐值]
        D2[敏感数据<br/>脱敏处理]
        D3[文件安全<br/>路径遍历防护]
    end
    
    subgraph Audit[审计日志]
        L1[访问日志<br/>操作记录]
        L2[错误日志<br/>异常追踪]
        L3[安全日志<br/>攻击检测]
    end
    
    Client --> Transport
    Transport --> ServerAuth
    ServerAuth --> DataSecurity
    DataSecurity --> Audit
    
    style Client fill:#ffeeee
    style Transport fill:#eeffee
    style ServerAuth fill:#eeeeff
    style DataSecurity fill:#ffffee
    style Audit fill:#eeffff
```

### 部署架构图

```mermaid
graph TB
    subgraph Users[用户层]
        Browser[浏览器访问]
        Mobile[移动端]
        APIClient[API客户端]
    end
    
    subgraph LoadBalancer[负载均衡层]
        LB[负载均衡器<br/>Nginx/Traefik]
    end
    
    subgraph ServerCluster[服务器集群]
        Server1[服务器1<br/>实例1]
        Server2[服务器2<br/>实例2]
        Server3[服务器3<br/>实例3]
    end
    
    subgraph StorageCluster[存储层]
        NFS[网络文件系统<br/>NFS共享存储]
        Local[本地存储<br/>各服务器本地]
        Cloud[云存储<br/>S3/OSS]
    end
    
    subgraph Monitoring[监控层]
        Metrics[性能监控<br/>Prometheus]
        Logs[日志收集<br/>ELK Stack]
        Alert[告警系统<br/>PagerDuty]
    end
    
    Users --> LB
    LB --> Server1 & Server2 & Server3
    Server1 & Server2 & Server3 --> NFS
    Server1 & Server2 & Server3 --> Local
    Server1 & Server2 & Server3 --> Cloud
    Server1 & Server2 & Server3 --> Monitoring
    
    style Users fill:#ffe6e6
    style LoadBalancer fill:#e6ffe6
    style ServerCluster fill:#e6e6ff
    style StorageCluster fill:#ffffe6
    style Monitoring fill:#e6ffff
```

### 模块依赖关系图

```mermaid
graph TD
    subgraph Frontend[前端模块]
        UI[用户界面]
        Router[路由管理]
        State[状态管理]
        API[API调用]
    end
    
    subgraph Backend[后端模块]
        Server[服务器主程序]
        Route[路由分发]
        Middleware[中间件]
        Controller[控制器]
        Service[业务服务]
        Model[数据模型]
        Utils[工具函数]
    end
    
    subgraph Database[数据层]
        Config[配置文件]
        Storage[文件存储]
        Session[会话存储]
        Cache[缓存系统]
    end
    
    subgraph Auth[认证模块]
        Login[登录服务]
        JWT[JWT令牌]
        Password[密码加密]
        Permission[权限控制]
    end
    
    UI --> Router
    Router --> State
    State --> API
    API --> Server
    
    Server --> Route
    Route --> Middleware
    Middleware --> Controller
    Controller --> Service
    Service --> Model
    Service --> Utils
    
    Controller --> Login
    Login --> JWT
    Login --> Password
    Service --> Permission
    
    Model --> Config
    Model --> Storage
    Service --> Session
    Utils --> Cache
    
    style Frontend fill:#ffe6e6
    style Backend fill:#e6ffe6
    style Database fill:#e6e6ff
    style Auth fill:#ffffe6
```

### 文件操作流程图

```mermaid
flowchart TD
    A[用户发起文件操作] --> B{操作类型}
    
    B -->|上传| C[验证文件大小]
    B -->|下载| D[验证文件存在]
    B -->|删除| E[验证文件权限]
    B -->|列表| F[读取目录内容]
    
    C --> G{文件大小检查}
    G -->|超限| H[返回错误]
    G -->|正常| I[保存到临时目录]
    I --> J[移动到存储目录]
    J --> K[更新文件索引]
    K --> L[返回上传成功]
    
    D --> M{文件存在检查}
    M -->|不存在| N[返回404错误]
    M -->|存在| O[读取文件内容]
    O --> P[返回文件流]
    
    E --> Q{权限检查}
    Q -->|无权限| R[返回403错误]
    Q -->|有权限| S[删除文件]
    S --> T[更新文件索引]
    T --> U[返回删除成功]
    
    F --> V[检查目录路径]
    V --> W{路径有效}
    W -->|无效| X[返回错误]
    W -->|有效| Y[遍历目录]
    Y --> Z[构建文件列表]
    Z --> AA[返回JSON数据]
    
    style A fill:#ff9999
    style L fill:#99ff99
    style P fill:#9999ff
    style U fill:#99ff99
    style AA fill:#99ffff
```

### 完整API交互序列图

```mermaid
sequenceDiagram
    participant U as 👤 用户
    participant F as 🌐 前端浏览器
    participant S as ⚙️ 后端服务器
    participant A as 🔐 认证服务
    participant DB as 💾 用户数据库
    participant FS as 📁 文件系统
    
    Note over U,F: 1️⃣ 首次访问
    U->>F: 访问 http://localhost:8080
    F->>S: GET /
    S-->>F: 返回 index.html
    F->>F: 渲染登录页面
    
    Note over U,F: 2️⃣ 用户登录
    U->>F: 输入用户名密码
    F->>S: POST /api/auth/login
    S->>A: 验证用户凭据
    A->>DB: 查询用户
    DB-->>A: 返回用户数据
    A-->>S: 验证通过
    S-->>F: 返回 JWT Token
    F->>F: 保存 Token 到本地存储
    
    Note over U,F: 3️⃣ 获取仪表盘数据
    F->>S: GET /api/stats (携带Token)
    S->>A: 验证 Token 有效性
    A-->>S: Token 有效
    S->>FS: 读取存储统计
    FS-->>S: 返回统计数据
    S-->>F: 返回统计数据
    F->>F: 渲染仪表盘
    
    Note over U,F: 4️⃣ 浏览文件列表
    F->>S: GET /api/files (携带Token)
    S->>FS: 读取文件列表
    FS-->>S: 返回文件列表
    S-->>F: 返回文件列表JSON
    F->>F: 渲染文件列表
    
    Note over U,F: 5️⃣ 上传新文件
    U->>F: 选择文件并上传
    F->>S: POST /api/files/upload
    S->>FS: 保存文件到存储
    FS-->>S: 文件保存成功
    S-->>F: 返回上传成功
    F->>F: 更新文件列表显示
    
    Note over U,F: 6️⃣ 获取用户列表
    F->>S: GET /api/users (携带Token)
    S->>DB: 查询所有用户
    DB-->>S: 返回用户列表
    S-->>F: 返回用户列表
    F->>F: 渲染用户管理页面
    
    Note over U,F: 7️⃣ 获取系统设置
    F->>S: GET /api/settings (携带Token)
    S-->>F: 返回系统设置
    F->>F: 渲染设置页面
    
    Note over U,F: 8️⃣ 登出系统
    U->>F: 点击登出按钮
    F->>F: 清除本地 Token
    F->>F: 跳转到登录页面
```

### 网络请求流程图

```mermaid
flowchart LR
    subgraph Browser[🌐 浏览器]
        B1[用户界面]
        B2[JavaScript引擎]
        B3[网络模块]
        B4[本地存储]
    end
    
    subgraph Request[📨 HTTP请求]
        R1[请求构建]
        R2[请求头设置]
        R3[Token附加]
        R4[发送请求]
    end
    
    subgraph Server[🖥️ 服务器处理]
        S1[接收请求]
        S2[中间件处理]
        S3[路由匹配]
        S4[控制器处理]
        S5[业务逻辑]
    end
    
    subgraph Response[📨 HTTP响应]
        Res1[响应构建]
        Res2[JSON序列化]
        Res3[状态码设置]
        Res4[返回客户端]
    end
    
    subgraph Data[💾 数据处理]
        D1[数据库操作]
        D2[文件IO操作]
        D3[缓存处理]
        D4[配置读取]
    end
    
    B1 --> B2
    B2 --> B3
    B3 --> R1
    R1 --> R2
    R2 --> R3
    R3 --> R4
    
    R4 --> S1
    S1 --> S2
    S2 --> S3
    S3 --> S4
    S4 --> S5
    
    S5 --> Res1
    Res1 --> Res2
    Res2 --> Res3
    Res3 --> Res4
    
    S5 --> D1
    S5 --> D2
    S5 --> D3
    S5 --> D4
    
    Res4 --> B3
    B3 --> B4
    
    style Browser fill:#e6f3ff
    style Request fill:#fff5e6
    style Server fill:#e6ffe6
    style Response fill:#ffe6f0
    style Data fill:#f0e6ff
```

### 用户认证流程图

```mermaid
flowchart TD
    A[👤 用户访问] --> B{是否已登录}
    
    B -->|是| C[检查Token有效性]
    C --> D{Token过期?}
    D -->|否| E[允许访问]
    D -->|是| F[尝试刷新Token]
    F --> G{刷新成功?}
    G -->|是| E
    G -->|否| H[跳转登录页]
    
    B -->|否| I{访问登录页?}
    I -->|是| J[显示登录表单]
    I -->|否| K[验证访问权限]
    K --> L{有权限?}
    L -->|是| E
    L -->|否| M[返回403禁止]
    
    J --> N{输入凭据}
    N --> O[提交登录请求]
    O --> P{验证成功?}
    P -->|是| Q[生成JWT Token]
    Q --> R[返回Token给前端]
    R --> S[前端存储Token]
    S --> E
    P -->|否| T[返回错误信息]
    T --> J
    
    E --> U[访问受保护资源]
    U --> V[返回请求内容]
    
    style A fill:#ff9999
    style E fill:#99ff99
    style H fill:#ff6666
    style M fill:#ff6666
    style T fill:#ffcc66
    style V fill:#99ff99
```

### 多语言版本技术对比图

```mermaid
graph TD
    subgraph Python[🐍 Python]
        P1[Flask框架]
        P2[JWT认证]
        P3[bcrypt加密]
        P4[自动安装依赖]
        P5[跨平台支持]
    end
    
    subgraph NodeJS[🟢 Node.js]
        N1[Express框架]
        N2[异步非阻塞]
        N3[npm生态]
        N4[高并发支持]
        N5[实时应用]
    end
    
    subgraph Java[☕ Java]
        J1[HttpServer]
        J2[无额外依赖]
        J3[强类型]
        J4[企业级]
        J5[JDK 11+]
    end
    
    subgraph PHP[🐘 PHP]
        PH1[内置服务器]
        PH2[广泛兼容]
        PH3[易于部署]
        PH4[共享主机]
        PH5[PHP 7.4+]
    end
    
    subgraph C[C语言]
        C1[Socket API]
        C2[高性能]
        C3[最小占用]
        C4[编译运行]
        C5[跨平台编译]
    end
    
    subgraph Shell[🐚 Shell]
        SH1[Bash脚本]
        SH2[Python HTTP]
        SH3[轻量级]
        SH4[Linux专用]
        SH5[快速启动]
    end
    
    subgraph Go[🔵 Go语言] 🆕
        G1[Gorilla Mux]
        G2[并发模型]
        G3[单二进制文件]
        G4[高性能]
        G5[跨平台编译]
    end
    
    subgraph Rust[🦀 Rust] 🆕
        R1[Actix-web]
        R2[内存安全]
        R3[零成本抽象]
        R4[极致性能]
        R5[无GC]
    end
    
    subgraph Ruby[💎 Ruby] 🆕
        RB1[Sinatra框架]
        RB2[优雅语法]
        RB3[Ruby生态]
        RB4[元编程能力]
        RB5[快速开发]
    end
    
    subgraph Kotlin[🟣 Kotlin] 🆕
        K1[Ktor框架]
        K2[协程支持]
        K3[JVM互操作]
        K4[空安全类型]
        K5[现代语法]
    end
    
    subgraph Swift[🍎 Swift] 🆕
        S1[Vapor 4框架]
        S2[Apple生态]
        S3[协议导向]
        S4[内存管理]
        S5[iOS/macOS集成]
    end
    
    style Python fill:#ffcccc
    style NodeJS fill:#ccffcc
    style Java fill:#ccccff
    style PHP fill:#ffccff
    style C fill:#ffffcc
    style Shell fill:#ccffff
    style Go fill:#cce6ff
    style Rust fill:#ffd9b3
    style Ruby fill:#e6ccff
    style Kotlin fill:#ffe6f0
    style Swift fill:#d9ffb3
```

## 🚀 快速开始

### 选择您的语言版本

本项目提供 **11种** 语言实现：

#### 🐍 解释型语言 (无需编译)

1. **Python版本** - 易于部署，生态丰富
   - 路径: [01_python_version](01_python_version/)
   - 框架: Flask
   - 启动: 双击 `scripts\启动.bat`

2. **Node.js版本** - 异步高性能
   - 路径: [02_nodejs_version](02_nodejs_version/)
   - 框架: Express
   - 启动: 双击 `scripts\启动.bat`

3. **PHP版本** - 广泛兼容
   - 路径: [04_php_version](04_php_version/)
   - 框架: 内置服务器
   - 启动: 双击 `scripts\启动.bat`

4. **Ruby版本** - 优雅简洁
   - 路径: [09_ruby_version](09_ruby_version/)
   - 框架: Sinatra
   - 启动: 双击 `scripts\启动.bat`

5. **Shell版本** - Linux/Unix专用
   - 路径: [06_shell_version](06_shell_version/)
   - 框架: Python HTTP + Bash
   - 启动: 运行 `scripts/启动.sh`

#### ⚙️ 编译型语言 (需要编译)

6. **Java版本** - 企业级可靠性
   - 路径: [03_java_version](03_java_version/)
   - 框架: JDK内置HttpServer
   - 启动: 双击 `scripts\启动.bat`

7. **Go语言版本** - 高并发性能
   - 路径: [07_go_version](07_go_version/)
   - 框架: Gorilla Mux
   - 启动: 双击 `scripts\启动.bat`

8. **Rust语言版本** - 内存安全+极致性能
   - 路径: [08_rust_version](08_rust_version/)
   - 框架: Actix-web
   - 启动: 双击 `scripts\启动.bat` (首次编译较慢)

9. **C语言版本** - 极致性能
   - 路径: [05_c_version](05_c_version/)
   - 框架: 原生Socket API
   - 编译: 双击 `scripts\编译.bat`
   - 启动: 双击 `scripts\启动.bat`

10. **Kotlin版本** - 现代化JVM语言
    - 路径: [10_kotlin_version](10_kotlin_version/)
    - 框架: Ktor
    - 启动: 双击 `scripts\启动.bat`

11. **Swift语言版本** - Apple生态系统
    - 路径: [11_swift_version](11_swift_version/)
    - 框架: Vapor 4
    - 启动: 运行 `scripts/启动.sh` (需要macOS或Linux)

## 📁 项目结构

```
小思超级NAS/
├── 01_python_version/          # Python版本 (Flask)
│   ├── src/                    # 源代码
│   ├── config/                 # 配置文件
│   └── scripts/                # 启动脚本
├── 02_nodejs_version/          # Node.js版本 (Express)
│   ├── src/
│   ├── config/
│   └── scripts/
├── 03_java_version/            # Java版本 (HttpServer)
│   ├── src/
│   ├── config/
│   └── scripts/
├── 04_php_version/            # PHP版本 (内置服务器)
│   ├── src/
│   ├── config/
│   └── scripts/
├── 05_c_version/               # C语言版本 (Socket API)
│   ├── src/
│   ├── config/
│   └── scripts/
├── 06_shell_version/          # Shell版本 (Python HTTP)
│   ├── src/
│   ├── config/
│   └── scripts/
├── 07_go_version/              # Go语言版本 (Gorilla Mux) 🆕
│   ├── src/
│   ├── config/
│   └── scripts/
├── 08_rust_version/            # Rust语言版本 (Actix-web) 🆕
│   ├── src/
│   ├── config/
│   └── scripts/
├── 09_ruby_version/            # Ruby版本 (Sinatra) 🆕
│   ├── src/
│   ├── config/
│   └── scripts/
├── 10_kotlin_version/          # Kotlin版本 (Ktor) 🆕
│   ├── src/
│   ├── config/
│   └── scripts/
├── 11_swift_version/           # Swift版本 (Vapor) 🆕
│   ├── src/
│   ├── config/
│   └── scripts/
└── public/                     # 公共前端文件 (所有版本共享)
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

### Go语言版本 🆕
- Gorilla Mux (路由)
- dgrijalva/jwt-go (JWT认证)
- golang.org/x/crypto (bcrypt加密)

### Rust语言版本 🆕
- Actix-web 4 (高性能Web框架)
- jsonwebtoken (JWT认证)
- bcrypt (密码加密)
- serde (序列化/反序列化)

### Ruby版本 🆕
- Sinatra 3.0 (轻量级Web框架)
- jwt gem (JWT认证)
- bcrypt gem (密码加密)

### Kotlin版本 🆕
- Ktor (异步Web框架)
- jjwt (JWT认证)
- kotlinx.serialization (JSON处理)

### Swift版本 🆕
- Vapor 4 (服务器端Swift框架)
- Vapor JWT插件 (JWT认证)
- Fluent ORM (数据库操作)

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
