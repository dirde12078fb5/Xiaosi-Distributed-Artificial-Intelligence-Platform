from __future__ import annotations

from dataclasses import dataclass
from typing import Final

TOP_N: Final[int] = 10


@dataclass(frozen=True)
class CategoryStats:
    name: str
    rss_kb: int
    count: int


@dataclass(frozen=True)
class MemSnapshot:
    ts: float
    total_rss_kb: int
    categories: list[CategoryStats]
    other_rss_kb: int
    other_count: int
