import cv2
import streamlit as st
import numpy as np
from ultralytics import YOLO
from sort import Sort  # Make sure sort.py is in same folder
import sounddevice as sd
from scipy.fft import fft
import time

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
pollution_metric = st.metric("🏭 Pollution Index", 0)
emissions_metric = st.metric("📉 Emissions Reduced (%)", 0)
lane_indicator = st.empty()  # Traffic light indicator
virtual_traffic_light = st.empty()
map_placeholder = st.empty()

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
total_congestion_score = 0
start_time = time.time()

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

    # ----------------------
    # 6. Environmental & Congestion Analysis
    # ----------------------
    # Define a simple "congestion score" based on vehicle count
    vehicle_count = nmv_count + emg_count  # You can refine this
    congestion_score = vehicle_count * 0.5  # A simple multiplier
    total_congestion_score += congestion_score

    # Calculate average pollution index (a simple simulation)
    current_pollution_index = min(100, congestion_score * 5)
    pollution_metric.metric("🏭 Pollution Index", f"{current_pollution_index:.1f}")

    # Calculate emissions reduction
    elapsed_time = time.time() - start_time
    if elapsed_time > 0:
        emissions_reduced = (total_congestion_score / elapsed_time) * 0.1
        emissions_metric.metric("📉 Emissions Reduced (%)", f"{emissions_reduced:.1f}")

    if current_pollution_index > 50 and emg_count == 0:
        status_placeholder.warning("⚠️ HIGH POLLUTION: Recommend short-cycle adjustments to cut idling.")

    # ----------------------
    # 7. Pedestrian Crossing & Augmented Bubble Space
    # ----------------------
    # Pedestrian Surge Logic
    if ped_count > 5: # Threshold for a "pedestrian surge"
        status_placeholder.info("🚶‍♂️ Pedestrian surge → trigger crosswalk phase.")
        overlay = frame.copy()
        cv2.circle(overlay, (frame.shape[1] // 2, frame.shape[0] // 2), 100, (0, 255, 0), -1)
        alpha = 0.3
        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
    
    # ----------------------
    # 8. Virtual Traffic Light
    # ----------------------
    siren_flag = detect_siren(duration=0.5)
    if emergency_detected and siren_flag:
        lane_indicator.success("🚦 GREEN LIGHT: Emergency Vehicle Detected!")
        cv2.putText(frame, "EMERGENCY GREEN LIGHT", (50,50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 3)
        virtual_traffic_light.success("🟢 GREEN LIGHT FOR EMERGENCY PATH")
    elif emergency_detected:
        lane_indicator.warning("🚦 Emergency Vehicle detected visually, siren not confirmed")
    elif ped_count > 5:
        lane_indicator.info("🚶‍♂️ Pedestrian surge → trigger crosswalk phase.")
        virtual_traffic_light.info("🚶‍♂️ PEDESTRIAN CROSSING PHASE")
    else:
        lane_indicator.info("🚦 Normal Traffic")
        virtual_traffic_light.info("🔴 NORMAL TRAFFIC FLOW")

    # ----------------------
    # 9. Simulated Google Maps Integration
    # ----------------------
    map_data = {
        'lat': [12.9716], # Example coordinates for a city
        'lon': [77.5946]
    }
    map_placeholder.map(map_data, zoom=12)

    # Update metrics
    ped_metric.metric("👥 Pedestrians", ped_count)
    nmv_metric.metric("🚲 Non-Motorized Vehicles", nmv_count)
    emg_metric.metric("🚑 Emergency Vehicles", emg_count)

    # Display frame
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    stframe.image(frame, channels="RGB")

cap.release()
