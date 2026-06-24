# miloco-miot

MIoT SDK for Xiaomi Miloco — provides device communication, RTSP streaming, and cloud API access for Xiaomi IoT devices.

## Install

```bash
pip install miloco-miot
```

## Usage

```python
from miot.client import MIoTClient

client = MIoTClient()
await client.init(cloud_server="cn")
devices = await client.get_devices()
```

## License

Xiaomi Miloco License Agreement
