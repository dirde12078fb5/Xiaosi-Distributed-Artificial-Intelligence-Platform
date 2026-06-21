"""
ConfigGUI · 轻量级 HTTP 服务（Python 标准库实现，零依赖）

功能：
  1. 提供 index.html、styles.css、*.js 等静态资源
  2. /api/workflow   GET=列出保存的工作流   POST=保存   DELETE=删除
  3. /api/workflow/<name>  GET=下载指定工作流 JSON
  4. /api/run       POST=执行工作流（模拟执行，返回执行日志和拓扑顺序）
  5. /api/nodes     GET=返回节点库元数据，供前端动态生成

使用：
  python server.py                        # 默认端口 8765
  python server.py --port 8080            # 自定义端口
  python server.py --host 0.0.0.0         # 允许局域网访问
  python server.py --data ./my_workflows  # 自定义工作流存储目录

启动后浏览器自动打开 http://127.0.0.1:<port>/
"""

from __future__ import annotations

import argparse
import html
import http.server
import json
import os
import socketserver
import sys
import threading
import time
import urllib.parse
import webbrowser
from pathlib import Path
from typing import Any


# ---------- 节点库（与前端 nodes.js 保持一致，供 API 查询） ----------
PORT_COLORS: dict[str, str] = {
    "MODEL": "#7aa2f7",
    "CLIP": "#bb9af7",
    "VAE": "#9ece6a",
    "LATENT": "#e0af68",
    "IMAGE": "#7dcfff",
    "CONDITIONING": "#f7768e",
    "MASK": "#73daca",
    "STRING": "#c0caf5",
    "INT": "#ffd166",
    "FLOAT": "#ffb86c",
    "BOOLEAN": "#c792ea",
    "SEED": "#ff9e64",
}

