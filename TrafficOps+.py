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
import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
try:
    import librosa
    import soundfile as sf
    from scipy import signal
    from scipy.fft import fft, fftfreq
    AUDIO_ANALYSIS_AVAILABLE = True
except ImportError:
    print("Audio analysis libraries not available. Install with: pip install librosa soundfile scipy")
    AUDIO_ANALYSIS_AVAILABLE = False
    # Create dummy functions
    def librosa_load(*args, **kwargs):
        return None, None
    def fft(*args, **kwargs):
        return None
    def fftfreq(*args, **kwargs):
        return None

import re
from pollutyion import get_pollution_data

def get_weather_data():
    # Use simulated pollution data instead of API
    return get_pollution_data()

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
audio_siren_detected = False
emergency_vehicle_types = {"ambulance": 0, "fire_truck": 0, "police": 0, "emergency": 0}

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

def detect_siren_lights(frame, x1, y1, x2, y2):
    """Detect red and blue siren lights on the TOP of vehicles - simple percentage-based approach"""
    roi = frame[int(y1):int(y2), int(x1):int(x2)]
    if roi.size == 0:
        return False, False
    
    # Focus on the TOP 25% of the vehicle where siren lights are located
    top_roi_height = int(roi.shape[0] * 0.25)  # Top 25% of vehicle
    top_roi = roi[0:top_roi_height, :]  # Only analyze top portion
    
    if top_roi.size == 0:
        return False, False
    
    # Convert to HSV for better color detection
    hsv = cv2.cvtColor(top_roi, cv2.COLOR_BGR2HSV)
    
    # Red color detection - broader range for daylight conditions
    red_lower1 = np.array([0, 50, 50])    # Lower thresholds for daylight
    red_upper1 = np.array([10, 255, 255])
    red_lower2 = np.array([170, 50, 50])
    red_upper2 = np.array([180, 255, 255])
    
    red_mask1 = cv2.inRange(hsv, red_lower1, red_upper1)
    red_mask2 = cv2.inRange(hsv, red_lower2, red_upper2)
    red_mask = red_mask1 + red_mask2
    
    # Blue color detection - broader range for daylight conditions
    blue_lower = np.array([100, 50, 50])  # Lower thresholds for daylight
    blue_upper = np.array([130, 255, 255])
    blue_mask = cv2.inRange(hsv, blue_lower, blue_upper)
    
    # Calculate color percentages in the top portion
    red_pixels = cv2.countNonZero(red_mask)
    blue_pixels = cv2.countNonZero(blue_mask)
    total_pixels = top_roi.shape[0] * top_roi.shape[1]
    
    red_percentage = red_pixels / total_pixels
    blue_percentage = blue_pixels / total_pixels
    combined_percentage = red_percentage + blue_percentage
    
    # Simple threshold: if top 25% has 20-30% red and blue pixels, it's likely a siren
    red_siren = red_percentage >= 0.20  # 20% red threshold
    blue_siren = blue_percentage >= 0.20  # 20% blue threshold
    
    # Combined threshold: total red+blue should be 20-30%
    is_emergency_colors = 0.20 <= combined_percentage <= 0.30
    
    print(f"Top region analysis: red={red_percentage:.2f}, blue={blue_percentage:.2f}, combined={combined_percentage:.2f}, emergency_colors={is_emergency_colors}")
    
    return red_siren or is_emergency_colors, blue_siren or is_emergency_colors

def detect_ambulance_text(roi):
    """Detect red 'AMBULANCE' text on the vehicle"""
    # Convert to HSV for better color detection
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    
    # Red color detection for "AMBULANCE" text
    red_lower1 = np.array([0, 50, 50])
    red_upper1 = np.array([10, 255, 255])
    red_lower2 = np.array([170, 50, 50])
    red_upper2 = np.array([180, 255, 255])
    
    red_mask1 = cv2.inRange(hsv, red_lower1, red_upper1)
    red_mask2 = cv2.inRange(hsv, red_lower2, red_upper2)
    red_mask = red_mask1 + red_mask2
    
    # Find contours in the red mask
    contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Look for text-like rectangular regions in red
    text_regions = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = w / h if h > 0 else 0
        area = cv2.contourArea(contour)
        
        # Look for horizontal text regions (AMBULANCE is written horizontally)
        if (3 < aspect_ratio < 15 and  # Wide aspect ratio for text
            w > 40 and h > 10 and      # Minimum size for readable text
            area > 300):               # Minimum area
            text_regions.append((x, y, w, h))
    
    # If we find multiple horizontal red regions, likely "AMBULANCE" text
    return len(text_regions) >= 1  # Lowered threshold since we're looking for red text specifically

