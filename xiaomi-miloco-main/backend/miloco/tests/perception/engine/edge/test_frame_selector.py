"""Tests for Edge Layer — Frame Selector."""

from miloco.perception.engine.config import IdentityConfig
from miloco.perception.engine.identity.frame_selector import select_frames
from miloco.perception.engine.types import FrameResolution, MotionState, TrackingBoxInfo


class TestSelectFrames:
    config = IdentityConfig()
    box_info = [TrackingBoxInfo(frame_index=i, boxes={"human_body": (100, 200, 300, 400)}) for i in range(6)]
    # frame 4 has largest bbox
    box_info_varied = box_info[:4] + [
        TrackingBoxInfo(frame_index=4, boxes={"human_body": (100, 200, 350, 450)}),
        box_info[5],
    ]

    def test_static_selects_one_frame(self):
        selections = select_frames(6, MotionState.STATIC, [self.box_info_varied], self.config)
        assert len(selections) == 1
        assert selections[0][1] == FrameResolution.HIGH
        assert selections[0][0] == 4  # largest bbox

    def test_dynamic_samples_up_to_three(self):
        selections = select_frames(6, MotionState.DYNAMIC, [self.box_info], self.config)
        assert len(selections) == 3
        assert [idx for idx, _ in selections] == [0, 3, 5]
        for _, res in selections:
            assert res == FrameResolution.MEDIUM

    def test_dynamic_few_detections_sends_all(self):
        few_boxes = [
            TrackingBoxInfo(frame_index=2, boxes={"human_body": (100, 200, 300, 400)}),
            TrackingBoxInfo(frame_index=5, boxes={"human_body": (100, 200, 300, 400)}),
        ]
        selections = select_frames(9, MotionState.DYNAMIC, [few_boxes], self.config)
        assert len(selections) == 2
        assert [idx for idx, _ in selections] == [2, 5]

    def test_no_box_info_picks_frame_zero(self):
        selections = select_frames(6, MotionState.STATIC, [], self.config)
        assert len(selections) == 1
        assert selections[0][0] == 0
