from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


DetectionStatus = Literal["Normal", "Abnormal Posture", "Fall Detected", "No Person", "Connection Lost", "Error"]


class AnalyzeFrameRequest(BaseModel):
    image: str = Field(..., description="JPEG frame as a data URL or raw base64 string")
    id: str = Field("unknown", description="Camera client device ID")
    source: str = Field("camera", description="Frame source, usually camera or screen")
    high_sensitivity: bool = False
    client_time: str | None = None


class AnalyzeFrameResponse(BaseModel):
    device: str
    source: str
    status: DetectionStatus
    fall: bool
    abnormal: bool
    confidence: float
    fall_score: float = 0.0
    latency_ms: int
    image: str | None = None
    debug: dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_path: str
    device: str
    cuda_available: bool
    gpu_name: str | None = None
