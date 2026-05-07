# AegisVision - AI Fall Alert Monitor

## Project Overview

AegisVision is a full-stack AI fall detection project for invention competitions, classroom demonstrations, and technical review. Camera and screen clients continuously send frames to a FastAPI backend. The backend runs YOLOv8 Pose, uses a multi-signal fall detector, and only creates a Dashboard event when a confirmed `Fall Detected` alert occurs.

The system does **not** save all realtime frames and does **not** record 30-second videos. It saves one processed snapshot only when a fall alert is triggered.

## Key Features

- YOLOv8 Pose fall detection with CUDA GPU auto-selection and CPU fallback
- Camera Client using `getUserMedia()`
- Screen Capture Client using `getDisplayMedia()` for desktop, window, software, or browser-tab capture
- Local AI Detection Preview on Camera and Screen clients
- Fall Alert Center Dashboard that only displays confirmed fall events
- WebSocket `fall_alert` notifications
- Browser notifications
- Snapshot-only alert storage for lower storage use and better privacy
- Offline video demo script using the same backend detector logic
- Automatic YOLO model download on first backend startup

## System Architecture

1. `website/camera.html` captures webcam frames and sends them to `/analyze_frame`.
2. `website/screen.html` captures a user-selected screen, window, or tab and sends frames to `/analyze_frame`.
3. `backend/app.py` decodes frames, runs `backend/detector.py`, and returns a processed AI preview image to the client.
4. Only `Fall Detected` frames outside cooldown create a fall alert event.
5. `website/main.html` displays Fall Alert Events only. It does not show Normal / No Person / Error realtime device status.

## Tech Stack

- Python, FastAPI, Uvicorn
- Ultralytics YOLOv8 Pose
- PyTorch / TorchVision
- OpenCV, NumPy, Pydantic
- Vanilla HTML, CSS, JavaScript
- WebSocket, Service Worker, PWA Manifest

## Final Project Structure

```text
.
  README.md
  requirements.txt
  .gitignore
  config.example.json

  backend/
    __init__.py
    app.py
    config.py
    detector.py
    model_loader.py
    schemas.py
    storage.py
    utils.py
    websocket_manager.py

  scripts/
    video_demo.py

  website/
    main.html
    camera.html
    screen.html
    manifest.json
    sw.js
    css/
      style.css
      dashboard.css
      camera.css
      screen.css
    js/
      config.js
      api.js
      main.js
      camera.js
      screen.js
      notification.js
      websocket.js
    img/
      aegisvision.ico
      aegisvision.jpeg
    fall_records/
      .gitkeep
      images/
        .gitkeep

  models/
    .gitkeep

  samples/
    .gitkeep
```

## Installation

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS / Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Model Auto Download

The default model path is:

```text
models/yolov8m-pose.pt
```

On first backend startup, if the model file is missing, the backend attempts to use Ultralytics automatic download:

```text
[MODEL] Model file not found, attempting automatic download...
[MODEL] Model ready.
```

If automatic download fails, check your network or manually download `yolov8m-pose.pt` and place it in `models/`. Model files are ignored by Git and should not be committed.

## GPU / CUDA Usage

The backend uses PyTorch through Ultralytics. If CUDA is available, it selects `cuda:0`; otherwise it falls back to `cpu`.

Check your environment:

```bash
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU only')"
```

`requirements.txt` installs the general Python dependencies. For NVIDIA GPU acceleration, install the PyTorch CUDA build that matches your driver/CUDA version. Do not hard-code a CUDA wheel in this repo because every machine may need a different build.

Backend startup prints:

```text
[MODEL] Loading YOLO model from: models/yolov8m-pose.pt
[MODEL] torch.cuda.is_available(): True / False
[MODEL] Selected device: cuda:0 / cpu
[MODEL] GPU name: NVIDIA ... / None
[MODEL] Model loaded successfully
```

## Start Backend Server

