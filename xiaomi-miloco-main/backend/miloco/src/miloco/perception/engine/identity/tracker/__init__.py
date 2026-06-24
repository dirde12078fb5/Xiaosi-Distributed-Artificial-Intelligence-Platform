#!/usr/bin/env python3
"""tracker 包。

身份识别可走端上 ``HumanReID`` 关联 + 云端 omni 模型双路:
  - v1.2 主动注册改造 (DeepSortTracker) 复用 ``HumanReID`` ReID embedding 给陌生人池去重
  - 轻量主路径 (SortTracker, ``identity/sort.py``) 用 IoU + Kalman, 不需要 ReID

人脸识别已统一走 omni 云模型,本地 face_recog / face_landmark onnx 链路已撤;
仅保留 ``FacePersonMatcher`` 做 face-body bbox 关联 (跟 onnx 无关)。
"""

from miloco.perception.engine.identity.face_person_match import FacePersonMatcher

from .config import TrackerConfig
from .detector import Detector
from .visualizer import Visualizer

__all__ = [
    "TrackerConfig",
    "Detector",
    "FacePersonMatcher",
    "Visualizer",
]
