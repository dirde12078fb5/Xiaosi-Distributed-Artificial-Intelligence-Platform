"""``time-compute`` CLI 子命令——时间锚点纯算（无 backend 依赖）。

LLM 只负责"识别 user 表达对应哪种 anchor"，本工具负责"按 anchor 算 ISO"。

时区按 ``deploy_timezone()`` 解读:优先 ``MILOCO_TIMEZONE`` env,其次系统 IANA 反查
(``TZ`` env / ``/etc/timezone`` / ``/etc/localtime``),兜底 ``Asia/Shanghai``。
跨时区部署天然支持(DST 时区由 ZoneInfo 处理)。

9 个 anchor primitives：
- ``end_of_day``                  今日 23:59:59
- ``end_of_week``                 本周日 23:59:59
- ``end_of_month``                本月末 23:59:59
- ``today_at {time}``             今日 ``HH:MM:SS``
- ``tomorrow_at {time}``          明日 ``HH:MM:SS``
- ``next_weekday {weekday, time?}`` 下一个匹配星期几（今天就是该星期 → 7 天后）
- ``add {amount, unit}``          相对加减（minutes/hours/days/weeks/months）
- ``date {month_day, time?}``     今年 MM-DD（已过则明年；2/29 非闰年 → 2/28）
- ``date_full {date, time?}``     绝对 YYYY-MM-DD

输出：``{ok: true, iso: "..."}`` 或 ``{ok: false, error: "...", detail?: "..."}``。
"""

import functools
import json
import logging
import os
import re
import sys
from datetime import datetime, timedelta, tzinfo
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import click

_logger = logging.getLogger(__name__)
_FALLBACK_TZ = ZoneInfo("Asia/Shanghai")
_warned_no_iana = False


