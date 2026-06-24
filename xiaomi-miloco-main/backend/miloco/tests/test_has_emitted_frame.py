"""``MIoTVideoStreamManager.has_emitted_frame`` 单测。

首帧看门狗(router.py::_first_frame_watchdog)用它判定"该不该判摄像头连不上"——
注册成功(reg_id≥0)但 12s 内一帧没出 → 连不上。这里钉死它的契约:

- 反映的是 ``_camera_seen_keyframe``(回调广播首个 IDR 时填充)的成员资格;
- key 必须是 ``f"{camera_id}.{channel}"``,与 ws.py 全局 camera_tag 拼法一致——
  若有人改了拼法,这条立刻红,挡住"看门狗永远早退/永远误判"的隐性回归。
"""

from __future__ import annotations

from miloco.miot.ws import MIoTVideoStreamManager


def test_false_before_any_frame():
    mgr = MIoTVideoStreamManager()
    assert mgr.has_emitted_frame("cam1", 0) is False


def test_true_after_keyframe_seen():
    mgr = MIoTVideoStreamManager()
    # 回调广播首个 IDR 时即 add 这个 tag(见 __video_stream_callback)
    mgr._camera_seen_keyframe.add("cam1.0")
    assert mgr.has_emitted_frame("cam1", 0) is True


def test_channel_not_conflated():
    """同一 camera_id 不同 channel 互不串——key 含 channel。"""
    mgr = MIoTVideoStreamManager()
    mgr._camera_seen_keyframe.add("cam1.0")
    assert mgr.has_emitted_frame("cam1", 0) is True
    assert mgr.has_emitted_frame("cam1", 1) is False


def test_key_format_matches_camera_tag():
    """key 拼法与 ws.py 各处 ``f"{camera_id}.{channel}"`` 一致——钉死防回归。"""
    mgr = MIoTVideoStreamManager()
    camera_id, channel = "1190512910", 2
    mgr._camera_seen_keyframe.add(f"{camera_id}.{channel}")
    assert mgr.has_emitted_frame(camera_id, channel) is True


def test_false_again_after_teardown_discard():
    """teardown 清掉 tag(全部订阅者退出)后回 False——看门狗生命周期回收依赖这点:
    下次新连接重新起看门狗。``_ensure_sdk_subscription``/``_teardown_if_idle`` 都会
    discard 这个 tag。"""
    mgr = MIoTVideoStreamManager()
    mgr._camera_seen_keyframe.add("cam1.0")
    assert mgr.has_emitted_frame("cam1", 0) is True
    mgr._camera_seen_keyframe.discard("cam1.0")
    assert mgr.has_emitted_frame("cam1", 0) is False
