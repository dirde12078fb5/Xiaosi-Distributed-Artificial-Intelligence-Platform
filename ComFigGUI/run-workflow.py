"""
ConfigGUI · 工作流执行脚本（命令行版）

从 JSON 文件加载工作流并模拟执行，输出执行报告。
也可与 server.py 中的 execute_workflow 函数直接互通。

使用示例：
  python run-workflow.py demo_workflow.json
  python run-workflow.py demo_workflow.json --out report.json
  python run-workflow.py --gen-demo demo_workflow.json      # 生成示例工作流
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# 复用 server.py 中定义的 execute_workflow / topological_order
# 这样只需要维护一份节点/逻辑定义
try:
    from server import execute_workflow  # type: ignore[attr-defined]
except Exception:  # noqa: BLE001
    # 独立运行的降级实现（仅当 server.py 不可用时）
    def execute_workflow(workflow):  # type: ignore[no-redef]
        nodes = workflow.get("nodes", [])
        wires = workflow.get("wires", [])
        id_set = {n["id"] for n in nodes}
        in_deg = {n["id"]: 0 for n in nodes}
        adj = {n["id"]: [] for n in nodes}
        for w in wires:
            fr, to = w["from"]["nodeId"], w["to"]["nodeId"]
            if fr in id_set and to in id_set:
                adj[fr].append(to)
                in_deg[to] += 1
        queue = [nid for nid, d in in_deg.items() if d == 0]
        order = []
        while queue:
            nid = queue.pop(0)
            order.append(nid)
            for nxt in adj[nid]:
                in_deg[nxt] -= 1
                if in_deg[nxt] == 0:
                    queue.append(nxt)
        if len(order) != len(nodes):
            raise ValueError("工作流存在循环依赖")
        logs = []
        node_by_id = {n["id"]: n for n in nodes}
        for idx, nid in enumerate(order, 1):
            n = node_by_id[nid]
            t0 = time.perf_counter()
            sleep_ms = {"KSampler": 40, "KSamplerAdvanced": 40,
                        "VAEDecode": 25, "VAEEncode": 25,
                        "CLIPTextEncode": 15}.get(n.get("type"), 5)
            time.sleep(sleep_ms / 1000.0)
            logs.append({
                "step": idx, "id": nid, "type": n.get("type"),
                "title": n.get("title"),
                "elapsed_ms": round((time.perf_counter() - t0) * 1000, 2),
                "params": n.get("params", {}),
            })
        return {"ok": True, "nodes": len(nodes), "wires": len(wires),
                "order": order, "logs": logs, "ts": time.strftime("%Y-%m-%d %H:%M:%S")}


DEMO_WORKFLOW = {
    "version": 1,
    "name": "demo_basic",
    "nodes": [
        {"id": "ckpt", "type": "CheckpointLoaderSimple",
         "title": "CheckpointLoaderSimple", "x": 60, "y": 80,
         "params": {"ckpt_name": "v1-5-pruned-emaonly.safetensors"}},
        {"id": "pos", "type": "CLIPTextEncode", "title": "CLIPTextEncode (正)",
         "x": 340, "y": 40,
         "params": {"text": "masterpiece, best quality, 1girl, blue sky, cherry blossoms"}},
        {"id": "neg", "type": "CLIPTextEncode", "title": "CLIPTextEncode (负)",
         "x": 340, "y": 220,
         "params": {"text": "lowres, bad anatomy, bad hands, blurry"}},
        {"id": "latent", "type": "EmptyLatentImage", "title": "EmptyLatentImage",
         "x": 640, "y": 80,
         "params": {"width": 512, "height": 768, "batch_size": 1}},
        {"id": "k", "type": "KSampler", "title": "KSampler", "x": 920, "y": 80,
         "params": {"seed": 1337, "steps": 20, "cfg": 7.0, "sampler_name": "euler",
                    "scheduler": "normal", "denoise": 1.0}},
        {"id": "vae", "type": "VAEDecode", "title": "VAEDecode", "x": 1240, "y": 120,
         "params": {}},
        {"id": "save", "type": "SaveImage", "title": "SaveImage", "x": 1540, "y": 140,
         "params": {"filename_prefix": "ComfyUI"}},
    ],
    "wires": [
        {"from": {"nodeId": "ckpt", "port": "MODEL"}, "to": {"nodeId": "k", "port": "model"}},
        {"from": {"nodeId": "ckpt", "port": "CLIP"}, "to": {"nodeId": "pos", "port": "clip"}},
        {"from": {"nodeId": "ckpt", "port": "CLIP"}, "to": {"nodeId": "neg", "port": "clip"}},
        {"from": {"nodeId": "ckpt", "port": "VAE"}, "to": {"nodeId": "vae", "port": "vae"}},
        {"from": {"nodeId": "pos", "port": "COND"}, "to": {"nodeId": "k", "port": "positive"}},
        {"from": {"nodeId": "neg", "port": "COND"}, "to": {"nodeId": "k", "port": "negative"}},
        {"from": {"nodeId": "latent", "port": "LATENT"}, "to": {"nodeId": "k", "port": "latent_image"}},
        {"from": {"nodeId": "k", "port": "LATENT"}, "to": {"nodeId": "vae", "port": "samples"}},
        {"from": {"nodeId": "vae", "port": "IMAGE"}, "to": {"nodeId": "save", "port": "images"}},
    ],
}


def main() -> int:
    parser = argparse.ArgumentParser(description="ConfigGUI · 执行工作流")
    parser.add_argument("file", nargs="?", help="工作流 JSON 文件路径")
    parser.add_argument("--gen-demo", metavar="OUT",
                        help="生成演示工作流 JSON 到指定文件并退出")
    parser.add_argument("--out", help="将结果保存为 JSON 报告")
    parser.add_argument("--quiet", action="store_true", help="不打印详细日志到控制台")
    args = parser.parse_args()

    if args.gen_demo:
        out = Path(args.gen_demo)
        out.write_text(json.dumps(DEMO_WORKFLOW, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        print(f"[OK] 已写入示例工作流：{out.resolve()}")
        return 0

    if not args.file:
        parser.print_help()
        return 2

    src = Path(args.file)
    if not src.is_file():
        print(f"[错误] 文件不存在：{src}", file=sys.stderr)
        return 1

    try:
        workflow = json.loads(src.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"[错误] JSON 解析失败：{e}", file=sys.stderr)
        return 1

    t0 = time.perf_counter()
    try:
        result = execute_workflow(workflow)
    except ValueError as e:
        print(f"[错误] {e}", file=sys.stderr)
        return 1
    except Exception as e:  # noqa: BLE001
        print(f"[错误] {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    elapsed = (time.perf_counter() - t0) * 1000

    if not args.quiet:
        print("=" * 56)
        print(f"  ConfigGUI · 工作流执行报告  ({result.get('ts')})")
        print("=" * 56)
        print(f"  工作流文件 : {src.resolve()}")
        print(f"  节点数     : {result.get('nodes')}")
        print(f"  连线数     : {result.get('wires')}")
        print(f"  执行顺序   : {' -> '.join(result.get('order', []))}")
        print(f"  总耗时     : {result.get('total_ms')} ms")
        print(f"  (测量开销) : {round(elapsed - result.get('total_ms', 0), 2)} ms")
        print("-" * 56)
        print(f"  {'#':>3}  {'节点类型':<22}  {'耗时(ms)':>9}  参数")
        print("-" * 56)
        for row in result.get("logs", []):
            param_preview = ", ".join(
                f"{k}={v}" for k, v in list(row.get("params", {}).items())[:3]
            )
            print(f"  {row['step']:>3}  {row.get('type',''):<22}  {row['elapsed_ms']:>9.2f}  {param_preview}")
        print("=" * 56)
        print("  执行成功 ✓")

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps({"source": str(src.resolve()), **result},
                       ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        if not args.quiet:
            print(f"  报告已保存 : {out_path.resolve()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
