"""``_truncate_ws_reason`` 边界单测。

WebSocket 关闭帧是 control frame,整帧 payload ≤125 字节;close code 占 2 字节,
reason 只剩 ≤123 字节(RFC 6455 §5.5)。``websockets`` 库超长直接抛
``ProtocolError: control frame too long``,把"优雅关闭并带原因"这步本身搞崩,
前端反收到无信息的 1006。``_truncate_ws_reason`` 按 UTF-8 字节截到 120(留 3 字节
余量),且不能切碎多字节字符。这里固化三类边界:短串直通、纯 ASCII 超长、含中文
(3 字节/字)在多字节边界附近截断不产生半个字。
"""

from __future__ import annotations

from miloco.miot.router import _truncate_ws_reason

# 协议安全上限:close code 2 字节 + reason ≤123 字节 = control frame payload ≤125。
# 函数截到 120,留 3 字节余量。
_REASON_BYTE_CAP = 123


def test_short_reason_passthrough():
    """≤120 字节(且无非法码位)round-trip 后值不变。

    实现对所有输入统一走 encode(replace)→[:120]→decode(ignore)(为净化孤立代理项,
    见 test_short_lone_surrogate_cleaned),没有"短串短路 return 原串"分支;纯 ASCII /
    合法中文 round-trip 后恒等于原串,所以这里仍是恒等。
    """
    s = "Server error: boom"
    assert _truncate_ws_reason(s) == s


def test_empty_string():
    assert _truncate_ws_reason("") == ""


def test_ascii_exactly_120_bytes_passthrough():
    """刚好 120 字节(ASCII)不截。"""
    s = "a" * 120
    assert _truncate_ws_reason(s) == s


def test_ascii_121_bytes_truncated_to_120():
    """121 字节 ASCII → 截到 120。"""
    s = "a" * 121
    out = _truncate_ws_reason(s)
    assert out == "a" * 120
    assert len(out.encode("utf-8")) == 120


def test_real_ppcs_reason_truncated_within_cap():
    """复现真实触发场景:PPCS 未握手时的中英文 reason 超 123 字节,截断后落回上限内。"""
    inner = (
        "Camera 1190512910 not registered with SDK (likely PPCS not "
        "handshaken). Try `miloco-cli account unbind && account bind`."
    )
    reason = f"Server error: {inner}"
    assert len(reason.encode("utf-8")) > _REASON_BYTE_CAP  # 不截会撑爆 control frame
    out = _truncate_ws_reason(reason)
    assert len(out.encode("utf-8")) <= 120


def test_chinese_no_half_char():
    """全中文(3 字节/字)截断后必须能干净 decode,不留半个字。"""
    s = "服务器错误" * 40  # 200 字 × 3 = 600 字节
    out = _truncate_ws_reason(s)
    encoded = out.encode("utf-8")
    assert len(encoded) <= 120
    # 能往返 decode 即说明没切碎多字节字符(errors 默认 strict 也不抛)
    assert encoded.decode("utf-8") == out
    # 120 / 3 = 40 整除,刚好 40 个完整汉字
    assert out == s[:40]


def test_lone_surrogate_does_not_raise():
    """含孤立代理项的 reason 不能让函数自己崩在 encode 上。

    reason 来自 f"Server error: {str(err)}";OS/文件系统异常的 str 在 PEP 383
    surrogateescape 下可能带孤立代理项(如 '\\udc80')。默认 strict encode 会抛
    UnicodeEncodeError —— 那样这个"为防关闭路径崩溃而生"的函数反而自爆。errors=
    "replace" 兜住,返回可安全交给 websocket.close() 的纯净串。
    """
    s = "Server error: " + "x" * 200 + "\udc80"
    out = _truncate_ws_reason(s)  # 不抛
    encoded = out.encode("utf-8")  # 结果可被 strict encode(无残留代理项)
    assert len(encoded) <= 120
    assert encoded.decode("utf-8") == out


def test_short_lone_surrogate_cleaned():
    """短串但含孤立代理项:即便不超长也要返回 round-trip 后的纯净串,
    不能 return 原串(原串交给 websocket.close 仍会在其内部 encode 崩)。"""
    out = _truncate_ws_reason("ok\udc80")
    # round-trip 后无残留代理项:strict encode→decode 不抛且恒等,即证明已净化。
    # 用显式断言而非裸 out.encode()(后者像死代码,且会被 ruff B018 告警)。
    assert out.encode("utf-8").decode("utf-8") == out


def test_mixed_ascii_chinese_boundary():
    """ASCII 前缀 + 中文,使字节边界落在某个汉字中间,验证不切碎。"""
    # 前缀 119 字节 ASCII,再接一个 3 字节汉字 → 第 120 字节落在汉字第 1 字节,
    # 截到 120 会切碎该汉字,errors="ignore" 应丢掉它。
    s = "a" * 119 + "好"
    out = _truncate_ws_reason(s)
    encoded = out.encode("utf-8")
    assert len(encoded) <= 120
    assert encoded.decode("utf-8") == out  # 无半字
    assert out == "a" * 119  # 被切碎的"好"整字丢弃
