import serial
import requests
import time

ser = serial.Serial('/dev/tty.usbmodem101', 9600)
lat = 43.4723
lon = -80.5449

distance = None
temperature = None

while True:
    try:
        line = ser.readline().decode().strip()
        # Parse distance and temperature
        if "Distance" in line and "Temp" in line:
            parts = line.split('|')
            distance = float(parts[0].split(':')[1].strip())
            temperature = float(parts[1].split(':')[1].strip())

        # Parse STATUS line from Arduino
        elif "STATUS" in line:
            if distance is None or temperature is None:
                continue  # skip if we haven't read the sensors yet

            if "HAZARD" in line:
                status = "HAZARD"
            else:
                status = "SAFE"

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

        time.sleep(0.1)  # small delay

    except Exception as e:
        print("Error:", e)
        continue