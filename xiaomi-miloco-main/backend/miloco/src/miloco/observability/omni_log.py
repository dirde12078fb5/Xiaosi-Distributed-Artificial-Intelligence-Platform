"""omni 交互 log 落盘。

debug-only。脱敏 multi-modal 块,buffer 攒批 + 30s 超时 flush,
multi-member gzip append 到 ``$MILOCO_HOME/trace/omni/YYYYMMDD.jsonl.gz``。
SIGTERM / atexit 强制 flush。
"""
from __future__ import annotations

import atexit
import copy
import gzip
import json
import logging
import os
import signal
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from miloco.observability.context import get_trace_id
from miloco.observability.debug import is_debug_enabled
from miloco.utils.paths import miloco_home
from miloco.utils.time_utils import deploy_timezone

logger = logging.getLogger(__name__)

MAX_RECORDS = 100
MAX_INTERVAL_S = 30.0
# 白名单反转:只保留纯文本块,其余 multi-modal 内容(图/音/视频/文件)全脱敏。
# 这样未来新加 multimodal type(如 video_url、file 等)自动被脱,不会因漏更新黑名单
# 导致原始 base64 数据写入 dump 文件。
_PRESERVE_TYPES = ("text",)

_buffer: list[dict[str, Any]] = []
_buffer_lock = threading.Lock()
_last_flush_ts = time.monotonic()
_atexit_registered = False
_sigterm_registered = False
# SIGTERM 注册前的原 handler,_on_sigterm flush 完后转调,避免覆盖 main.py 的链路。
_prev_sigterm_handler: Any = None


def redact_multimodal(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """脱敏 multi-modal 块,深拷贝后改,不影响原 message。

    content list 内 type ∉ _PRESERVE_TYPES → 替换为 {type, _redacted: true}。
    string 类型 content (如 system prompt)整体保留。
    """
    out = copy.deepcopy(messages)
    for msg in out:
        content = msg.get("content")
        if isinstance(content, list):
            for i, blk in enumerate(content):
                if isinstance(blk, dict):
                    t = blk.get("type", "")
                    if t not in _PRESERVE_TYPES:
                        content[i] = {"type": t, "_redacted": True}
    return out


def _log_dir() -> Path:
    return miloco_home() / "trace" / "omni"


def _pick_target_file(max_bytes: int) -> Path:
    """选今天 append 的目标文件,支持 size rotate。

    max_bytes <= 0 → 关 rotate,永远用 YYYYMMDD.jsonl.gz(老行为)。
    否则从 base 起按序号找第一个不存在或 size < max_bytes 的:
      YYYYMMDD.jsonl.gz → YYYYMMDD.1.jsonl.gz → YYYYMMDD.2.jsonl.gz → ...
    每次 flush 重算,不缓存——多进程 / 重启场景下也能自动接到当前未满文件。
    """
    d = _log_dir()
    d.mkdir(parents=True, exist_ok=True)
    day = datetime.now().strftime("%Y%m%d")
    base = d / f"{day}.jsonl.gz"
    if max_bytes <= 0:
        return base
    if not base.exists() or base.stat().st_size < max_bytes:
        return base
    n = 1
    while True:
        candidate = d / f"{day}.{n}.jsonl.gz"
        if not candidate.exists() or candidate.stat().st_size < max_bytes:
            return candidate
        n += 1


def publish_omni_log(
    *,
    device_trace_id: str,
    device_id: str,
    room_name: str,
    messages: list[dict[str, Any]],
    response: str,
    usage: dict[str, Any],
    latency_ms: float,
    error: dict[str, Any] | None = None,
    model: str = "",
) -> None:
    """omni 调用完成后调用。

    debug off → 直接返回零开销;debug on → 脱敏 + push buffer + 阈值触发 flush。
    """
    if not is_debug_enabled():
        return
    _ensure_atexit()

    now_dt = datetime.now(deploy_timezone())
    record = {
        "ts": int(now_dt.timestamp() * 1000),
        "local_time": now_dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + now_dt.strftime("%z"),
        "trace_id": get_trace_id(),
        "device_trace_id": device_trace_id,
        "device_id": device_id,
        "room_name": room_name,
        "model": model,
        "messages": redact_multimodal(messages),
        "response": response,
        "usage": usage,
        "latency_ms": latency_ms,
        "error": error,
    }

    with _buffer_lock:
        _buffer.append(record)
        need_flush = (
            len(_buffer) >= MAX_RECORDS
            or (time.monotonic() - _last_flush_ts) >= MAX_INTERVAL_S
        )

    if need_flush:
        flush()


def flush() -> None:
    """把 buffer 中所有 record 以 multi-member gzip 方式 append 到当天文件。

    单文件超过 ``perf.omni_log_max_file_mb`` 时 rotate 到 YYYYMMDD.N.jsonl.gz。
    """
    global _last_flush_ts
    with _buffer_lock:
        if not _buffer:
            _last_flush_ts = time.monotonic()
            return
        records = list(_buffer)
        _buffer.clear()
        _last_flush_ts = time.monotonic()

    max_bytes = _max_bytes_from_settings()
    path = _pick_target_file(max_bytes)
    payload = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)
    try:
        with open(path, "ab") as f:
            with gzip.GzipFile(fileobj=f, mode="wb") as gz:
                gz.write(payload.encode("utf-8"))
    except Exception:
        logger.exception("omni_log flush failed; %d records dropped", len(records))


