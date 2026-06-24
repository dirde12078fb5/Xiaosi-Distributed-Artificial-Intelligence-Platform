"""Gallery composite —— 把同一 person 的多张 crop 横向拼成一张 composite 图。

策略：

    - 每张 crop **resize 到统一高度**（body 256 / face 128），宽按原比例缩放
    - 横向 ``np.hstack`` 拼接，**不加白条/分隔符**（避免 omni 把分隔当语义信号）
    - **不在图上画文字**——人名走相邻的 OpenAI ``text`` content 块
    - body / face 各拼一张，分别作为独立 ``image_url`` content 推送

调用方（``prompt_builder.build_fused_payload``）拿到 composite 后做 jpeg
编码再 base64，每个 person 在 prompt 里产出一对 image_url：

    [text] 【张三】
    [text] 体型/全身参考：
    [image] <body composite>
    [text] 面部参考：
    [image] <face composite>
"""

from __future__ import annotations

import logging
from typing import Optional

import cv2
import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)


# =============================================================================
# 默认尺寸
# =============================================================================

DEFAULT_BODY_HEIGHT = 256       # body composite 拼接后高度（宽不限）
DEFAULT_FACE_HEIGHT = 128       # face composite 拼接后高度
DEFAULT_JPEG_QUALITY = 100
DEFAULT_MAX_WIDTH = 768         # 防异常情况下 composite 横向过宽（如同一 person 上百张图）


# =============================================================================
# 工具
# =============================================================================


def hstack_to_height(
    crops: list[NDArray[np.uint8]],
    target_height: int,
    *,
    max_total_width: int | None = DEFAULT_MAX_WIDTH,
) -> Optional[NDArray[np.uint8]]:
    """把一组 BGR 图横向拼成 ``target_height`` 高，每张维持长宽比。

    Args:
        crops:           BGR uint8 图列表
        target_height:   目标高度
        max_total_width: 拼接后总宽度上限；超出时按比例再整体缩窄。
                         None 时不做约束。

    Returns:
        拼接好的 BGR uint8 图；输入为空时返回 None。
    """
    valid = [c for c in crops if c is not None and c.size > 0]
    if not valid:
        return None

    resized: list[NDArray[np.uint8]] = []
    for im in valid:
        h, w = im.shape[:2]
        new_w = max(1, int(round(w * target_height / h)))
        resized.append(cv2.resize(im, (new_w, target_height)))

    out = np.hstack(resized)

    # 总宽度兜底：如果拼接后宽度过大（比如同一 person 上百张 face），整体再缩
    # 这里一定是降采样，用 INTER_AREA 抗混叠（拼接的 hstack 会引入新边界，
    # 降采样时 LINEAR 容易在边界产生伪影）
    if max_total_width is not None and out.shape[1] > max_total_width:
        scale = max_total_width / out.shape[1]
        new_w = int(out.shape[1] * scale)
        new_h = int(target_height * scale)
        out = cv2.resize(out, (new_w, new_h), interpolation=cv2.INTER_AREA)

    return out


def encode_jpeg_bytes(
    image: NDArray[np.uint8],
    quality: int = DEFAULT_JPEG_QUALITY,
) -> Optional[bytes]:
    """``image`` → jpeg bytes，编码失败返回 None。"""
    if image is None or image.size == 0:
        return None
    ok, buf = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        return None
    return buf.tobytes()


# =============================================================================
# 一站式 helpers（推荐入口）
# =============================================================================


def build_body_composite_jpeg(
    crops: list[NDArray[np.uint8]],
    *,
    height: int = DEFAULT_BODY_HEIGHT,
    quality: int = DEFAULT_JPEG_QUALITY,
) -> Optional[bytes]:
    """把 body crops 拼成 composite，返回 jpeg bytes。"""
    composite = hstack_to_height(crops, height)
    if composite is None:
        return None
    return encode_jpeg_bytes(composite, quality=quality)


def build_face_composite_jpeg(
    crops: list[NDArray[np.uint8]],
    *,
    height: int = DEFAULT_FACE_HEIGHT,
    quality: int = DEFAULT_JPEG_QUALITY,
) -> Optional[bytes]:
    """把 face crops 拼成 composite，返回 jpeg bytes。"""
    composite = hstack_to_height(crops, height)
    if composite is None:
        return None
    return encode_jpeg_bytes(composite, quality=quality)


# —— PNG 无损版（注入 omni + 落盘统一走 PNG，保住画质；上方 jpeg composite 已无调用方）——


def encode_png_bytes(
    image: NDArray[np.uint8],
    quality: int = DEFAULT_JPEG_QUALITY,
) -> Optional[bytes]:
    """``image`` → png bytes（无损），编码失败返回 None。

    ``quality`` 入参仅为兼容 ``_merge_and_encode`` 的 ``encode_fn(img, quality=...)``
    协议而保留；PNG 无损，不受此值影响。
    """
    if image is None or image.size == 0:
        return None
    ok, buf = cv2.imencode(".png", image)
    if not ok:
        return None
    return buf.tobytes()


def build_body_composite_png(
    crops: list[NDArray[np.uint8]],
    *,
    height: int = DEFAULT_BODY_HEIGHT,
) -> Optional[bytes]:
    """把 body crops 拼成 composite，返回 png bytes（无损）。"""
    composite = hstack_to_height(crops, height)
    if composite is None:
        return None
    return encode_png_bytes(composite)


def build_face_composite_png(
    crops: list[NDArray[np.uint8]],
    *,
    height: int = DEFAULT_FACE_HEIGHT,
) -> Optional[bytes]:
    """把 face crops 拼成 composite，返回 png bytes（无损）。"""
    composite = hstack_to_height(crops, height)
    if composite is None:
        return None
    return encode_png_bytes(composite)
