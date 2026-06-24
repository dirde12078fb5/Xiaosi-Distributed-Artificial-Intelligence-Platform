"""统一时间工具函数。

提供 perception / rule / repo / task_record 等模块共用的时间能力。

# 不变量

- DB 内时间字段统一 `INTEGER` (Unix ms,UTC 绝对时刻)
- 应用层拿到的时间字段统一 `str`,带偏移的本地时区 ISO(如 ``+08:00``),repo 出口已转
- API 出口统一带偏移本地 ISO(``ms_to_iso_local`` 走 ``deploy_timezone()``),
  跨时区客户端 JS ``new Date(value)`` 仍正确解析为本地时区
- `now_ms()` 是项目内唯一获取"当前时刻"的函数
- `deploy_timezone()` 是项目内唯一获取"部署时区"的函数
"""

import functools
import logging
import os
import time
from datetime import datetime, timedelta, tzinfo
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from miloco.middleware.exceptions import ValidationException

_logger = logging.getLogger(__name__)


def now_ms() -> int:
    """当前时刻的 Unix ms (UTC 绝对时刻)。项目内唯一获取当前时间的入口。"""
    return int(time.time() * 1000)


def ms_to_iso_local(ms: int | str | None) -> str | None:
    """Unix ms → 部署时区带偏移 ISO 8601(如 ``2026-06-16T17:19:45+08:00``)。

    API 出口与 repo 出口默认转换,内部走 ``deploy_timezone()``。
    跨时区客户端 JS ``new Date(value)`` 仍能正确解析为浏览器本地时区。

    字符串入参兜底:SQLite INTEGER 列 type affinity 允许字符串塞入,迁移残留或
    测试 fixture 直插字符串时透传,避免上层炸。
    """
    if ms is None:
        return None
    if isinstance(ms, str):
        return ms
    return datetime.fromtimestamp(ms / 1000, tz=deploy_timezone()).isoformat(
        timespec="seconds"
    )


def ms_to_iso_at(ms: int | None, tz: tzinfo) -> str | None:
    """Unix ms → 指定时区的 ISO 8601 字符串。仅日志 / CLI 展示用,API 别用这个。"""
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=tz).isoformat(timespec="seconds")


def iso_to_ms(s: str | None) -> int | None:
    """ISO 8601 字符串 → Unix ms。

    aware / naive 都接受;naive 按 ``deploy_timezone()`` 解读(符合 ISO 8601 标准约定)。
    """
    if s is None:
        return None
    s = s.replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=deploy_timezone())
    return int(dt.timestamp() * 1000)


def ms_to_aware_dt(ms: int, tz: tzinfo | None = None) -> datetime:
    """Unix ms → aware datetime。默认 ``deploy_timezone()``,给业务逻辑层(rollover/today)用。"""
    return datetime.fromtimestamp(ms / 1000, tz=tz or deploy_timezone())


_FALLBACK_TZ = ZoneInfo("Asia/Shanghai")
_warned_no_iana = False


@functools.lru_cache(maxsize=1)
def _system_iana_tz() -> ZoneInfo | None:
    """读 ``TZ`` env / ``/etc/timezone`` / ``/etc/localtime`` symlink → ``ZoneInfo``。

    进程级缓存:系统时区运行时不会变。任何一步拿到合法 IANA 名即返回,全失败返回 ``None``。
    返回 ``ZoneInfo`` 对象意味着 DST 规则内建生效,跟固定 offset 行为完全不同。
    """
    if name := os.environ.get("TZ"):
        try:
            return ZoneInfo(name)
        except ZoneInfoNotFoundError:
            pass
    p = Path("/etc/timezone")
    if p.is_file():
        try:
            return ZoneInfo(p.read_text().strip())
        except (ZoneInfoNotFoundError, OSError):
            pass
    p = Path("/etc/localtime")
    if p.is_symlink():
        try:
            target = os.readlink(p)
            # rfind:真正的 IANA 名一定在最右侧的 "zoneinfo/" 之后,
            # 防止 target 路径中其他位置出现 "zoneinfo" 子串切错位置。
            idx = target.rfind("zoneinfo/")
            if idx >= 0:
                return ZoneInfo(target[idx + len("zoneinfo/") :])
        except (ZoneInfoNotFoundError, OSError):
            pass
    return None


