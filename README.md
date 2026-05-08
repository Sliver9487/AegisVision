# AegisVision - AI Fall Alert Monitor

## Project Overview

AegisVision is an AI fall detection system designed for a high school invention competition. It uses a camera or screen capture feed, analyzes human posture with YOLOv8 Pose, and sends an alert when a possible fall is detected.

The goal is to support elderly care, hospital monitoring, classroom demonstrations, and other safety scenarios where quick fall awareness is important.

The system does **not** save continuous video. It only saves one processed snapshot when a confirmed fall alert occurs.

## Key Features

- AI human pose detection using YOLOv8 Pose
- Camera detection through a browser webcam page
- Screen capture detection for testing videos, windows, or browser tabs
- Dashboard that shows confirmed fall alerts
- AI preview with skeletons, bounding boxes, and detection status
- Browser notification when a fall alert is triggered
- Snapshot-only storage for better privacy
- CPU support with optional NVIDIA GPU acceleration

## How It Works

1. The Camera or Screen page captures image frames.
2. Frames are sent to the FastAPI backend.
3. The backend uses YOLOv8 Pose to detect body keypoints.
4. The fall detector checks posture signals such as body angle, height ratio, and keypoint position.
5. If a fall is confirmed, the system saves a snapshot and updates the Dashboard.

## Tech Stack

- Python
- FastAPI
- Ultralytics YOLOv8 Pose
- PyTorch
- OpenCV
- HTML, CSS, JavaScript
- WebSocket notifications

## Project Structure

```text
backend/      AI backend, detector logic, API server
website/      Dashboard, Camera Client, Screen Capture Client
scripts/      Offline video demo script
models/       YOLO model file location
samples/      Sample videos for testing
```

## Installation

Create a Python virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

Activate it on macOS / Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Model File

The default model path is:

```text
models/yolov8m-pose.pt
```

On first backend startup, the system will try to download the model automatically. If that fails, manually download `yolov8m-pose.pt` and place it inside the `models/` folder.

## Start the Backend

```bash
uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

## Open the Web Pages

Dashboard:

```text
website/main.html
```

Camera Client:

```text
website/camera.html
```

Screen Capture Client:

```text
website/screen.html
```

Use this API Base URL in the web pages:

```text
http://127.0.0.1:8000
```

## Competition Demo Flow

1. Start the backend server.
2. Open `website/main.html` as the Dashboard.
3. Open `website/camera.html` or `website/screen.html`.
4. Set API Base URL to `http://127.0.0.1:8000`.
5. Click **Start Camera** or **Start Screen Capture**.
6. Click **Start Detection**.
7. Simulate a fall or play a test video.
8. The Dashboard shows a fall alert.
9. A processed snapshot is saved in `website/fall_records/images/`.

## Offline Video Demo

Use this for testing a prepared video without opening the browser clients:

```bash
python scripts/video_demo.py --input samples/fall.mp4 --output outputs/fall_result.mp4 --model models/yolov8m-pose.pt
```

Show a realtime preview while processing:

```bash
python scripts/video_demo.py --input samples/fall.mp4 --output outputs/fall_result.mp4 --model models/yolov8m-pose.pt --show
```

## Troubleshooting

- If the backend fails to start, check that dependencies are installed.
- If the model is missing, place `yolov8m-pose.pt` in the `models/` folder.
- If detection is slow, use a smaller model or an NVIDIA GPU with CUDA-enabled PyTorch.
- If Screen Capture cannot start, use `localhost` or HTTPS and start it with a manual button click.
- If the Dashboard is empty, no confirmed fall alert has been triggered yet.