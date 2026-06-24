import gzip
import json
from datetime import datetime

from miloco.observability import omni_log as ol


def test_redact_multimodal_replaces_image_audio_blocks():
    messages = [
        {"role": "system", "content": "system text"},
        {"role": "user", "content": [
            {"type": "input_image", "image": {"data": "BASE64..."}},
            {"type": "input_audio", "audio": {"data": "BASE64..."}},
            {"type": "text", "text": "hello"},
        ]},
    ]
    redacted = ol.redact_multimodal(messages)
    # 不改原消息
    assert messages[1]["content"][0]["image"]["data"] == "BASE64..."
    # 多模态块替换
    assert redacted[1]["content"][0] == {"type": "input_image", "_redacted": True}
    assert redacted[1]["content"][1] == {"type": "input_audio", "_redacted": True}
    # 文本块保留
    assert redacted[1]["content"][2] == {"type": "text", "text": "hello"}
    # system 不变
    assert redacted[0]["content"] == "system text"


def test_redact_multimodal_strips_video_url_and_image_url():
    """omni 实际写 type=video_url / image_url(数据是 base64 url),必须脱敏。"""
    messages = [
        {"role": "user", "content": [
            {"type": "text", "text": "已识别人物:无"},
            {"type": "video_url", "video_url": {
                "url": "data:video/mp4;base64,AAAAIGZ0eXBpc29t..."
            }, "fps": 3},
            {"type": "image_url", "image_url": {
                "url": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
            }},
        ]},
    ]
    redacted = ol.redact_multimodal(messages)
    assert redacted[0]["content"][0] == {"type": "text", "text": "已识别人物:无"}
    assert redacted[0]["content"][1] == {"type": "video_url", "_redacted": True}
    assert redacted[0]["content"][2] == {"type": "image_url", "_redacted": True}
    # 不改原消息
    assert "base64,AAAAIGZ" in messages[0]["content"][1]["video_url"]["url"]


def test_redact_multimodal_strips_unknown_future_types():
    """白名单反转设计:未来 omni 新加 multimodal type 自动被脱敏,不会漏。"""
    messages = [
        {"role": "user", "content": [
            {"type": "text", "text": "ok"},
            {"type": "file", "file_data": "BIG_BASE64..."},
            {"type": "some_new_modal_2027", "payload": "X"},
        ]},
    ]
    redacted = ol.redact_multimodal(messages)
    assert redacted[0]["content"][1] == {"type": "file", "_redacted": True}
    assert redacted[0]["content"][2] == {"type": "some_new_modal_2027", "_redacted": True}


def test_publish_omni_log_disabled_when_debug_off(tmp_path, monkeypatch):
    monkeypatch.setenv("MILOCO_HOME", str(tmp_path))
    from miloco.observability import debug
    debug._reset_cache_for_tests()
    ol.reset_buffer_for_tests()
    ol.publish_omni_log(
        device_trace_id="dt-1", device_id="did-1", room_name="r1",
        messages=[{"role": "user", "content": "hi"}],
        response="ok", usage={"input_tokens": 10},
        latency_ms=50.0,
    )
    assert ol._buffer_size() == 0


def test_publish_omni_log_appends_when_debug_on(tmp_path, monkeypatch):
    monkeypatch.setenv("MILOCO_HOME", str(tmp_path))
    (tmp_path / ".debug_observability").write_text("")
    from miloco.observability import debug
    debug._reset_cache_for_tests()
    ol.reset_buffer_for_tests()
    ol.publish_omni_log(
        device_trace_id="dt-1", device_id="did-1", room_name="r1",
        messages=[{"role": "user", "content": [
            {"type": "input_image", "image": "X"},
            {"type": "text", "text": "hi"},
        ]}],
        response="ok", usage={"input_tokens": 10, "output_tokens": 5},
        latency_ms=50.0,
    )
    assert ol._buffer_size() == 1


