"""Tests for Data Input Layer — Video Splitter."""

import numpy as np
from miloco.perception.engine.input.video_splitter import create_input_slice


class TestCreateInputSlice:
    def test_creates_slice_from_buffers(self):
        frames = [np.zeros((100, 100, 3), dtype=np.uint8) for _ in range(6)]
        audio = np.zeros(16000, dtype=np.int16)

        s = create_input_slice("study-room", frames, audio)

        assert s.room_name == "study-room"
        assert len(s.frames) == 6
        assert len(s.audio_clip) == 16000
        assert s.end_timestamp > s.start_timestamp
        assert s.end_timestamp - s.start_timestamp == 3000

    def test_uses_provided_timestamps(self):
        frames = [np.zeros((10, 10, 3), dtype=np.uint8)]
        audio = np.zeros(100, dtype=np.int16)

        s = create_input_slice("room", frames, audio, start_timestamp=1000, end_timestamp=4000)

        assert s.start_timestamp == 1000
        assert s.end_timestamp == 4000
