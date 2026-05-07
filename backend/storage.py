from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import cv2
import numpy as np

from . import config
from .utils import compact_timestamp, now_display, now_iso, safe_filename


class FallStorage:
    def __init__(
        self,
        records_dir: Path = config.FALL_RECORDS_DIR,
        image_dir: Path = config.FALL_IMAGE_DIR,
        log_path: Path = config.FALL_LOG_PATH,
    ):
        self.records_dir = records_dir
        self.image_dir = image_dir
        self.log_path = log_path
        self.records_dir.mkdir(parents=True, exist_ok=True)
        self.image_dir.mkdir(parents=True, exist_ok=True)
        self.ensure_log_file()

    def ensure_log_file(self) -> None:
        if not self.log_path.exists():
            self._atomic_write([])
            return
        try:
            data = self.read_events()
            if not isinstance(data, list):
                self._atomic_write([])
        except json.JSONDecodeError:
            backup = self.log_path.with_suffix(".corrupt.json")
            try:
                self.log_path.replace(backup)
            finally:
                self._atomic_write([])

    def read_events(self) -> list[dict]:
        if not self.log_path.exists():
            return []
        with self.log_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []

    def append_event(self, event: dict) -> dict:
        events = self.read_events()
        events.append(event)
        self._atomic_write(events)
        return event

    def create_fall_event(self, device_id: str, source: str, frame: np.ndarray, confidence: float, fall_score: float, debug: dict) -> dict:
        safe_device = safe_filename(device_id, "unknown")
        event_stamp = compact_timestamp()
        event_id = f"{safe_device}_{event_stamp}"
        filename = f"{event_id}.jpg"
        path = self.image_dir / filename
        cv2.imwrite(str(path), frame)

        event = {
            "event_id": event_id,
            "device_id": device_id or "unknown",
            "source": source,
            "timestamp": now_iso(),
            "lastUpdate": now_display(),
            "status": "Fall Detected",
            "snapshot": f"./fall_records/images/{filename}",
            "fall_score": fall_score,
            "confidence": confidence,
            "debug": {
                **(debug or {}),
                "trigger_reason": "fall_score threshold exceeded for confirmed frames",
            },
        }
        return self.append_event(event)

    def get_event(self, event_id: str) -> dict | None:
        for event in self.read_events():
            if event.get("event_id") == event_id:
                return event
        return None

    def _atomic_write(self, events: list[dict]) -> None:
        self.records_dir.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix="log_", suffix=".json", dir=str(self.records_dir))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(events, f, indent=2, ensure_ascii=False)
            Path(temp_name).replace(self.log_path)
        finally:
            temp_path = Path(temp_name)
            if temp_path.exists():
                temp_path.unlink()
