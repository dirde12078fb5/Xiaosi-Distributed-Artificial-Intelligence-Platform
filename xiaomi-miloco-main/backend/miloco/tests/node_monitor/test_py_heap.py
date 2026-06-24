from miloco.node_monitor.py_heap import (
    PY_HEAP_TOP_N,
    PyHeapSnapshot,
    sample_py_heap,
)


class TestSamplePyHeap:
    def test_returns_valid_snapshot(self):
        snap = sample_py_heap()
        assert isinstance(snap, PyHeapSnapshot)
        assert snap.total_objects > 0
        assert snap.total_size_kb >= 0

    def test_types_sorted_by_size_desc(self):
        snap = sample_py_heap()
        for a, b in zip(snap.types, snap.types[1:]):
            assert a.size_kb >= b.size_kb

    def test_top_n_length_bounded(self):
        snap = sample_py_heap()
        assert len(snap.types) <= PY_HEAP_TOP_N

    def test_sum_invariant_within_rounding(self):
        """sum(types.size_kb) + other_size_kb ≈ total_size_kb，
        允许 ≤ N+1 KB 的整除余数。"""
        snap = sample_py_heap()
        cat_sum = sum(t.size_kb for t in snap.types) + snap.other_size_kb
        diff = abs(cat_sum - snap.total_size_kb)
        assert diff <= len(snap.types) + 1

    def test_count_invariant(self):
        snap = sample_py_heap()
        cat_count = sum(t.count for t in snap.types) + snap.other_count
        assert cat_count == snap.total_objects

    def test_qualname_format_for_business_type(self):
        class _MarkerClass:
            pass

        instances = [_MarkerClass() for _ in range(50)]
        snap = sample_py_heap()
        # sample 调用应正常完成；不强求 50 个 instance 进 top-20
        assert len(instances) == 50
        # 任何 types 项的 qualname 都应符合 `module.name` 格式
        for t in snap.types:
            assert "." in t.qualname or t.qualname.startswith("None.")

    def test_qualname_format_for_stdlib(self):
        snap = sample_py_heap()
        dict_entry = next(
            (t for t in snap.types if t.qualname == "builtins.dict"), None
        )
        if dict_entry is not None:
            assert dict_entry.count > 0
