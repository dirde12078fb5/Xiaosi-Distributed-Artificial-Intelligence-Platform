"""Tests for Edge Layer — Tracking Service (mock + convert + real)."""

from miloco.perception.engine.identity.tracking_service import (
    MockTrackingService,
    convert_response,
    create_mock_response_with_movement,
)
from miloco.perception.engine.types import ObjectType


class TestMockTrackingService:
    def test_returns_default_response(self):
        service = MockTrackingService()
        resp = service.analyze([])
        assert resp.frame_info.fps == 2
        assert len(resp.object_info) == 1
        assert resp.object_info[0].type == ObjectType.HUMAN_WITH_FACE
        assert resp.object_info[0].face_id == "wangshihao"

    def test_returns_custom_response(self):
        custom = create_mock_response_with_movement()
        service = MockTrackingService(custom)
        resp = service.analyze([])
        assert len(resp.object_info[0].box_info) == 6
        first_x = resp.object_info[0].box_info[0].boxes["human_body"][0]
        last_x = resp.object_info[0].box_info[5].boxes["human_body"][0]
        assert last_x - first_x == 250


class TestConvertResponse:
    """Test convert_response: raw API dict → TrackingResponse dataclass."""

    def test_human_with_face(self):
        raw = {
            "frames_info": {"start_timestamp": 1000, "end_timestamp": 4000, "fps": 2},
            "objects_info": [
                {
                    "type": "human_with_face",
                    "face_id": "new_face_1",
                    "track_id": 0,
                    "box_info": [
                        [
                            0,
                            {
                                "human_body": [100, 200, 300, 400],
                                "human_face": [120, 210, 80, 80],
                            },
                        ],
                        [
                            1,
                            {
                                "human_body": [105, 205, 300, 400],
                                "human_face": [125, 215, 80, 80],
                            },
                        ],
                    ],
                }
            ],
        }
        resp = convert_response(raw)

        assert resp.frame_info.fps == 2
        assert resp.frame_info.start_timestamp == 1000
        assert len(resp.object_info) == 1

        obj = resp.object_info[0]
        assert obj.type == ObjectType.HUMAN_WITH_FACE
        assert obj.face_id == "new_face_1"
        assert obj.track_id == 0
        assert len(obj.box_info) == 2
        assert obj.box_info[0].frame_index == 0
        assert obj.box_info[0].boxes["human_body"] == (100, 200, 300, 400)
        assert obj.box_info[0].boxes["human_face"] == (120, 210, 80, 80)

    def test_human_body_only(self):
        raw = {
            "frames_info": {"start_timestamp": 0, "end_timestamp": 3000, "fps": 2},
            "objects_info": [
                {
                    "type": "human_body",
                    "face_id": "none",
                    "track_id": 1,
                    "box_info": [[0, {"human_body": [50, 60, 200, 350]}]],
                }
            ],
        }
        resp = convert_response(raw)
        obj = resp.object_info[0]
        assert obj.type == ObjectType.HUMAN_BODY
        assert obj.face_id == "none"

    def test_pet(self):
        raw = {
            "frames_info": {"start_timestamp": 0, "end_timestamp": 3000, "fps": 2},
            "objects_info": [
                {
                    "type": "pet",
                    "face_id": "none",
                    "track_id": 2,
                    "box_info": [
                        [0, {"pet_body": [300, 400, 100, 80]}],
                        [2, {"pet_body": [320, 400, 100, 80]}],
                    ],
                }
            ],
        }
        resp = convert_response(raw)
        obj = resp.object_info[0]
        assert obj.type == ObjectType.PET
        assert len(obj.box_info) == 2
        assert obj.box_info[0].frame_index == 0
        assert obj.box_info[1].frame_index == 2

    def test_human_face_only(self):
        raw = {
            "frames_info": {"start_timestamp": 0, "end_timestamp": 3000, "fps": 2},
            "objects_info": [
                {
                    "type": "human_face",
                    "face_id": "new_face_2",
                    "track_id": 3,
                    "box_info": [[1, {"human_face": [200, 100, 60, 60]}]],
                }
            ],
        }
        resp = convert_response(raw)
        obj = resp.object_info[0]
        assert obj.type == ObjectType.HUMAN_FACE
        assert obj.face_id == "new_face_2"
        assert obj.box_info[0].boxes["human_face"] == (200, 100, 60, 60)

    def test_multiple_objects(self):
        raw = {
            "frames_info": {"start_timestamp": 0, "end_timestamp": 3000, "fps": 2},
            "objects_info": [
                {
                    "type": "human_with_face",
                    "face_id": "new_face_1",
                    "track_id": 0,
                    "box_info": [[0, {"human_body": [100, 200, 300, 400]}]],
                },
                {
                    "type": "pet",
                    "face_id": "none",
                    "track_id": 1,
                    "box_info": [[0, {"pet_body": [500, 300, 80, 60]}]],
                },
            ],
        }
        resp = convert_response(raw)
        assert len(resp.object_info) == 2
        assert resp.object_info[0].type == ObjectType.HUMAN_WITH_FACE
        assert resp.object_info[1].type == ObjectType.PET

    def test_empty_objects(self):
        raw = {
            "frames_info": {"start_timestamp": 0, "end_timestamp": 3000, "fps": 2},
            "objects_info": [],
        }
        resp = convert_response(raw)
        assert len(resp.object_info) == 0
        assert resp.frame_info.fps == 2