def detect_star_of_life(roi):
    """Detect Star of Life symbol with stricter criteria"""
    # Convert to grayscale
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # Apply edge detection
    edges = cv2.Canny(gray, 50, 150)
    
    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Look for star-like shapes with stricter criteria
    for contour in contours:
        approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        # Stricter criteria for Star of Life
        if (len(approx) >= 6 and  # Star of Life has 6 points
            area > 300 and         # Larger minimum area
            perimeter > 50 and     # Minimum perimeter
            area / (perimeter * perimeter) > 0.1):  # Compactness check
            return True
    
    return False

def detect_emergency_vehicle_advanced(frame, x1, y1, x2, y2, vehicle_type="truck"):
    """Enhanced emergency vehicle detection: siren lights + red AMBULANCE text"""
    roi = frame[int(y1):int(y2), int(x1):int(x2)]
    if roi.size == 0:
        return False, "unknown"
    
    # 1. Siren light detection in top portion
    red_siren, blue_siren = detect_siren_lights(frame, x1, y1, x2, y2)
    
    # 2. Red "AMBULANCE" text detection throughout the vehicle
    has_ambulance_text = detect_ambulance_text(roi)
    
    # 3. Decision logic
    if red_siren or blue_siren:
        # Determine vehicle type based on siren colors
        if red_siren and blue_siren:
            vehicle_class = "ambulance"  # Both red and blue = ambulance
        elif red_siren:
            vehicle_class = "fire_truck"  # Only red = fire truck
        elif blue_siren:
            vehicle_class = "police"  # Only blue = police
        else:
            vehicle_class = "emergency"  # Fallback
        
        print(f"Emergency vehicle detected: {vehicle_class} (red_siren={red_siren}, blue_siren={blue_siren}, ambulance_text={has_ambulance_text})")
        return True, vehicle_class
    
    # 4. Check for red "AMBULANCE" text even without siren lights
    elif has_ambulance_text:
        print(f"Ambulance detected by text: AMBULANCE text found")
        return True, "ambulance"
    
    # 5. No emergency indicators = regular vehicle
    return False, "regular"

def extract_audio_from_video(video_source, duration=1.0):
    """Extract audio from video source for siren detection"""
    if not AUDIO_ANALYSIS_AVAILABLE:
        print("Audio analysis not available - install required libraries")
        return None
        
    try:
        # For camera input, we can't easily extract audio
        if isinstance(video_source, int):
            print("Camera input detected - audio analysis disabled")
            return None
        
        # For video files, try to extract audio
        if isinstance(video_source, str):
            # Check if it's a local file
            if video_source.endswith(('.mp4', '.avi', '.mov', '.mkv', '.mpg', '.mpeg', '.wmv', '.flv')):
                try:
                    print(f"Attempting to extract audio from: {video_source}")
                    # Use librosa to load audio
                    audio_data, sample_rate = librosa.load(video_source, duration=duration, sr=22050)
                    print(f"Audio extracted successfully - {len(audio_data)} samples at {sample_rate}Hz")
                    return audio_data, sample_rate
                except Exception as e:
                    print(f"Failed to extract audio from video file: {e}")
                    return None
            # Check if it's a URL (YouTube, etc.)
            elif video_source.startswith(('http://', 'https://')):
                print("URL detected - audio analysis disabled for streaming sources")
                return None
            else:
                print(f"Unknown file type: {video_source}")
                return None
        
        print(f"Unsupported video source type: {type(video_source)}")
        return None
    except Exception as e:
        print(f"Audio extraction error: {e}")
        return None

