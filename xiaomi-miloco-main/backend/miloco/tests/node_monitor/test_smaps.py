from pathlib import Path

import pytest
from miloco.node_monitor.smaps import TOP_N, _normalize_name, parse_smaps

FIXTURE_DIR = Path(__file__).parent / "fixtures"


class TestNormalizeName:
    def test_empty_name_to_anon(self):
        assert _normalize_name("") == "[anon]"

    def test_bracket_special_preserved(self):
        assert _normalize_name("[heap]") == "[heap]"
        assert _normalize_name("[stack]") == "[stack]"
        assert _normalize_name("[vdso]") == "[vdso]"
        assert _normalize_name("[vvar]") == "[vvar]"

    def test_named_anon_collapsed(self):
        assert _normalize_name("[anon:libc_malloc]") == "[anon]"
        assert _normalize_name("[anon:.bss]") == "[anon]"

    def test_file_path_to_basename(self):
        assert (
            _normalize_name("/usr/lib/x86_64-linux-gnu/libpython3.12.so.1.0")
            == "libpython3.12.so.1.0"
        )
        assert _normalize_name("/home/user/app/libfoo.so") == "libfoo.so"

    def test_deleted_suffix_preserved(self):
        assert _normalize_name("/tmp/libfoo.so (deleted)") == "libfoo.so (deleted)"


class TestParseSmaps:
    def test_parse_basic_totals(self):
        snap = parse_smaps(str(FIXTURE_DIR / "smaps_basic.txt"))
        assert snap.total_rss_kb == 1168

    def test_parse_basic_categories_sorted_desc(self):
        snap = parse_smaps(str(FIXTURE_DIR / "smaps_basic.txt"))
        names = [c.name for c in snap.categories]
        assert names[0] == "[heap]"
        assert names[1] == "libpython3.12.so.1.0"
        for a, b in zip(snap.categories, snap.categories[1:]):
            assert a.rss_kb >= b.rss_kb

    def test_anon_collapsed_with_count(self):
        snap = parse_smaps(str(FIXTURE_DIR / "smaps_basic.txt"))
        anon = next((c for c in snap.categories if c.name == "[anon]"), None)
        assert anon is not None
        assert anon.count == 2
        assert anon.rss_kb == 12

    def test_sum_invariant_rss(self):
        snap = parse_smaps(str(FIXTURE_DIR / "smaps_basic.txt"))
        cat_sum = sum(c.rss_kb for c in snap.categories)
        assert cat_sum + snap.other_rss_kb == snap.total_rss_kb

    def test_file_not_found_raises(self):
        with pytest.raises(OSError):
            parse_smaps("/nonexistent/smaps")

    def test_empty_smaps(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("")
        snap = parse_smaps(str(f))
        assert snap.total_rss_kb == 0
        assert snap.categories == []
        assert snap.other_rss_kb == 0


class TestParseSmapsTruncation:
    def test_top_n_truncation(self, tmp_path):
        lines = []
        for i in range(TOP_N + 5):
            lines.append(
                f"7f{i:010x}-7f{i:010x} r-xp 00000000 fd:01 {i}   /lib/libtest{i}.so\n"
            )
            lines.append("Size:               1000 kB\n")
            lines.append(f"Rss:                 {100 - i} kB\n")
            lines.append("VmFlags: rd ex mr mw me\n")
        f = tmp_path / "many.txt"
        f.write_text("".join(lines))
        snap = parse_smaps(str(f))
        assert len(snap.categories) == TOP_N
        assert snap.other_count == 5
        assert snap.other_rss_kb > 0


def _build_task_dir(tmp_path, tid: int, comm: str, startstack: int):
    """搭一个 /proc/PID/task 形态的临时目录，用于线程栈反查测试。"""
    task_root = tmp_path / "task"
    tdir = task_root / str(tid)
    tdir.mkdir(parents=True)
    (tdir / "comm").write_text(comm + "\n")
    # stat 第 28 字段是 startstack；前面随便填合法占位
    fields_before = (
        f"S 1 1 1 0 -1 4194304 100 0 0 0 0 0 0 0 20 0 1 0 100 8192 100 "
        f"1000000 1000 1000 {startstack} 0 0 0"
    )
    (tdir / "stat").write_text(f"{tid} ({comm}) {fields_before}\n")
    return str(task_root)


class TestParseSmapsDetect:
    def test_neighbor_so_anon_renamed(self):
        """anon 紧贴 .so 后边 → detect:[anon:libfoo.so]"""
        snap = parse_smaps(str(FIXTURE_DIR / "smaps_detect.txt"))
        names = [c.name for c in snap.categories]
        assert "detect:[anon:libfoo.so]" in names

    def test_isolated_anon_remains_anon(self):
        """anon 没邻居/不在栈范围 → [anon]"""
        snap = parse_smaps(str(FIXTURE_DIR / "smaps_detect.txt"))
        anon = next((c for c in snap.categories if c.name == "[anon]"), None)
        assert anon is not None
        # region 3 (1000 kB) + region 4 (16 kB) + region 6 (60 kB,gap 太大不命中) = 1076 kB
        assert anon.rss_kb == 1000 + 16 + 60

    def test_neighbor_gap_too_far_not_detected(self):
        """anon 紧跟 .so 但 gap > 64KB → 不命中"""
        snap = parse_smaps(str(FIXTURE_DIR / "smaps_detect.txt"))
        names = [c.name for c in snap.categories]
        assert "detect:[anon:libbar.so]" not in names

    def test_thread_stack_detected_with_task_dir(self, tmp_path):
        """传 task_dir + startstack 落在 anon region → detect:[anon:线程名]"""
        task_dir = _build_task_dir(
            tmp_path,
            tid=12345,
            comm="resource-monitor",
            startstack=0x7F8000400000,
        )
        snap = parse_smaps(str(FIXTURE_DIR / "smaps_detect.txt"), task_dir=task_dir)
        names = [c.name for c in snap.categories]
        assert "detect:[anon:resource-monitor]" in names

    def test_task_dir_none_disables_stack_detect(self):
        """不传 task_dir → 栈维度不启用,8MB region 仍归 [anon]"""
        snap = parse_smaps(str(FIXTURE_DIR / "smaps_detect.txt"))
        names = [c.name for c in snap.categories]
        assert not any(n.startswith("detect:[anon:resource-monitor") for n in names)