@functools.lru_cache(maxsize=1)
def _system_iana_tz() -> ZoneInfo | None:
    """读 ``TZ`` env / ``/etc/timezone`` / ``/etc/localtime`` symlink → ``ZoneInfo``。

    进程级缓存。返回 ``ZoneInfo`` 而非固定偏移,DST 规则内建生效。全失败返回 ``None``。
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
            # rfind:防止 target 路径中其他位置出现 "zoneinfo" 子串切错位置。
            idx = target.rfind("zoneinfo/")
            if idx >= 0:
                return ZoneInfo(target[idx + len("zoneinfo/") :])
        except (ZoneInfoNotFoundError, OSError):
            pass
    return None


def deploy_timezone() -> tzinfo:
    """部署时区。优先级:

    1. ``MILOCO_TIMEZONE`` env (CLI 不读 backend ``config.json``,仅 env)
    2. 系统 IANA 反查 (``TZ`` / ``/etc/timezone`` / ``/etc/localtime``)
    3. 兜底 ``Asia/Shanghai`` + warning

    第 2 步必须拿 IANA 名(而非 ``datetime.now().astimezone().tzinfo`` 那种固定偏移),
    DST 区跨切换日才不会偏 1 小时。
    """
    if name := os.environ.get("MILOCO_TIMEZONE"):
        return ZoneInfo(name)
    if iana := _system_iana_tz():
        return iana
    global _warned_no_iana
    if not _warned_no_iana:
        _logger.warning(
            "Could not detect system IANA timezone; falling back to Asia/Shanghai. "
            "If running outside China, set MILOCO_TIMEZONE to your IANA zone name "
            "(e.g. America/Los_Angeles, Europe/London)."
        )
        _warned_no_iana = True
    return _FALLBACK_TZ

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d):([0-5]\d)$")
_MONTH_DAY_RE = re.compile(r"^(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")
_DATE_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")

_MAX_DAYS_OF_MONTH = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
_WEEKDAY_TO_MON1 = {
    "monday": 1,
    "tuesday": 2,
    "wednesday": 3,
    "thursday": 4,
    "friday": 5,
    "saturday": 6,
    "sunday": 7,
}

_END_OF_DAY = (23, 59, 59)


def _err(error: str, detail: str | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"ok": False, "error": error}
    if detail is not None:
        out["detail"] = detail
    return out


def _parse_now(iso: str) -> datetime | None:
    """解析 ISO8601 到部署时区视角的 datetime。"""
    try:
        dt = datetime.fromisoformat(iso)
    except ValueError:
        return None
    tz = deploy_timezone()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    return dt.astimezone(tz)


def _format_iso(dt: datetime) -> str:
    """部署时区 ISO 8601 字符串,带动态偏移后缀(如 ``+08:00`` / ``-08:00``)。"""
    tz = deploy_timezone()
    return dt.astimezone(tz).isoformat(timespec="seconds")


def _last_day_of_month(y: int, m: int) -> int:
    if m == 12:
        next_month = datetime(y + 1, 1, 1)
    else:
        next_month = datetime(y, m + 1, 1)
    return (next_month - timedelta(days=1)).day


def _parse_time(s: str) -> tuple[int, int, int] | None:
    m = _TIME_RE.match(s)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def _parse_month_day(s: str) -> tuple[int, int] | None:
    m = _MONTH_DAY_RE.match(s)
    if not m:
        return None
    month = int(m.group(1))
    day = int(m.group(2))
    if day > _MAX_DAYS_OF_MONTH[month - 1]:
        return None
    return month, day


def _parse_date(s: str) -> tuple[int, int, int] | None:
    if not _DATE_RE.match(s):
        return None
    parts = s.split("-")
    y, mo, d = int(parts[0]), int(parts[1]), int(parts[2])
    if d > _last_day_of_month(y, mo):
        return None
    return y, mo, d


def _make_iso(y: int, m: int, d: int, t: tuple[int, int, int]) -> dict[str, Any]:
    h, mi, s = t
    dt = datetime(y, m, d, h, mi, s, tzinfo=deploy_timezone())
    return {"ok": True, "iso": _format_iso(dt)}


def _day_mon1(dt: datetime) -> int:
    """Monday=1, Sunday=7（Python weekday() 是 Mon=0..Sun=6）。"""
    return dt.weekday() + 1


def _compute_add(now: datetime, amount: int | float, unit: str) -> dict[str, Any]:
    if unit == "minutes":
        return _datetime_to_ok(now + timedelta(minutes=amount))
    if unit == "hours":
        return _datetime_to_ok(now + timedelta(hours=amount))
    if unit == "days":
        return _datetime_to_ok(now + timedelta(days=amount))
    if unit == "weeks":
        return _datetime_to_ok(now + timedelta(weeks=amount))
    if unit == "months":
        # 月增加按"日期同位 + 月末截断"算
        amount_int = int(amount)
        target_month_idx = now.month - 1 + amount_int
        target_y = now.year + target_month_idx // 12
        target_m = target_month_idx % 12 + 1
        last_day = _last_day_of_month(target_y, target_m)
        target_d = min(now.day, last_day)
        return _make_iso(
            target_y, target_m, target_d, (now.hour, now.minute, now.second)
        )
    return _err(
        "invalid_unit",
        f"expected minutes|hours|days|weeks|months, got {unit}",
    )


def _datetime_to_ok(dt: datetime) -> dict[str, Any]:
    return {"ok": True, "iso": _format_iso(dt)}


def compute_anchor(now_iso: str, anchor: dict[str, Any]) -> dict[str, Any]:
    """主入口：按 ``anchor.kind`` 分发计算。"""
    now = _parse_now(now_iso)
    if now is None:
        return _err("invalid_now_iso")
    if not isinstance(anchor, dict) or "kind" not in anchor:
        return _err("invalid_anchor", "anchor 必须含 kind 字段")
    kind = anchor.get("kind")

    if kind == "end_of_day":
        return _make_iso(now.year, now.month, now.day, _END_OF_DAY)

    if kind == "end_of_week":
        days_to_sunday = 7 - _day_mon1(now)
        target = now + timedelta(days=days_to_sunday)
        return _make_iso(target.year, target.month, target.day, _END_OF_DAY)

    if kind == "end_of_month":
        last_day = _last_day_of_month(now.year, now.month)
        return _make_iso(now.year, now.month, last_day, _END_OF_DAY)

    if kind == "today_at":
        t = _parse_time(anchor.get("time", ""))
        if t is None:
            return _err(
                "invalid_time", f"expected HH:MM:SS, got {anchor.get('time')!r}"
            )
        return _make_iso(now.year, now.month, now.day, t)

    if kind == "tomorrow_at":
        t = _parse_time(anchor.get("time", ""))
        if t is None:
            return _err(
                "invalid_time", f"expected HH:MM:SS, got {anchor.get('time')!r}"
            )
        tomorrow = now + timedelta(days=1)
        return _make_iso(tomorrow.year, tomorrow.month, tomorrow.day, t)

    if kind == "next_weekday":
        weekday = anchor.get("weekday")
        target_mon1 = _WEEKDAY_TO_MON1.get(weekday)
        if target_mon1 is None:
            return _err(
                "invalid_weekday",
                f"expected monday..sunday, got {weekday!r}",
            )
        diff = target_mon1 - _day_mon1(now)
        if diff <= 0:
            diff += 7
        target = now + timedelta(days=diff)
        time_str = anchor.get("time")
        t = _parse_time(time_str) if time_str else _END_OF_DAY
        if t is None:
            return _err("invalid_time", f"expected HH:MM:SS, got {time_str!r}")
        return _make_iso(target.year, target.month, target.day, t)

    if kind == "add":
        amount = anchor.get("amount")
        unit = anchor.get("unit")
        if not isinstance(amount, (int, float)):
            return _err(
                "invalid_amount", f"expected finite number, got {amount!r}"
            )
        return _compute_add(now, amount, unit)

    if kind == "date":
        md = _parse_month_day(anchor.get("month_day", ""))
        if md is None:
            return _err(
                "invalid_month_day",
                f"expected MM-DD, got {anchor.get('month_day')!r}",
            )
        m, d = md
        this_year_max = _last_day_of_month(now.year, m)
        day_this_year = min(d, this_year_max)
        is_future_this_year = m > now.month or (
            m == now.month and day_this_year >= now.day
        )
        year = now.year if is_future_this_year else now.year + 1
        final_day = d if d <= _last_day_of_month(year, m) else _last_day_of_month(year, m)
        time_str = anchor.get("time")
        t = _parse_time(time_str) if time_str else _END_OF_DAY
        if t is None:
            return _err("invalid_time", f"expected HH:MM:SS, got {time_str!r}")
        return _make_iso(year, m, final_day, t)

    if kind == "date_full":
        ymd = _parse_date(anchor.get("date", ""))
        if ymd is None:
            return _err(
                "invalid_date",
                f"expected YYYY-MM-DD, got {anchor.get('date')!r}",
            )
        y, m, d = ymd
        time_str = anchor.get("time")
        t = _parse_time(time_str) if time_str else _END_OF_DAY
        if t is None:
            return _err("invalid_time", f"expected HH:MM:SS, got {time_str!r}")
        return _make_iso(y, m, d, t)

    return _err("invalid_anchor", f"unknown kind: {kind!r}")


# ── Click 命令 ───────────────────────────────────────────────────────────────


@click.command("time-compute")
@click.option(
    "--now",
    required=True,
    help="当前时间 ISO8601（含或不含时区；不含按 Asia/Shanghai）",
)
@click.option("--anchor", required=True, help="anchor JSON")
@click.option("--pretty", is_flag=True)
def time_compute_cmd(now, anchor, pretty):
    """时间锚点纯算。本地执行，不调 backend。"""
    try:
        anchor_obj = json.loads(anchor)
    except json.JSONDecodeError as e:
        print(
            json.dumps(
                {"ok": False, "error": "invalid_anchor", "detail": e.msg},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        sys.exit(1)
    result = compute_anchor(now, anchor_obj)
    out = json.dumps(
        result, ensure_ascii=False, indent=2 if pretty else None
    )
    print(out)
    if not result.get("ok"):
        sys.exit(1)
