# miloco

Python backend for Xiaomi Miloco — a smart home perception and automation server.

## Install

```bash
uv tool install miloco
```

## Quick Start

```bash
# Start the server
miloco-backend

# Or via CLI
miloco-cli service start
```

The server listens on `http://127.0.0.1:1810` by default.

## Configuration

Config lives in `$MILOCO_HOME/config.json` (default `~/.openclaw/miloco/config.json`).

```bash
# Set AI model API key
miloco-cli config set model.omni.api_key sk-xxxxx
```

## License

For license details, please see [LICENSE.md](https://raw.githubusercontent.com/XiaoMi/xiaomi-miloco/main/LICENSE.md).

**Important Notice**: This project is limited to non-commercial use only. Without written authorization from Xiaomi Corporation, this project may not be used for developing applications, web services, or other forms of software.
