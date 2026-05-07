from __future__ import annotations

from pathlib import Path
import shutil
from threading import Lock

import torch
from ultralytics import YOLO

from . import config


class ModelLoader:
    def __init__(self) -> None:
        self.model = None
        self.device = "cpu"
        self.cuda_available = False
        self.gpu_name: str | None = None
        self._lock = Lock()

    def load(self):
        with self._lock:
            if self.model is not None:
                return self.model

            model_path = Path(config.MODEL_PATH)
            self.cuda_available = torch.cuda.is_available()
            if self.cuda_available:
                self.device = "cuda:0"
                self.gpu_name = torch.cuda.get_device_name(0)
            else:
                self.device = "cpu"
                self.gpu_name = None

            print(f"[MODEL] Loading YOLO model from: {model_path}")
            print(f"[MODEL] torch.cuda.is_available(): {self.cuda_available}")
            print(f"[MODEL] Selected device: {self.device}")
            print(f"[MODEL] GPU name: {self.gpu_name}")

            if not model_path.exists():
                print("[MODEL] Model file not found, attempting automatic download...")
                model_path = self._download_model(model_path)

            self.model = YOLO(str(model_path))
            try:
                self.model.to(self.device)
            except Exception as exc:
                print(f"[MODEL] model.to({self.device}) skipped/failed: {exc}")

            print("[MODEL] Model loaded successfully")
            print("[MODEL] Model ready.")
            return self.model

    def _download_model(self, model_path: Path) -> Path:
        model_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            downloaded_model = YOLO(config.DEFAULT_MODEL_NAME)
            source_path = Path(getattr(downloaded_model, "ckpt_path", "") or config.DEFAULT_MODEL_NAME)
            if source_path.exists() and source_path.resolve() != model_path.resolve():
                shutil.copy2(source_path, model_path)
            elif not model_path.exists() and Path(config.DEFAULT_MODEL_NAME).exists():
                shutil.copy2(config.DEFAULT_MODEL_NAME, model_path)
            if not model_path.exists():
                raise FileNotFoundError(f"Ultralytics download completed but {model_path} was not created.")
            print(f"[MODEL] Downloaded model saved to: {model_path}")
            return model_path
        except Exception as exc:
            print(f"[MODEL] Automatic download failed: {exc}")
            print("[MODEL] Please check your network, or manually download yolov8m-pose.pt and place it in models/.")
            raise

    def get_model(self):
        if self.model is None:
            return self.load()
        return self.model

    def is_model_loaded(self) -> bool:
        return self.model is not None

    def get_device_info(self) -> dict:
        return {
            "device": self.device,
            "cuda_available": self.cuda_available,
            "gpu_name": self.gpu_name,
        }


model_loader = ModelLoader()


def get_model():
    return model_loader.get_model()


def is_model_loaded() -> bool:
    return model_loader.is_model_loaded()


def get_device_info() -> dict:
    return model_loader.get_device_info()