```bash
uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

The response includes `model_loaded`, `model_path`, `device`, `cuda_available`, and `gpu_name`.

## Open Dashboard

Open:

```text
website/main.html
```

The Dashboard is a **Fall Alert Center**. It only shows confirmed fall alert events from `website/fall_records/log.json` and realtime WebSocket alerts.

## Use Camera Client

Open:

```text
website/camera.html
```

1. Set Device ID, for example `Kitchen`.
2. Set API Base URL, for example `http://127.0.0.1:8000`.
3. Click **Start Camera**.
4. Click **Start Detection**.
5. Use the AI Detection Preview to inspect skeletons, bounding boxes, and local result status.

## Use Screen Capture Client

Open:

```text
website/screen.html
```

1. Set Device ID, for example `Desktop-01`.
2. Set API Base URL.
3. Click **Start Screen Capture**.
4. Choose entire screen, a specific window, or a browser tab.
5. Click **Start Detection**.

Browser rules:

- `getDisplayMedia()` must be triggered by a user click.
- Browsers do not allow silent screen sharing startup.
- `localhost` or HTTPS is required by most browsers.
- Hide Preview does not stop capture or AI detection.
- If the selected window is minimized, some operating systems may stop updating its pixels.

## API Base URL Configuration

Both Camera and Screen clients read API Base URL from `website/js/config.js` and `localStorage`. There is no hard-coded Cloudflare Tunnel URL.

Default:

```text
http://127.0.0.1:8000
```

For phone testing, use your computer LAN IP or a trusted Cloudflare Tunnel / ngrok URL.

## Fall Alert Flow

1. Client sends frames to `/analyze_frame`.
2. Backend returns local AI result and processed preview image.
3. If status is not `Fall Detected`, nothing is saved and Dashboard is not updated.
4. If status is `Fall Detected` and the device is outside cooldown:
   - Snapshot is saved.
   - Event metadata is written to `log.json`.
   - WebSocket pushes `fall_alert`.
   - Dashboard adds a new Alert Card.
   - Browser notification is shown if permission is granted.

Cooldown default:

```text
ALERT_COOLDOWN_SECONDS = 30
```

Cooldown limits Dashboard alerts and log writes only. The local Camera/Screen AI Preview still shows `Fall Detected`.

## Alert Snapshot Storage

Snapshots:

```text
website/fall_records/images/
```

Event log:

```text
website/fall_records/log.json
```

Event format:

```json
{
  "event_id": "Desktop-01_20260507_201500",
  "device_id": "Desktop-01",
  "source": "screen",
  "status": "Fall Detected",
  "timestamp": "2026-05-07T20:15:00",
  "lastUpdate": "2026-05-07 20:15:00",
  "snapshot": "./fall_records/images/Desktop-01_20260507_201500.jpg",
  "fall_score": 0.91,
  "confidence": 0.86,
  "debug": {
    "person_count": 1,
    "fall_score": 0.91,
    "trigger_reason": "fall_score threshold exceeded for confirmed frames"
  }
}
```

Images and `log.json` are ignored by Git.

## WebSocket Notification

`/ws` only pushes `fall_alert` messages:

```json
{
  "type": "fall_alert",
  "event_id": "Desktop-01_20260507_201500",
  "device_id": "Desktop-01",
  "source": "screen",
  "status": "Fall Detected",
  "time": "2026-05-07 20:15:00",
  "snapshot": "./fall_records/images/Desktop-01_20260507_201500.jpg",
  "fall_score": 0.91,
  "confidence": 0.86,
  "message": "Fall detected!"
}
```

## Browser Notification

Dashboard can request browser notification permission. When a `fall_alert` arrives, it shows a notification through `website/js/notification.js`.

## Offline Video Demo

The offline demo analyzes a local video file and writes an annotated output video to `outputs/`. This is separate from the realtime Dashboard, which does not save videos.

```bash
python scripts/video_demo.py --input samples/fall.mp4 --output outputs/fall_result.mp4 --model models/yolov8m-pose.pt
```

Optional preview:

```bash
python scripts/video_demo.py --input samples/fall.mp4 --output outputs/fall_result.mp4 --model models/yolov8m-pose.pt --show
```

## API Reference

