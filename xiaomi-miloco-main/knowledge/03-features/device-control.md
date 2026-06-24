# 设备控制

## 背景与目标

用户想让 AI 帮自己控制家里的灯、空调、风扇。传统方式需要打开米家 App 找到设备再操作；Miloco 让 Agent 直接理解用户意图并执行。

设备控制模块提供完整的米家设备操作能力：单属性写入、批量属性写入、动作调用、属性查询、场景执行，覆盖用户在 Agent 对话中所有可能的设备操作需求。

---

## 产品面

### 能做什么

- **属性控制**：设置设备的任意可写属性（亮度、色温、温度、开关、模式）；同一设备多属性可合并为一次请求
- **动作调用**：触发设备支持的动作（如音箱播报 TTS、扫地机开始清扫、空气净化器启动自动清洁）
- **属性查询**：读取设备当前状态，用于 Agent 回答"客厅灯现在是多少亮度"
- **场景执行**：一键触发米家配置的智能场景（多设备联动预设），如"回家模式""睡眠模式"
- **Scope 管理**：配置 Miloco 管控哪些家庭和摄像头，是设备接入的前置配置

### 典型场景

**场景 1 — 对话控制**：对 Agent 说"把客厅的灯调到 60% 亮度"。Agent 选择 `miloco-devices` Skill，通过 CLI 调 `/api/miot/devices/{did}/control`，后端执行属性写入，用户约 1 秒内看到灯光变化。

**场景 2 — 规则自动化**：感知流水线检测到"有人进入书房"，STATIC 规则触发，`RuleRunner` 直接调 `MiotProxy.set_device_properties` 打开书房台灯，无需 Agent 介入，无 LLM 额外调用。

**场景 3 — 家庭面板操作**：用户在浏览器打开家庭面板"设备"标签，按房间浏览设备列表，点击开关或滑块直接发起控制请求。

**场景 4 — 音箱 TTS**：Agent 需要向用户播报提醒，通过 `miloco-devices` Skill 找到房间内的音箱设备，调用 `play-text` 动作完成播报。

### 能力边界

- 仅操作已绑定小米账号、且被纳入启用家庭（scope）的设备，其余请求一律拒绝（返回 scope 校验错误）
- 设备联网状态由小米云管理，Server 不感知"控制是否真正送达硬件"——返回成功仅表示指令已发出
- 场景执行由小米云侧完成，Server 只负责转发
- 不支持自定义协议或非米家生态设备
- MiOT OAuth 未绑定时相关端点返回 `code=3201`（`MiotOAuthException`）
- 局域网直连（LAN 路径）仅限同子网，无法跨路由器

---

## 研发面

### 架构概览（数据流图）

```
CLI / Agent（miloco-devices Skill）
  → POST /api/miot/devices/{did}/control
  → MiotService（scope 校验 + 类型分发）（miot/service.py）
  → MiotProxy（miot/client.py）
  → MIoTClient（backend/miot/src/miot/client.py）
      Cloud 路径 → MIoTHttpClient → 小米云 HTTP API → 设备
      LAN 路径  → MIoTLan        → 局域网 UDP 直连 → 设备
```

属性查询入口为 `MiotService.get_device_status`，场景触发为 `trigger_scene` → `MiotProxy.execute_miot_scene`，链路结构相同。

规则触发的 STATIC 控制路径较短：`RuleRunner`（`rule/runner.py`）直接调 `MiotProxy`，绕过 `MiotService`（规则在创建时已绑定 scope 内设备，设计上已保证安全）。

### 核心模块

**MiotService**（`miot/service.py`）

业务编排层，主要职责：

- **scope 校验**：检查请求 did 所属家庭是否在启用集内（KV 存储 home 白名单）
- **控制类型分发**：将 `set_property` / `set_properties` / `call_action` 请求转换为对应 MiOT 参数类型
- **LRU 设备目录维护**：记录用户操作过的设备及属性，确保其出现在 Agent 设备目录（catalog）中
- **home / camera scope 管理**：`switch_home` / `toggle_camera` 写 KV 后触发后台刷新并同步感知层 adapter
- **OAuth 校验**：未绑定或 token 过期时抛 `MiotOAuthException`（code=3201）

**MiotProxy**（`miot/client.py`）

Server 代理层，主要职责：

- **token 生命周期**：后台自动刷新，失效时清空 OAuth 缓存；token 通过 `KVRepo` 持久化，重启后自动恢复
- **数据缓存**：设备/摄像头/场景列表内存维护，重启时重新拉取
- **device spec 按需缓存**：首次使用时加载并缓存，避免启动时全量拉取拖慢启动
- **摄像头 manager 管理**：维护每个摄像头的 `CameraVisionHandler`（`miot/camera_handler.py`）实例