def deploy_timezone() -> tzinfo:
    """业务侧"部署时区"。优先级:

    1. ``settings.timezone`` (显式配置,IANA 名如 ``Asia/Shanghai``;
       ``MILOCO_TIMEZONE`` env 由 pydantic 自动并入此字段)
    2. 系统 IANA 反查 (``TZ`` env / ``/etc/timezone`` / ``/etc/localtime``)
    3. 兜底 ``Asia/Shanghai`` + 启动期 warning

    第 2 步必须拿到 IANA 名(而非固定 offset),因为 ``ZoneInfo`` 内建 DST 规则。
    旧实现用 ``datetime.now().astimezone().tzinfo`` 拿到的是启动时刻的固定偏移,
    跨过 DST 切换日会偏 1 小时。

    用于"今天 / 本周 / rollover"等部署侧业务概念,以及 API 出口 ISO 偏移后缀
    (``ms_to_iso_local`` 走本函数)。DB 存储始终 INTEGER ms (UTC 绝对时刻),
    与本函数无关。
    """
    # Lazy import:避免 utils ← config 的循环引用。
    from miloco.config import get_settings

    try:
        tz_name = get_settings().timezone
    except (LookupError, AttributeError):
        # 仅吞"settings 尚未初始化"类异常;ValidationError 应启动期暴露。
        tz_name = None
    if tz_name:
        return ZoneInfo(tz_name)
    if iana := _system_iana_tz():
        return iana
    global _warned_no_iana
    if not _warned_no_iana:
        _logger.warning(
            "Could not detect system IANA timezone; falling back to Asia/Shanghai. "
            "If deploying outside China, set MILOCO_TIMEZONE or settings.timezone "
            "to your IANA zone name (e.g. America/Los_Angeles, Europe/London)."
        )
        _warned_no_iana = True
    return _FALLBACK_TZ


def now_iso() -> str:
    """当前时刻的部署时区带偏移 ISO 8601 字符串。

    保留作为向后兼容别名:等价于 ``ms_to_iso_local(now_ms())``。新代码优先用 ``now_ms()``,
    需要 ISO 字符串时再 ``ms_to_iso_local()``。
    """
    return ms_to_iso_local(now_ms())  # type: ignore[return-value]


def parse_since(since_str: str) -> timedelta:
    """解析相对时间字符串为 timedelta。

    支持 h/m/s/d 单单位及组合:1h, 30m, 90s, 7d, 2h30m, 1h30m20s
    """
    if not since_str:
        raise ValidationException("Empty 'since' value")

    total_seconds = 0
    current_num = ""

    for ch in since_str.strip():
        if ch.isdigit():
            current_num += ch
        elif ch in ("h", "m", "s", "d") and current_num:
            multiplier = {"h": 3600, "m": 60, "s": 1, "d": 86400}
            total_seconds += int(current_num) * multiplier[ch]
            current_num = ""
        else:
            raise ValidationException(
                f"Invalid 'since' format: {since_str}. "
                "Expected e.g. '30m', '1h', '2h30m', '7d'."
            )

    if current_num:
        total_seconds += int(current_num) * 60

    if total_seconds <= 0:
        raise ValidationException(f"Invalid 'since' value: {since_str}")

    return timedelta(seconds=total_seconds)


def parse_iso_ms(value: str, field_name: str) -> int:
    """解析 ISO 8601 时间戳为 Unix ms。naive 字符串按 ``deploy_timezone()`` 解读。"""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationException(
            f"Invalid ISO 8601 timestamp for {field_name!r}: {value}"
        ) from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=deploy_timezone())
    return int(dt.timestamp() * 1000)


def since_to_ms(since_str: str) -> int:
    """解析相对时间字符串,返回对应的绝对 Unix ms 时间戳 (当前时间 - delta)。"""
    td = parse_since(since_str)
    return int((time.time() - td.total_seconds()) * 1000)
