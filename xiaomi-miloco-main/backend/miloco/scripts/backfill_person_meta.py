# Copyright (C) 2025 Xiaomi Corporation
# This software may be used and distributed according to the terms of the Xiaomi Miloco License Agreement.

"""手动把 SQL person(name/role) 回填到文件层 persons/<id>/meta.json。

平时由 ``build_identity_library`` 在启动时自动跑一次；本脚本用于手动触发 / 排查
（例如想看回填了几条、有没有孤儿目录）。

用法：
    cd backend/miloco && python scripts/backfill_person_meta.py
"""

import sys
from pathlib import Path

# 让脚本能 import miloco（src 布局）
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def main() -> None:
    from miloco.perception.engine.identity.config_loader import resolve_library_root
    from miloco.perception.engine.identity.library import IdentityLibrary
    from miloco.perception.engine.identity.meta_sync import sync_person_meta_from_sql

    # 直接构造裸 library（不走 build_identity_library，避免它内部已自动同步导致本次统计恒为 0）
    lib = IdentityLibrary(resolve_library_root())
    stats = sync_person_meta_from_sql(lib)
    print(f"backfill_person_meta done: {stats}")


if __name__ == "__main__":
    main()
