# ConfigGUI · 节点式配置界面

> 基于 ComfyUI 内置节点设计风格的简约节点式配置工具，支持拖拽、连线、参数编辑、工作流保存/加载与模拟执行。

![ConfigGUI 界面预览](https://img.shields.io/badge/Python-3.7%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

---

## 目录

- [特性](#特性)
- [快速开始](#快速开始)
  - [方式一：双击运行（推荐）](#方式一-双击运行推荐)
  - [方式二：命令行运行](#方式二-命令行运行)
- [界面使用指南](#界面使用指南)
  - [节点库](#节点库)
  - [画布操作](#画布操作)
  - [节点操作](#节点操作)
  - [连线](#连线)
  - [属性面板](#属性面板)
  - [工具栏按钮](#工具栏按钮)
- [命令行工具](#命令行工具)
  - [server.py](#serverpy)
  - [run-workflow.py](#run-workflowpy)
  - [start-server.bat](#start-serverbat)
  - [exec-workflow.bat](#exec-workflowbat)
- [REST API](#rest-api)
- [节点类型参考](#节点类型参考)
- [项目结构](#项目结构)
- [常见问题](#常见问题)

---

## 特性

- **节点式工作流设计**：拖拽节点、连接端口、编辑参数，无需编码
- **简约深色主题**：参考 ComfyUI 风格，数据类型端口颜色区分
- **多种运行方式**：前端模拟运行 / 服务端执行 / 命令行批处理
- **工作流持久化**：保存到本地 JSON 文件，支持导入导出
- **零依赖**：纯 Python 标准库 HTTP 服务，无需安装额外包

---

## 快速开始

### 方式一：双击运行（推荐）

**Windows 用户**只需双击以下文件即可启动：

| 文件 | 说明 |
|---|---|
| `start-server.bat` | 启动 HTTP 服务并自动打开浏览器 |
| `exec-workflow.bat demo_workflow.json` | 执行指定工作流 JSON |

启动后浏览器自动打开 http://127.0.0.1:8765/

> 首次运行会提示允许 Python 通过防火墙，点击"允许"即可。

---

### 方式二：命令行运行

```bash
# 前置要求：已安装 Python 3.7+

# 1. 启动服务
python server.py
# 或指定端口
python server.py --port 8080
# 或允许局域网访问
python server.py --host 0.0.0.0 --port 8080
# 不自动打开浏览器
python server.py --no-browser

# 2. 浏览器访问 http://127.0.0.1:8765/
```

```bash
# 执行工作流 JSON（命令行）
python run-workflow.py demo_workflow.json
# 生成示例工作流
python run-workflow.py --gen-demo demo.json
# 执行并保存报告
python run-workflow.py demo.json --out report.json
```

---

## 界面使用指南

### 节点库

左侧面板按分类展示所有可用节点：

- **加载器** — CheckpointLoaderSimple、VAELoader
- **条件** — CLIPTextEncode、ConditioningZeroOut
- **采样** — KSampler、KSamplerAdvanced
- **潜空间** — EmptyLatentImage、LatentUpscaleBy
- **解码** — VAEDecode、VAEEncode
- **图像** — LoadImage、SaveImage、ImageScale、ImageInvert
- **高级** — SetNoiseSeed、备注节点

**添加节点到画布的方式：**
- 点击节点项 → 直接添加到画布中央
- 拖拽节点项 → 拖到画布任意位置松开

右上角搜索框支持按名称、类型、描述关键词过滤节点。

### 画布操作

| 操作 | 方法 |
|---|---|
| 移动画布 | Alt + 鼠标左键拖拽，或鼠标中键拖拽 |
| 缩放 | Ctrl + 滚轮（或底部 + / − 按钮） |
| 重置视图 | 点击 ⟳ 按钮 |
| 取消选择 / 取消连线 | 按 Esc |

### 节点操作

| 操作 | 方法 |
|---|---|
| 选中节点 | 点击节点卡片 |
| 移动节点 | 拖拽节点标题栏 |
| 删除节点 | 选中后按 Delete / Backspace，或点击节点右上角 × |
| 编辑参数 | 在节点内联控件直接修改，或右侧属性面板 |

### 连线

1. 将鼠标移至输出端口（右侧，圆形）→ 端口高亮
2. 按住鼠标左键拖拽到目标输入端口（左侧，圆形）
3. 松开鼠标完成连接

**连线规则：**
- 只允许 output → input 方向的连线
- 数据类型必须匹配（端口颜色相同表示类型兼容）
- 同一输入端口只能有一条连线（连接新线会自动替换旧线）
- 点击已有连线可将其删除

### 属性面板

选中节点后，右侧面板显示：
- 节点基本信息（类型、ID）
- 节点说明
- 所有参数（可编辑，实时同步到节点卡内联控件）
- 端口列表（输入/输出，含类型标签）

### 工具栏按钮

| 按钮 | 说明 |
|---|---|
| 新建 | 清空画布，重新开始 |
| 保存 | 将当前工作流保存到服务端 `workflows/` 目录 |
| 加载 | 从服务端已保存列表中选择并加载工作流 |
| 导出 | 下载当前工作流为 JSON 文件到本地 |
| 导入 | 从本地 JSON 文件加载工作流 |
| 远端运行 | 将当前工作流发送到服务端执行（模拟执行） |
| 运行 | 在前端直接模拟执行工作流（节点依次高亮动画） |

---

## 命令行工具

### server.py

HTTP 服务，提供静态页面 + REST API。

```bash
python server.py [OPTIONS]

选项：
  --host ADDR        绑定地址（默认 127.0.0.1，仅本机访问）
                     设为 0.0.0.0 可允许局域网设备访问
  --port PORT        监听端口（默认 8765）
  --data DIR         工作流存储目录（默认 ./workflows）
  --no-browser       不自动打开浏览器
```

> 启动后 `workflows/` 目录会自动创建，无需手动新建。

### run-workflow.py

命令行工作流执行器，适合 CI/CD 或脚本集成。

```bash
# 执行已有工作流
python run-workflow.py <工作流.json>

# 生成示例工作流文件
python run-workflow.py --gen-demo output.json

# 执行并保存详细报告
python run-workflow.py <工作流.json> --out report.json

# 静默模式（仅退出码）
python run-workflow.py <工作流.json> --quiet
```

**输出示例：**
```
========================================================
  ConfigGUI · 工作流执行报告  (2026-06-21 18:34:33)
========================================================
  工作流文件 : D:\...\demo_workflow.json
  节点数     : 7
  连线数     : 9
  执行顺序   : ckpt -> latent -> pos -> neg -> k -> vae -> save
  总耗时     : 113.01 ms
--------------------------------------------------------
     #  节点类型                       耗时(ms)  参数
--------------------------------------------------------
     1  CheckpointLoaderSimple       5.55  ckpt_name=...
     2  EmptyLatentImage             5.56  width=512, height=768
     3  CLIPTextEncode              15.44  text=masterpiece, best quality...
     ...
========================================================
  执行成功 ✓
```

### start-server.bat

双击即可启动服务，Windows 专用。

```bat
:: 默认启动（端口 8765，自动开浏览器）
start-server.bat

:: 指定端口
start-server.bat 8080

:: 指定端口且不打开浏览器
start-server.bat 8080 --no-browser
```

### exec-workflow.bat

双击执行工作流，Windows 专用。

```bat
:: 执行本地工作流文件
exec-workflow.bat my_workflow.json

:: 执行并保存报告
exec-workflow.bat my_workflow.json --out report.json

:: 生成示例工作流
exec-workflow.bat --gen-demo demo.json

:: 无参数时显示帮助
exec-workflow.bat
```

---

## REST API

服务启动后可通过以下接口管理工作流：

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/workflow` | 列出所有已保存工作流 |
| POST | `/api/workflow` | 保存工作流（请求体为 JSON） |
| GET | `/api/workflow/<name>` | 下载指定工作流 JSON |
| DELETE | `/api/workflow/<name>` | 删除指定工作流 |
| POST | `/api/run` | 执行工作流，返回执行日志 |
| GET | `/api/nodes` | 获取节点库元数据 |

**保存工作流示例：**
```bash
curl -X POST http://127.0.0.1:8765/api/workflow \
  -H "Content-Type: application/json" \
  -d '{"name":"my_wf","nodes":[...],"wires":[...]}'
```

**执行工作流示例：**
```bash
curl -X POST http://127.0.0.1:8765/api/run \
  -H "Content-Type: application/json" \
  -d @my_workflow.json
```

**响应格式：**
```json
{
  "ok": true,
  "nodes": 7,
  "wires": 9,
  "order": ["ckpt", "latent", "pos", "neg", "k", "vae", "save"],
  "logs": [
    {"step": 1, "id": "ckpt", "type": "CheckpointLoaderSimple",
     "title": "CheckpointLoaderSimple", "elapsed_ms": 5.55, "params": {}}
  ],
  "total_ms": 113.01,
  "ts": "2026-06-21 18:34:33"
}
```

---

## 节点类型参考

| 节点 | 类型 | 说明 |
|---|---|---|
| CheckpointLoaderSimple | 加载器 | 加载 .safetensors / .ckpt 模型，输出 MODEL / CLIP / VAE |
| VAELoader | 加载器 | 单独加载 VAE 模型 |
| CLIPTextEncode | 条件 | 将文本通过 CLIP 编码为条件向量 |
| ConditioningZeroOut | 条件 | 将条件向量置零 |
| KSampler | 采样 | 核心扩散采样器，输出 LATENT |
| KSamplerAdvanced | 采样 | 进阶采样，支持指定起始/结束步 |
| EmptyLatentImage | 潜空间 | 生成空白潜在图像（指定宽/高/批次） |
| LatentUpscaleBy | 潜空间 | 按倍率放大潜在图像 |
| VAEDecode | 解码 | 将 LATENT 解码为 IMAGE |
| VAEEncode | 解码 | 将 IMAGE 编码为 LATENT |
| LoadImage | 图像 | 加载图像文件，输出 IMAGE + MASK |
| SaveImage | 图像 | 将图像保存到输出目录 |
| ImageScale | 图像 | 缩放图像到指定尺寸 |
| ImageInvert | 图像 | 反转图像颜色 |
| SetNoiseSeed | 高级 | 设置固定噪声种子 |
| Note | 高级 | 文本备注节点 |

**端口颜色编码：**

| 颜色 | 类型 |
|---|---|
| 蓝 `#7aa2f7` | MODEL |
| 紫 `#bb9af7` | CLIP |
| 绿 `#9ece6a` | VAE |
| 橙 `#e0af68` | LATENT |
| 青 `#7dcfff` | IMAGE |
| 红 `#f7768e` | CONDITIONING |
| 薄荷绿 `#73daca` | MASK |

---

## 项目结构

```
ComFigGUI/
├── index.html          # 主页面（三栏布局：节点库 / 画布 / 属性面板）
├── styles.css          # 深色主题样式，节点卡 / 连线 / 面板样式
├── nodes.js            # 节点库数据定义（15 种节点类型）
├── app.js              # 核心交互逻辑（拖拽 / 连线 / 参数 / 模拟运行）
├── server.py           # Python HTTP 服务（静态文件 + REST API）
├── run-workflow.py     # 命令行工作流执行器
├── start-server.bat    # Windows 一键启动服务
├── exec-workflow.bat   # Windows 执行工作流批处理
├── .gitignore          # Git 忽略文件
└── workflows/          # 工作流存储目录（由 server.py 自动创建）
    └── .gitkeep        # 保持目录结构，workflows/*.json 不提交
```

---

## 常见问题

**Q: 双击 `start-server.bat` 报错"未检测到 Python"**
> 请先从 https://www.python.org/downloads/ 安装 Python 3.7+，安装时勾选 **Add Python to PATH**，然后重新双击。

**Q: 浏览器打开页面空白或 JS 报错**
> 确认是通过 `start-server.bat` 启动的服务访问页面（`file://` 协议下部分浏览器会有 CORS 限制）。推荐始终通过 http://127.0.0.1:8765/ 访问。

**Q: 如何连接到远程服务器？**
> 在服务端运行 `python server.py --host 0.0.0.0 --port 8765`，然后在浏览器中访问 `http://<服务端IP>:8765/`。

**Q: 工作流文件保存在哪里？**
> 默认保存在 `workflows/` 目录（与 `server.py` 同级），可通过 `python server.py --data ./其他目录` 自定义。

**Q: 如何扩展自定义节点？**
> 在 `nodes.js` 的 `NODE_LIBRARY` 数组中添加节点定义，在 `server.py` 的 `NODE_LIBRARY` 中同步添加（两者保持一致），刷新页面即可在节点库中看到新节点。

**Q: 执行时提示"工作流存在循环依赖"**
> 工作流中存在从下游指向上游的连线，导致无法确定执行顺序。请检查并删除形成循环的连线。

---

## 许可证

MIT License
