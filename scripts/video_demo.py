from __future__ import annotations

import argparse
import time
from pathlib import Path

import cv2

from backend.detector import FallDetector
from ultralytics import YOLO


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run AegisVision fall detection on a local video.")
    parser.add_argument("--input", required=True, help="Input video path, e.g. samples/fall.mp4")
    parser.add_argument("--output", default="outputs/fall_result.mp4", help="Output annotated video path")
    parser.add_argument("--model", default="models/yolov8m-pose.pt", help="YOLOv8 pose model path")
    parser.add_argument("--alerts-dir", default="outputs/fall_alerts", help="Directory for alert snapshots")
    parser.add_argument("--device-id", default="video-demo", help="Logical device ID used by the detector")
    parser.add_argument("--show", action="store_true", help="Show a realtime preview window")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    alerts_dir = Path(args.alerts_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    alerts_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise FileNotFoundError(f"Input video not found: {input_path}")
    if not Path(args.model).exists():
        raise FileNotFoundError(f"Model not found: {args.model}")

    detector = FallDetector(YOLO(args.model))
    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {input_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    writer = cv2.VideoWriter(str(output_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))

    frame_count = 0
    fall_frames = 0
    saved_alerts = 0
    start = time.perf_counter()

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame_count += 1
            result = detector.analyze(frame, device_id=args.device_id, persist=True)
            processed = result["processed_frame"]
            writer.write(processed)

            if result["fall_detected"]:
                fall_frames += 1
                if detector.can_alert(args.device_id):
                    alert_path = alerts_dir / f"{args.device_id}_{frame_count:06d}.jpg"
                    cv2.imwrite(str(alert_path), processed)
                    saved_alerts += 1

            if args.show:
                cv2.imshow("AegisVision Video Demo", processed)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    finally:
        cap.release()
        writer.release()
        if args.show:
            cv2.destroyAllWindows()

    elapsed = max(time.perf_counter() - start, 0.001)
    print("AegisVision video demo complete")
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print(f"Total frames: {frame_count}")
    print(f"Fall frames: {fall_frames}")
    print(f"Average FPS: {frame_count / elapsed:.2f}")
    print(f"Saved alert snapshots: {saved_alerts}")


if __name__ == "__main__":
    main()

