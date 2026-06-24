# MiOT SDK 依赖

## L1：它是什么

小米 MiOT SDK（`backend/miot/src/miot/`）是 Miloco 访问小米智能家居生态的底层库。它封装了 OAuth2 认证、小米云 HTTP API、局域网 OT 协议直连、摄像头流媒体（C 库封装）、mDNS 局域网发现等能力，由小米内部维护，以预编译形式（Python wheel + `.so`/`.dylib`）分发。

### 能力范围

- **OAuth2 + 云端 API**：账号授权、设备列表、属性读写、动作触发、场景执行、App 推送通知
- **LAN 直连（OT 协议）**：UDP 广播发现局域网 MiOT 设备，维护在线/离线状态，本地低延迟控制
- **摄像头流媒体**：通过 C 动态库（`libmiot_camera_lite.so`/`.dylib`）建立 PPCS P2P 连接，接收 H.264/H.265 视频流和 Opus 音频流
- **媒体解码**：基于 PyAV 解码原始码流为 BGR ndarray（视频）和 s16 PCM（音频）
- **mDNS 发现**：基于 zeroconf 发现局域网 MiOT Central Service 节点，用于 MQTT 本地路由
- **MQTT**：通过 `MIoTMipsCloud`（`mips_cloud.py`）订阅三类推送事件——用户设备绑定 / 解绑、设备 meta 变更（含跨家庭移入 hr_change）、家庭场景变更（改 / 删 / 重命名）。绑定与移入驱动设备欢迎，场景变更驱动场景列表刷新，与米家保持同步

---

## L2：我们怎么用

### 封装层

Miloco 在 MiOT SDK 之上有一层封装：`MiotProxy`（`miot/client.py`），对整个 Server 暴露统一的异步接口。MiotProxy 负责：

- token 生命周期管理（后台自动刷新，SDK 本身不做）
- 内存缓存（设备/摄像头/场景列表），屏蔽 SDK 的直接 HTTP 调用
- scope 判定分两处作用：**home 白名单**在摄像头 manager 创建侧过滤（`refresh_cameras` 只为启用家庭内的摄像头建 manager）；**camera 黑名单**只在感知投喂订阅侧生效（`perception/collect/camera_adapter.py`），不影响 manager 存续与 watch 直播
- 摄像头实例（`CameraVisionHandler`，`miot/camera_handler.py`）生命周期管理

未绑定小米账号或 OAuth token 过期时，`MiotService` 抛 `MiotOAuthException`（code=3201）；调用失败时抛 `MiotServiceException`（code=3200）。

详细使用方式见 [设备控制](../03-features/device-control.md) 和 [感知流水线](../03-features/perception-pipeline.md)。

### 集成约束

- **OAuth 绑定要求**：所有 Cloud API 调用必须先完成小米账号 OAuth2 授权（`miloco-cli account bind`）。未绑定时设备列表为空，感知无法启动。
- **C 库依赖**：摄像头流依赖闭源预编译的 `libmiot_camera_lite.so`/`.dylib`，仅提供 Linux（x86_64 / aarch64）和 macOS（x86_64 / arm64）预编译版本，不支持交叉编译或源码定制。
- **PPCS UDP 穿透**：摄像头 P2P 连接依赖 UDP 入站，防火墙需要允许来自局域网的 UDP 包（常见问题，见 [故障排查 · 摄像头连接问题](../06-dev-guide/troubleshooting.md#摄像头连接问题)）。
- **单进程约束**：SDK 部分子模块（LAN daemon、摄像头 C 库绑定）假设单进程运行，Miloco Server 的 `workers=1` 约束正是为此而设。

### 已知限制

- LAN 发现仅限同子网（OT 广播 UDP 无法跨路由器）
- 摄像头在线判定依赖 SDK 内部状态，设备实际离线时状态可能未及时更新

### 出问题找谁

MiOT SDK 由小米内部团队维护，Miloco 工程侧不持有源码。遇到 SDK 层问题（C 库崩溃、OAuth 接口变更、LAN 协议异常）需向小米内部 SDK 维护团队反映。Miloco 侧能做的是通过 `MiotProxy` 封装层做隔离和降级。
