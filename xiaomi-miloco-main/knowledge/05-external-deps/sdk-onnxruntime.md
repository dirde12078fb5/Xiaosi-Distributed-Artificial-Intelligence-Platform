# ONNX Runtime 依赖

## L1：它是什么

ONNX Runtime 是微软开源的跨平台推理引擎，支持运行 ONNX 格式的机器学习模型。Miloco 用它在本地运行感知流水线中的视觉模型，无需外部 API 调用，保护隐私且延迟可控。

---

## L2：我们怎么用

### 活跃模型

| 模型文件                      | 用途                                                                                       | 必需性 |
| ----------------------------- | ------------------------------------------------------------------------------------------ | ------ |
| `det_4C.onnx`                 | 人体检测：输出每个人的检测框和置信度，是感知运行的前提                                     | 必需   |
| `human_body_reid_v2.onnx`     | 人体 ReID：提取外观嵌入用于跨帧身份关联，也用于陌生人池跨 track 去重与 tier_a 注册嵌入提取 | 必需   |
| `silero_vad.onnx`             | 语音活动检测（VAD）：Gate 层判定音频窗口是否含人声，过滤无语音窗口                         | 可选   |
| `bge-small-zh-v1.5-int8.onnx` | 文本句向量嵌入：有价值事件 / 建议的语义去重（需配套 `bge-small-zh-v1.5-tokenizer.json`）   | 可选   |

必需模型缺失则引擎进入 `PREREQ_MISSING` 降级；可选模型缺失只让对应子能力（语音门控 / 语义去重）退化，引擎主链路仍可运行（校验清单见 `perception/engine/resource_validator.py`）。

所有模型均通过 ONNX Runtime 在专用 `ThreadPoolExecutor`（`perception-infer` 线程）中执行，与主事件循环解耦。模型加载封装在 `perception/inference/ort_utils.py`，运行时从 `directories.models_dir`（默认 `$MILOCO_HOME/models/`）加载，包内 `perception/models/` 作兜底。

### 安装时下载校验机制

模型文件存放在 `$MILOCO_HOME/models/` 目录下（路径由 `directories.models` 配置，见 `settings.yaml::directories`）。安装时由 `install.py` 负责：优先从随开发者构建包附带的模型包内恢复，失败时从云端下载，并对每个模型文件做完整性校验。

模型文件不随 Python wheel 分发（避免包体过大），安装脚本负责确保模型就位。

### 模型缺失时的降级行为

`PerceptionEngineProxy`（`perception/client.py`）在初始化时做启动前校验：

- `MODELS_MISSING`：引擎进入 `PREREQ_MISSING` 降级状态，感知推理跳过，需要引擎的端点以 `503` 拒绝，但 Server 其他功能（设备控制、规则 CRUD 等）不受影响
- 降级状态通过 `GET /api/perception/engine/status` 可查，响应体 `engine.status` 字段为 `models_missing`
- 修复方式：重跑 `install.sh` 补全模型文件；或检查 `directories.models` 配置是否指向正确目录

### 出问题找谁

ONNX Runtime 本身是公开开源库（Microsoft），遇到引擎层问题查 ONNX Runtime 官方 issue。模型文件本身（`det_4C.onnx` / `human_body_reid_v2.onnx`）由小米内部提供，模型质量/精度问题反馈给小米 AI 视觉团队。
