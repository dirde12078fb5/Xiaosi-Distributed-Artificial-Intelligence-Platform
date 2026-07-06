# 小思超级NAS服务 - Python实现 (第二代)

## 简介

这是小思超级多版本NAS服务的第二代Python实现，具有以下特点：

- **零依赖**：仅使用Python标准库，无需安装第三方包
- **完整功能**：包含存储管理、用户管理、SMB共享、文件推送、IP管理等完整功能
- **多语言支持**：支持28种语言（中文、英语、日语、韩语等）
- **跨平台**：支持Windows、Linux、MacOS等操作系统

## 文件结构

```
小思超级多版本NAS 2/
├── python/
│   ├── nas_server.py      # 主程序文件
│   ├── start.bat          # Windows启动脚本
│   └── start.sh           # Unix/Linux启动脚本
├── config/
│   └── config.json        # 配置文件
└── README.md              # 本说明文件
```

## 快速启动

### Windows系统

1. 双击运行 `python/start.bat`
2. 或在命令行中执行：
   ```
   cd python
   python nas_server.py
   ```

### Linux/MacOS系统

1. 执行启动脚本：
   ```bash
   cd python
   chmod +x start.sh
   ./start.sh
   ```
2. 或直接运行：
   ```bash
   python3 nas_server.py
   ```

### 自定义端口

可以指定端口启动（默认8080）：

```bash
python nas_server.py 9000
```

## API接口

### 存储管理
- `GET /api/storage/volumes` - 获取存储卷列表
- `POST /api/storage/volumes` - 创建存储卷
- `POST /api/storage/volumes/delete` - 删除存储卷

### 用户管理
- `GET /api/users` - 获取用户列表
- `POST /api/users` - 创建用户
- `POST /api/users/delete` - 删除用户

### SMB共享
- `GET /api/smb/shares` - 获取SMB共享列表
- `POST /api/smb/shares` - 创建SMB共享
- `POST /api/smb/shares/delete` - 删除SMB共享
- `GET /api/smb/status` - 获取SMB服务状态

### IP管理
- `GET /api/ip/local` - 获取本机IP地址
- `GET /api/ip/scan` - 扫描局域网设备

### 文件推送
- `GET /api/push/targets` - 获取推送目标列表
- `POST /api/push/targets` - 添加推送目标
- `POST /api/push/targets/delete` - 删除推送目标
- `POST /api/push/folder` - 推送文件夹
- `GET /api/push/status` - 获取推送状态
- `POST /api/push/receive` - 接收推送文件

### 多语言
- `GET /api/i18n?lang=zh_CN` - 获取指定语言的翻译

## 支持的语言

支持28种语言，包括：
- zh_CN (简体中文)
- zh_TW (繁体中文)
- en_US (English US)
- en_GB (English UK)
- ja_JP (日本語)
- ko_KR (한국어)
- fr_FR (Français)
- de_DE (Deutsch)
- es_ES (Español)
- it_IT (Italiano)
- pt_BR (Português)
- ru_RU (Русский)
- ar_SA (العربية)
- hi_IN (हिन्दी)
- tr_TR (Türkçe)
- th_TH (ไทย)
- vi_VN (Tiếng Việt)
- id_ID (Bahasa Indonesia)
- nl_NL (Nederlands)
- pl_PL (Polski)
- sv_SE (Svenska)
- da_DK (Dansk)
- fi_FI (Suomi)
- he_IL (עברית)
- hu_HU (Magyar)
- cs_CZ (Čeština)
- uk_UA (Українська)
- ro_RO (Română)

## 配置文件

配置文件位于 `../config/config.json`，包含：

```json
{
  "server": {
    "port": 8080,
    "language": "zh_CN"
  },
  "storage": {
    "volumes": []
  },
  "users": [],
  "smb": {
    "shares": []
  },
  "push": {
    "targets": []
  },
  "data_dir": "nas_data",
  "receive_dir": "nas_data/received"
}
```

## Web管理界面

启动服务后，在浏览器中访问：

- 本地访问：http://localhost:8080
- 网络访问：http://[你的IP]:8080

管理界面包含5个主要功能模块：
1. 控制台 - 查看系统状态和IP信息
2. 存储管理 - 管理存储卷
3. 用户管理 - 管理NAS用户
4. 共享管理 - 管理SMB共享
5. 推送管理 - 管理文件推送目标

## 技术特点

- **零依赖**：仅使用Python标准库（os, sys, json, socket, threading等）
- **RESTful API**：标准REST API设计，支持JSON数据交换
- **多线程处理**：文件推送和局域网扫描使用多线程提升性能
- **CORS支持**：跨域请求支持，方便前后端分离
- **设备识别**：基于机器名+UUID生成设备唯一ID

## 许可证

小思分布式人工智能平台 - 小思超级NAS服务

## 版本信息

- 版本：第二代
- 语言：Python 3.6+
- 依赖：零依赖（仅标准库）

---

小思分布式人工智能平台 © 2024