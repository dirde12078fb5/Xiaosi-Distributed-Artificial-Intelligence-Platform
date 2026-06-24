# Copyright (C) 2025 Xiaomi Corporation
# This software may be used and distributed according to the terms of the Xiaomi Miloco License Agreement.

"""Unit tests for miloco.utils.time_utils."""

import time

import pytest
from miloco.middleware.exceptions import ValidationException
from miloco.utils.time_utils import (
    ms_to_iso_local,
    parse_iso_ms,
    parse_since,
    since_to_ms,
)


class TestParseSince:
    def test_single_hour(self):
        td = parse_since("1h")
        assert td.total_seconds() == 3600

    def test_single_minute(self):
        td = parse_since("30m")
        assert td.total_seconds() == 1800

    def test_single_second(self):
        td = parse_since("90s")
        assert td.total_seconds() == 90

    def test_single_day(self):
        td = parse_since("7d")
        assert td.total_seconds() == 7 * 86400

    def test_combined_hour_minute(self):
        td = parse_since("2h30m")
        assert td.total_seconds() == 2 * 3600 + 30 * 60

    def test_combined_hour_minute_second(self):
        td = parse_since("1h30m20s")
        assert td.total_seconds() == 3600 + 1800 + 20

    def test_bare_number_defaults_to_minutes(self):
        td = parse_since("5")
        assert td.total_seconds() == 300

    def test_empty_raises(self):
        with pytest.raises(ValidationException):
            parse_since("")

    def test_invalid_unit_raises(self):
        with pytest.raises(ValidationException):
            parse_since("10x")

    def test_zero_raises(self):
        with pytest.raises(ValidationException):
            parse_since("0s")


class TestParseIsoMs:
    def test_utc_timestamp(self):
        ms = parse_iso_ms("2026-03-30T12:00:00Z", "test")
        assert ms == 1774872000000

    def test_offset_timestamp(self):
        ms = parse_iso_ms("2026-03-30T20:00:00+08:00", "test")
        assert ms == 1774872000000

    def test_naive_timestamp_treated_as_deploy_timezone(self, monkeypatch):
        """v10 起 naive 字符串按 deploy_timezone() 解读(原行为是按 UTC)。

        deploy_timezone() 默认随系统时区,这里 monkeypatch 锁定 Asia/Shanghai
        让断言独立于 CI 容器 TZ。
        """
        from zoneinfo import ZoneInfo

        from miloco.utils import time_utils

        monkeypatch.setattr(
            time_utils, "deploy_timezone", lambda: ZoneInfo("Asia/Shanghai")
        )
        # 12:00 in Asia/Shanghai == 04:00 UTC == ms 1774843200000
        ms = parse_iso_ms("2026-03-30T12:00:00", "test")
        assert ms == 1774843200000

    def test_invalid_raises(self):
        with pytest.raises(ValidationException, match="test_field"):
            parse_iso_ms("not-a-date", "test_field")


class TestSinceToMs:
    def test_returns_past_timestamp(self):
        before = int(time.time() * 1000)
        result = since_to_ms("1h")
        after = int(time.time() * 1000)
        assert before - 3600 * 1000 <= result <= after - 3600 * 1000 + 100


class TestMsToIsoLocal:
    def test_converts_to_iso(self):
        result = ms_to_iso_local(1774872000000)
        assert "2026-03-30" in result or "2026-03-31" in result
        assert "+" in result or "Z" in result
