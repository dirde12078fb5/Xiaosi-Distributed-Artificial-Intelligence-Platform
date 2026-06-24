"""ColoredFormatter 单测:WARNING/ERROR 的 levelname+message 上色,INFO 不染色,
且格式化后还原 record(防其它 handler 复用时带色码)。"""

from __future__ import annotations

import logging

from miloco.utils.logger import ColoredFormatter

_FMT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_RESET = "\033[0m"
_YELLOW = "\033[48;5;240;93m"  # 灰底亮黄
_RED = "\033[48;5;240;91m"     # 灰底亮红


def _make(level: int, msg: str) -> logging.LogRecord:
    return logging.LogRecord("miloco.test", level, __file__, 1, msg, None, None)


def test_warning_levelname_and_message_colored():
    out = ColoredFormatter(fmt=_FMT, datefmt="%H:%M:%S").format(
        _make(logging.WARNING, "[omni] 调用失败 | ReadTimeout")
    )
    assert f"{_YELLOW}WARNING{_RESET}" in out
    assert f"{_YELLOW}[omni] 调用失败 | ReadTimeout{_RESET}" in out
    assert out.count(_YELLOW) == 2  # 仅 levelname + message 两段被裹
    assert " - miloco.test - " in out  # logger name 不染色


def test_error_colored_red():
    out = ColoredFormatter(fmt=_FMT).format(_make(logging.ERROR, "[omni] fused 主调用失败"))
    assert f"{_RED}ERROR{_RESET}" in out
    assert f"{_RED}[omni] fused 主调用失败{_RESET}" in out


def test_info_not_colored():
    out = ColoredFormatter(fmt=_FMT).format(_make(logging.INFO, "normal"))
    assert "\033[" not in out  # INFO 无任何色码


def test_non_marker_warning_not_colored():
    """非白名单 WARNING（如 dup_id 噪音）不染色——只有 omni 失败相关才染。"""
    out = ColoredFormatter(fmt=_FMT).format(
        _make(logging.WARNING, "track_id=422 收到 dup_id 标记")
    )
    assert "\033[" not in out


def test_non_marker_error_not_colored():
    out = ColoredFormatter(fmt=_FMT).format(
        _make(logging.ERROR, "Batch pipeline failed: something")
    )
    assert "\033[" not in out


def test_record_restored_after_format():
    rec = _make(logging.ERROR, "[omni] boom")  # 含 marker → 走染色路径
    ColoredFormatter(fmt=_FMT).format(rec)
    assert rec.levelname == "ERROR"
    assert rec.msg == "[omni] boom"
    assert "\033[" not in rec.getMessage()
