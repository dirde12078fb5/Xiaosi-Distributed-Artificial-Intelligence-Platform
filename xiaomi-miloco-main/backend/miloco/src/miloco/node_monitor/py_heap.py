from __future__ import annotations

import gc
import logging
import sys
import time
from dataclasses import dataclass
from typing import Final

logger = logging.getLogger(__name__)

PY_HEAP_TOP_N: Final[int] = 10


@dataclass(frozen=True)
class PyTypeStats:
    qualname: str
    count: int
    size_kb: int


@dataclass(frozen=True)
class PyHeapSnapshot:
    ts: float
    total_objects: int
    total_size_kb: int
    types: list[PyTypeStats]
    other_size_kb: int
    other_count: int


def sample_py_heap() -> PyHeapSnapshot:
    """gc.get_objects() + sys.getsizeof 按 module.qualname 聚合，top-N by size。"""
    ts = time.time()
    counts: dict[str, int] = {}
    sizes: dict[str, int] = {}
    total_n = 0
    total_sz = 0

    for obj in gc.get_objects():
        try:
            t = type(obj)
            qualname = f"{t.__module__}.{t.__name__}"
            sz = sys.getsizeof(obj)
        except Exception:
            continue
        counts[qualname] = counts.get(qualname, 0) + 1
        sizes[qualname] = sizes.get(qualname, 0) + sz
        total_n += 1
        total_sz += sz

    sorted_keys = sorted(sizes.keys(), key=lambda k: sizes[k], reverse=True)
    top_keys = sorted_keys[:PY_HEAP_TOP_N]
    other_keys = sorted_keys[PY_HEAP_TOP_N:]

    types = [
        PyTypeStats(qualname=k, count=counts[k], size_kb=sizes[k] // 1024)
        for k in top_keys
    ]
    other_count = sum(counts[k] for k in other_keys)
    other_size_kb = sum(sizes[k] for k in other_keys) // 1024

    return PyHeapSnapshot(
        ts=ts,
        total_objects=total_n,
        total_size_kb=total_sz // 1024,
        types=types,
        other_size_kb=other_size_kb,
        other_count=other_count,
    )
