import random
import time

# Function to simulate pollution sensor values
def get_pollution_data():
    # Random Air Quality Index (AQI) between 0 - 500
    aqi = random.randint(10, 300)

    # Random gas concentration levels (ppm)
    co = round(random.uniform(0.1, 9.9), 2)     # Carbon Monoxide
    no2 = round(random.uniform(0.01, 0.5), 2)   # Nitrogen Dioxide
    so2 = round(random.uniform(0.01, 0.3), 2)   # Sulfur Dioxide
    pm25 = random.randint(5, 150)               # Particulate Matter 2.5
    pm10 = random.randint(10, 200)              # Particulate Matter 10

    return {
        "AQI": aqi,
        "CO (ppm)": co,
        "NO2 (ppm)": no2,
        "SO2 (ppm)": so2,
        "PM2.5 (µg/m³)": pm25,
        "PM10 (µg/m³)": pm10
    }

# Run simulation (like sensor continuously streaming)
if __name__ == "__main__":
    print("🌍 Pollution Sensor Simulator (Random Data)")
    while True:
        data = get_pollution_data()
        print(data)
        time.sleep(2)  # update every 2 seconds