def test_flush_writes_multi_member_gzip(tmp_path, monkeypatch):
    monkeypatch.setenv("MILOCO_HOME", str(tmp_path))
    (tmp_path / ".debug_observability").write_text("")
    from miloco.observability import debug
    debug._reset_cache_for_tests()
    ol.reset_buffer_for_tests()
    for i in range(3):
        ol.publish_omni_log(
            device_trace_id=f"dt-{i}", device_id="did-1", room_name="r1",
            messages=[{"role": "user", "content": [
                {"type": "text", "text": f"hi-{i}"},
            ]}],
            response=f"resp-{i}", usage={},
            latency_ms=50.0,
        )
    ol.flush()
    assert ol._buffer_size() == 0

    log_dir = tmp_path / "trace" / "omni"
    files = list(log_dir.glob("*.jsonl.gz"))
    assert len(files) == 1

    # 再 flush 一批 → multi-member gzip append
    ol.publish_omni_log(
        device_trace_id="dt-4", device_id="did-1", room_name="r1",
        messages=[{"role": "user", "content": [{"type": "text", "text": "x"}]}],
        response="r4", usage={}, latency_ms=10.0,
    )
    ol.flush()

    with gzip.open(files[0], "rt", encoding="utf-8") as f:
        lines = [ln for ln in f if ln.strip()]
    assert len(lines) == 4
    parsed = [json.loads(ln) for ln in lines]
    assert parsed[0]["device_trace_id"] == "dt-0"
    assert parsed[3]["device_trace_id"] == "dt-4"


def test_flush_triggers_on_max_records(tmp_path, monkeypatch):
    monkeypatch.setenv("MILOCO_HOME", str(tmp_path))
    (tmp_path / ".debug_observability").write_text("")
    from miloco.observability import debug
    debug._reset_cache_for_tests()
    ol.reset_buffer_for_tests()

    # 攒到 MAX_RECORDS-1 不触发
    for i in range(ol.MAX_RECORDS - 1):
        ol.publish_omni_log(
            device_trace_id=f"dt-{i}", device_id="d", room_name="r",
            messages=[{"role": "user", "content": "x"}],
            response="ok", usage={}, latency_ms=1.0,
        )
    assert ol._buffer_size() == ol.MAX_RECORDS - 1
    # 第 MAX_RECORDS 条触发 flush,整批一起落盘
    ol.publish_omni_log(
        device_trace_id="dt-extra", device_id="d", room_name="r",
        messages=[{"role": "user", "content": "y"}],
        response="ok", usage={}, latency_ms=1.0,
    )
    assert ol._buffer_size() == 0
    # 文件含 MAX_RECORDS 行
    log_dir = tmp_path / "trace" / "omni"
    files = list(log_dir.glob("*.jsonl.gz"))
    assert len(files) == 1
    with gzip.open(files[0], "rt", encoding="utf-8") as f:
        lines = [ln for ln in f if ln.strip()]
    assert len(lines) == ol.MAX_RECORDS


def test_pick_target_file_rotates_when_base_full(tmp_path, monkeypatch):
    """base 文件超 max_bytes → 选 YYYYMMDD.1.jsonl.gz;再满 → YYYYMMDD.2.jsonl.gz。"""
    monkeypatch.setenv("MILOCO_HOME", str(tmp_path))
    day = datetime.now().strftime("%Y%m%d")
    log_dir = tmp_path / "trace" / "omni"
    log_dir.mkdir(parents=True)

    base = log_dir / f"{day}.jsonl.gz"
    base.write_bytes(b"x" * 200)
    # max_bytes=100 → base 已超,应选 YYYYMMDD.1.jsonl.gz
    picked = ol._pick_target_file(max_bytes=100)
    assert picked.name == f"{day}.1.jsonl.gz"

    # 把 .1 也写满,应选 .2
    picked.write_bytes(b"x" * 200)
    picked2 = ol._pick_target_file(max_bytes=100)
    assert picked2.name == f"{day}.2.jsonl.gz"


def test_pick_target_file_uses_base_when_under_limit(tmp_path, monkeypatch):
    monkeypatch.setenv("MILOCO_HOME", str(tmp_path))
    day = datetime.now().strftime("%Y%m%d")
    log_dir = tmp_path / "trace" / "omni"
    log_dir.mkdir(parents=True)
    base = log_dir / f"{day}.jsonl.gz"
    base.write_bytes(b"x" * 50)
    picked = ol._pick_target_file(max_bytes=100)
    assert picked == base


def test_pick_target_file_disabled_when_max_zero(tmp_path, monkeypatch):
    """max_bytes<=0 → 永远用 base 文件,等同关 rotate。"""
    monkeypatch.setenv("MILOCO_HOME", str(tmp_path))
    day = datetime.now().strftime("%Y%m%d")
    log_dir = tmp_path / "trace" / "omni"
    log_dir.mkdir(parents=True)
    base = log_dir / f"{day}.jsonl.gz"
    base.write_bytes(b"x" * 10_000_000)  # 10MB
    picked = ol._pick_target_file(max_bytes=0)
    assert picked == base