- `POST /analyze_frame`: returns current AI result and processed image for local client preview.
- `GET /health`: backend, model, CUDA, and GPU status.
- `GET /events`: confirmed Fall Alert Events only.
- `GET /events/{event_id}`: one event detail.
- `GET /devices`: lightweight connection heartbeat summary; not used as Dashboard main content.
- `WebSocket /ws`: fall alerts only.

## Configuration

Primary backend configuration is in `backend/config.py`. Optional local overrides can be placed in `config.json`.

Important parameters:

- `MODEL_PATH`
- `DEFAULT_MODEL_NAME`
- `MIN_CONFIDENCE`
- `MIN_KEYPOINT_CONFIDENCE`
- `MIN_VISIBLE_KEYPOINTS`
- `FALL_SCORE_THRESHOLD`
- `FALL_CONFIRM_FRAMES`
- `ALERT_COOLDOWN_SECONDS`
- `SAVE_ONLY_ON_FALL`
- `FALL_IMAGE_DIR`
- `FALL_LOG_PATH`

Frontend defaults are in `website/js/config.js`.

`config.example.json` is an example for release documentation and local reference.

## FAQ

**Does the system save realtime video?**  
No. It does not save all frames and does not save 30-second videos. It saves one processed snapshot only when a fall alert is confirmed.

**Why is Dashboard empty while clients show Normal or No Person?**  
That is expected. Dashboard only shows Fall Alert Events.

**Where is the YOLO model?**  
The backend uses `models/yolov8m-pose.pt`. It attempts automatic download on first run. `.pt` files are ignored by Git.

**Does GPU always work?**  
Only if your installed PyTorch build supports CUDA. If not, the backend uses CPU.

## Troubleshooting

- Open `/health` to confirm model and device status.
- If the model download fails, manually place `yolov8m-pose.pt` in `models/`.
- If Screen Capture cannot start, use `localhost` or HTTPS and click the start button manually.
- If browser notifications do not show, enable notification permission in Dashboard.
- If AI Preview shows `Error`, check terminal `[ANALYZE_ERROR]` traceback and browser DevTools `[AI_ANALYSIS_ERROR]`.

## Invention Competition Demo Flow

1. Start backend:
   `uvicorn backend.app:app --host 0.0.0.0 --port 8000`
2. Open Dashboard:
   `website/main.html`
3. Open Camera Client or Screen Capture Client.
4. Set API Base URL:
   `http://127.0.0.1:8000`
5. Click **Start Camera** or **Start Screen Capture**.
6. Click **Start Detection**.
7. Simulate a fall or play a test scene.
8. Dashboard displays a Fall Alert.
9. Snapshot is saved in `website/fall_records/images/`.
10. `log.json` records the event.

## Privacy Notes

- The system does not save all realtime frames.
- The system does not save 30-second videos.
- Only confirmed fall snapshots and event metadata are saved.
- Avoid selecting screens or windows that contain sensitive information.
- Do not expose the backend publicly without access control.
- If using Cloudflare Tunnel or ngrok, share links only with trusted people.

## GitHub Release Checklist

- [ ] requirements.txt 已更新
- [ ] .gitignore 已完整
- [ ] models/*.pt 不会被提交
- [ ] fall_records 图片不会被提交
- [ ] README 与实际功能一致
- [ ] Dashboard 只显示 Fall Alert Events
- [ ] 没有 30 秒视频记录残留
- [ ] Camera Client 可运行
- [ ] Screen Capture Client 可运行
- [ ] 后端 /health 正常
- [ ] YOLO 模型可自动下载
- [ ] CUDA 可用时使用 GPU
- [ ] CPU fallback 正常
- [ ] WebSocket alert 正常
- [ ] Browser notification 正常
- [ ] 项目可以从 clean clone 开始运行

## Future Improvements

- Add authentication for deployed dashboards
- Store events in SQLite or PostgreSQL
- Add camera grouping and location metadata
- Add evaluation metrics and sample datasets
- Add edge deployment documentation

## License

MIT License is a suitable default for a student invention project unless your school or competition requires a different license.