def analyze_audio_for_siren(audio_data, sample_rate=22050):
    """Analyze audio data for siren sounds"""
    if not AUDIO_ANALYSIS_AVAILABLE:
        return False
        
    if audio_data is None or len(audio_data) == 0:
        return False
    
    try:
        # Convert to numpy array if needed
        if hasattr(audio_data, 'numpy'):
            audio_data = audio_data.numpy()
        
        # Ensure we have audio data
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        # Apply FFT to get frequency spectrum
        fft_data = fft(audio_data)
        freqs = fftfreq(len(audio_data), 1/sample_rate)
        
        # Siren frequencies typically range from 200-2000 Hz
        siren_freq_range = (freqs >= 200) & (freqs <= 2000)
        siren_power = np.sum(np.abs(fft_data[siren_freq_range])**2)
        total_power = np.sum(np.abs(fft_data)**2)
        
        # Calculate siren power ratio
        siren_ratio = siren_power / total_power if total_power > 0 else 0
        
        # Detect siren based on power in siren frequency range
        return siren_ratio > 0.1  # 10% threshold
        
    except Exception as e:
        print(f"Audio analysis error: {e}")
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
    global audio_siren_detected, emergency_vehicle_types

    cap = cv2.VideoCapture(video_source)

    if not cap.isOpened():
        st.error("⚠️ Cannot open video source.")
        running = False
        return

    # Try to extract audio for siren detection
    audio_result = extract_audio_from_video(video_source)
    if audio_result is not None:
        audio_data, sample_rate = audio_result
        audio_analysis_enabled = True
    else:
        audio_data, sample_rate = None, None
        audio_analysis_enabled = False

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
        
        # Reset emergency vehicle type counts
        emergency_vehicle_types = {"ambulance": 0, "fire_truck": 0, "police": 0, "emergency": 0}
        
        # Audio analysis for siren detection (every 30 frames to avoid performance issues)
        if audio_analysis_enabled and audio_data is not None and cap.get(cv2.CAP_PROP_POS_FRAMES) % 30 == 0:
            try:
                audio_siren_detected = analyze_audio_for_siren(audio_data, sample_rate)
            except:
                audio_siren_detected = False
        else:
            audio_siren_detected = False

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
                    
                    # Advanced emergency vehicle detection
                    is_emergency, vehicle_class = detect_emergency_vehicle_advanced(frame, x1, y1, x2, y2, label)
                    
                    if is_emergency:
                        emergency_count += 1
                        emergency_detected = True
                        emergency_vehicle_types[vehicle_class] += 1
                        
                        # Determine vehicle-specific styling and emoji
                        if vehicle_class == "ambulance":
                            emoji = "🚑"
                            color = (0, 0, 255)  # Red
                            text_color = (0, 0, 255)
                        elif vehicle_class == "fire_truck":
                            emoji = "🚒"
                            color = (0, 0, 255)  # Red
                            text_color = (0, 0, 255)
                        elif vehicle_class == "police":
                            emoji = "🚔"
                            color = (255, 0, 0)  # Blue
                            text_color = (255, 0, 0)
                        else:
                            emoji = "🚨"
                            color = (0, 255, 255)  # Yellow
                            text_color = (0, 255, 255)
                        
                        # Draw emergency vehicle with special styling
                        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 4)
                        
                        # Add audio confirmation indicator
                        audio_indicator = " 🔊" if audio_siren_detected else ""
                        cv2.putText(frame, f"{emoji} {vehicle_class.upper()}{audio_indicator} {conf:.2f}",
                                    (int(x1), int(y1) - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2)
                        
                        # Draw flashing effect with pulsing animation
                        center_x, center_y = int((x1+x2)/2), int((y1+y2)/2)
                        pulse_radius = int(25 + 10 * np.sin(time.time() * 8))  # Pulsing effect
                        cv2.circle(frame, (center_x, center_y), pulse_radius, color, 3)
                        
                        # Add siren light indicators
                        red_siren, blue_siren = detect_siren_lights(frame, x1, y1, x2, y2)
                        if red_siren:
                            cv2.circle(frame, (int(x1) + 10, int(y1) + 10), 8, (0, 0, 255), -1)
                        if blue_siren:
                            cv2.circle(frame, (int(x2) - 10, int(y1) + 10), 8, (255, 0, 0), -1)
                        
                        # Add AMBULANCE text indicator
                        roi = frame[int(y1):int(y2), int(x1):int(x2)]
                        has_ambulance_text = detect_ambulance_text(roi)
                        if has_ambulance_text:
                            cv2.putText(frame, "AMBULANCE TEXT", (int(x1), int(y2) + 20),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                        
                        # Draw the top region being analyzed for siren lights
                        top_region_height = int((y2 - y1) * 0.25)  # Top 25% of vehicle
                        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y1 + top_region_height)), (255, 255, 0), 2)
                        cv2.putText(frame, "SIREN ZONE (25%)", (int(x1), int(y1 + top_region_height + 15)),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
                        
                        # Add audio siren indicator
                        if audio_siren_detected:
                            cv2.circle(frame, (center_x, int(y2) - 10), 6, (255, 255, 0), -1)  # Yellow dot for audio
                        
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

        # Enhanced status text with detailed emergency info
        status_text = f"Vehicles: {vehicle_count} | Pedestrians: {pedestrian_count} | Emergencies: {emergency_count}"
        
        # Add detailed emergency vehicle breakdown
        if emergency_count > 0:
            emergency_details = []
            for vehicle_type, count in emergency_vehicle_types.items():
                if count > 0:
                    emoji_map = {"ambulance": "🚑", "fire_truck": "🚒", "police": "🚔", "emergency": "🚨"}
                    emergency_details.append(f"{emoji_map[vehicle_type]} {count}")
            if emergency_details:
                status_text += f" | {' '.join(emergency_details)}"
        
        if hotspot_zone:
            status_text += f" | 🚩 {hotspot_zone} (AQI {aqi_level})"
        if emergency_detected:
            status_text += " | 🚨 EMERGENCY DETECTED"
        if audio_siren_detected:
            status_text += " | 🔊 SIREN AUDIO DETECTED"

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
                
                # Emergency metric with detailed breakdown
                emergency_details_html = ""
                if emergency_count > 0:
                    for vehicle_type, count in emergency_vehicle_types.items():
                        if count > 0:
                            emoji_map = {"ambulance": "🚑", "fire_truck": "🚒", "police": "🚔", "emergency": "🚨"}
                            emergency_details_html += f"<div style='font-size: 0.8rem; color: #666; margin: 0.2rem 0;'>{emoji_map[vehicle_type]} {vehicle_type.replace('_', ' ').title()}: {count}</div>"
                
                emergency_metric.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">🚨 {emergency_count}</div>
                    <div class="metric-label">Emergency Vehicles</div>
                    {emergency_details_html}
                    {f"<div style='font-size: 0.8rem; color: #ff6b6b; margin: 0.2rem 0;'>🔊 Audio Siren Detected</div>" if audio_siren_detected else ""}
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
    pollution_details = st.empty()

    # Always show pollution metrics, regardless of running state
    pollution_data = get_pollution_data()
    aqi_value = pollution_data["AQI"]
    aqi_color = "red" if aqi_value > 150 else "orange" if aqi_value > 100 else "green"
    hotspot_label = hotspot_zone if hotspot_zone else "General Zone"

    pollution_metric.markdown(f"""
    <div class="metric-card" style="border-left-color: {aqi_color};">
        <div class="metric-value" style="color: {aqi_color};">🌍 {aqi_value}</div>
        <div class="metric-label">{hotspot_label}</div>
        <div style="margin-top: 1rem;">
            <div style="background: #e9ecef; border-radius: 10px; height: 20px; overflow: hidden;">
                <div style="background: linear-gradient(90deg, #2ed573, #ffa502, #ff4757); 
                            height: 100%; width: {min(aqi_value/300*100, 100)}%; 
                            border-radius: 10px; transition: width 0.5s ease;"></div>
            </div>
            <small style="color: #6c757d;">AQI Level: {aqi_value}</small>
        </div>
    </div>
    """, unsafe_allow_html=True)

    pollution_details.markdown(f"""
    <div class="metric-card" style="border-left-color: #764ba2;">
        <div class="metric-label">Detailed Pollution Metrics</div>
        <ul style="list-style:none; padding-left:0; font-size:1.1rem;">
            <li>CO (ppm): <strong>{pollution_data['CO (ppm)']}</strong></li>
            <li>NO₂ (ppm): <strong>{pollution_data['NO2 (ppm)']}</strong></li>
            <li>SO₂ (ppm): <strong>{pollution_data['SO2 (ppm)']}</strong></li>
            <li>PM2.5 (µg/m³): <strong>{pollution_data['PM2.5 (µg/m³)']}</strong></li>
            <li>PM10 (µg/m³): <strong>{pollution_data['PM10 (µg/m³)']}</strong></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Emergency alerts with stunning design
emergency_alert = st.empty()
pedestrian_alert = st.empty()

if running:
    with frame_lock:
        if latest_frame is not None:
            if emergency_detected:
                # Create detailed emergency alert
                emergency_breakdown = []
                for vehicle_type, count in emergency_vehicle_types.items():
                    if count > 0:
                        emoji_map = {"ambulance": "🚑", "fire_truck": "🚒", "police": "🚔", "emergency": "🚨"}
                        emergency_breakdown.append(f"{emoji_map[vehicle_type]} {count}")
                
                emergency_breakdown_text = " | ".join(emergency_breakdown)
                audio_indicator = " + 🔊 AUDIO SIREN" if audio_siren_detected else ""
                
                emergency_alert.markdown(f"""
                <div class="emergency-alert">
                    <h4 style="margin: 0; font-size: 1.5rem;">🚨 EMERGENCY VEHICLE DETECTED!</h4>
                    <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem;">{emergency_breakdown_text}{audio_indicator}</p>
                    <p style="margin: 0.5rem 0 0 0; font-size: 1rem;">All lanes cleared for emergency passage</p>
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
