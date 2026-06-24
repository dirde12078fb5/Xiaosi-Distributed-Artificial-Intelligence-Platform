"""output.py 测试。"""

import json
from datetime import datetime
from pathlib import Path

from miloco_cli.output import dump, print_result


def test_dump_compact():
    data = {"code": 0, "message": "ok"}
    result = dump(data)
    assert result == '{"code": 0, "message": "ok"}'
    assert "\n" not in result


def test_dump_pretty():
    data = {"code": 0, "message": "ok"}
    result = dump(data, pretty=True)
    parsed = json.loads(result)
    assert parsed == data
    assert "\n" in result


def test_dump_chinese():
    data = {"name": "爸爸"}
    result = dump(data)
    assert "爸爸" in result
    assert "\\u" not in result


def test_dump_non_serializable_default_str():
    """不可序列化对象应转为字符串而非抛 TypeError。"""
    data = {"path": Path("/tmp/test"), "ts": datetime(2025, 1, 1)}
    result = dump(data)
    parsed = json.loads(result)
    assert parsed["path"] == "/tmp/test"
    assert "2025" in parsed["ts"]


def test_print_result_stdout(capsys):
    print_result({"code": 0})
    out = capsys.readouterr().out.strip()
    assert json.loads(out) == {"code": 0}


def test_print_result_pretty_stdout(capsys):
    print_result({"code": 0}, pretty=True)
    out = capsys.readouterr().out.strip()
    assert "\n" in out
    assert json.loads(out) == {"code": 0}


