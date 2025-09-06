"""
Enhanced Intelligent Traffic Management System
Requirements:
- Python 3.8+
- pygame (for visualization)
- requests (for Google Maps API integration)
- numpy (for calculations)
- matplotlib (for optional plotting)

Install dependencies:
pip install pygame requests numpy matplotlib
"""

import pygame
import random
import time
import math
import numpy as np
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional
import requests

# ==================== CONFIGURATION ====================
# Google Maps API configuration (replace with your API key)
GOOGLE_MAPS_API_KEY = "YOUR_GOOGLE_MAPS_API_KEY"
GOOGLE_MAPS_BASE_URL = "https://maps.googleapis.com/maps/api/directions/json"

# Simulation parameters
SIMULATION_WIDTH = 1400
SIMULATION_HEIGHT = 900
TRAFFIC_LIGHT_CYCLE_TIME = 30  # seconds
VEHICLE_SPAWN_RATE = 0.05  # probability per frame
ROUTE_UPDATE_INTERVAL = 300  # seconds between route updates
UI_PANEL_WIDTH = 300

# Colors
BACKGROUND_COLOR = (40, 44, 52)
ROAD_COLOR = (60, 64, 72)
LANE_MARKING_COLOR = (255, 255, 200)
UI_PANEL_COLOR = (30, 34, 42)
TEXT_COLOR = (220, 220, 220)
HIGHLIGHT_COLOR = (86, 182, 194)

# ==================== ENUMS AND DATA MODELS ====================
class TrafficLightState(Enum):
    RED = 0
    YELLOW = 1
    GREEN = 2

