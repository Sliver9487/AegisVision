from __future__ import annotations

import base64
import re
from datetime import datetime

import cv2
import numpy as np

from . import config


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def now_display() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def compact_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def safe_filename(value: str, fallback: str = "device") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    cleaned = cleaned.strip("._")
    return cleaned or fallback


def decode_base64_image(image_data: str) -> np.ndarray:
    if not image_data:
        raise ValueError("Failed to decode image. Empty image payload.")
    if "," in image_data:
        image_data = image_data.split(",", 1)[1]
    try:
        image_bytes = base64.b64decode(image_data, validate=False)
    except Exception as exc:
        raise ValueError(f"Failed to decode base64 image: {exc}") from exc
    np_arr = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("Failed to decode image. cv2.imdecode returned None.")
    if frame.size == 0:
        raise ValueError("Failed to decode image. Decoded frame is empty.")
    return frame


def encode_frame_base64(frame: np.ndarray, quality: int | None = None) -> str:
    if frame is None:
        raise ValueError("Cannot encode None frame")
    encode_quality = quality if quality is not None else config.JPEG_QUALITY
    ok, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), encode_quality])
    if not ok:
        raise ValueError("Failed to encode frame as JPEG")
    encoded = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"


def image_public_path(filename: str) -> str:
    return f"./fall_records/{filename}"
