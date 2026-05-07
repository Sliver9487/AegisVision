from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]


DEFAULTS: dict[str, Any] = {
    "APP_NAME": "AegisVision",
    "MODEL_PATH": str(ROOT_DIR / "models" / "yolov8m-pose.pt"),
    "DEFAULT_MODEL_NAME": "yolov8m-pose.pt",
    "FALL_RECORDS_DIR": str(ROOT_DIR / "website" / "fall_records"),
    "FALL_IMAGE_DIR": str(ROOT_DIR / "website" / "fall_records" / "images"),
    "FALL_LOG_PATH": str(ROOT_DIR / "website" / "fall_records" / "log.json"),
    "CORS_ORIGINS": ["*"],
    "MIN_CONFIDENCE": 0.35,
    "MIN_KEYPOINT_CONFIDENCE": 0.4,
    "MIN_VISIBLE_KEYPOINTS": 8,
    "FALL_SCORE_THRESHOLD": 0.65,
    "FALL_CONFIRM_FRAMES": 3,
    "ALERT_COOLDOWN_SECONDS": 30,
    "ABNORMAL_SCORE_THRESHOLD": 0.45,
    "MOTION_DROP_THRESHOLD": 0.08,
    "JPEG_QUALITY": 85,
    "SAVE_ONLY_ON_FALL": True,
}


def _load_override() -> dict[str, Any]:
    config_path = ROOT_DIR / "config.json"
    if not config_path.exists():
        return {}
    try:
        with config_path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
            return {str(key).upper(): value for key, value in raw.items()}
    except (OSError, json.JSONDecodeError):
        return {}


_config = {**DEFAULTS, **_load_override()}

APP_NAME: str = _config["APP_NAME"]
MODEL_PATH: str = _config["MODEL_PATH"]
DEFAULT_MODEL_NAME: str = _config["DEFAULT_MODEL_NAME"]
FALL_RECORDS_DIR: Path = Path(_config["FALL_RECORDS_DIR"])
FALL_IMAGE_DIR: Path = Path(_config["FALL_IMAGE_DIR"])
FALL_LOG_PATH: Path = Path(_config["FALL_LOG_PATH"])
CORS_ORIGINS: list[str] = _config["CORS_ORIGINS"]

MIN_CONFIDENCE: float = float(_config["MIN_CONFIDENCE"])
MIN_KEYPOINT_CONFIDENCE: float = float(_config["MIN_KEYPOINT_CONFIDENCE"])
MIN_VISIBLE_KEYPOINTS: int = int(_config["MIN_VISIBLE_KEYPOINTS"])
FALL_SCORE_THRESHOLD: float = float(_config["FALL_SCORE_THRESHOLD"])
FALL_CONFIRM_FRAMES: int = int(_config["FALL_CONFIRM_FRAMES"])
ALERT_COOLDOWN_SECONDS: int = int(_config["ALERT_COOLDOWN_SECONDS"])
ABNORMAL_SCORE_THRESHOLD: float = float(_config["ABNORMAL_SCORE_THRESHOLD"])
MOTION_DROP_THRESHOLD: float = float(_config["MOTION_DROP_THRESHOLD"])
JPEG_QUALITY: int = int(_config["JPEG_QUALITY"])
SAVE_ONLY_ON_FALL: bool = bool(_config["SAVE_ONLY_ON_FALL"])
