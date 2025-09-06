import cv2
import streamlit as st
import numpy as np
import threading
import time
from ultralytics import YOLO
import yt_dlp
import requests
import json
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd

# ---------------------
# CONFIG
# ---------------------
MODEL_PATH = "yolov8s.pt"
GOOGLE_MAPS_API_KEY = st.secrets.get("GOOGLE_MAPS_API_KEY", "")
OPENWEATHER_API_KEY = st.secrets.get("OPENWEATHER_API_KEY", "")

# Traffic light states
TRAFFIC_LIGHT_STATES = {
    "red": (0, 0, 255),
    "yellow": (0, 255, 255), 
    "green": (0, 255, 0)
}

# Emergency zones
EMERGENCY_ZONES = {
    "hospital": {"lat": 28.6139, "lng": 77.2090, "radius": 500, "name": "Delhi Hospital"},
    "school": {"lat": 28.6141, "lng": 77.2092, "radius": 300, "name": "Central School"}
}

# ---------------------
# LOAD YOLOv8 MODEL
# ---------------------
@st.cache_resource
def load_model():
    return YOLO(MODEL_PATH)

model = load_model()

# ---------------------
# GLOBAL STATE
# ---------------------
running = False
frame_lock = threading.Lock()
latest_frame = None
vehicle_count = 0
pedestrian_count = 0
emergency_count = 0
hotspot_zone = None
aqi_level = 0
traffic_light_state = "green"
pedestrian_waiting = False
emergency_detected = False
congestion_level = 0
lane_allocations = {"lane1": "normal", "lane2": "normal", "lane3": "normal"}

