import urllib.request
import os

def download_file(url, dest):
    print(f"Downloading {url} to {dest}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(dest, 'wb') as out_file:
            out_file.write(response.read())
        print("Download complete.")
    except Exception as e:
        print(f"Error downloading {url}: {e}")

if __name__ == "__main__":
    os.makedirs("models", exist_ok=True)
    
    # 1. Weapon Detection (YOLOv8)
    weapon_url = "https://huggingface.co/RishavSinha/yolov8-weapon-detection/resolve/main/best.pt"
    download_file(weapon_url, "models/weapon_detection.pt")
    
    # 2. Face Detection (YuNet)
    yunet_url = "https://huggingface.co/opencv/face_detection_yunet/resolve/main/face_detection_yunet_2023mar.onnx"
    download_file(yunet_url, "models/face_detection_yunet.onnx")
    
    # 3. Face Recognition (SFace)
    sface_url = "https://huggingface.co/opencv/face_recognition_sface/resolve/main/face_recognition_sface_2021dec.onnx"
    download_file(sface_url, "models/face_recognition_sface.onnx")
