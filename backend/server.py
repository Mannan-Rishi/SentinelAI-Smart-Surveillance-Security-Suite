from contextlib import asynccontextmanager
from notifier import EmailNotifier
import cv2
import json
import asyncio
import os
import threading
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse
from engine import CameraService, DetectionEngine
from datetime import datetime

# Setup paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")
STORAGE_DIR = os.path.join(os.path.dirname(BASE_DIR), "storage")
SNAPSHOT_DIR = os.path.join(STORAGE_DIR, "snapshots")

if not os.path.exists(SNAPSHOT_DIR): os.makedirs(SNAPSHOT_DIR)

# Global State
camera = CameraService(source=0)
engine = DetectionEngine(model_path="yolov8n.pt")
notifier = EmailNotifier(
    sender_email="YOUR EMAIL",
    password="YOUR PASSWORD"
)
connected_clients = set()

# Shared buffers for decoupled processing
latest_results = {
    "stats": {
        "authorized_count": 0,
        "unauthorized_count": 0,
        "weapon_count": 0,
        "total_people": 0
    },
    "event": None,
    "detections": []
}
frame_lock = threading.Lock()

# System Config (Initial state)
system_config = {
    "email_enabled": True,
    "snapshot_enabled": True,
    "face_threshold": 0.40,
    "weapon_threshold": 0.50  # Default UI value
}
engine.update_thresholds(system_config["face_threshold"], system_config["weapon_threshold"])

def ai_processing_worker():
    global latest_results
    print("AI Worker Thread started.")
    while True:
        frame = camera.get_frame()
        if frame is None:
            time.sleep(0.1)
            continue
        
        try:
            # Process frame for AI
            _, results = engine.process_frame(frame)
            
            with frame_lock:
                latest_results["stats"] = {
                    "authorized_count": results.get("authorized_count", 0),
                    "unauthorized_count": results.get("unauthorized_count", 0),
                    "total_authorized": results.get("total_authorized", 0),
                    "total_unauthorized": results.get("total_unauthorized", 0),
                    "weapon_count": results.get("weapon_count", 0),
                    "total_people": results.get("authorized_count", 0) + results.get("unauthorized_count", 0)
                }
                latest_results["detections"] = results.get("detections", [])
                latest_results["event"] = results.get("new_event")
                
        except Exception as e:
            print(f"AI Worker Error: {e}")
            time.sleep(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    camera.start()
    app.state.main_loop = asyncio.get_running_loop()
    
    # Start AI worker thread
    ai_thread = threading.Thread(target=ai_processing_worker, daemon=True)
    ai_thread.start()
    
    # Start Broadcast task
    broadcast_task = asyncio.create_task(broadcast_updates())
    
    yield
    # Shutdown
    broadcast_task.cancel()
    camera.stop()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def get_dashboard():
    with open(os.path.join(FRONTEND_DIR, "index.html"), "r") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.get("/snapshots/{filename}")
async def get_snapshot(filename: str):
    return FileResponse(os.path.join(SNAPSHOT_DIR, filename))

async def handle_new_event(event, frame):
    if not system_config["snapshot_enabled"]:
        return event
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"event_{timestamp}_{event['type']}.jpg"
    filepath = os.path.join(SNAPSHOT_DIR, filename)
    cv2.imwrite(filepath, frame)
    event["snapshot"] = f"/snapshots/{filename}"
    
    if system_config["email_enabled"] and event["type"] in ["weapon", "unauthorized"]:
        asyncio.create_task(notifier.send_alert(
            subject=f"{event['type'].upper()} Detected",
            message=f"At {event['time']}: {event['message']}",
            image_path=filepath
        ))
    return event

async def broadcast_data(data):
    if not connected_clients: return
    message = json.dumps(data)
    for client in list(connected_clients):
        try:
            await client.send_text(message)
        except Exception:
            connected_clients.remove(client)

async def broadcast_updates():
    print("Broadcaster Task started.")
    while True:
        try:
            if connected_clients:
                new_event = None
                if latest_results.get("event"):
                    raw = camera.get_frame()
                    new_event = await handle_new_event(latest_results["event"], raw)
                    latest_results["event"] = None 

                await broadcast_data({
                    **latest_results["stats"], 
                    "detections": latest_results["detections"],
                    "new_event": new_event
                })
        except Exception as e:
            print(f"Broadcast Error: {e}")
        await asyncio.sleep(0.05) 

def generate_frames():
    while True:
        # STREAM RAW FRAME (Fastest possible)
        display_frame = camera.get_frame()
            
        if display_frame is None:
            time.sleep(0.001)
            continue

        ret, buffer = cv2.imencode('.jpg', display_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in connected_clients:
            connected_clients.remove(websocket)

@app.post("/capture")
async def capture_frame():
    frame = camera.get_frame()
    if frame is not None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"capture_{timestamp}.jpg"
        filepath = os.path.join(SNAPSHOT_DIR, filename)
        cv2.imwrite(filepath, frame)
        return {"status": "success", "filename": filename}
    return {"status": "error", "message": "Camera not available"}

@app.get("/history")
async def get_history():
    files = []
    if os.path.exists(SNAPSHOT_DIR):
        for f in sorted(os.listdir(SNAPSHOT_DIR), reverse=True):
            if f.endswith(".jpg"):
                files.append({
                    "filename": f,
                    "url": f"/snapshots/{f}",
                    "time": datetime.fromtimestamp(os.path.getctime(os.path.join(SNAPSHOT_DIR, f))).strftime("%Y-%m-%d %H:%M:%S")
                })
    return {"history": files}

@app.get("/authorized_data")
async def get_authorized_data():
    auth_dir = os.path.join(engine.storage_dir, "authorized_faces")
    people = []
    if os.path.exists(auth_dir):
        for f in os.listdir(auth_dir):
            if f.lower().endswith((".jpg", ".png", ".jpeg")):
                people.append({
                    "name": os.path.splitext(f)[0].capitalize(),
                    "filename": f,
                    "url": f"/authorized_img/{f}"
                })
    return {"people": people}

@app.get("/authorized_img/{filename}")
async def get_auth_img(filename: str):
    return FileResponse(os.path.join(engine.storage_dir, "authorized_faces", filename))

@app.post("/upload_authorized")
async def upload_authorized(request: Request):
    form = await request.form()
    name = form.get("name")
    image = form.get("image")
    
    if not name or not image:
        return {"status": "error", "message": "Name and image are required"}
    
    auth_dir = os.path.join(engine.storage_dir, "authorized_faces")
    if not os.path.exists(auth_dir): os.makedirs(auth_dir)
    
    filename = f"{name.replace(' ', '_')}{os.path.splitext(image.filename)[1]}"
    filepath = os.path.join(auth_dir, filename)
    
    content = await image.read()
    with open(filepath, "wb") as f:
        f.write(content)
        
    # Trigger engine to reload faces
    engine.load_authorized_faces()
    
    return {"status": "success", "message": f"Successfully registered {name}"}

@app.post("/update_settings")
async def update_settings(request: Request):
    global system_config
    try:
        new_config = await request.json()
        system_config.update(new_config)
        
        # Update Engine
        engine.update_thresholds(
            float(system_config["face_threshold"]), 
            float(system_config["weapon_threshold"])
        )
        
        print(f"[Server] Settings updated: {system_config}")
        return {"status": "success", "config": system_config}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