NODE_LIBRARY: list[dict[str, Any]] = [
    {
        "category": "加载器",
        "color": PORT_COLORS["MODEL"],
        "nodes": [
            {"type": "CheckpointLoaderSimple", "title": "CheckpointLoaderSimple",
             "description": "加载检查点模型（ckpt / safetensors），输出模型、CLIP 和 VAE。",
             "inputs": [{"name": "ckpt_name", "type": "STRING", "default": "v1-5-pruned-emaonly.safetensors",
                         "control": "text", "label": "模型名称"}],
             "outputs": [{"name": "MODEL", "type": "MODEL"},
                         {"name": "CLIP", "type": "CLIP"},
                         {"name": "VAE", "type": "VAE"}]},
            {"type": "VAELoader", "title": "VAELoader", "description": "单独加载 VAE 模型。",
             "inputs": [{"name": "vae_name", "type": "STRING", "default": "vae-ft-mse-840000.safetensors",
                         "control": "text", "label": "VAE 名称"}],
             "outputs": [{"name": "VAE", "type": "VAE"}]},
        ],
    },
    {
        "category": "条件",
        "color": PORT_COLORS["CONDITIONING"],
        "nodes": [
            {"type": "CLIPTextEncode", "title": "CLIPTextEncode",
             "description": "使用 CLIP 将文本编码为条件向量，用于正向或反向提示。",
             "inputs": [{"name": "clip", "type": "CLIP"},
                        {"name": "text", "type": "STRING",
                         "default": "masterpiece, best quality, 1girl, blue sky, cherry blossoms",
                         "control": "textarea", "label": "文本"}],
             "outputs": [{"name": "COND", "type": "CONDITIONING"}]},
            {"type": "ConditioningZeroOut", "title": "ConditioningZeroOut",
             "description": "将条件向量置零，提供一个中性起点。",
             "inputs": [{"name": "conditioning", "type": "CONDITIONING"}],
             "outputs": [{"name": "COND", "type": "CONDITIONING"}]},
        ],
    },
    {
        "category": "采样",
        "color": PORT_COLORS["LATENT"],
        "nodes": [
            {"type": "KSampler", "title": "KSampler", "description": "核心扩散采样器，从模型采样出潜在图像。",
             "inputs": [{"name": "model", "type": "MODEL"},
                        {"name": "positive", "type": "CONDITIONING"},
                        {"name": "negative", "type": "CONDITIONING"},
                        {"name": "latent_image", "type": "LATENT"}],
             "outputs": [{"name": "LATENT", "type": "LATENT"}],
             "params": [
                 {"name": "seed", "type": "INT", "default": 1337, "control": "number", "label": "种子 (seed)",
                  "min": 0, "max": 9999999999},
                 {"name": "steps", "type": "INT", "default": 20, "control": "number", "label": "步数", "min": 1, "max": 100},
                 {"name": "cfg", "type": "FLOAT", "default": 7.0, "control": "number", "label": "CFG", "step": 0.1, "min": 0, "max": 30},
                 {"name": "sampler_name", "type": "STRING", "default": "euler", "control": "select", "label": "采样器",
                  "options": ["euler", "euler_ancestral", "dpmpp_2m", "dpmpp_sde", "heun", "dpm_2", "dpm_2_ancestral", "lms"]},
                 {"name": "scheduler", "type": "STRING", "default": "normal", "control": "select", "label": "调度器",
                  "options": ["normal", "karras", "simple", "ddim_uniform"]},
                 {"name": "denoise", "type": "FLOAT", "default": 1.0, "control": "number", "label": "去噪强度",
                  "step": 0.01, "min": 0, "max": 1},
             ]},
            {"type": "KSamplerAdvanced", "title": "KSamplerAdvanced",
             "description": "进阶采样器，可指定起始/结束步。",
             "inputs": [{"name": "model", "type": "MODEL"},
                        {"name": "positive", "type": "CONDITIONING"},
                        {"name": "negative", "type": "CONDITIONING"},
                        {"name": "latent_image", "type": "LATENT"}],
             "outputs": [{"name": "LATENT", "type": "LATENT"}],
             "params": [
                 {"name": "seed", "type": "INT", "default": 1337, "control": "number", "label": "种子", "min": 0},
                 {"name": "steps", "type": "INT", "default": 20, "control": "number", "label": "步数", "min": 1},
                 {"name": "cfg", "type": "FLOAT", "default": 7.0, "control": "number", "label": "CFG", "step": 0.1},
                 {"name": "start_at_step", "type": "INT", "default": 0, "control": "number", "label": "起始步", "min": 0},
                 {"name": "end_at_step", "type": "INT", "default": 20, "control": "number", "label": "结束步", "min": 0},
                 {"name": "denoise", "type": "FLOAT", "default": 1.0, "control": "number", "label": "去噪强度",
                  "step": 0.01, "min": 0, "max": 1},
             ]},
        ],
    },
    {
        "category": "潜空间",
        "color": PORT_COLORS["LATENT"],
        "nodes": [
            {"type": "EmptyLatentImage", "title": "EmptyLatentImage",
             "description": "生成指定尺寸的空白潜在图像。",
             "inputs": [], "outputs": [{"name": "LATENT", "type": "LATENT"}],
             "params": [
                 {"name": "width", "type": "INT", "default": 512, "control": "number", "label": "宽度",
                  "min": 64, "max": 4096, "step": 8},
                 {"name": "height", "type": "INT", "default": 512, "control": "number", "label": "高度",
                  "min": 64, "max": 4096, "step": 8},
                 {"name": "batch_size", "type": "INT", "default": 1, "control": "number", "label": "批次大小",
                  "min": 1, "max": 64},
             ]},
            {"type": "LatentUpscaleBy", "title": "LatentUpscaleBy",
             "description": "按倍率放大潜在图像。",
             "inputs": [{"name": "samples", "type": "LATENT"}],
             "outputs": [{"name": "LATENT", "type": "LATENT"}],
             "params": [
                 {"name": "upscaler", "type": "STRING", "default": "nearest-exact", "control": "select",
                  "label": "上采样方法", "options": ["nearest-exact", "bilinear", "area", "bicubic"]},
                 {"name": "scale_by", "type": "FLOAT", "default": 1.5, "control": "number", "label": "倍率",
                  "step": 0.1, "min": 0.1},
             ]},
        ],
    },
    {
        "category": "解码",
        "color": PORT_COLORS["VAE"],
        "nodes": [
            {"type": "VAEDecode", "title": "VAEDecode",
             "description": "使用 VAE 将潜在图像解码为像素图像。",
             "inputs": [{"name": "samples", "type": "LATENT"}, {"name": "vae", "type": "VAE"}],
             "outputs": [{"name": "IMAGE", "type": "IMAGE"}]},
            {"type": "VAEEncode", "title": "VAEEncode",
             "description": "使用 VAE 将图像编码为潜在图像。",
             "inputs": [{"name": "pixels", "type": "IMAGE"}, {"name": "vae", "type": "VAE"}],
             "outputs": [{"name": "LATENT", "type": "LATENT"}]},
        ],
    },
    {
        "category": "图像",
        "color": PORT_COLORS["IMAGE"],
        "nodes": [
            {"type": "LoadImage", "title": "LoadImage", "description": "从文件加载图像。",
             "inputs": [], "outputs": [{"name": "IMAGE", "type": "IMAGE"}, {"name": "MASK", "type": "MASK"}],
             "params": [{"name": "image", "type": "STRING", "default": "example.png", "control": "text",
                         "label": "图像文件名"}]},
            {"type": "SaveImage", "title": "SaveImage", "description": "将图像保存到输出目录。",
             "inputs": [{"name": "images", "type": "IMAGE"}], "outputs": [],
             "params": [{"name": "filename_prefix", "type": "STRING", "default": "ComfyUI", "control": "text",
                         "label": "文件名前缀"}]},
            {"type": "ImageScale", "title": "ImageScale", "description": "缩放图像到指定尺寸。",
             "inputs": [{"name": "image", "type": "IMAGE"}], "outputs": [{"name": "IMAGE", "type": "IMAGE"}],
             "params": [
                 {"name": "method", "type": "STRING", "default": "lanczos", "control": "select",
                  "label": "插值方法", "options": ["nearest-exact", "bilinear", "bicubic", "lanczos"]},
                 {"name": "width", "type": "INT", "default": 512, "control": "number", "label": "宽度", "min": 1},
                 {"name": "height", "type": "INT", "default": 512, "control": "number", "label": "高度", "min": 1},
             ]},
            {"type": "ImageInvert", "title": "ImageInvert", "description": "反转图像颜色。",
             "inputs": [{"name": "image", "type": "IMAGE"}], "outputs": [{"name": "IMAGE", "type": "IMAGE"}]},
        ],
    },
    {
        "category": "高级",
        "color": "#bb9af7",
        "nodes": [
            {"type": "SetNoise", "title": "SetNoiseSeed",
             "description": "为工作流设置固定噪声种子，便于复现。",
             "inputs": [{"name": "noise", "type": "LATENT"}],
             "outputs": [{"name": "NOISE", "type": "LATENT"}],
             "params": [{"name": "seed", "type": "INT", "default": 0, "control": "number", "label": "种子", "min": 0}]},
            {"type": "Note", "title": "备注 / Note",
             "description": "一个纯文本备注，用于工作流文档化。",
             "inputs": [], "outputs": [],
             "params": [{"name": "content", "type": "STRING", "default": "在此记录本节点段的用途、参考或参数...",
                         "control": "textarea", "label": "内容"}]},
        ],
    },
]


