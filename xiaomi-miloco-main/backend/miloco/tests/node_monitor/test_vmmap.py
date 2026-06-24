"""vmmap.py 单测 —— mock libc.proc_pidinfo / _iter_regions，不依赖 macOS。"""

from __future__ import annotations

import ctypes
import struct
from unittest.mock import MagicMock

import pytest
from miloco.node_monitor import vmmap
from miloco.node_monitor.mem_snapshot import TOP_N, MemSnapshot
from miloco.node_monitor.vmmap import (
    _BUF_SIZE,
    _O_ADDR,
    _O_PAGES_RES,
    _O_PATH,
    _O_SIZE,
    _O_TAG,
    _PAGE_SIZE_KB,
    _aggregate,
    _classify,
    _iter_regions,
    parse_vmmap,
)


def _make_region_bytes(
    tag: int = 0,
    pages_res: int = 0,
    addr: int = 0,
    size: int = 4096,
    path: str = "",
) -> bytes:
    """构造一段伪 proc_regionwithpathinfo 字节，验证 struct.unpack_from 偏移。"""
    b = bytearray(_BUF_SIZE)
    struct.pack_into("<I", b, _O_TAG, tag)
    struct.pack_into("<I", b, _O_PAGES_RES, pages_res)
    struct.pack_into("<Q", b, _O_ADDR, addr)
    struct.pack_into("<Q", b, _O_SIZE, size)
    if path:
        path_bytes = path.encode("utf-8")
        b[_O_PATH : _O_PATH + len(path_bytes)] = path_bytes
    return bytes(b)


def _fake_proc_pidinfo(items: list):
    """模拟 proc_pidinfo：依次喂入预制 bytes（写入 buf 并返回长度）或整数返回值。"""
    idx = [0]

    def fake(_pid, _flavor, _addr, buf, _bufsize):
        if idx[0] >= len(items):
            return 0
        item = items[idx[0]]
        idx[0] += 1
        if isinstance(item, int):
            return item
        ctypes.memmove(buf, item, len(item))
        return len(item)

    return fake


class TestClassify:
    def test_file_backed_returns_basename(self):
        assert _classify(0, "/usr/lib/libfoo.dylib") == "libfoo.dylib"
        assert (
            _classify(99, "/System/Library/Frameworks/Foundation.framework/Foundation")
            == "Foundation"
        )

    def test_stack_tag(self):
        assert _classify(30, "") == "[stack]"

    def test_malloc_tags(self):
        for tag in (1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13):
            assert _classify(tag, "") == "[heap]"

    def test_other_anon(self):
        for tag in (0, 10, 14, 20, 31, 100):
            assert _classify(tag, "") == "[anon]"

    def test_path_wins_over_tag(self):
        # 即便 tag=STACK，有 backing 文件仍按 basename
        assert _classify(30, "/x/libfoo.dylib") == "libfoo.dylib"


class TestAggregate:
    def test_empty_regions(self):
        snap = _aggregate(iter([]))
        assert isinstance(snap, MemSnapshot)
        assert snap.total_rss_kb == 0
        assert snap.categories == []
        assert snap.other_rss_kb == 0
        assert snap.other_count == 0

    def test_basic_aggregation(self):
        regs = [
            (1, 100, 0x1000, 0x1000, ""),
            (30, 50, 0x10000, 0x1000, ""),
            (0, 20, 0x20000, 0x1000, "/x/libfoo.dylib"),
        ]
        snap = _aggregate(iter(regs))
        names = {c.name for c in snap.categories}
        assert names == {"[heap]", "[stack]", "libfoo.dylib"}
        heap = next(c for c in snap.categories if c.name == "[heap]")
        assert heap.rss_kb == 100 * _PAGE_SIZE_KB
        assert heap.count == 1

    def test_sorted_desc_by_rss(self):
        regs = [
            (1, 10, 0, 0x1000, ""),
            (30, 200, 0, 0x1000, ""),
            (0, 50, 0, 0x1000, "/x/foo.dylib"),
        ]
        snap = _aggregate(iter(regs))
        for a, b in zip(snap.categories, snap.categories[1:]):
            assert a.rss_kb >= b.rss_kb
        assert snap.categories[0].name == "[stack]"

    def test_sum_invariant(self):
        regs = [
            (1, 10, 0, 0x1000, ""),
            (30, 20, 0, 0x1000, ""),
            (0, 30, 0, 0x1000, "/x/foo.dylib"),
            (0, 5, 0, 0x1000, "/x/bar.dylib"),
        ]
        snap = _aggregate(iter(regs))
        cat_sum = sum(c.rss_kb for c in snap.categories)
        assert cat_sum + snap.other_rss_kb == snap.total_rss_kb

    def test_top_n_truncation(self):
        regs = [(0, 100 - i, 0, 0x1000, f"/x/lib{i}.dylib") for i in range(TOP_N + 5)]
        snap = _aggregate(iter(regs))
        assert len(snap.categories) == TOP_N
        assert snap.other_count == 5
        assert snap.other_rss_kb > 0

    def test_same_category_merged_across_tags(self):
        # 不同 malloc 子分类都归 [heap]，count 应累加
        regs = [
            (1, 10, 0, 0x1000, ""),
            (2, 20, 0, 0x1000, ""),
            (3, 30, 0, 0x1000, ""),
        ]
        snap = _aggregate(iter(regs))
        heap = next(c for c in snap.categories if c.name == "[heap]")
        assert heap.count == 3
        assert heap.rss_kb == 60 * _PAGE_SIZE_KB


