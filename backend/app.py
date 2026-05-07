from __future__ import annotations

import time
import traceback

import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import config
from .detector import FallDetector
from .model_loader import get_device_info, get_model, is_model_loaded
from .schemas import AnalyzeFrameRequest, AnalyzeFrameResponse, HealthResponse
from .storage import FallStorage
from .utils import decode_base64_image, encode_frame_base64, now_display
from .websocket_manager import WebSocketManager


app = FastAPI(title="AegisVision Fall Detection API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

storage = FallStorage()
websockets = WebSocketManager()
device_state: dict[str, dict] = {}
detector: FallDetector | None = None


@app.on_event("startup")
def startup() -> None:
    global detector
    try:
        detector = FallDetector(get_model(), device=get_device_info()["device"])
    except FileNotFoundError as exc:
        print(f"[MODEL] Startup model load skipped: {exc}")
        detector = None
    storage.ensure_log_file()


def get_detector() -> FallDetector:
    global detector
    if detector is None:
        detector = FallDetector(get_model(), device=get_device_info()["device"])
    return detector


@app.exception_handler(Exception)
async def unhandled_exception_handler(_, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "device": "unknown",
            "source": "camera",
            "status": "Error",
            "fall": False,
            "abnormal": False,
            "confidence": 0.0,
            "fall_score": 0.0,
            "latency_ms": 0,
            "image": None,
            "debug": {"message": "Unhandled backend error", "error": str(exc)},
        },
    )


@app.get("/health", response_model=HealthResponse)
def health() -> dict:
    return {
        "status": "ok",
        "model_loaded": is_model_loaded(),
        "model_path": str(config.MODEL_PATH),
        **get_device_info(),
    }


@app.get("/events")
def events() -> list[dict]:
    return [event for event in storage.read_events() if "fall" in str(event.get("status", "")).lower()]


@app.get("/events/{event_id}")
def event_detail(event_id: str):
    event = storage.get_event(event_id)
    if event is None:
        return JSONResponse(status_code=404, content={"detail": "Event not found"})
    return event


@app.get("/devices")
def devices() -> list[dict]:
    now = time.time()
    result = []
    for state in device_state.values():
        age = now - float(state.get("seen_at", 0))
        connection = "online" if age <= 5 else "unstable" if age <= 15 else "offline"
        result.append(
            {
                "device_id": state.get("id"),
                "source": state.get("source"),
                "last_seen": state.get("last_seen"),
                "connection": connection,
            }
        )
    return result


@app.post("/analyze_frame", response_model=AnalyzeFrameResponse)
async def analyze_frame(payload: AnalyzeFrameRequest) -> dict:
    start = time.perf_counter()
    device_id = payload.id.strip() or "unknown"
    source = (payload.source or "camera").strip().lower()
    if source not in {"camera", "screen"}:
        source = "camera"
    state_key = f"{source}:{device_id}"
    detector_key = f"{source}:{device_id}"
    frame = None

    try:
        frame = decode_base64_image(payload.image)
        result = get_detector().analyze(frame, device_id=detector_key, high_sensitivity=payload.high_sensitivity)
        encoded_image = encode_frame_base64(result["processed_frame"])
        latency_ms = int((time.perf_counter() - start) * 1000)
        fall_score = float(result["debug"].get("fall_score", result["confidence"]) or 0.0)

        response = {
            "device": device_id,
            "source": source,
            "status": result["status"],
            "fall": result["fall_detected"],
            "abnormal": result["abnormal_detected"],
            "confidence": result["confidence"],
            "fall_score": fall_score,
            "latency_ms": latency_ms,
            "image": encoded_image,
            "debug": result["debug"],
        }

        device_state[state_key] = {
            "id": device_id,
            "source": source,
            "last_seen": now_display(),
            "seen_at": time.time(),
        }

        if result["fall_detected"] and get_detector().can_alert(detector_key):
            event = storage.create_fall_event(
                device_id=device_id,
                source=source,
                frame=result["processed_frame"],
                confidence=result["confidence"],
                fall_score=fall_score,
                debug=result["debug"],
            )
            await websockets.broadcast(
                {
                    "type": "fall_alert",
                    "event_id": event["event_id"],
                    "device_id": event["device_id"],
                    "source": source,
                    "status": "Fall Detected",
                    "time": event["lastUpdate"],
                    "timestamp": event["timestamp"],
                    "snapshot": event["snapshot"],
                    "fall_score": event["fall_score"],
                    "confidence": event["confidence"],
                    "message": "Fall detected!",
                }
            )
        print(
            f"[ANALYZE] device={device_id} source={source} status={result['status']} "
            f"persons={result['debug'].get('person_count', 0)} latency={latency_ms}ms "
            f"confidence={result['confidence']}"
        )
        return response
    except Exception as exc:
        latency_ms = int((time.perf_counter() - start) * 1000)
        encoded_image = None
        if frame is not None:
            try:
                error_frame = frame.copy()
                cv2.putText(error_frame, "Error during AI analysis", (20, 42), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (128, 128, 128), 2)
                encoded_image = encode_frame_base64(error_frame)
            except Exception:
                encoded_image = None
        if encoded_image is None:
            error_frame = np.full((360, 640, 3), 235, dtype=np.uint8)
            cv2.putText(error_frame, "Error: invalid frame or AI analysis failed", (24, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (128, 128, 128), 2)
            encoded_image = encode_frame_base64(error_frame)
        debug = {
            "person_count": 0,
            "visible_keypoints": 0,
            "torso_angle": None,
            "aspect_ratio": None,
            "fall_score": 0.0,
            "message": "Error during AI analysis",
            "error": str(exc),
        }
        device_state[state_key] = {
            "id": device_id,
            "source": source,
            "last_seen": now_display(),
            "seen_at": time.time(),
        }
        print(f"[ANALYZE_ERROR] device={device_id} source={source} error={exc}")
        traceback.print_exc()
        return {
            "device": device_id,
            "source": source,
            "status": "Error",
            "fall": False,
            "abnormal": False,
            "confidence": 0.0,
            "fall_score": 0.0,
            "latency_ms": latency_ms,
            "image": encoded_image,
            "debug": debug,
        }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websockets.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websockets.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)