# ---------- 工作流工具函数（可被脚本复用） ----------
def topological_order(nodes: list[dict[str, Any]], wires: list[dict[str, Any]]) -> list[str]:
    """返回按拓扑排序的节点 id 列表；若存在环则抛 ValueError。"""
    id_set = {n["id"] for n in nodes}
    in_deg = {n["id"]: 0 for n in nodes}
    adj: dict[str, list[str]] = {n["id"]: [] for n in nodes}
    for w in wires:
        fr, to = w["from"]["nodeId"], w["to"]["nodeId"]
        if fr not in id_set or to not in id_set:
            continue
        adj[fr].append(to)
        in_deg[to] = in_deg.get(to, 0) + 1
    queue = [nid for nid, d in in_deg.items() if d == 0]
    result: list[str] = []
    while queue:
        nid = queue.pop(0)
        result.append(nid)
        for nxt in adj[nid]:
            in_deg[nxt] -= 1
            if in_deg[nxt] == 0:
                queue.append(nxt)
    if len(result) != len(nodes):
        raise ValueError("工作流存在循环依赖，无法执行")
    return result


def execute_workflow(workflow: dict[str, Any]) -> dict[str, Any]:
    """模拟执行工作流，返回执行日志与耗时。"""
    nodes = workflow.get("nodes", [])
    wires = workflow.get("wires", [])
    t0 = time.perf_counter()
    order = topological_order(nodes, wires)
    logs: list[dict[str, Any]] = []
    node_by_id = {n["id"]: n for n in nodes}
    for idx, nid in enumerate(order, 1):
        n = node_by_id[nid]
        step_t0 = time.perf_counter()
        # 简单模拟：根据节点类型做不同耗时
        sleep_ms = {"KSampler": 40, "KSamplerAdvanced": 40,
                    "VAEDecode": 25, "VAEEncode": 25,
                    "CLIPTextEncode": 15}.get(n.get("type"), 5)
        time.sleep(sleep_ms / 1000.0)
        logs.append({
            "step": idx,
            "id": nid,
            "type": n.get("type"),
            "title": n.get("title"),
            "elapsed_ms": round((time.perf_counter() - step_t0) * 1000, 2),
            "params": n.get("params", {}),
        })
    return {
        "ok": True,
        "nodes": len(nodes),
        "wires": len(wires),
        "order": order,
        "logs": logs,
        "total_ms": round((time.perf_counter() - t0) * 1000, 2),
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


# ---------- HTTP 请求处理 ----------
class ConfigGUIHandler(http.server.SimpleHTTPRequestHandler):
    """将静态资源与 JSON API 结合在同一端口。"""

    server_version = "ConfigGUI/1.0"

    # 通过子类化注入 data_dir
    data_dir: Path = Path("workflows")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent), **kwargs)

    # ---------- 日志 ----------
    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: D401
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))

    # ---------- 路由 ----------
    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        if path == "/" or path == "":
            self.serve_file("index.html", "text/html; charset=utf-8")
            return
        if path == "/api/nodes":
            self.send_json({"port_colors": PORT_COLORS, "library": NODE_LIBRARY})
            return
        if path == "/api/workflow":
            files = []
            if self.data_dir.is_dir():
                for f in sorted(self.data_dir.glob("*.json")):
                    try:
                        data = json.loads(f.read_text(encoding="utf-8"))
                        files.append({
                            "name": f.stem,
                            "nodes": len(data.get("nodes", [])),
                            "wires": len(data.get("wires", [])),
                            "size": f.stat().st_size,
                            "mtime": time.strftime("%Y-%m-%d %H:%M:%S",
                                                   time.localtime(f.stat().st_mtime)),
                        })
                    except Exception:
                        continue
            self.send_json({"workflows": files})
            return
        if path.startswith("/api/workflow/"):
            name = urllib.parse.unquote(path[len("/api/workflow/"):])
            safe_name = Path(name).name  # 防止路径穿越
            fp = self.data_dir / f"{safe_name}.json"
            if not fp.is_file():
                self.send_error(404, "工作流不存在")
                return
            self.send_json(json.loads(fp.read_text(encoding="utf-8")))
            return
        # 其余走静态文件
        return super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        body = self._read_body()
        if path == "/api/workflow":
            data = json.loads(body) if body else {}
            name = (data.get("name") or time.strftime("wf_%Y%m%d_%H%M%S")).strip()
            # 过滤非法字符
            safe_name = "".join(c for c in name if c.isalnum() or c in "_- ")
            if not safe_name:
                self.send_error(400, "name 无效")
                return
            self.data_dir.mkdir(parents=True, exist_ok=True)
            fp = self.data_dir / f"{safe_name}.json"
            payload = {
                "version": data.get("version", 1),
                "name": safe_name,
                "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "nodes": data.get("nodes", []),
                "wires": data.get("wires", []),
            }
            fp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            self.send_json({"ok": True, "path": str(fp), "name": safe_name})
            return
        if path == "/api/run":
            try:
                workflow = json.loads(body) if body else {}
                result = execute_workflow(workflow)
                self.send_json(result)
            except ValueError as e:
                self.send_json({"ok": False, "error": str(e)}, status=422)
            except Exception as e:  # noqa: BLE001
                self.send_json({"ok": False, "error": f"{type(e).__name__}: {e}"}, status=500)
            return
        self.send_error(404, "接口未实现")

    def do_DELETE(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        if path.startswith("/api/workflow/"):
            name = urllib.parse.unquote(path[len("/api/workflow/"):])
            safe_name = Path(name).name
            fp = self.data_dir / f"{safe_name}.json"
            if not fp.is_file():
                self.send_error(404, "工作流不存在")
                return
            fp.unlink()
            self.send_json({"ok": True, "deleted": safe_name})
            return
        self.send_error(404, "接口未实现")

    # ---------- 辅助 ----------
    def _read_body(self) -> str:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return ""
        raw = self.rfile.read(length)
        return raw.decode("utf-8", errors="replace")

    def send_json(self, obj: Any, status: int = 200) -> None:
        payload = json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def serve_file(self, filename: str, mime: str) -> None:
        fp = Path(__file__).parent / filename
        if not fp.is_file():
            self.send_error(404, "文件不存在")
            return
        data = fp.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    # 默认处理静态文件时让 list_directory 返回友好 HTML
    def list_directory(self, path):  # type: ignore[override]
        try:
            entries = sorted(os.listdir(path))
        except OSError:
            self.send_error(403, "无权限列出目录")
            return None
        html_parts = [
            "<!doctype html><html><head><meta charset='utf-8'>"
            "<title>ConfigGUI · 文件列表</title>"
            "<style>body{font-family:system-ui;max-width:760px;margin:40px auto;padding:0 16px;color:#222}"
            "h1{font-size:20px}li{margin:4px 0}a{color:#1565c0}</style></head>"
            f"<body><h1>ConfigGUI · {html.escape(os.path.basename(path) or '/')}</h1>"
            "<ul>",
        ]
        for e in entries:
            link = urllib.parse.quote(e)
            html_parts.append(f"<li><a href='{link}'>{html.escape(e)}</a></li>")
        html_parts.append("</ul></body></html>")
        data = "".join(html_parts).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
        return None


class ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main() -> int:
    parser = argparse.ArgumentParser(description="ConfigGUI 轻量级 HTTP 服务")
    parser.add_argument("--host", default="127.0.0.1", help="绑定地址（默认 127.0.0.1）")
    parser.add_argument("--port", type=int, default=8765, help="监听端口（默认 8765）")
    parser.add_argument("--data", default="workflows", help="工作流存储目录（相对脚本路径）")
    parser.add_argument("--no-browser", action="store_true", help="启动后不自动打开浏览器")
    args = parser.parse_args()

    # 将工作流目录设置为相对脚本位置，避免在不同 cwd 下跑时散落
    script_parent = Path(__file__).resolve().parent
    data_dir = Path(args.data)
    if not data_dir.is_absolute():
        data_dir = script_parent / data_dir
    data_dir.mkdir(parents=True, exist_ok=True)

    # 绑定 data_dir 到 handler 类属性
    ConfigGUIHandler.data_dir = data_dir

    url = f"http://{args.host}:{args.port}/"
    print(f"[ConfigGUI] 服务已启动 -> {url}")
    print(f"[ConfigGUI] 工作流目录 -> {data_dir}")
    print("[ConfigGUI] 按 Ctrl+C 可退出")

    if not args.no_browser:
        # 给服务器一点时间启动，再打开浏览器
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()

    try:
        with ThreadingServer((args.host, args.port), ConfigGUIHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[ConfigGUI] 已停止")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
