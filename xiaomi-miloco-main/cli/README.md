# miloco-cli

Command-line interface for Xiaomi Miloco — manage the backend service, devices, and configuration.

## Install

miloco-cli 随 Miloco 一起安装，不单独发布到 PyPI。运行官方安装脚本即可（脚本会从 GitHub Release 下载本平台归档并本地安装）：

```bash
curl -LsSf https://github.com/XiaoMi/xiaomi-miloco/releases/latest/download/install.sh | bash
```

## Quick Start

```bash
# Start miloco server
miloco-cli service start

# List connected devices
miloco-cli device list --pretty

# Configure
miloco-cli config set model.omni.api_key sk-xxxxx
miloco-cli config show
```

## Commands

| Command | Description |
|---------|-------------|
| `service start/stop/status/logs` | Manage the backend service |
| `device list/control` | Interact with IoT devices |
| `config show/get/set` | View and modify configuration |
| `account bind` | Bind Xiaomi account via OAuth |

## Configuration

Config file: `$MILOCO_HOME/config.json` (default `~/.openclaw/miloco/config.json`).

Override with environment variables using `MILOCO_` prefix and `__` for nesting:

```bash
MILOCO_SERVER__URL=https://192.168.1.100:1810 miloco-cli service status
```

## License

For license details, please see [LICENSE.md](https://raw.githubusercontent.com/XiaoMi/xiaomi-miloco/main/LICENSE.md).

**Important Notice**: This project is limited to non-commercial use only. Without written authorization from Xiaomi Corporation, this project may not be used for developing applications, web services, or other forms of software.
