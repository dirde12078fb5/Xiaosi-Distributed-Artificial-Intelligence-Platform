"""Tests for Edge Layer — Orchestrator."""

import numpy as np
import pytest
from miloco.perception.engine.config import IdentityConfig
from miloco.perception.engine.identity.identity import run_identity
from miloco.perception.engine.identity.tracking_service import (
    MockTrackingService,
    create_default_mock_response,
    create_mock_response_with_movement,
)
from miloco.perception.engine.types import (
    AudioType,
    GatePacket,
    GateTrigger,
    MotionState,
)


def _make_gate_packet() -> GatePacket:
    frame = np.zeros((600, 800, 3), dtype=np.uint8)
    return GatePacket(
        packet_id="test-gate-1",
        room_name="study-room",
        timestamp=1000.0,
        trigger=GateTrigger(
            visual_changed=True,
            visual_change_score=0.5,
            audio_active=False,
            audio_energy_level=0.0,
        ),
        frames=[frame] * 6,
        audio_clip=np.zeros(16000, dtype=np.int16),
    )


class TestEdgeOrchestrator:
    config = IdentityConfig()

    @pytest.mark.asyncio
    async def test_static_scene(self):
        gp = _make_gate_packet()
        service = MockTrackingService(create_default_mock_response())
        result = await run_identity(gp, self.config, service)

        assert result.room_name == "study-room"
        assert result.scene_motion == MotionState.STATIC
        assert len(result.targets) == 1
        # no identity_engine → person_id defaults to "none"
        assert result.targets[0].person_id == "none"
        assert result.audio_analysis.type == AudioType.SILENCE

    @pytest.mark.asyncio
    async def test_dynamic_scene(self):
        gp = _make_gate_packet()
        service = MockTrackingService(create_mock_response_with_movement())
        result = await run_identity(gp, self.config, service)

        # motion_analyzer 已停用，scene_motion 固定为 STATIC
        assert result.scene_motion == MotionState.STATIC
        assert len(result.targets) == 1
