# 小思超级PXE - 故障排除指南

## 常见问题

### 1. DHCP 无法连接

#### 问题描述
客户端无法获取IP地址，或无法连接到DHCP服务器。

#### 诊断步骤

**步骤1：运行诊断工具**
```bash
python diagnose.py
```
这将检查系统环境、权限、端口和配置。

**步骤2：检查权限**
- Windows：必须以**管理员身份**运行
- Linux/macOS：必须使用 `sudo` 运行
```bash
# Windows (以管理员打开命令提示符或PowerShell)
python gui.py

# Linux/macOS
sudo python3 gui.py
```

**步骤3：检查网络配置**
确保服务器和客户端在同一个网段：
- 服务器IP：例如 192.168.1.1
- DHCP范围：192.168.1.100 - 192.168.1.200
- 子网掩码：255.255.255.0

编辑 `config.json` 文件来匹配您的网络环境。

**步骤4：检查防火墙**
防火墙可能阻止了DHCP/TFTP流量：

**Windows：**
```powershell
# 添加防火墙规则 (以管理员身份运行)
netsh advfirewall firewall add rule name="SuperPXE DHCP" dir=in action=allow protocol=UDP localport=67
netsh advfirewall firewall add rule name="SuperPXE TFTP" dir=in action=allow protocol=UDP localport=69
```

**Linux (ufw)：**
```bash
sudo ufw allow 67/udp
sudo ufw allow 68/udp
sudo ufw allow 69/udp
sudo ufw allow 8080/tcp
```

**Linux (firewalld)：**
```bash
sudo firewall-cmd --permanent --add-port=67/udp
sudo firewall-cmd --permanent --add-port=68/udp
sudo firewall-cmd --permanent --add-port=69/udp
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
```

**步骤5：检查是否有其他DHCP服务器**
同一网络中只能有一个DHCP服务器：

**Windows：**
```powershell
# 检查DHCP客户端服务
sc query dhcp

# 检查是否有其他DHCP服务器在运行
netstat -ano | findstr :67
```

**Linux：**
```bash
# 检查端口占用
sudo netstat -ulpn | grep :67
# 或
sudo ss -ulpn | grep :67
```

如果发现其他DHCP服务器，请停止它。

### 2. 端口被占用

#### 错误信息
```
OSError: [Errno 98] Address already in use
```

#### 解决方案

**查找占用端口的进程：**

**Windows：**
```powershell
netstat -ano | findstr :67
taskkill /PID <进程ID> /F
```

**Linux：**
```bash
sudo lsof -i :67
sudo kill -9 <进程ID>
```

**常见占用端口的程序：**
- dhcpd (ISC DHCP服务)
- dnsmasq
- 路由器内置DHCP
- VMware/VirtualBox的网络服务

### 3. 客户端无法启动

#### 问题
客户端可以获取IP，但无法下载启动文件。

#### 检查清单

1. **检查TFTP文件**
   - 确保 `tftpboot` 目录存在
   - 确保必要文件在目录中：
     - pxelinux.0
     - menu.c32
     - memdisk
     - ldlinux.c32
     - vmlinuz (内核文件)
     - initrd.img (ramdisk文件)

2. **检查启动菜单配置**
   - 确保 `tftpboot/pxelinux.cfg/default` 存在
   - 使用GUI工具或手动编辑启动菜单

3. **检查HTTP服务**
   - 访问 `http://<服务器IP>:8080` 确认HTTP服务正常
   - 确保大文件在 `httpboot` 目录中

### 4. 配置文件问题

#### 创建配置文件
```bash
# 复制示例配置
cp config.example.json config.json

# 编辑配置
# Windows: 记事本 config.json
# Linux/macOS: nano config.json
```

#### 配置说明
```json
{
  "dhcp": {
    "enabled": true,          // 启用DHCP服务器
    "server_ip": "192.168.1.1", // 服务器IP地址(重要!)
    "start_ip": "192.168.1.100", // DHCP起始地址
    "end_ip": "192.168.1.200",   // DHCP结束地址
    "gateway": "192.168.1.1",    // 网关地址
    "subnet_mask": "255.255.255.0", // 子网掩码
    "dns_servers": ["8.8.8.8", "8.8.4.4"], // DNS服务器
    "boot_file": "pxelinux.0"      // 启动文件名
  }
}
```

**重要：** 必须将 `server_ip` 和 `gateway` 改为您服务器的实际IP地址！

## 快速启动检查清单

在启动服务器前，请确认：

- [ ] 已以管理员/root权限运行
- [ ] 已创建配置文件 `config.json`
- [ ] 配置中的IP地址与网络环境匹配
- [ ] 防火墙已允许相关端口
- [ ] 没有其他DHCP服务器在同一网络中
- [ ] 客户端设置为网络启动 (PXE/LAN启动)

## 获取帮助

如果问题仍然存在：

1. 查看日志输出（GUI底部或命令行）
2. 运行 `python diagnose.py` 获取诊断信息
3. 检查您的网络设备是否有特殊限制
4. 确认客户端支持PXE启动

## 调试模式

启用详细日志记录来诊断问题：

编辑 `config.json`，设置：
```json
{
  "log_level": "DEBUG"
}
```

这将显示更详细的网络数据包信息。