class TestIterRegions:
    """验证字节偏移、迭代终止、错误传播。"""

    def test_iterates_until_zero_return(self, monkeypatch):
        r1 = _make_region_bytes(tag=1, pages_res=10, addr=0x1000, size=0x1000)
        r2 = _make_region_bytes(tag=30, pages_res=5, addr=0x2000, size=0x1000)
        fake_libc = MagicMock()
        fake_libc.proc_pidinfo = _fake_proc_pidinfo([r1, r2, 0])
        monkeypatch.setattr(vmmap, "_libc", fake_libc)
        results = list(_iter_regions(pid=12345))
        assert results == [
            (1, 10, 0x1000, 0x1000, ""),
            (30, 5, 0x2000, 0x1000, ""),
        ]

    def test_path_extraction(self, monkeypatch):
        r1 = _make_region_bytes(
            tag=0,
            pages_res=20,
            addr=0x1000,
            size=0x1000,
            path="/usr/lib/libsystem_kernel.dylib",
        )
        fake_libc = MagicMock()
        fake_libc.proc_pidinfo = _fake_proc_pidinfo([r1, 0])
        monkeypatch.setattr(vmmap, "_libc", fake_libc)
        results = list(_iter_regions(pid=1))
        assert results[0][4] == "/usr/lib/libsystem_kernel.dylib"

    def test_negative_return_raises_oserror(self, monkeypatch):
        fake_libc = MagicMock()
        fake_libc.proc_pidinfo = _fake_proc_pidinfo([-1])
        monkeypatch.setattr(vmmap, "_libc", fake_libc)
        with pytest.raises(OSError):
            list(_iter_regions(pid=1))

    def test_zero_size_region_breaks_loop(self, monkeypatch):
        # size=0 时 next_addr == address，触发防御性 break
        r1 = _make_region_bytes(tag=1, pages_res=10, addr=0, size=0)
        fake_libc = MagicMock()
        fake_libc.proc_pidinfo = _fake_proc_pidinfo([r1])
        monkeypatch.setattr(vmmap, "_libc", fake_libc)
        results = list(_iter_regions(pid=1))
        assert len(results) == 1


class TestParseVmmap:
    def test_end_to_end_with_mocked_iter(self, monkeypatch):
        fake_regions = [
            (1, 100, 0x1000, 0x1000, ""),
            (30, 50, 0x10000, 0x1000, ""),
            (0, 20, 0x20000, 0x1000, "/usr/lib/libfoo.dylib"),
        ]
        monkeypatch.setattr(
            vmmap, "_iter_regions", lambda _pid: iter(fake_regions)
        )
        snap = parse_vmmap()
        assert isinstance(snap, MemSnapshot)
        assert snap.total_rss_kb == (100 + 50 + 20) * _PAGE_SIZE_KB
        names = {c.name for c in snap.categories}
        assert names == {"[heap]", "[stack]", "libfoo.dylib"}
