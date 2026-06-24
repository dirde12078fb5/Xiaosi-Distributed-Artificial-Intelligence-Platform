"""Tests for Edge Layer — Cropper."""

import numpy as np
from miloco.perception.engine.config import IdentityConfig
from miloco.perception.engine.identity.cropper import crop_targets
from miloco.perception.engine.types import FrameResolution, TrackingBoxInfo


class TestCropTargets:
    config = IdentityConfig()

    def test_crops_with_padding(self):
        frame = np.zeros((600, 800, 3), dtype=np.uint8)
        targets = [
            {
                "track_id": 1,
                "box_info": [TrackingBoxInfo(frame_index=0, boxes={"human_body": (200, 100, 200, 300)})],
            }
        ]
        crops = crop_targets(frame, 0, targets, FrameResolution.HIGH, self.config)

        assert len(crops) == 1
        assert crops[0].track_id == 1
        assert crops[0].resolution == FrameResolution.HIGH
        # Crop should be larger than bbox due to padding
        assert crops[0].image.shape[1] > 200  # width
        assert crops[0].image.shape[0] > 300  # height

    def test_empty_for_missing_frame(self):
        frame = np.zeros((600, 800, 3), dtype=np.uint8)
        targets = [
            {
                "track_id": 1,
                "box_info": [TrackingBoxInfo(frame_index=5, boxes={"human_body": (200, 100, 200, 300)})],
            }
        ]
        crops = crop_targets(frame, 0, targets, FrameResolution.HIGH, self.config)
        assert len(crops) == 0

    def test_clamps_to_image_bounds(self):
        frame = np.zeros((300, 400, 3), dtype=np.uint8)
        targets = [
            {
                "track_id": 1,
                "box_info": [TrackingBoxInfo(frame_index=0, boxes={"human_body": (350, 250, 100, 100)})],
            }
        ]
        crops = crop_targets(frame, 0, targets, FrameResolution.HIGH, self.config)
        assert len(crops) == 1
        assert crops[0].image.shape[1] <= 400
        assert crops[0].image.shape[0] <= 300
