# 🚦 TrafficOps+ - Smart City Traffic Management System

**Safer, Greener City Traffic Playbook** - A comprehensive real-time traffic management solution powered by computer vision and AI.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Latest-green.svg)](https://ultralytics.com)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-orange.svg)](https://opencv.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🌟 Overview

TrafficOps+ is an advanced traffic management system that goes beyond simple vehicle counting to address real city pain points:

- **🚨 Emergency Vehicle Detection** - Automatic detection and priority routing for ambulances, fire trucks, and police vehicles
- **🚶 Pedestrian Safety** - Smart crosswalk timing based on pedestrian density
- **🌍 Environmental Monitoring** - Real-time AQI tracking and pollution hotspot detection
- **🚦 Smart Traffic Control** - Dynamic lane allocation and virtual traffic light system
- **📊 Real-time Analytics** - Live metrics, visualizations, and traffic insights

## 🎯 Key Features

### 🚨 Emergency Response System
- **Multi-layer Detection**: Color analysis, shape recognition, and text detection
- **Automatic Lane Clearing**: Emergency vehicles get priority access
- **Route Optimization**: Real-time route suggestions for emergency services
- **Visual Alerts**: Flashing indicators and emergency notifications

### 🚶 Pedestrian Safety
- **Crosswalk Detection**: Identifies pedestrians waiting at intersections
- **Adaptive Timing**: Adjusts signal timing based on pedestrian density
- **Safety Metrics**: Tracks pedestrian-vehicle interactions

### 🌍 Environmental Impact
- **Pollution Monitoring**: Real-time AQI calculation and display, now with detailed metrics for CO, NO₂, SO₂, PM2.5, and PM10.
- **Hotspot Detection**: Identifies high-pollution areas near hospitals and schools.
- **Emission Tracking**: Monitors vehicle idling and congestion patterns.
- **Live Pollution Data Simulation**: Uses `pollutyion.py` to simulate sensor readings for development and testing.

---

## 🆕 Recent Updates

- **Integrated live pollution metrics** (AQI, CO, NO₂, SO₂, PM2.5, PM10) into the dashboard.
- **Pollution metrics are always visible** in the Air Quality Monitor section, regardless of detection state.
- **Added `pollutyion.py`**: Simulates pollution sensor data for AQI and gas concentrations.
- **Enhanced dashboard UI**: Displays detailed air quality metrics with improved visuals.
- **Modular integration**: Pollution data can be used independently or with traffic detection.

---

## 🧪 Pollution Data Simulation

The `pollutyion.py` module provides simulated pollution sensor data for development and testing.

**Usage:**
```python
from pollutyion import get_pollution_data

data = get_pollution_data()
print(data)  # {'AQI': ..., 'CO (ppm)': ..., ...}
```

**Standalone Simulation:**
```bash
python pollutyion.py
```
This will print random pollution metrics every 2 seconds.

---

## 🚀 Quick Start (Updated)

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the dashboard**
   ```bash
   streamlit run trf2.py
   ```

3. **(Optional) Run pollution sensor simulation**
   ```bash
   python pollutyion.py
   ```

---

## 📁 File Structure (Updated)

- `trf2.py` — Main dashboard and traffic detection logic (now includes live pollution metrics)
- `pollutyion.py` — Pollution sensor simulator and data provider

---

## 📝 How It Works (Environmental Monitoring)

- The dashboard fetches pollution metrics using `get_pollution_data()` from `pollutyion.py`.
- Metrics for AQI, CO, NO₂, SO₂, PM2.5, and PM10 are displayed in the Air Quality Monitor section.
- Pollution metrics update independently from traffic detection and are always visible.

---

## 📊 System Requirements

### Minimum Requirements
- **CPU**: Intel i5 or AMD Ryzen 5
- **RAM**: 8GB
- **GPU**: Integrated graphics (CUDA recommended for better performance)
- **Storage**: 2GB free space
- **OS**: Windows 10+, macOS 10.14+, or Linux

### Recommended Requirements
- **CPU**: Intel i7 or AMD Ryzen 7
- **RAM**: 16GB
- **GPU**: NVIDIA GTX 1060 or better with CUDA support
- **Storage**: 5GB free space
- **OS**: Windows 11, macOS 12+, or Ubuntu 20.04+

## 🔧 Configuration

### Environment Variables
```bash
# Optional API Keys
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
OPENWEATHER_API_KEY=your_openweather_api_key

# Model Configuration
MODEL_PATH=yolov8s.pt  # or custom trained model
```

### Emergency Zones
```python
EMERGENCY_ZONES = {
    "hospital": {
        "lat": 28.6139, 
        "lng": 77.2090, 
        "radius": 500, 
        "name": "Delhi Hospital"
    },
    "school": {
        "lat": 28.6141, 
        "lng": 77.2092, 
        "radius": 300, 
        "name": "Central School"
    }
}
```

## 📈 Performance Optimization

### For Better Performance
1. **Use GPU acceleration** with CUDA-enabled PyTorch
2. **Limit video resolution** to 720p or lower
3. **Close unnecessary applications** to free up system resources
4. **Use local video files** instead of streaming for testing

### For Better Detection
1. **Ensure good lighting** conditions
2. **Use high-quality video sources**
3. **Position camera at appropriate angles**
4. **Test with different video types** (traffic cams, dashcams, etc.)

## 🎯 Use Cases

### Smart City Integration
- **Traffic Management Centers**: Real-time city-wide traffic monitoring
- **Emergency Services**: Automated emergency vehicle detection and routing
- **Urban Planning**: Data-driven infrastructure development
- **Environmental Monitoring**: Air quality and pollution tracking

### Research and Development
- **Traffic Pattern Analysis**: Historical data and trend analysis
- **Algorithm Development**: Custom detection model training
- **Performance Testing**: System efficiency and accuracy evaluation
- **Academic Research**: Urban mobility and environmental impact studies

### Commercial Applications
- **Traffic Consulting**: City planning and optimization services
- **Emergency Response**: Hospital and fire department integration
- **Transportation Management**: Bus and fleet management systems
- **Environmental Services**: Air quality monitoring and reporting

## 🤝 Contributing

We welcome contributions! 

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and test thoroughly
4. Commit your changes: `git commit -m 'Add amazing feature'`
5. Push to the branch: `git push origin feature/amazing-feature`
6. Open a Pull Request

### Code Style
- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings for all functions
- Include type hints where appropriate

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **YOLOv8** by Ultralytics for state-of-the-art object detection
- **Streamlit** for the amazing web framework
- **OpenCV** for computer vision processing
- **Google Maps API** for traffic and routing data
- **OpenWeather API** for environmental data
- **Plotly** for interactive visualizations


---

**Built with ❤️ for safer, greener cities**

*TrafficOps+ - Transforming urban mobility through intelligent traffic and environmental management*
