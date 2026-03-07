# python.py
import serial
import requests
import time

# Adjust this to your Arduino serial port
ser = serial.Serial('/dev/tty.usbmodem101', 9600)

# Fixed coordinates for the sensor
lat = 43.4723
lon = -80.5449

while True:
    try:
        line = ser.readline().decode().strip()

        # Parse distance and temperature
        if "Distance" in line and "Temp" in line:
            parts = line.split('|')
            distance = float(parts[0].split(':')[1].strip())
            temperature = float(parts[1].split(':')[1].strip())

            # Calculate status like Arduino LED
            status = "HAZARD" if distance < 10 or temperature <= 1 else "SAFE"

            data = {
                "lat": lat,
                "lon": lon,
                "distance": distance,
                "temperature": temperature,
                "status": status
            }

            try:
                requests.post("http://localhost:5000/data", json=data)
            except requests.exceptions.RequestException as e:
                print("Error sending data:", e)

        # Ignore other lines like separator lines or status debug lines
        time.sleep(1)  # match Arduino delay

    except Exception as e:
        print("Error:", e)
        continue