**MIoTClient**（`backend/miot/src/miot/client.py`）

MiOT SDK 顶层客户端，聚合 Cloud、LAN、mDNS、MQTT、摄像头等子模块，对 MiotProxy 暴露统一异步接口。详见 [sdk-miot.md](../05-external-deps/sdk-miot.md)。

### Scope 机制

Scope 定义了"Miloco 管控哪些设备"的边界，分为两个维度：

**家庭维度（Home Scope）**：用户的小米账号下可能有多个家庭（如"公寓""父母家"），Miloco 同一时刻只管控一个家庭的设备。启用的家庭白名单持久化在 `miloco.db::kv` 表中，由 `filter.py`（`miot/filter.py`）读取后应用于过滤。

**摄像头维度（Camera Scope）**：在启用家庭内，用户可以进一步禁用某些摄像头（如不想让 Miloco 看客厅）。被禁用的摄像头 DID 以黑名单形式存在 KV 表中——新摄像头默认被感知，用户选择性关闭。

**Scope 过滤的作用点**：

- 设备列表 / 场景列表接口返回前，`filter.py` 过滤掉不在启用家庭的条目
- 控制设备前，`MiotService` 校验 did 所属家庭是否在启用集内，不在则拒绝
- 感知流水线层：摄像头 scope 变更后，`MiotService` 热同步对应摄像头的**感知投喂订阅**（仅影响感知解码，不重建 camera manager、不中断正在进行的直播），无需重启服务

**Scope 变更**：切换家庭或摄像头时，Server 以单事务落持久化，并立即通知感知层 adapter 同步，无需重启服务。账号切换时清空所有家庭与摄像头 scope，回到干净状态。若启用集为空或无效，自动回退到首个可见家庭，避免感知全黑。

**在哪配置**：web 面板"概览"标签（摄像头在用切换）和顶部 TopBar 家庭切换器；也可通过 `miloco-miot-scope` Skill 在 CLI 完成。

### 关键设计决策

#### Cloud vs LAN 两条控制路径

| 路径      | 实现                                                                  | 适用场景               |
| --------- | --------------------------------------------------------------------- | ---------------------- |
| **Cloud** | `MIoTHttpClient`（`backend/miot/src/miot/cloud.py`）→ 小米云 HTTP API | 默认路径，支持远程访问 |
| **LAN**   | `MIoTLan`（`backend/miot/src/miot/lan.py`）→ 局域网 UDP 直连          | 本地低延迟，不依赖外网 |

两条路径由 `MIoTClient` 内部协调，上层调用方无需感知。

**为什么 STATIC 规则绕过 MiotService**：规则在创建时已绑定 scope 内设备，MiotService 的 scope 校验是冗余的。STATIC 规则执行路径需要极低延迟（感知到设备响应），省掉 service 层的开销。

**Scope 为什么用 KV 而非配置文件**：Scope 是运行期可变的用户选择，不是静态配置。KV 表提供事务性单行原子写，读路径走内存缓存，变更即生效，与配置文件的"重启才生效"语义不同。

### 如果我要修改设备控制相关功能

| 修改目标              | 去看哪个文件                                                                     |
| --------------------- | -------------------------------------------------------------------------------- |
| 修改 scope 过滤逻辑   | `miot/filter.py`                                                                 |
| 修改 scope CRUD 逻辑  | `miot/service.py`（`switch_home` / `toggle_camera` / `list_cameras_with_state`） |
| 修改设备控制 API 端点 | `miot/router.py`                                                                 |
| 修改 MiOT SDK 封装层  | `miot/client.py`（MiotProxy），更底层看 `backend/miot/src/miot/`                 |
| 修改摄像头管理逻辑    | `miot/camera_handler.py`（`CameraVisionHandler`）                                |

### 设备控制相关 API 路径

主要入口：`POST /api/miot/devices/{did}/control`（控制设备），`GET /api/miot/device_list`（设备列表），完整端点见 `miot/router.py`。

### 与其他模块的关系

**上游**：`miloco-devices` Skill 通过 CLI 调 `/api/miot/devices/{did}/control`，是主要控制入口。`RuleRunner`（`rule/runner.py`）在 STATIC 规则条件满足时直接调用 `MiotProxy`。

**下游**：所有指令最终发往小米云 HTTP API 或 LAN 直连。

**互动**：scope 变更（切换家庭/启停摄像头）后，`MiotService` 通知感知层 adapter 同步摄像头的感知投喂订阅（不影响正在进行的直播）。OAuth 完成后，`MiotService` 主动重启感知引擎，让摄像头 adapter 重新注册帧回调。
