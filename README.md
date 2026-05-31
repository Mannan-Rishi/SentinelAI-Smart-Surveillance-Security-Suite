# 🛡️ Sentinel AI — Smart Surveillance Security Suite

Sentinel AI is a high-performance, real-time computer vision security system designed for advanced threat monitoring and perimeter control. It features person tracking, facial recognition (verifying authorized vs. unauthorized individuals), specialized weapon detection, temporal alert confirmation, and instant email notifications with photo attachments. All of this is managed through a stunning, glassmorphism-themed administrative dashboard.

---

## ✨ Key Features

*   **⚡ Multi-Threaded Decoupled Architecture**: Separates the high-frequency camera frame grabbing thread, heavy AI model inference thread, and WebSocket-based client broadcast loops to ensure zero UI lag and smooth real-time video feeds.
*   **👤 Biometric Identification (Face Verification)**:
    *   **Detection**: Uses OpenCV's **YuNet** ONNX model for fast, high-performance facial boundary detection.
    *   **Recognition**: Uses OpenCV's **SFace** ONNX model to generate facial embeddings and verify individuals against an authorized whitelist database.
*   **⚔️ Specialized Weapon Detection**: Combines a global YOLOv8 scan with targeted crop-zooming around detected persons to identify weapons (e.g., knives, scissors, or custom weapons) with high precision even when partially hidden.
*   **⏱️ Temporal Alert Confirmation**: Prevents hand-gesture flickers and false alarms by requiring threats to persist for a customizable number of consecutive frames before triggering a system alert.
*   **📧 Automated Alerts**: Instant SMTP email notifications featuring captured event snapshots are dispatched immediately when unauthorized intruders or critical weapon threats are verified.
*   **🎛️ Live System Tuning**: Adjust face recognition confidence tolerances and weapon detection thresholds live via the web interface.
*   **📸 Forensic Logs & Snapshots**: Browse high-resolution automated snapshots and manual screen captures directly from the web interface.

---

## 📁 Repository Layout

```text
├── backend/
│   ├── server.py              # FastAPI application, WebSockets, routes & email alerts
│   ├── engine.py              # Camera threading, face biometrics & YOLOv8 engines
│   ├── notifier.py            # Async SMTP mailer for security snapshots
│   └── yolov8n.pt             # Core YOLO model weights (auto-cached/fallback)
├── frontend/
│   └── index.html             # Premium glassmorphism Tailwind/JS web client
├── models/
│   ├── face_detection_yunet.onnx      # ONNX Face Detector weights
│   ├── face_recognition_sface.onnx    # ONNX Face Recognizer weights
│   └── weapon_detection.pt            # Specialized YOLOv8 weapon weights (optional)
├── scripts/
│   └── download_models.py     # Automates downloading model weights from Hugging Face
└── storage/
    ├── authorized_faces/      # Database of whitelisted personnel portraits
    └── snapshots/             # Automatically saved threat snaps & manual captures
```

---

## 🚀 Getting Started

### 📋 Prerequisites

To run this project, you need **Python 3.8+** installed on your system. 

Install the required packages using pip:

```bash
pip install fastapi uvicorn opencv-python numpy ultralytics
```

> [!NOTE]
> Make sure your OpenCV version is modern (`opencv-python` or `opencv-contrib-python` >= 4.5.4) to ensure support for `FaceDetectorYN` and `FaceRecognizerSF`.

### 🔧 Installation & Setup

1.  **Clone the Repository** and navigate to the project directory:
    ```bash
    cd "d:/Projects/Detection Model/Detection Model"
    ```

2.  **Download AI Model Weights**:
    Run the provided automation script to fetch SFace, YuNet, and specialized weapon detection weights directly from Hugging Face:
    ```bash
    python scripts/download_models.py
    ```

3.  **Configure Mail Alerts (Optional)**:
    Open `backend/server.py` and modify the `EmailNotifier` configuration in the global state block:
    ```python
    notifier = EmailNotifier(
        sender_email="your-email@gmail.com",
        password="your-app-password" # Use a Gmail App Password
    )
    ```

4.  **Register Whitelisted Faces**:
    You can register whitelisted personnel either by:
    *   Using the **"Register New Subject"** modal on the web interface.
    *   Placing clear portrait photos directly into `storage/authorized_faces/`. Rename the image files to match the person's name (e.g., `john_doe.jpg`). The engine will automatically crop and compute embeddings on server startup or registration.

---

## 🖥️ Running the Application

1.  Start the FastAPI application:
    ```bash
    python backend/server.py
    ```
2.  Open your web browser and navigate to:
    ```
    http://localhost:8000
    ```

---

## 🛠️ Tech Stack & Library References

*   **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Uvicorn server)
*   **Computer Vision**: [OpenCV](https://opencv.org/) (ONNX Inference Engine)
*   **Object Detection & Tracking**: [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
*   **Frontend UI**: Vanilla HTML5, [Tailwind CSS CDN](https://tailwindcss.com/), [Lucide Icons](https://lucide.dev/), & Native WebSocket APIs.
*   **Communication Layer**: WebSockets for fast, full-duplex binary/text streaming.
