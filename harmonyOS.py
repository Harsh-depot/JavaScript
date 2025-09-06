import cv2
import streamlit as st
from ultralytics import YOLO
import numpy as np
import time

# Load YOLOv8 model (replace with your trained model if available)
MODEL_PATH = "yolov8s.pt"
model = YOLO(MODEL_PATH)

# Categories we care about
TARGET_CLASSES = {
    "person": "Pedestrian",
    "bicycle": "Non-motorized",
    "motorcycle": "Non-motorized",
    "ambulance": "Emergency",
    "fire_truck": "Emergency"  # If using custom dataset with these labels
}

# Fallback mapping for COCO dataset (ambulance/fire_truck are not native)
EMERGENCY_CLASSES = ["truck", "bus"]  # heuristic for now

# Streamlit dashboard
st.title("🚦 TrafficOps+ Live Dashboard")
stframe = st.empty()
status_placeholder = st.empty()

# Metrics
pedestrian_count = st.metric("👥 Pedestrians", 0)
non_motor_count = st.metric("🚲 Non-Motorized Vehicles", 0)
emergency_count = st.metric("🚑 Emergency Vehicles", 0)

cap = cv2.VideoCapture(0)  # 0 = default camera

if not cap.isOpened():
    st.error("❌ Camera not accessible")
else:
    st.success("✅ Camera started... press 'Stop' button to end")

stop_btn = st.button("Stop Camera")

while cap.isOpened() and not stop_btn:
    ret, frame = cap.read()
    if not ret:
        st.warning("⚠️ Stream ended or cannot fetch frame.")
        break

    # Run detection
    results = model(frame, verbose=False)

    # Counts
    ped_count = 0
    nmv_count = 0
    emg_count = 0

    # Process detections
    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            label = model.names[cls_id]
            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            if label == "person":
                ped_count += 1
                color = (0, 255, 0)
                cv2.putText(frame, "Pedestrian", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            elif label in ["bicycle", "motorcycle"]:
                nmv_count += 1
                color = (255, 255, 0)
                cv2.putText(frame, "Non-Motorized", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            elif label in EMERGENCY_CLASSES:
                emg_count += 1
                color = (0, 0, 255)
                cv2.putText(frame, "Emergency", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

    # Update metrics
    pedestrian_count.metric("👥 Pedestrians", ped_count)
    non_motor_count.metric("🚲 Non-Motorized Vehicles", nmv_count)
    emergency_count.metric("🚑 Emergency Vehicles", emg_count)

    # Show frame
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    stframe.image(frame, channels="RGB")

cap.release()
