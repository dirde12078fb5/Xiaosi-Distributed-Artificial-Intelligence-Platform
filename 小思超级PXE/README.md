# 小思超级PXE - Python跨平台网络安装系统

一个纯Python实现的跨平台PXE网络安装系统，包含DHCP、TFTP、HTTP服务器，支持通过网络启动和安装操作系统。

## 功能特性

- ✅ **DHCP服务器** - 自动分配IP地址和启动文件
- ✅ **TFTP服务器** - 传输启动文件
- ✅ **HTTP服务器** - 传输大文件和ISO镜像
- ✅ **跨平台支持** - Windows、Linux、macOS
- ✅ **启动菜单管理** - 灵活的PXE启动配置
- ✅ **图形用户界面(GUI)** - 友好的图形界面
- ✅ **无额外依赖** - 使用Python标准库

## 快速开始

### 1. 准备环境

确保已安装Python 3.6+。

### 2. 配置系统

```bash
# 复制配置文件
cp config.example.json config.json

# 编辑配置文件，根据需要修改网络设置
```

### 3. 启动程序

#### 使用GUI（推荐）

```bash
# 启动图形用户界面
python gui.py
```

在GUI界面中，您可以：
- 点击"启动服务器"按钮启动PXE服务
- 在"配置管理"标签页中修改网络设置
- 在"启动菜单"标签页中添加和管理启动项
- 查看实时日志信息

#### 使用命令行

```bash
# Windows (需要管理员权限)
python cli.py server

# Linux/macOS (需要root权限)
sudo python3 cli.py server
```

### 4. 添加启动项

```bash
# 添加本地启动项
python cli.py entry add "从本地硬盘启动" local

# 添加Linux启动项
python cli.py entry add "Ubuntu 22.04" linux \
  --kernel vmlinuz \
  --initrd initrd.img \
  --append "boot=casper netboot=nfs nfsroot=192.168.1.1:/srv/nfs/ubuntu"
```

## 项目结构

```
小思超级PXE/
├── pxe_server.py          # 主服务器模块
├── cli.py                  # 命令行界面
├── gui.py                  # GUI启动入口
├── config.example.json     # 配置文件示例
├── requirements.txt        # 依赖说明
├── README.md             # 说明文档
├── servers/              # 服务器模块
│   ├── __init__.py
│   ├── dhcp_server.py  # DHCP服务器
│   ├── tftp_server.py  # TFTP服务器
│   └── http_server.py  # HTTP服务器
├── pxe/                  # PXE配置管理
│   ├── __init__.py
│   └── boot_manager.py  # 启动配置管理器
├── gui/                  # GUI模块
│   ├── __init__.py
│   └── main_window.py  # GUI主窗口
└── utils/                # 工具模块
    ├── __init__.py
    └── platform.py     # 跨平台工具
```

## 使用说明

### 服务器命令

```bash
# 启动服务器
python cli.py server

# 使用指定配置文件
python cli.py server -c myconfig.json
```

### 菜单管理

```bash
# 列出所有菜单
python cli.py menu list

# 添加菜单
python cli.py menu add "维护工具" "系统维护工具菜单" --timeout 60

# 设置默认菜单
python cli.py menu default "维护工具"

# 删除菜单
python cli.py menu remove "旧菜单"
```

### 启动项管理

```bash
# 列出启动项
python cli.py entry list

# 添加本地启动
python cli.py entry add "从本地启动" local

# 添加Linux启动
python cli.py entry add "Ubuntu" linux --kernel vmlinuz --initrd initrd.img

# 添加ISO启动
python cli.py entry add "Windows PE" iso --iso-path iso/winpe.iso

# 删除启动项
python cli.py entry remove "旧启动项"
```

## PXE启动文件

### 需要的文件

将以下文件放入 `tftpboot/` 目录：

- `pxelinux.0` - PXELINUX启动加载器
- `menu.c32` - 菜单系统
- `memdisk` - ISO启动
- `ldlinux.c32` - 依赖库
- 内核文件 (vmlinuz, initrd.img等)

可以从Syslinux项目获取这些文件。

### HTTP文件服务

HTTP服务器根目录为 `httpboot/`，可以存放：
- ISO镜像
- 安装源文件
- 其他大文件

## 注意事项

1. **权限要求**：需要管理员/root权限来绑定67/68/69等低端口
2. **网络环境**：确保没有其他DHCP服务器在同一网络运行
3. **防火墙**：确保防火墙允许相关端口
4. **客户端配置**：确保客户机网卡支持网络启动

## 开发说明

### 项目使用Python标准库，无需额外安装依赖。

### 扩展功能

可以修改相关模块扩展功能：
- `servers/dhcp_server.py` - DHCP协议
- `servers/tftp_server.py` - TFTP协议
- `servers/http_server.py` - HTTP服务
- `pxe/boot_manager.py` - 启动配置

## 许可证

小思超级PXE系统
