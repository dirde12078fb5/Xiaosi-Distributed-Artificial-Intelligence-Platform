#!/usr/bin/env python3
"""
Visualization utilities for drawing detection boxes, IDs and class labels.
Supports CJK text rendering via PIL.
"""

import os
from typing import Dict, List, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# CJK font search paths
_CJK_FONT_PATHS = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
]


def _load_cjk_font(size=16):
    for p in _CJK_FONT_PATHS:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


class Visualizer:
    """
    Visualization utility class.
    """

    # Class colors (BGR format)
    COLORS = {
        "human": (0, 180, 0),  # dark green
        "cat": (0, 120, 200),  # dark orange
        "dog": (0, 180, 200),  # dark yellow
        "head": (180, 0, 180),  # dark purple
        "face": (200, 0, 0),  # dark blue
        "unknown": (100, 100, 100),  # dark gray
    }

    def __init__(
        self,
        font_size: int = 16,
        box_thickness: int = 2,
        show_confidence: bool = True,
        # Backward compatibility
        font_scale: float = 0.6,
        font_thickness: int = 2,
    ):
        self.font_size = font_size
        self.box_thickness = box_thickness
        self.show_confidence = show_confidence

        # PIL font (supports CJK)
        self.pil_font = _load_cjk_font(font_size)
        self._measure_draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))

    def get_color(self, class_name: str) -> Tuple[int, int, int]:
        return self.COLORS.get(class_name, self.COLORS["unknown"])

    def _measure_text(self, text: str) -> Tuple[int, int]:
        bbox = self._measure_draw.textbbox((0, 0), text, font=self.pil_font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def _put_text_pil(
        self,
        image: np.ndarray,
        text: str,
        position: Tuple[int, int],
        text_color: Tuple[int, int, int] = (255, 255, 255),
    ) -> np.ndarray:
        pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_img)
        color_rgb = (text_color[2], text_color[1], text_color[0])
        draw.text(position, text, font=self.pil_font, fill=color_rgb)
        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    def draw_detection(
        self,
        image: np.ndarray,
        bbox: Tuple[int, int, int, int],
        class_name: str,
        confidence: float = None,
        track_id: int = None,
        color: Tuple[int, int, int] = None,
    ) -> np.ndarray:
        x1, y1, x2, y2 = bbox
        if color is None:
            color = self.get_color(class_name)

        cv2.rectangle(image, (x1, y1), (x2, y2), color, self.box_thickness)

        label_parts = []
        if track_id is not None:
            label_parts.append(f"ID:{track_id}")
        label_parts.append(class_name)
        if self.show_confidence and confidence is not None:
            label_parts.append(f"{confidence:.2f}")

        label = " ".join(label_parts)

        padding = 4
        tw, th = self._measure_text(label)

        bg_y1 = max(0, y1 - th - 2 * padding)
        bg_x2 = x1 + tw + 2 * padding
        cv2.rectangle(image, (x1, bg_y1), (bg_x2, y1), color, -1)

        image = self._put_text_pil(
            image, label, (x1 + padding, bg_y1 + padding), text_color=(255, 255, 255)
        )

        return image

    def draw_detections(self, image: np.ndarray, detections: List[Dict]) -> np.ndarray:
        for det in detections:
            if "xyxy" in det:
                bbox = det["xyxy"]
            elif "bbox" in det:
                bbox_val = det["bbox"]
                if len(bbox_val) == 4:
                    x, y, w, h = bbox_val
                    if w > 0 and h > 0 and x + w > x and y + h > y:
                        bbox = (int(x), int(y), int(x + w), int(y + h))
                    else:
                        bbox = tuple(bbox_val)
                else:
                    bbox = tuple(bbox_val)
            else:
                continue

            image = self.draw_detection(
                image=image,
                bbox=bbox,
                class_name=det.get("class", "unknown"),
                confidence=det.get("confidence"),
                track_id=det.get("id"),
            )

        return image

    def draw_tracking_results(
        self, image: np.ndarray, tracks: List[Dict]
    ) -> np.ndarray:
        return self.draw_detections(image, tracks)

    def draw_face_body_matches(
        self,
        image: np.ndarray,
        face_detections: List,
        body_detections: List,
        matches: List,
    ) -> np.ndarray:
        for i, face in enumerate(face_detections):
            image = self.draw_detection(image, face.xyxy, "face", face.confidence)

        for i, body in enumerate(body_detections):
            image = self.draw_detection(image, body.xyxy, "human", body.confidence)

        for match in matches:
            face_bbox = match.face_bbox
            body_bbox = match.body_bbox

            face_center = (
                (face_bbox[0] + face_bbox[2]) // 2,
                (face_bbox[1] + face_bbox[3]) // 2,
            )
            body_center = (
                (body_bbox[0] + body_bbox[2]) // 2,
                (body_bbox[1] + body_bbox[3]) // 2,
            )

            cv2.line(image, face_center, body_center, (0, 255, 255), 2)

        return image

    def draw_info(
        self, image: np.ndarray, info: Dict, position: Tuple[int, int] = (10, 30)
    ) -> np.ndarray:
        x, y = position
        line_height = self.font_size + 8
        for key, value in info.items():
            text = f"{key}: {value}"
            image = self._put_text_pil(image, text, (x, y))
            y += line_height

        return image

    def create_video_writer(
        self, output_path: str, fps: float, width: int, height: int, codec: str = "mp4v"
    ) -> cv2.VideoWriter:
        fourcc = cv2.VideoWriter_fourcc(*codec)
        return cv2.VideoWriter(output_path, fourcc, fps, (width, height))
