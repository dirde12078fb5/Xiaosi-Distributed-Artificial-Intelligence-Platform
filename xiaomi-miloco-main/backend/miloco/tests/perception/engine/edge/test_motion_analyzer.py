"""Tests for Edge Layer — Motion Analyzer."""

from miloco.perception.engine.config import IdentityConfig
from miloco.perception.engine.identity.motion_analyzer import analyze_motion
from miloco.perception.engine.identity.tracking_service import (
    create_default_mock_response,
    create_mock_response_with_movement,
)
from miloco.perception.engine.types import MotionState, ObjectType


class TestAnalyzeMotion:
    config = IdentityConfig()

    def test_static_object(self):
        resp = create_default_mock_response()
        targets, scene = analyze_motion(resp.object_info, self.config)
        assert len(targets) == 1
        assert scene == MotionState.STATIC

    def test_dynamic_object(self):
        resp = create_mock_response_with_movement()
        targets, scene = analyze_motion(resp.object_info, self.config)
        assert len(targets) == 1
        assert scene == MotionState.DYNAMIC

    def test_human_without_face_needs_verify(self):
        resp = create_default_mock_response()
        resp.object_info[0].type = ObjectType.HUMAN
        targets, _ = analyze_motion(resp.object_info, self.config)
        assert targets[0].needs_omni_verify is True

    def test_new_face_needs_verify(self):
        resp = create_default_mock_response()
        resp.object_info[0].face_id = "new_face_1"
        targets, _ = analyze_motion(resp.object_info, self.config)
        assert targets[0].needs_omni_verify is True

    def test_registered_face_no_verify(self):
        resp = create_default_mock_response()
        targets, _ = analyze_motion(resp.object_info, self.config)
        assert targets[0].needs_omni_verify is False

    def test_scene_dynamic_if_any_target_dynamic(self):
        resp = create_default_mock_response()
        moving = create_mock_response_with_movement()
        resp.object_info.append(moving.object_info[0])
        _, scene = analyze_motion(resp.object_info, self.config)
        assert scene == MotionState.DYNAMIC
