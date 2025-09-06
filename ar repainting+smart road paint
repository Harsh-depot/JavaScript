import json
import time
import random
import cv2
import numpy as np

# ----------------------------
# MQTT safe import (optional)
# ----------------------------
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    print("[INFO] paho-mqtt not installed. MQTT features disabled.")
    MQTT_AVAILABLE = False


# ----------------------------
# Config
# ----------------------------
ROAD_SEGMENTS = {
    "seg_1": {"center": (100, 200), "orientation": 0},
    "seg_2": {"center": (300, 200), "orientation": 0},
    "seg_3": {"center": (500, 200), "orientation": 0},
}

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_BASE_TOPIC = "road/segment"


# ----------------------------
# MQTT Client (only if available)
# ----------------------------
if MQTT_AVAILABLE:
    client = mqtt.Client()
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        print("[INFO] Connected to MQTT broker.")
    except Exception as e:
        print(f"[WARN] Could not connect to MQTT broker: {e}")
        MQTT_AVAILABLE = False


def publish_signal(segment_id, state):
    """Publish to MQTT or print to console."""
    payload = {"segment": segment_id, "state": state, "ts": time.time()}
    if MQTT_AVAILABLE:
        topic = f"{MQTT_BASE_TOPIC}/{segment_id}/signal"
        client.publish(topic, json.dumps(payload))
    print("[SIGNAL]", payload)


# ----------------------------
# Simulation: ambulance movement
# ----------------------------
def simulate_ambulance_position():
    """Fake ambulance positions across road segments"""
    while True:
        seg = random.choice(list(ROAD_SEGMENTS.keys()))
        yield seg
        time.sleep(2)


# ----------------------------
# Visualization: AR overlay
# ----------------------------
def draw_overlay(active_segment):
    """Draw AR-like overlay showing emergency lane"""
    frame = np.zeros((400, 600, 3), dtype=np.uint8)

    # Draw road segments
    for seg_id, data in ROAD_SEGMENTS.items():
        x, y = data["center"]
        color = (50, 50, 50)  # normal road
        if seg_id == active_segment:
            color = (0, 0, 255)  # highlight in red
        cv2.rectangle(frame, (x - 80, y - 40), (x + 80, y + 40), color, -1)
        cv2.putText(frame, seg_id, (x - 30, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # AR text overlay
    if active_segment:
        cv2.putText(
            frame,
            f"Emergency Lane Active: {active_segment}",
            (50, 350),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )

    cv2.imshow("Dynamic Lane Repainting (AR Simulation)", frame)


# ----------------------------
# Main loop
# ----------------------------
if __name__ == "__main__":  # ✅ fixed
    ambulance_positions = simulate_ambulance_position()
    for seg in ambulance_positions:
        publish_signal(seg, "EMERGENCY_LEFT")
        for _ in range(10):  # update display for ~1 second
            draw_overlay(seg)
            if cv2.waitKey(100) & 0xFF == 27:  # ESC to quit
                cv2.destroyAllWindows()
                exit(0)