def _max_bytes_from_settings() -> int:
    """读 settings,失败时禁用 rotate(返回 0),保证 flush 不因配置异常崩溃。"""
    try:
        from miloco.config import get_settings
        mb = get_settings().perf.omni_log_max_file_mb
        return int(mb) * 1024 * 1024 if mb > 0 else 0
    except Exception:
        return 0


def _ensure_atexit() -> None:
    """atexit 兜底:进程退出前 flush buffer。

    atexit.register 不限线程,任意路径首次 publish 时注册即可;signal handler
    必须主线程注册,见 register_sigterm_handler。两者生命周期不同,故拆开 flag
    分别守护 — 共用 flag 会让 signal 静默注册失败时 atexit 看似成功,隐患。
    """
    global _atexit_registered
    if _atexit_registered:
        return
    atexit.register(flush)
    _atexit_registered = True


def register_sigterm_handler() -> None:
    """主线程注册 SIGTERM flush hook。由 main.py lifespan 在主线程显式调用。

    signal.signal 只能主线程调,放 publish_omni_log 的 lazy 注册路径里有竞态:
    若首次 publish 跑在 threadpool 线程,signal 注册静默失败而 atexit 成功,
    SIGTERM 来时不 flush。改由 lifespan 入口显式调用,确保主线程执行。
    """
    global _sigterm_registered, _prev_sigterm_handler
    if _sigterm_registered:
        return
    try:
        # 不能盲目覆盖原 handler:main.py 等可能已注册自己的 SIGTERM 钩子。
        # 取出原 handler 暂存,_on_sigterm flush 完后把信号转给原 handler。
        _prev_sigterm_handler = signal.signal(signal.SIGTERM, _on_sigterm)
        _sigterm_registered = True
    except ValueError:
        # 极端兜底:理论上 lifespan 一定在主线程,不该走到。logger 留 trace 排查。
        logger.warning("register_sigterm_handler called off main thread; skipped")


def _on_sigterm(signum, frame) -> None:
    flush()
    prev = _prev_sigterm_handler
    if callable(prev):
        prev(signum, frame)
    elif prev == signal.SIG_DFL:
        # 默认 = 进程被 SIGTERM 终止;flush 后照默认行为退出。
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        os.kill(os.getpid(), signal.SIGTERM)
    # SIG_IGN 或 None:原本就忽略,什么都不做


def _buffer_size() -> int:
    return len(_buffer)


def reset_buffer_for_tests() -> None:
    global _last_flush_ts
    with _buffer_lock:
        _buffer.clear()
        _last_flush_ts = time.monotonic()
