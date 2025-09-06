import numpy as np
import matplotlib
matplotlib.use("TkAgg")  # works if tk installed, else use "QtAgg"
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
from matplotlib.animation import FuncAnimation
import random

WIDTH, HEIGHT = 40, 20
NUM_CARS = 20
DT = 0.03
FPS = 25

CAR_COLOR = "#1f77b4"
AMB_COLOR = "#d62728"
CAR_LENGTH, CAR_WIDTH = 1.0, 0.5
AMB_LENGTH, AMB_WIDTH = 1.2, 0.6
BUBBLE_ALPHA = 0.25
CAR_RADIUS = 0.5
AMB_RADIUS = 2.0
MAX_SPEED = 0.5
AMB_SPEED = 1.0
FORCE_GAIN = 0.5 

roads = [
    {'start':[2,4], 'end':[38,4]},   # horizontal bottom
    {'start':[2,10], 'end':[38,10]}, # horizontal middle
    {'start':[2,16], 'end':[38,16]}, # horizontal top
    {'start':[10,2], 'end':[10,18]}, # vertical left
    {'start':[25,2], 'end':[25,18]}, # vertical right
]

class Car:
    def _init_(self, road):  # FIXED constructor
        self.road = road
        self.start = np.array(road['start'])
        self.end = np.array(road['end'])
        # position along road + small lateral offset in lane
        self.pos = self.start + random.uniform(0,1)*(self.end - self.start)
        self.radius = CAR_RADIUS
        self.speed = MAX_SPEED
        dir_vec = self.end - self.start
        self.vel = dir_vec / np.linalg.norm(dir_vec) * self.speed

    def update(self, ambulances):
        road_dir = (self.end - self.start)/np.linalg.norm(self.end - self.start)
        perp_dir = np.array([-road_dir[1], road_dir[0]])
        force = np.zeros(2)
        for amb in ambulances:
            offset = self.pos - amb.pos
            dist = np.linalg.norm(offset)
            if dist < (self.radius + amb.radius):
                if dist < 0.1:
                    dist = 0.1
                force += perp_dir*(np.dot(perp_dir, offset)/dist)*FORCE_GAIN

        self.vel += force*DT
        speed = np.linalg.norm(self.vel)
        if speed > self.speed:
            self.vel = self.vel / speed * self.speed

        self.pos += self.vel*DT

        along = np.dot(self.pos - self.start, road_dir)
        along = np.clip(along, 0, np.linalg.norm(self.end - self.start))
        lateral = np.dot(self.pos - self.start, perp_dir)
        self.pos = self.start + along*road_dir + lateral*perp_dir

class Ambulance:
    def _init_(self, road, start_frac=0.0):  # FIXED constructor
        self.road = road
        self.start = np.array(road['start'])
        self.end = np.array(road['end'])
        self.pos = self.start + start_frac*(self.end - self.start)
        self.radius = AMB_RADIUS
        self.speed = AMB_SPEED
        self.dir_vec = self.end - self.start
        self.vel = self.dir_vec / np.linalg.norm(self.dir_vec) * self.speed

    def update(self):
        self.pos += self.vel*DT
        if np.linalg.norm(self.pos - self.start) < 0.1 or np.linalg.norm(self.pos - self.end) < 0.1:
            self.vel *= -1

ambulance = Ambulance(roads[1], start_frac=0.2)
ambulances = [ambulance]

cars = []
for _ in range(NUM_CARS):
    road = random.choice(roads)
    cars.append(Car(road))

agents = cars + ambulances

fig, ax = plt.subplots(figsize=(12,6))
ax.set_xlim(0, WIDTH)
ax.set_ylim(0, HEIGHT)
ax.set_aspect('equal')
ax.set_title("TrafficOS: Cars move on roads and avoid ambulance")

# draw roads
for road in roads:
    ax.plot([road['start'][0], road['end'][0]],
            [road['start'][1], road['end'][1]],
            color='gray', linewidth=4, zorder=0)

bubble_patches=[]
rect_patches=[]
for ag in agents:
    bubble = Circle((ag.pos[0], ag.pos[1]), ag.radius,
                    color=AMB_COLOR if ag in ambulances else CAR_COLOR, alpha=BUBBLE_ALPHA)
    rect = Rectangle((ag.pos[0]-CAR_LENGTH/2, ag.pos[1]-CAR_WIDTH/2),
                     CAR_LENGTH, CAR_WIDTH,
                     color=AMB_COLOR if ag in ambulances else CAR_COLOR)
    ax.add_patch(bubble)
    ax.add_patch(rect)
    bubble_patches.append(bubble)
    rect_patches.append(rect)

def update(frame):
    ambulance.update()
    for car in cars:
        car.update(ambulances)
    for i, ag in enumerate(agents):
        bubble_patches[i].center = (ag.pos[0], ag.pos[1])
        rect_patches[i].set_xy((ag.pos[0]-CAR_LENGTH/2, ag.pos[1]-CAR_WIDTH/2))
    return bubble_patches + rect_patches

ani = FuncAnimation(fig, update, frames=1000, interval=1000/FPS, blit=False, repeat=True)
plt.show(block=True)
from ultralytics import YOLO
import cv2
import numpy as np

# Load YOLOv8 small model
model = YOLO("yolov8s.pt")

# Open webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
    exit()

# Function to detect red/blue lights (siren simulation)
def detect_siren(vehicle_roi):
    hsv = cv2.cvtColor(vehicle_roi, cv2.COLOR_BGR2HSV)
    # Red range
    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170,120,70])
    upper_red2 = np.array([180,255,255])
    # Blue range
    lower_blue = np.array([100,150,0])
    upper_blue = np.array([140,255,255])

    mask_red = cv2.inRange(hsv, lower_red1, upper_red1) + cv2.inRange(hsv, lower_red2, upper_red2)
    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
    
    red_pixels = cv2.countNonZero(mask_red)
    blue_pixels = cv2.countNonZero(mask_blue)

    if red_pixels > 50 or blue_pixels > 50:
        return True
    return False

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame)
    annotated_frame = results[0].plot()
    boxes = results[0].boxes

    for box, cls in zip(boxes.xyxy, boxes.cls.cpu().numpy()):
        x1, y1, x2, y2 = map(int, box)
        label = results[0].names[int(cls)]

        if label == "person":
            print("🚶 Pedestrian detected → Trigger crosswalk phase")
            cv2.putText(annotated_frame, "Pedestrian", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

        elif label in ["bicycle", "motorcycle"]:
            print("🚲 Non-motorized vehicle detected")
            cv2.putText(annotated_frame, "Non-motorized", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,0), 2)

        elif label in ["car", "bus", "truck"]:
            vehicle_roi = frame[y1:y2, x1:x2]
            if detect_siren(vehicle_roi):
                print("🚑 Emergency vehicle detected → Extend green +30s")
                cv2.putText(annotated_frame, "Emergency Vehicle", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)

    cv2.imshow("TrafficOps+ Live Camera MVP", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