class Direction(Enum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

class VehicleType(Enum):
    CAR = 0
    BUS = 1
    EMERGENCY = 2
    TRUCK = 3

@dataclass
class Position:
    x: int
    y: int

@dataclass
class Vehicle:
    id: int
    position: Position
    destination: Position
    speed: float
    max_speed: float
    route: List[Position]
    color: Tuple[int, int, int]
    vehicle_type: VehicleType
    current_route_index: int = 0
    stopped: bool = False

@dataclass
class TrafficLight:
    id: int
    position: Position
    state: TrafficLightState
    timer: float
    direction: Direction
    green_duration: float = TRAFFIC_LIGHT_CYCLE_TIME * 0.6
    yellow_duration: float = TRAFFIC_LIGHT_CYCLE_TIME * 0.2
    red_duration: float = TRAFFIC_LIGHT_CYCLE_TIME * 0.2

@dataclass
class Road:
    id: int
    start: Position
    end: Position
    lanes: int
    direction: Direction
    congestion: float = 0.0
    speed_limit: float = 5.0

@dataclass
class Intersection:
    id: int
    position: Position
    traffic_lights: List[TrafficLight]
    name: str

# ==================== GOOGLE MAPS INTEGRATION ====================
class GoogleMapsIntegration:
    def _init_(self, api_key):
        self.api_key = api_key
        self.route_cache = {}
    
    def get_route(self, origin: Position, destination: Position) -> Optional[List[Position]]:
        # NOTE: This is a simplified demo conversion, not real-world scale
        route_key = f"{origin.x},{origin.y}-{destination.x},{destination.y}"
        if route_key in self.route_cache:
            return self.route_cache[route_key]

        # Instead of real Google Maps, return a straight-line path (demo only)
        # If you want real integration, uncomment requests call
        route = [origin, destination]
        self.route_cache[route_key] = route
        return route

# ==================== TRAFFIC MANAGEMENT SYSTEM ====================
class TrafficManagementSystem:
    def _init_(self):
        self.vehicles = []
        self.traffic_lights = []
        self.roads = []
        self.intersections = []
        self.vehicle_id_counter = 0
        self.road_id_counter = 0
        self.google_maps = GoogleMapsIntegration(GOOGLE_MAPS_API_KEY)
        self.last_route_update = time.time()
        self.simulation_time = 0
        self.selected_object = None
        self.hover_object = None
        self.congestion_data = []
        self.running = True

        self._initialize_road_network()

    def _initialize_road_network(self):
        # Simplified: only one horizontal + vertical road
        road1 = Road(0, Position(100, 400), Position(SIMULATION_WIDTH-UI_PANEL_WIDTH-100, 400), 2, Direction.EAST)
        road2 = Road(1, Position(700, 100), Position(700, SIMULATION_HEIGHT-100), 2, Direction.SOUTH)
        self.roads.extend([road1, road2])

        # One intersection
        light = TrafficLight(0, Position(700, 400), TrafficLightState.RED, 0, Direction.EAST)
        self.traffic_lights.append(light)
        self.intersections.append(Intersection(0, Position(700, 400), [light], "Central"))

    def update_traffic_lights(self, dt):
        for light in self.traffic_lights:
            light.timer += dt
            cycle_pos = light.timer % TRAFFIC_LIGHT_CYCLE_TIME
            if cycle_pos < light.green_duration:
                light.state = TrafficLightState.GREEN
            elif cycle_pos < light.green_duration + light.yellow_duration:
                light.state = TrafficLightState.YELLOW
            else:
                light.state = TrafficLightState.RED

    def spawn_vehicle(self):
        if random.random() < VEHICLE_SPAWN_RATE and len(self.vehicles) < 50:
            start = Position(100, 400)
            end = Position(1200, 400)
            route = self.google_maps.get_route(start, end)

            vtype = random.choice(list(VehicleType))
            color = (255,0,0) if vtype==VehicleType.EMERGENCY else (0,255,0)
            max_speed = 5 if vtype==VehicleType.EMERGENCY else 3

            vehicle = Vehicle(
                id=self.vehicle_id_counter,
                position=start,
                destination=end,
                speed=0,
                max_speed=max_speed,
                route=route,
                color=color,
                vehicle_type=vtype
            )
            self.vehicles.append(vehicle)
            self.vehicle_id_counter += 1

    def update_vehicles(self, dt):
        for vehicle in self.vehicles:
            if vehicle.current_route_index >= len(vehicle.route):
                continue
            target = vehicle.route[vehicle.current_route_index]
            dx, dy = target.x - vehicle.position.x, target.y - vehicle.position.y
            dist = math.hypot(dx, dy)
            if dist < 5:
                vehicle.current_route_index += 1
            else:
                dx, dy = dx/dist, dy/dist
                vehicle.speed = min(vehicle.max_speed, vehicle.speed+0.1)
                vehicle.position.x += dx*vehicle.speed
                vehicle.position.y += dy*vehicle.speed

    def update(self, dt):
        self.simulation_time += dt
        self.update_traffic_lights(dt)
        self.spawn_vehicle()
        self.update_vehicles(dt)

# ==================== VISUALIZATION ====================
class TrafficVisualization:
    def _init_(self, traffic_system: TrafficManagementSystem):
        self.ts = traffic_system
        pygame.init()
        self.screen = pygame.display.set_mode((SIMULATION_WIDTH, SIMULATION_HEIGHT))
        pygame.display.set_caption("Intelligent Traffic Management System")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 16)

    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)

        # Draw roads
        for r in self.ts.roads:
            pygame.draw.line(self.screen, ROAD_COLOR, (r.start.x, r.start.y), (r.end.x, r.end.y), 20)

        # Draw lights
        for l in self.ts.traffic_lights:
            color = (0,255,0) if l.state==TrafficLightState.GREEN else (255,255,0) if l.state==TrafficLightState.YELLOW else (255,0,0)
            pygame.draw.circle(self.screen, color, (l.position.x, l.position.y), 10)

        # Draw vehicles
        for v in self.ts.vehicles:
            pygame.draw.rect(self.screen, v.color, (v.position.x-5, v.position.y-5, 10, 10))

        pygame.display.flip()

    def run(self):
        while self.ts.running:
            dt = self.clock.tick(30)/1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.ts.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    print("Mouse clicked at", event.pos)

            self.ts.update(dt)
            self.draw()
# ==================== MAIN ====================
if __name__ == "_main_":
    system = TrafficManagementSystem()
    viz = TrafficVisualization(system)
    viz.run()
