# 小思NAS服务 - Swift版本

<p align="center">
  <img src="https://img.shields.io/badge/Swift-5.7-orange.svg" alt="Swift">
  <img src="https://img.shields.io/badge/Platform-macOS%20%7C%20Linux-lightgrey.svg" alt="Platform">
  <img src="https://img.shields.io/badge/Port-8089-blue.svg" alt="Port">
</p>

基于SwiftNIO构建的高性能NAS服务实现。

## 🚀 快速开始

### 系统要求

- Swift 5.7 或更高版本
- macOS 12+ 或 Linux

### 安装Swift

**macOS:**
```bash
# Swift已预装在macOS上，或通过Xcode安装
xcode-select --install
```

**Linux:**
```bash
# Ubuntu/Debian
wget https://swift.org/builds/swift-5.9-release/ubuntu2204/swift-5.9-RELEASE/swift-5.9-RELEASE-ubuntu22.04.tar.gz
tar xzf swift-5.9-RELEASE-ubuntu22.04.tar.gz
export PATH="$PWD/swift-5.9-RELEASE-ubuntu22.04/usr/bin:$PATH"
```

### 运行服务

**方式一：使用启动脚本**
```bash
./start.sh
```

**方式二：手动运行**
```bash
cd swift
swift build
swift run
```

服务将在 **http://localhost:8089** 启动

## 📚 API接口

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
POST   /api/users/delete             # 删除用户
```

### SMB共享

```
GET    /api/smb/shares               # 获取共享列表
POST   /api/smb/shares               # 创建共享
POST   /api/smb/shares/delete        # 删除共享
```

### IP与推送

```
GET    /api/ip/local                 # 获取本机IP列表
GET    /api/ip/scan?port=8089        # 扫描局域网设备
GET    /api/push/targets             # 获取推送目标
POST   /api/push/targets             # 添加推送目标
GET    /api/push/status              # 推送状态/历史
POST   /api/push/receive             # 接收文件
```

### 多语言

```
GET    /api/i18n/?lang=zh_CN         # 获取翻译
```

## 🌍 支持28种语言

| 区域 | 语言代码 |
|------|---------|
| 中文 | zh_CN, zh_TW |
| 英语 | en_US, en_GB |
| 东亚 | ja_JP, ko_KR |
| 欧洲 | fr_FR, de_DE, es_ES, it_IT, pt_BR, ru_RU |
| 东欧 | uk_UA, pl_PL, cs_CZ |
| 中东 | ar_SA, he_IL, tr_TR |
| 亚洲其他 | hi_IN, th_TH, vi_VN, id_ID |
| 北欧 | nl_NL, sv_SE, da_DK, fi_FI |
| 其他 | hu_HU, ro_RO |

## 📁 项目结构

```
swift/
├── Package.swift              # Swift Package Manager配置
├── Sources/
│   ├── main.swift            # 主程序入口
│   ├── NAS/
│   │   ├── Handlers/
│   │   │   └── HTTPHandler.swift   # HTTP请求处理
│   │   ├── Models/
│   │   │   └ Models.swift          # 数据模型
│   │   └── Utils/
│   │       ├── ConfigManager.swift # 配置管理
│   │       ├── I18nManager.swift   # 多语言支持
│   │       ├── StorageManager.swift# 存储管理
│   │       ├── UserManager.swift   # 用户管理
│   │       ├── SMBManager.swift    # SMB管理
│   │       └── PushManager.swift   # 推送管理
├── start.sh                  # 启动脚本
└── README.md                 # 本文档
```

## ⚙️ 配置文件

配置文件位于 `../config/config.json`:

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8089,
    "language": "zh_CN"
  },
  "storage": {
    "volumes": []
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

## 🔧 开发

### 构建

```bash
swift build
```

### 运行

```bash
swift run
```

### 测试

```bash
swift test
```

## 📝 技术特性

- **SwiftNIO**: 高性能异步事件驱动网络框架
- **Swift Package Manager**: 官方依赖管理工具
- **Codable协议**: 简洁的JSON序列化/反序列化
- **内存安全**: Swift的强类型和内存管理特性
- **跨平台**: 支持macOS和Linux

## 🎯 性能优化

- 使用SwiftNIO的非阻塞I/O
- 多线程事件循环
- 高效的内存管理
- 优化的JSON解析

## 📄 许可证

MIT License