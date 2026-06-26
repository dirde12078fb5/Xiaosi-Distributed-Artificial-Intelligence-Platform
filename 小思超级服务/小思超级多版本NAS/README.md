# 小思超级多版本NAS服务

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.7+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Mac-green.svg" alt="Platform">
  <img src="https://img.shields.io/badge/Languages-28-orange.svg" alt="Languages">
</p>

一款功能强大的跨平台NAS管理服务，支持多语言界面和局域网文件推送。

---

## 功能特性

### 核心功能
- **存储卷管理** - 创建、删除存储卷，设置配额
- **用户管理** - 用户CRUD、密码加密存储
- **SMB共享** - 创建文件共享，设置读写权限
- **文件夹推送** - 局域网内一键推送文件夹到其他NAS设备

### 多语言支持
支持 **28种语言**，包括：
- 🇨🇳 简体中文、繁体中文
- 🇺🇸 英语(美式/英式)
- 🇯🇵 日语、韩语
- 🇪🇺 德语、法语、西班牙语、意大利语、葡萄牙语
- 🇷🇺 俄语、乌克兰语、波兰语、捷克语
- 🇸🇦 阿拉伯语、希伯来语、土耳其语
- 🇮🇳 印地语、泰语、越南语、印尼语
- 🇳🇱 荷兰语、瑞典语、丹麦语、芬兰语、匈牙利语、罗马尼亚语

### IP与推送
- 自动检测本机所有网卡IP地址
- 局域网设备扫描发现
- 支持多网卡/多网段环境
- 设备唯一标识，避免重复

---

## 快速开始

### 环境要求
- Python 3.7 或更高版本
- Windows / Linux / macOS

### 安装运行

**Windows:**
```bash
# 双击运行
start.bat

# 或命令行运行
python nas_server.py
```

**Linux / macOS:**
```bash
chmod +x start.sh
./start.sh

# 或
python3 nas_server.py
```

### 访问服务

启动后访问：**http://localhost:8080**

界面语言可在右上角切换。

---

## 使用指南

### 控制台首页

- 查看存储卷、用户、共享数量
- 查看本机所有IP地址
- 快速扫描局域网设备

### 存储卷管理

1. 点击「存储管理」
2. 点击「创建」按钮
3. 填写名称、路径、配额
4. 保存

### 用户管理

1. 点击「用户管理」
2. 点击「创建」按钮
3. 填写用户名、密码
4. 保存

### 共享管理

1. 点击「共享管理」
2. 点击「创建」按钮
3. 填写共享名称、路径
4. 保存

### 文件夹推送（核心功能）

#### 添加推送目标

**方式一：手动添加**
1. 点击「推送管理」
2. 点击「添加目标」
3. 填写目标名称、IP、端口
4. 保存

**方式二：自动扫描**
1. 点击「扫描局域网」
2. 发现同WiFi下的NAS设备
3. 点击「添加」快速添加

#### 推送文件夹

1. 选择目标设备
2. 输入本地文件夹路径（如 `C:\Users\Public\Documents`）
3. 点击「立即推送」
4. 查看进度和推送历史

### 多网卡环境

本服务自动检测所有网卡IP：

| 类型 | 说明 |
|------|------|
| WAN出口 | 默认路由出口IP |
| LAN局域网 | 各网卡分配的局域网IP |
| 本地 | 127.0.0.1 |

每个IP都会标记对应的网卡名称，方便区分。

---

## 目录结构

```
小思超级多版本NAS/
├── nas_server.py      # 主程序（Python，无需编译直接运行）
├── start.bat          # Windows启动脚本
├── start.sh           # Linux/macOS启动脚本
├── config.json        # 配置文件
├── README.md          # 本文档
├── LICENSE            # MIT许可证
└── nas_data/         # 数据目录（自动创建）
    └── received/      # 接收的文件存放目录
```

---

## API接口

### 存储管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/storage/volumes` | 获取存储卷列表 |
| POST | `/api/storage/volumes` | 创建存储卷 |
| POST | `/api/storage/volumes/delete` | 删除存储卷 |

### 用户管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/users` | 获取用户列表 |
| POST | `/api/users` | 创建用户 |
| POST | `/api/users/delete` | 删除用户 |

### IP与推送
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/ip/local` | 获取本机IP列表 |
| GET | `/api/ip/scan?port=8080` | 扫描局域网设备 |
| GET | `/api/push/targets` | 获取推送目标 |
| POST | `/api/push/targets` | 添加推送目标 |
| POST | `/api/push/folder` | 推送文件夹 |
| GET | `/api/push/status` | 推送状态/历史 |
| POST | `/api/push/receive` | 接收文件 |

### 多语言
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/i18n/?lang=zh_CN` | 获取翻译 |

---

## 配置文件

`config.json` 示例：

```json
{
  "server": {
    "port": 8080,
    "language": "zh_CN"
  },
  "storage": {
    "volumes": [
      {"name": "data", "path": "/mnt/data", "quota_gb": 1000}
    ]
  },
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

---

## 推送协议说明

推送使用 HTTP multipart/form-data 协议：

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

## 常见问题

### Q: 推送失败怎么办？
1. 确认目标NAS服务已启动
2. 检查防火墙是否放行8080端口
3. 确认目标IP和端口正确

### Q: 如何查看本机IP？
启动后自动在控制台显示，或在Web界面「控制台」页面查看

### Q: 支持那些文件夹路径格式？
- Windows: `C:\Users\Public\Documents`
- Linux: `/home/user/documents`
- macOS: `/Users/Shared`

### Q: 如何添加新语言？
编辑 `nas_server.py` 中的 `TRANSLATIONS` 字典，添加新的语言代码和翻译映射。

---

## 开发说明

### Python版本（直接运行）
```bash
python nas_server.py
```

### Go版本（需要编译）
```bash
cd cmd/server
go build -o xiaosi-nas.exe
./xiaosi-nas.exe
```

### 添加依赖
```bash
pip install -r requirements.txt
```

---

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 联系方式

- 问题反馈: Gitcode Issues
- 功能建议: Gitcode Discussions

---

<p align="center">
  用 ❤️ 和 ☕ 构建 | 小思超级NAS服务 v1.0
</p>
