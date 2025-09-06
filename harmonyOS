import streamlit as st
from ultralytics import YOLO
import cv2
import numpy as np
import sounddevice as sd
import threading
import queue
from PIL import Image

st.set_page_config(page_title="TrafficOps+ Live Dashboard", layout="wide")
st.title("🚦 TrafficOps+ Live Traffic Dashboard")


siren_detected = False
ped_count = 0
non_motor_count = 0
emergency_count = 0
q_audio = queue.Queue()
running = False

def listen_siren():
    global siren_detected, running
    fs = 44100
    duration = 1

    def detect_siren(audio_chunk):
        fft = np.fft.fft(audio_chunk)
        freqs = np.fft.fftfreq(len(fft), 1/fs)
        magnitude = np.abs(fft)
        siren_range = (freqs > 500) & (freqs < 2000)
        siren_energy = magnitude[siren_range].sum()
        return siren_energy > 100000

    while running:
        audio = sd.rec(int(duration*fs), samplerate=fs, channels=1, dtype='float32')
        sd.wait()
        audio = audio.flatten()
        siren_detected = detect_siren(audio)



model = YOLO("yolov8s.pt")
cap = None

def detect_frame(frame):
    global ped_count, non_motor_count, emergency_count
    results = model(frame)
    annotated_frame = results[0].plot()
    boxes = results[0].boxes

    for box, cls in zip(boxes.xyxy, boxes.cls.cpu().numpy()):
        x1, y1, x2, y2 = map(int, box)
        label = results[0].names[int(cls)]

        if label == "person":
            ped_count += 1
            cv2.putText(annotated_frame, "Pedestrian", (x1, y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
        elif label in ["bicycle", "motorcycle"]:
            non_motor_count += 1
            cv2.putText(annotated_frame, "Non-motorized", (x1, y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,0), 2)
        elif label in ["car", "bus", "truck"]:
            vehicle_roi = frame[y1:y2, x1:x2]
            hsv = cv2.cvtColor(vehicle_roi, cv2.COLOR_BGR2HSV)
            mask_red = cv2.inRange(hsv, np.array([0,120,70]), np.array([10,255,255])) + \
                       cv2.inRange(hsv, np.array([170,120,70]), np.array([180,255,255]))
            mask_blue = cv2.inRange(hsv, np.array([100,150,0]), np.array([140,255,255]))
            red_pixels = cv2.countNonZero(mask_red)
            blue_pixels = cv2.countNonZero(mask_blue)
            lights_detected = red_pixels>50 or blue_pixels>50

            if lights_detected or siren_detected:
                emergency_count += 1
                cv2.putText(annotated_frame, "Emergency Vehicle", (x1, y1-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)

    return annotated_frame


start_btn = st.button("Start Detection")
stop_btn = st.button("Stop Detection")

frame_placeholder = st.empty()
col1, col2, col3 = st.columns(3)
ped_metric = col1.metric("🚶 Pedestrians", 0)
non_motor_metric = col2.metric("🚲 Non-motorized Vehicles", 0)
emergency_metric = col3.metric("🚑 Emergency Vehicles", 0)

if start_btn and not running:
    running = True
    ped_count = 0
    non_motor_count = 0
    emergency_count = 0
    cap = cv2.VideoCapture(0)

    
    audio_thread = threading.Thread(target=listen_siren, daemon=True)
    audio_thread.start()

while running:
    ret, frame = cap.read()
    if not ret:
        st.warning("Cannot open camera.")
        break

    frame = detect_frame(frame)

    
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_placeholder.image(frame_rgb, channels="RGB")


    ped_metric.metric("🚶 Pedestrians", ped_count)
    non_motor_metric.metric("🚲 Non-motorized Vehicles", non_motor_count)
    emergency_metric.metric("🚑 Emergency Vehicles", emergency_count)

    if stop_btn:
        running = False
        break

if cap:
    cap.release()
cv2.destroyAllWindows()
