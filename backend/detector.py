from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any

import cv2
import numpy as np

from . import config


SKELETON = [
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
    (5, 11), (6, 12), (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
]


@dataclass
class PersonState:
    last_center_y: float | None = None
    last_height: float | None = None
    abnormal_counter: int = 0
    last_alert_time: float = 0


@dataclass
class FallDetector:
    model: Any
    device: str = "cpu"
    states: dict[str, PersonState] = field(default_factory=dict)
    last_debug: dict[str, Any] = field(default_factory=dict)

    def analyze(self, frame: np.ndarray, device_id: str = "default", persist: bool = True, high_sensitivity: bool = False) -> dict[str, Any]:
        if frame is None or frame.size == 0:
            raise ValueError("Invalid frame: frame is None or empty")
        processed = frame.copy()
        results = self.model.predict(
            processed,
            verbose=False,
            conf=config.MIN_CONFIDENCE,
            device=self.device,
        )[0]

        people = self._extract_people(results)
        if not people:
            return self.no_person_result(processed)

        fall_detected = False
        abnormal_detected = False
        best_score = 0.0
        best_debug: dict[str, Any] = {"person_count": len(people)}

        for index, person in enumerate(people):
            person_key = f"{device_id}:{person.get('track_id', index)}"
            state = self.states.setdefault(person_key, PersonState())
            features = self._person_features(person, state)
            score = features["fall_score"]
            best_score = max(best_score, score)
            if score >= config.ABNORMAL_SCORE_THRESHOLD:
                state.abnormal_counter += 1
            else:
                state.abnormal_counter = max(0, state.abnormal_counter - 1)

            confirm_frames = 2 if high_sensitivity else config.FALL_CONFIRM_FRAMES
            is_confirmed_fall = (
                score >= config.FALL_SCORE_THRESHOLD
                and state.abnormal_counter >= confirm_frames
            )
            is_abnormal = score >= config.ABNORMAL_SCORE_THRESHOLD

            fall_detected = fall_detected or is_confirmed_fall
            abnormal_detected = abnormal_detected or is_abnormal
            if score >= best_debug.get("fall_score", -1):
                best_debug = {"person_count": len(people), **features}

            self._draw_person(processed, person, features, is_confirmed_fall, is_abnormal)
            state.last_center_y = person["center_y"]
            state.last_height = person["height"]

        if fall_detected:
            status = "Fall Detected"
        elif abnormal_detected:
            status = "Abnormal Posture"
        else:
            status = "Normal"
        cv2.putText(processed, f"{status} people={len(people)} score={best_score:.2f}", (20, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 255) if fall_detected else (0, 165, 255) if abnormal_detected else (30, 180, 80), 2)

        return self._result(processed, status, fall_detected, abnormal_detected, round(best_score, 3), best_debug)

    def can_alert(self, device_id: str) -> bool:
        state = self.states.setdefault(f"{device_id}:device", PersonState())
        now = time.time()
        if now - state.last_alert_time >= config.ALERT_COOLDOWN_SECONDS:
            state.last_alert_time = now
            return True
        return False

    def _extract_people(self, results: Any) -> list[dict[str, Any]]:
        if results is None:
            return []
        if results.boxes is None or len(results.boxes) == 0:
            return []
        if results.keypoints is None:
            return []
        if getattr(results.keypoints, "xy", None) is None or getattr(results.keypoints, "conf", None) is None:
            return []
        if results.keypoints.xy is None or results.keypoints.conf is None:
            return []

        if getattr(results.boxes, "xyxy", None) is None or getattr(results.boxes, "xywh", None) is None or getattr(results.boxes, "conf", None) is None:
            return []

        boxes_xyxy = results.boxes.xyxy.cpu().numpy()
        boxes_xywh = results.boxes.xywh.cpu().numpy()
        confidences = results.boxes.conf.cpu().numpy()
        if len(confidences) == 0:
            return []
        track_ids = None
        if getattr(results.boxes, "id", None) is not None:
            track_ids = results.boxes.id.cpu().numpy().astype(int)
        keypoints_all = results.keypoints.xy.cpu().numpy()
        keypoint_scores = results.keypoints.conf.cpu().numpy()
        if len(keypoints_all) == 0 or len(keypoint_scores) == 0:
            return []

        people: list[dict[str, Any]] = []
        for index, confidence in enumerate(confidences):
            if index >= len(keypoints_all) or index >= len(keypoint_scores) or index >= len(boxes_xywh) or index >= len(boxes_xyxy):
                continue
            if confidence < config.MIN_CONFIDENCE:
                continue
            if len(keypoints_all[index]) < 17 or len(keypoint_scores[index]) < 17:
                continue
            x, y, width, height = boxes_xywh[index]
            if width <= 0 or height <= 0:
                continue
            people.append(
                {
                    "index": index,
                    "track_id": int(track_ids[index]) if track_ids is not None else index,
                    "confidence": float(confidence),
                    "xyxy": boxes_xyxy[index],
                    "xywh": boxes_xywh[index],
                    "keypoints": keypoints_all[index],
                    "scores": keypoint_scores[index],
                    "center_y": float(y),
                    "height": float(height),
                    "width": float(width),
                }
            )
        return people

    def _person_features(self, person: dict[str, Any], state: PersonState) -> dict[str, Any]:
        scores = person["scores"]
        keypoints = person["keypoints"]
        visible_keypoints = int(np.sum(scores > config.MIN_KEYPOINT_CONFIDENCE))
        width = person["width"]
        height = person["height"]
        aspect_ratio = width / max(height, 1.0)
        torso_angle = self._torso_angle(keypoints, scores)

        center_drop = 0.0
        if state.last_center_y is not None and state.last_height:
            center_drop = (person["center_y"] - state.last_center_y) / max(state.last_height, 1.0)

        score = 0.0
        if visible_keypoints < config.MIN_VISIBLE_KEYPOINTS:
            score -= 0.25
        if aspect_ratio >= 0.9:
            score += 0.35
        elif aspect_ratio >= 0.72:
            score += 0.18
        if torso_angle is not None:
            horizontal_torso = min(abs(torso_angle), abs(180 - torso_angle))
            if horizontal_torso <= 45:
                score += 0.3
            elif horizontal_torso <= 60:
                score += 0.15
        if center_drop >= config.MOTION_DROP_THRESHOLD:
            score += 0.25
        if aspect_ratio >= 0.9 and center_drop >= config.MOTION_DROP_THRESHOLD / 2:
            score += 0.12

        score = max(0.0, min(score, 1.0))
        return {
            "visible_keypoints": visible_keypoints,
            "torso_angle": round(torso_angle, 2) if torso_angle is not None else None,
            "aspect_ratio": round(aspect_ratio, 3),
            "center_drop": round(center_drop, 3),
            "fall_score": round(score, 3),
            "raw_confidence": round(person["confidence"], 3),
        }

    def no_person_result(self, frame: np.ndarray, message: str = "No person detected") -> dict[str, Any]:
        processed = frame.copy()
        cv2.putText(processed, message, (20, 42), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (128, 128, 128), 2)
        debug = {
            "person_count": 0,
            "visible_keypoints": 0,
            "torso_angle": None,
            "aspect_ratio": None,
            "fall_score": 0.0,
            "message": message,
        }
        return self._result(processed, "No Person", False, False, 0.0, debug)

    def _torso_angle(self, keypoints: np.ndarray, scores: np.ndarray) -> float | None:
        required = [5, 6, 11, 12]
        if any(scores[i] < config.MIN_KEYPOINT_CONFIDENCE for i in required):
            return None
        shoulder = ((keypoints[5][0] + keypoints[6][0]) / 2, (keypoints[5][1] + keypoints[6][1]) / 2)
        hip = ((keypoints[11][0] + keypoints[12][0]) / 2, (keypoints[11][1] + keypoints[12][1]) / 2)
        dx = hip[0] - shoulder[0]
        dy = hip[1] - shoulder[1]
        return abs(math.degrees(math.atan2(dy, dx)))

    def _draw_person(self, frame: np.ndarray, person: dict[str, Any], features: dict[str, Any], fall: bool, abnormal: bool) -> None:
        color = (0, 0, 255) if fall else (0, 165, 255) if abnormal else (30, 180, 80)
        label = "Fall Detected" if fall else "Abnormal Posture" if abnormal else "Normal"
        x1, y1, x2, y2 = person["xyxy"].astype(int)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, f"{label} score={features['fall_score']:.2f}", (x1, max(24, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.62, color, 2)

        keypoints = person["keypoints"]
        scores = person["scores"]
        for a, b in SKELETON:
            if scores[a] > config.MIN_KEYPOINT_CONFIDENCE and scores[b] > config.MIN_KEYPOINT_CONFIDENCE:
                pt1 = tuple(keypoints[a].astype(int))
                pt2 = tuple(keypoints[b].astype(int))
                cv2.line(frame, pt1, pt2, color, 2)
        for index, point in enumerate(keypoints):
            if scores[index] > config.MIN_KEYPOINT_CONFIDENCE:
                cv2.circle(frame, tuple(point.astype(int)), 3, (255, 255, 255), -1)

    def _result(self, frame: np.ndarray, status: str, fall: bool, abnormal: bool, confidence: float, debug: dict[str, Any]) -> dict[str, Any]:
        self.last_debug = debug
        return {
            "processed_frame": frame,
            "status": status,
            "fall_detected": fall,
            "abnormal_detected": abnormal,
            "confidence": confidence,
            "debug": debug,
        }
