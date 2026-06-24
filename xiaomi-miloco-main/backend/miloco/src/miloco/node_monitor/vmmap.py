"""macOS 进程内存 region 监控。

通过 libc.proc_pidinfo(PROC_PIDREGIONPATHINFO) 迭代当前进程的 VM region，
按 Mach VM tag + backing path 分类，返回与 smaps.parse_smaps 同构的 MemSnapshot。

只支持自监控 pid=os.getpid()。监控外部进程需要 task port + entitlement，
当前场景不需要。
"""

from __future__ import annotations

import ctypes
import ctypes.util
import logging
import os
import struct
import time
from typing import Any, Final, Iterable, Iterator

from miloco.node_monitor.mem_snapshot import TOP_N, CategoryStats, MemSnapshot

logger = logging.getLogger(__name__)

_PROC_PIDREGIONPATHINFO: Final[int] = 8

# proc_regionwithpathinfo 大小 = 96 (proc_regioninfo) + 152 (vnode_info)
# + 1024 (vip_path[MAXPATHLEN]) = 1272 字节。
# 字段偏移按 <sys/proc_info.h>（macOS 10.5+ 稳定 ABI）：
_BUF_SIZE: Final[int] = 1272
_O_TAG: Final[int] = 32  # pri_user_tag (u32)
_O_PAGES_RES: Final[int] = 36  # pri_pages_resident (u32)
_O_ADDR: Final[int] = 80  # pri_address (u64)
_O_SIZE: Final[int] = 88  # pri_size (u64)
_O_PATH: Final[int] = 248  # vip_path 起点 (96 + 152)
_PATH_MAX: Final[int] = 1024

# <mach/vm_statistics.h> 的 VM_MEMORY_* tag
_VM_TAG_STACK: Final[int] = 30
# 各类 malloc 分区都视作 [heap]：1 MALLOC / 2 MALLOC_SMALL / 3 MALLOC_LARGE /
# 4 MALLOC_HUGE / 5 SBRK / 6 REALLOC / 7 MALLOC_TINY /
# 8 MALLOC_LARGE_REUSABLE / 9 MALLOC_LARGE_REUSED / 11 MALLOC_NANO /
# 12 MALLOC_MEDIUM / 13 MALLOC_PGUARD。10 ANALYSIS_TOOL 不属于 malloc。
_VM_MALLOC_TAGS: Final[frozenset[int]] = frozenset(
    {1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13}
)

_PAGE_SIZE_KB: Final[int] = os.sysconf("SC_PAGESIZE") // 1024

_libc: Any = None


def _bind_libc() -> None:
    """惰性绑定 libc.proc_pidinfo。仅在调用 parse_vmmap 时才解析符号，
    保证 Linux 上 import 不报错（便于跑 _aggregate 单元测试）。"""
    global _libc
    if _libc is not None:
        return
    path = ctypes.util.find_library("c")
    if not path:
        raise OSError("libc not found via ctypes.util.find_library")
    lib = ctypes.CDLL(path, use_errno=True)
    lib.proc_pidinfo.argtypes = [
        ctypes.c_int,  # pid
        ctypes.c_int,  # flavor
        ctypes.c_uint64,  # arg (address)
        ctypes.c_void_p,  # buffer
        ctypes.c_int,  # buffersize
    ]
    lib.proc_pidinfo.restype = ctypes.c_int
    _libc = lib


def _classify(tag: int, path: str) -> str:
    """region → 分类 key。规则与 smaps Linux-风对齐：
    file-backed → basename；STACK tag → [stack]；MALLOC 系 tag → [heap]；其他 → [anon]。
    """
    if path:
        return path.rsplit("/", 1)[-1]
    if tag == _VM_TAG_STACK:
        return "[stack]"
    if tag in _VM_MALLOC_TAGS:
        return "[heap]"
    return "[anon]"


def _iter_regions(pid: int) -> Iterator[tuple[int, int, int, int, str]]:
    """yields (tag, pages_resident, address, size, path) per region。

    迭代约定：proc_pidinfo(arg=address) 返回 address 起的下一段；
    推进 address = pri_address + pri_size 直到返回 ≤ 0。
    返回 0 = EOF 正常退出；< 0 抛 OSError。
    """
    _bind_libc()
    buf = (ctypes.c_ubyte * _BUF_SIZE)()
    address = 0
    while True:
        ret = _libc.proc_pidinfo(
            pid,
            _PROC_PIDREGIONPATHINFO,
            address,
            ctypes.cast(buf, ctypes.c_void_p),
            _BUF_SIZE,
        )
        if ret == 0:
            return
        if ret < 0:
            errno = ctypes.get_errno()
            raise OSError(errno, f"proc_pidinfo failed: {os.strerror(errno)}")
        b = bytes(buf)
        tag = struct.unpack_from("<I", b, _O_TAG)[0]
        pages_res = struct.unpack_from("<I", b, _O_PAGES_RES)[0]
        addr = struct.unpack_from("<Q", b, _O_ADDR)[0]
        size = struct.unpack_from("<Q", b, _O_SIZE)[0]
        path_bytes = b[_O_PATH : _O_PATH + _PATH_MAX]
        nul = path_bytes.find(b"\0")
        path = path_bytes[: nul if nul >= 0 else _PATH_MAX].decode(
            "utf-8", errors="replace"
        )
        yield tag, pages_res, addr, size, path
        next_addr = addr + size
        # 防御：address 没前进则止住，避免死循环
        if next_addr <= address:
            return
        address = next_addr


def _aggregate(regions: Iterable[tuple[int, int, int, int, str]]) -> MemSnapshot:
    """region 迭代器 → MemSnapshot。tests 直接构造 region 列表喂入，绕开 libc。"""
    raw_rss: dict[str, int] = {}
    raw_count: dict[str, int] = {}
    for tag, pages_res, _addr, _size, path in regions:
        name = _classify(tag, path)
        raw_rss[name] = raw_rss.get(name, 0) + pages_res * _PAGE_SIZE_KB
        raw_count[name] = raw_count.get(name, 0) + 1

    names_sorted = sorted(raw_rss.keys(), key=lambda n: raw_rss[n], reverse=True)
    top = names_sorted[:TOP_N]
    other = names_sorted[TOP_N:]

    categories = [
        CategoryStats(name=n, rss_kb=raw_rss[n], count=raw_count[n]) for n in top
    ]
    return MemSnapshot(
        ts=time.time(),
        total_rss_kb=sum(raw_rss.values()),
        categories=categories,
        other_rss_kb=sum(raw_rss[n] for n in other),
        other_count=sum(raw_count[n] for n in other),
    )


def parse_vmmap() -> MemSnapshot:
    """采集当前进程内存 region 快照。"""
    return _aggregate(_iter_regions(os.getpid()))
