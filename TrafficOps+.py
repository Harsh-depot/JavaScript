import cv2
import streamlit as st
import numpy as np
from ultralytics import YOLO
from sort import Sort  # Make sure sort.py is in same folder
import sounddevice as sd
from scipy.fft import fft

# ----------------------
# 1. Model & Tracker
# ----------------------
MODEL_PATH = "yolov8s.pt"
model = YOLO(MODEL_PATH)
tracker = Sort(max_age=5, min_hits=2, iou_threshold=0.3)

# ----------------------
# 2. Streamlit Setup
# ----------------------
st.set_page_config(page_title="TrafficOps+ Dashboard", layout="wide")
st.title("🚦 TrafficOps+ Smart Traffic Dashboard")

stframe = st.empty()
status_placeholder = st.empty()

ped_metric = st.metric("👥 Pedestrians", 0)
nmv_metric = st.metric("🚲 Non-Motorized Vehicles", 0)
emg_metric = st.metric("🚑 Emergency Vehicles", 0)
lane_indicator = st.empty()  # Traffic light indicator

# ----------------------
# 3. Camera Capture
# ----------------------
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    st.error("Camera could not be opened! Check if it's used by another app or permissions.")
  # 0 for default camera

# ----------------------
# 4. Siren Detection
# ----------------------
SIREN_THRESHOLD = 0.3  # Adjust experimentally

def detect_siren(duration=1, fs=44100):
    try:
        audio = sd.rec(int(duration*fs), samplerate=fs, channels=1, dtype='float32')
        sd.wait()
        fft_data = np.abs(fft(audio[:,0]))
        fft_data = fft_data[:len(fft_data)//2]
        # Detect dominant frequencies typical for siren (500-2000Hz)
        freq_indices = np.arange(len(fft_data)) * fs / len(audio)
        siren_band = fft_data[(freq_indices >= 500) & (freq_indices <= 2000)]
        if np.any(siren_band > SIREN_THRESHOLD):
            return True
        return False
    except Exception as e:
        return False

# ----------------------
# 5. Main Loop
# ----------------------
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        st.warning("Cannot read camera frame.")
        break

    # YOLOv8 detection
    results = model(frame, verbose=False)
    dets = []

    # Initialize counts
    ped_count, nmv_count, emg_count = 0, 0, 0
    emergency_detected = False

    # Process detections
    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            label = model.names[cls_id]
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])

            # Build SORT input: [x1, y1, x2, y2, confidence]
            dets.append([x1, y1, x2, y2, conf])

    # SORT tracking
    tracks = tracker.update(np.array(dets))

    # Draw boxes and assign counts
    for trk in tracks:
        x1, y1, x2, y2, track_id = map(int, trk[:5])
        # Find class for this track
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                label = model.names[cls_id]
                bx1, by1, bx2, by2 = map(int, box.xyxy[0])
                if abs(bx1 - x1) < 5 and abs(by1 - y1) < 5:  # approximate match
                    color = (0,255,0)
                    if label == "person":
                        ped_count += 1
                        color = (0,255,0)
                        cv2.putText(frame, "Pedestrian", (x1, y1-10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                    elif label in ["bicycle", "motorcycle"]:
                        nmv_count += 1
                        color = (255,255,0)
                        cv2.putText(frame, "Non-Motorized", (x1, y1-10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                    elif label in ["truck", "bus"]:  # placeholder for emergency vehicle
                        emg_count += 1
                        color = (0,0,255)
                        cv2.putText(frame, "Emergency", (x1, y1-10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                        emergency_detected = True
                    cv2.rectangle(frame, (x1,y1), (x2,y2), color, 2)

    # Siren detection (run in parallel if needed, simplified here)
    siren_flag = detect_siren(duration=0.5)
    if emergency_detected and siren_flag:
        lane_indicator.success("🚦 GREEN LIGHT: Emergency Vehicle Detected!")
        cv2.putText(frame, "EMERGENCY GREEN LIGHT", (50,50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 3)
    elif emergency_detected:
        lane_indicator.warning("🚦 Emergency Vehicle detected visually, siren not confirmed")
    else:
        lane_indicator.info("🚦 Normal Traffic")

    # Update metrics
    ped_metric.metric("👥 Pedestrians", ped_count)
    nmv_metric.metric("🚲 Non-Motorized Vehicles", nmv_count)
    emg_metric.metric("🚑 Emergency Vehicles", emg_count)

    # Display frame
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    stframe.image(frame, channels="RGB")

cap.release()