# ---------------------
# UTILITY FUNCTIONS
# ---------------------
def get_real_aqi_data(lat, lng):
    """Get real AQI data from OpenWeather API"""
    if not OPENWEATHER_API_KEY:
        return None
    try:
        url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lng}&appid={OPENWEATHER_API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data['list'][0]['main']['aqi']
    except:
        pass
    return None

def calculate_congestion_level(vehicle_count, pedestrian_count):
    """Calculate congestion level based on traffic density"""
    if vehicle_count > 30:
        return 3  # High congestion
    elif vehicle_count > 15:
        return 2  # Medium congestion
    elif vehicle_count > 5:
        return 1  # Low congestion
    return 0  # No congestion

def suggest_emergency_route(emergency_zone):
    """Suggest optimal route for emergency vehicles"""
    return f"Emergency route to {emergency_zone} - All lanes cleared"

def detect_ambulance_simple(frame, x1, y1, x2, y2):
    """Simplified but effective ambulance detection"""
    roi = frame[int(y1):int(y2), int(x1):int(x2)]
    if roi.size == 0:
        return False
    
    # Convert to HSV for better color detection
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    
    # Red color detection (ambulances are usually red/white)
    red_lower1 = np.array([0, 50, 50])
    red_upper1 = np.array([10, 255, 255])
    red_lower2 = np.array([170, 50, 50])
    red_upper2 = np.array([180, 255, 255])
    
    red_mask1 = cv2.inRange(hsv, red_lower1, red_upper1)
    red_mask2 = cv2.inRange(hsv, red_lower2, red_upper2)
    red_mask = red_mask1 + red_mask2
    
    # White color detection (ambulances have white parts)
    white_lower = np.array([0, 0, 200])
    white_upper = np.array([180, 30, 255])
    white_mask = cv2.inRange(hsv, white_lower, white_upper)
    
    # Calculate color percentages
    red_pixels = cv2.countNonZero(red_mask)
    white_pixels = cv2.countNonZero(white_mask)
    total_pixels = roi.shape[0] * roi.shape[1]
    
    red_percentage = red_pixels / total_pixels
    white_percentage = white_pixels / total_pixels
    
    # Ambulance detection: red + white combination
    if red_percentage > 0.1 and white_percentage > 0.1:
        return True
    elif red_percentage > 0.2:  # High red percentage
        return True
    
    return False

def draw_traffic_light(frame, state, position=(50, 50)):
    """Draw virtual traffic light on frame"""
    x, y = position
    color = TRAFFIC_LIGHT_STATES[state]
    
    # Draw traffic light background with gradient effect
    cv2.rectangle(frame, (x-25, y-70), (x+25, y+70), (30, 30, 30), -1)
    cv2.rectangle(frame, (x-20, y-65), (x+20, y+65), (60, 60, 60), -1)
    
    # Draw light circles with glow effect
    cv2.circle(frame, (x, y-40), 18, color if state == "red" else (40, 40, 40), -1)
    cv2.circle(frame, (x, y-20), 18, color if state == "yellow" else (40, 40, 40), -1)
    cv2.circle(frame, (x, y), 18, color if state == "green" else (40, 40, 40), -1)
    
    # Add inner bright circles for active lights
    if state == "red":
        cv2.circle(frame, (x, y-40), 12, (0, 0, 255), -1)
    elif state == "yellow":
        cv2.circle(frame, (x, y-20), 12, (0, 255, 255), -1)
    elif state == "green":
        cv2.circle(frame, (x, y), 12, (0, 255, 0), -1)

def draw_augmented_bubbles(frame, vehicle_count, pedestrian_count):
    """Draw augmented bubble space visualization"""
    h, w = frame.shape[:2]
    
    # Create bubble effect based on traffic density
    bubble_size = min(50, max(10, vehicle_count * 2))
    bubble_alpha = min(0.3, vehicle_count * 0.01)
    
    # Draw semi-transparent circles
    overlay = frame.copy()
    cv2.circle(overlay, (w//2, h//2), bubble_size, (0, 255, 255), -1)
    cv2.addWeighted(overlay, bubble_alpha, frame, 1 - bubble_alpha, 0, frame)
    
    # Add pedestrian bubbles
    if pedestrian_count > 0:
        for i in range(min(pedestrian_count, 5)):
            x = w - 100 + i * 20
            y = h - 100
            cv2.circle(frame, (x, y), 15, (255, 0, 255), 2)

# ---------------------
# VIDEO SOURCE HANDLER
# ---------------------
def get_video_source(input_type, file_path=None, yt_url=None):
    if input_type == "Camera":
        return 0
    elif input_type == "Local File" and file_path:
        return file_path
    elif input_type == "YouTube" and yt_url:
        try:
            # Handle Google Drive links
            if "share.google" in yt_url or "drive.google" in yt_url:
                st.warning("⚠️ Google Drive links may not work directly. Please use a direct YouTube URL.")
                return None
            
            ydl_opts = {
                "format": "best[height<=720]",
                "noplaylist": True,
                "quiet": True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(yt_url, download=False)
                if 'url' in info:
                    return info["url"]
                else:
                    st.error("⚠️ Could not extract video URL")
                    return None
        except Exception as e:
            st.error(f"⚠️ Error loading video: {e}")
            return None
    return None

# ---------------------
# DETECTION THREAD
# ---------------------
def run_detection(video_source):
    global running, latest_frame, vehicle_count, pedestrian_count, emergency_count, hotspot_zone, aqi_level
    global traffic_light_state, pedestrian_waiting, emergency_detected, congestion_level, lane_allocations

    cap = cv2.VideoCapture(video_source)

    if not cap.isOpened():
        st.error("⚠️ Cannot open video source.")
        running = False
        return

    while running:
        ret, frame = cap.read()
        if not ret:
            st.error("⚠️ Stream ended or cannot fetch frame.")
            break

        # YOLOv8 Inference
        results = model(frame, stream=True)

        vehicle_count = 0
        pedestrian_count = 0
        emergency_count = 0
        hotspot_zone = None
        aqi_level = 0
        pedestrian_waiting = False
        emergency_detected = False

        for r in results:
            boxes = r.boxes.xyxy.cpu().numpy()
            classes = r.boxes.cls.cpu().numpy().astype(int)
            confs = r.boxes.conf.cpu().numpy()

            # Process detections
            for (x1, y1, x2, y2), cls, conf in zip(boxes, classes, confs):
                label = model.names[int(cls)]

                # Count categories
                if label in ["car", "bus", "truck", "motorbike", "bicycle"]:
                    vehicle_count += 1
                    
                    # Check for ambulance using simplified detection
                    if detect_ambulance_simple(frame, x1, y1, x2, y2):
                        emergency_count += 1
                        emergency_detected = True
                        
                        # Draw emergency vehicle with special styling
                        color = (0, 0, 255)  # Red for emergency vehicles
                        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 4)
                        cv2.putText(frame, f"🚑 AMBULANCE {conf:.2f}",
                                    (int(x1), int(y1) - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                        
                        # Draw flashing effect
                        cv2.circle(frame, (int((x1+x2)/2), int((y1+y2)/2)), 25, color, 3)
                    else:
                        # Regular vehicle
                        color = (0, 255, 0)  # Green for vehicles
                        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                        cv2.putText(frame, f"{label} {conf:.2f}",
                                    (int(x1), int(y1) - 5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                        
                elif label == "person":
                    pedestrian_count += 1
                    # Check if pedestrian is near crosswalk (bottom half of frame)
                    if y2 > frame.shape[0] * 0.6:
                        pedestrian_waiting = True
                    
                    # Draw pedestrian
                    color = (255, 0, 255)  # Magenta for pedestrians
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                    cv2.putText(frame, f"{label} {conf:.2f}",
                                (int(x1), int(y1) - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Enhanced Pollution Hotspot Logic
        congestion_level = calculate_congestion_level(vehicle_count, pedestrian_count)
        
        if congestion_level >= 2:  # Medium to high congestion
            for zone_name, zone_data in EMERGENCY_ZONES.items():
                if zone_name == "hospital" and vehicle_count > 15:
                    hotspot_zone = f"{zone_data['name']} Zone"
                    real_aqi = get_real_aqi_data(zone_data['lat'], zone_data['lng'])
                    aqi_level = real_aqi if real_aqi else min(300, vehicle_count * 8)
                    break
            else:
                hotspot_zone = "General Traffic Zone"
                aqi_level = min(200, vehicle_count * 5)

        # Traffic Light Logic
        if emergency_detected:
            traffic_light_state = "green"  # Emergency priority
        elif pedestrian_waiting and vehicle_count < 5:
            traffic_light_state = "red"  # Pedestrian priority
        elif congestion_level >= 2:
            traffic_light_state = "yellow"  # Caution
        else:
            traffic_light_state = "green"  # Normal flow

        # Dynamic Lane Allocation
        if emergency_detected:
            lane_allocations = {"lane1": "emergency", "lane2": "emergency", "lane3": "normal"}
        elif congestion_level >= 2:
            lane_allocations = {"lane1": "bus", "lane2": "normal", "lane3": "normal"}
        else:
            lane_allocations = {"lane1": "normal", "lane2": "normal", "lane3": "normal"}

        # Draw Visual Elements
        draw_traffic_light(frame, traffic_light_state, (frame.shape[1] - 100, 100))
        draw_augmented_bubbles(frame, vehicle_count, pedestrian_count)
        
        # Draw lane allocation indicators
        lane_y = frame.shape[0] - 50
        for i, (lane, status) in enumerate(lane_allocations.items()):
            x = 50 + i * 150
            color = (0, 255, 0) if status == "normal" else (0, 0, 255) if status == "emergency" else (0, 255, 255)
            cv2.putText(frame, f"{lane}: {status}", (x, lane_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # Enhanced status text
        status_text = f"Vehicles: {vehicle_count} | Pedestrians: {pedestrian_count} | Emergencies: {emergency_count}"
        if hotspot_zone:
            status_text += f" | 🚩 {hotspot_zone} (AQI {aqi_level})"
        if emergency_detected:
            status_text += " | 🚨 EMERGENCY DETECTED"

        cv2.putText(frame, status_text, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        # Save frame for dashboard
        with frame_lock:
            latest_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    cap.release()

# ---------------------
# STREAMLIT DASHBOARD
# ---------------------
st.set_page_config(
    page_title="TrafficOps+", 
    page_icon="🚦", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for stunning visuals
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        text-align: center;
        color: white;
    }
    
    .main-header h1 {
        font-size: 3rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    
    .traffic-light-container {
        background: linear-gradient(145deg, #2c3e50, #34495e);
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.3);
        text-align: center;
        margin: 1rem 0;
        border: 3px solid #3498db;
    }
    
    .traffic-light {
        display: inline-block;
        background: #2c3e50;
        padding: 1rem;
        border-radius: 15px;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.5);
        margin: 1rem 0;
    }
    
    .light {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        margin: 0.5rem;
        display: inline-block;
        box-shadow: 0 0 20px rgba(0,0,0,0.5);
        transition: all 0.3s ease;
    }
    
    .light.red {
        background: radial-gradient(circle, #ff4757, #c44569);
        box-shadow: 0 0 30px #ff4757;
        animation: pulse-red 2s infinite;
    }
    
    .light.yellow {
        background: radial-gradient(circle, #ffa502, #ff6348);
        box-shadow: 0 0 30px #ffa502;
        animation: pulse-yellow 1s infinite;
    }
    
    .light.green {
        background: radial-gradient(circle, #2ed573, #1e90ff);
        box-shadow: 0 0 30px #2ed573;
        animation: pulse-green 3s infinite;
    }
    
    .light.inactive {
        background: #34495e;
        box-shadow: none;
        animation: none;
    }
    
    @keyframes pulse-red {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.1); opacity: 0.8; }
    }
    
    @keyframes pulse-yellow {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.05); opacity: 0.9; }
    }
    
    @keyframes pulse-green {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.08); opacity: 0.85; }
    }
    
    .metric-card {
        background: linear-gradient(145deg, #ffffff, #f8f9fa);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        border-left: 5px solid #1f77b4;
        margin: 0.5rem 0;
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 35px rgba(0,0,0,0.15);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin: 0;
    }
    
    .metric-label {
        font-size: 1rem;
        color: #6c757d;
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .emergency-alert {
        background: linear-gradient(135deg, #ff6b6b, #ee5a24);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(255,107,107,0.4);
        animation: emergency-pulse 1s infinite;
        margin: 1rem 0;
    }
    
    @keyframes emergency-pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.02); }
    }
</style>
""", unsafe_allow_html=True)

# Stunning Header
st.markdown("""
<div class="main-header">
    <h1>🚦 TrafficOps+</h1>
    <p><strong>Safer, Greener City Traffic Playbook</strong> - Real-time Traffic Management & Emergency Response</p>
</div>
""", unsafe_allow_html=True)

# Sidebar for controls
with st.sidebar:
    st.header("🎛️ Control Panel")
    
    # Input Selector
    input_type = st.selectbox("🎥 Select Input Source", ["Camera", "Local File", "YouTube"])
    
    video_source = None
    if input_type == "Local File":
        file_path = st.text_input("Enter video file path:", "traffic.mp4")
        video_source = get_video_source(input_type, file_path=file_path)
    elif input_type == "YouTube":
        yt_url = st.text_input("Enter YouTube video URL:")
        if yt_url:
            video_source = get_video_source(input_type, yt_url=yt_url)
    else:
        video_source = get_video_source("Camera")
    
    # Control buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶ Start", type="primary"):
            if not running and video_source is not None:
                running = True
                t = threading.Thread(target=run_detection, args=(video_source,))
                t.start()
                st.success("Detection started!")

    with col2:
        if st.button("⏹ Stop"):
            running = False
            st.info("Detection stopped!")
    
    # Emergency zones info
    st.header("🏥 Emergency Zones")
    for zone_name, zone_data in EMERGENCY_ZONES.items():
        st.info(f"**{zone_data['name']}**\nLat: {zone_data['lat']:.4f}\nLng: {zone_data['lng']:.4f}")

# Main dashboard layout
col1, col2 = st.columns([2, 1])

with col1:
    # Video feed
    st.header("📹 Live Video Feed")
    frame_display = st.empty()
    
    # Google Maps integration
    if GOOGLE_MAPS_API_KEY:
        st.header("🗺️ Traffic Map")
        m = folium.Map(location=[28.6139, 77.2090], zoom_start=12)
        
        # Add emergency zones
        for zone_name, zone_data in EMERGENCY_ZONES.items():
            folium.CircleMarker(
                [zone_data['lat'], zone_data['lng']],
                radius=zone_data['radius']/100,
                popup=f"{zone_data['name']} - {zone_name.title()} Zone",
                color='red' if zone_name == 'hospital' else 'blue',
                fill=True
            ).add_to(m)
        
        # Add traffic hotspot if detected
        if hotspot_zone:
            folium.Marker(
                [28.6139, 77.2090],
                popup=f"🚩 {hotspot_zone} - AQI: {aqi_level}",
                icon=folium.Icon(color='orange', icon='warning-sign')
            ).add_to(m)
        
        st_folium(m, width=700, height=300)

with col2:
    # Stunning Traffic Light Component
    st.markdown("""
    <div class="traffic-light-container">
        <h3 style="color: white; margin-bottom: 1rem;">🚦 LIVE TRAFFIC SIGNAL</h3>
        <div class="traffic-light">
            <div class="light red" id="red-light"></div><br>
            <div class="light yellow" id="yellow-light"></div><br>
            <div class="light green" id="green-light"></div>
        </div>
        <p style="color: #ecf0f1; margin-top: 1rem; font-weight: 600;" id="light-status">STATUS: READY</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Real-time metrics with stunning cards
    st.markdown("### 📊 Live Traffic Metrics")
    
    # Traffic metrics - using placeholders for real-time updates
    col_a, col_b = st.columns(2)
    with col_a:
        vehicles_metric = st.empty()
        pedestrians_metric = st.empty()
    with col_b:
        emergency_metric = st.empty()
        congestion_metric = st.empty()
    
    # Update metrics in real-time with beautiful cards
    if running:
        with frame_lock:
            if latest_frame is not None:
                # Vehicles metric
                vehicles_metric.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">🚗 {vehicle_count}</div>
                    <div class="metric-label">Vehicles Detected</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Pedestrians metric
                pedestrians_metric.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">🚶 {pedestrian_count}</div>
                    <div class="metric-label">Pedestrians</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Emergency metric
                emergency_metric.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">🚨 {emergency_count}</div>
                    <div class="metric-label">Emergency Vehicles</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Congestion metric
                congestion_metric.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">🚧 {congestion_level}</div>
                    <div class="metric-label">Congestion Level</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Pollution metrics with stunning design
    st.markdown("### 🌍 Air Quality Monitor")
    pollution_metric = st.empty()
    
    if running:
        with frame_lock:
            if latest_frame is not None:
                if hotspot_zone:
                    aqi_color = "red" if aqi_level > 150 else "orange" if aqi_level > 100 else "green"
                    pollution_metric.markdown(f"""
                    <div class="metric-card" style="border-left-color: {aqi_color};">
                        <div class="metric-value" style="color: {aqi_color};">🌍 {aqi_level}</div>
                        <div class="metric-label">{hotspot_zone}</div>
                        <div style="margin-top: 1rem;">
                            <div style="background: #e9ecef; border-radius: 10px; height: 20px; overflow: hidden;">
                                <div style="background: linear-gradient(90deg, #2ed573, #ffa502, #ff4757); 
                                            height: 100%; width: {min(aqi_level/300*100, 100)}%; 
                                            border-radius: 10px; transition: width 0.5s ease;"></div>
                            </div>
                            <small style="color: #6c757d;">AQI Level: {aqi_level}</small>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    pollution_metric.markdown("""
                    <div class="metric-card" style="border-left-color: #2ed573;">
                        <div class="metric-value" style="color: #2ed573;">✅ Good</div>
                        <div class="metric-label">Air Quality Status</div>
                    </div>
                    """, unsafe_allow_html=True)

# Emergency alerts with stunning design
emergency_alert = st.empty()
pedestrian_alert = st.empty()

if running:
    with frame_lock:
        if latest_frame is not None:
            if emergency_detected:
                emergency_alert.markdown("""
                <div class="emergency-alert">
                    <h4 style="margin: 0; font-size: 1.5rem;">🚨 EMERGENCY VEHICLE DETECTED!</h4>
                    <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem;">All lanes cleared for emergency passage</p>
                </div>
                """, unsafe_allow_html=True)
                st.info(suggest_emergency_route("hospital"))
            else:
                emergency_alert.empty()
            
            if pedestrian_waiting:
                pedestrian_alert.markdown("""
                <div style="background: linear-gradient(135deg, #ffa502, #ff6348); 
                            color: white; padding: 1rem; border-radius: 10px; 
                            margin: 1rem 0; text-align: center; font-weight: 600;">
                    🚶 PEDESTRIANS WAITING - Crosswalk signal activated
                </div>
                """, unsafe_allow_html=True)
            else:
                pedestrian_alert.empty()

# Dynamic Traffic Light JavaScript
st.markdown("""
<script>
function updateTrafficLight(state) {
    const redLight = document.getElementById('red-light');
    const yellowLight = document.getElementById('yellow-light');
    const greenLight = document.getElementById('green-light');
    const status = document.getElementById('light-status');
    
    // Reset all lights
    redLight.className = 'light inactive';
    yellowLight.className = 'light inactive';
    greenLight.className = 'light inactive';
    
    // Activate current state
    if (state === 'red') {
        redLight.className = 'light red';
        status.textContent = 'STATUS: STOP';
        status.style.color = '#ff4757';
    } else if (state === 'yellow') {
        yellowLight.className = 'light yellow';
        status.textContent = 'STATUS: CAUTION';
        status.style.color = '#ffa502';
    } else if (state === 'green') {
        greenLight.className = 'light green';
        status.textContent = 'STATUS: GO';
        status.style.color = '#2ed573';
    }
}
</script>
""", unsafe_allow_html=True)

# Live data visualization with stunning design
st.markdown("### 📈 Real-time Traffic Analytics")
chart_container = st.empty()

if running:
    with frame_lock:
        if latest_frame is not None:
            # Create sample data for visualization
            timestamps = pd.date_range(start=datetime.now() - timedelta(minutes=10), 
                                      end=datetime.now(), freq='30s')
            
            # Simulate traffic data
            traffic_data = pd.DataFrame({
                'timestamp': timestamps,
                'vehicles': np.random.poisson(vehicle_count, len(timestamps)),
                'pedestrians': np.random.poisson(pedestrian_count, len(timestamps)),
                'aqi': np.random.poisson(aqi_level if aqi_level > 0 else 50, len(timestamps))
            })
            
            # Traffic flow chart with stunning design
            fig = px.line(traffic_data, x='timestamp', y=['vehicles', 'pedestrians'], 
                          title="🚗 Traffic Flow Over Time",
                          color_discrete_sequence=['#667eea', '#764ba2'])
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(size=14),
                title_font_size=20,
                title_font_color='#2c3e50'
            )
            fig.update_traces(line=dict(width=3))
            
            chart_container.plotly_chart(fig, use_container_width=True)
            
            # AQI chart
            if aqi_level > 0:
                fig_aqi = px.line(traffic_data, x='timestamp', y='aqi', 
                                 title="🌍 Air Quality Index (AQI)",
                                 color_discrete_sequence=['#ff6b6b'])
                fig_aqi.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(size=14),
                    title_font_size=20,
                    title_font_color='#2c3e50'
                )
                fig_aqi.update_traces(line=dict(width=3))
                chart_container.plotly_chart(fig_aqi, use_container_width=True)

# Dynamic Traffic Light Update
if running:
    with frame_lock:
        if latest_frame is not None:
            # Update traffic light with JavaScript
            st.markdown(f"""
            <script>
            updateTrafficLight('{traffic_light_state}');
            </script>
            """, unsafe_allow_html=True)

# Stunning Footer
st.markdown("""
<div style="background: linear-gradient(135deg, #2c3e50, #34495e); 
            padding: 2rem; border-radius: 15px; margin-top: 2rem; 
            text-align: center; color: white;">
    <h3 style="margin: 0; color: #ecf0f1;">🚦 TrafficOps+ - Smart City Solution</h3>
    <p style="margin: 0.5rem 0; opacity: 0.8;">Real-time Traffic Management • Emergency Response • Environmental Monitoring</p>
    <div style="margin-top: 1rem;">
        <span style="background: #3498db; padding: 0.5rem 1rem; border-radius: 20px; margin: 0 0.5rem; display: inline-block;">
            🚗 Vehicle Detection
        </span>
        <span style="background: #e74c3c; padding: 0.5rem 1rem; border-radius: 20px; margin: 0 0.5rem; display: inline-block;">
            🚨 Emergency Response
        </span>
        <span style="background: #2ecc71; padding: 0.5rem 1rem; border-radius: 20px; margin: 0 0.5rem; display: inline-block;">
            🌍 Air Quality
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# Live loop for video display
while True:
    if running:
        with frame_lock:
            if latest_frame is not None:
                frame_display.image(latest_frame, channels="RGB")

    time.sleep(0.05)
