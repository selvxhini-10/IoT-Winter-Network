# python.py
import serial
import requests

ser = serial.Serial('/dev/tty.usbmodem101', 9600)

lat = 43.4723
lon = -80.5449

while True:
    line = ser.readline().decode().strip()
    
    # Example line: "Distance (cm): 5 | Temp (C): 0"
    try:
        parts = line.split('|')
        distance = float(parts[0].split(':')[1].strip())
        temperature = float(parts[1].split(':')[1].strip())
    except:
        continue  # skip invalid lines

    data = {
        "lat": lat,
        "lon": lon,
        "distance": distance,
        "temperature": temperature
    }

    try:
        requests.post("http://localhost:5000/data", json=data)
    except requests.exceptions.RequestException as e:
        print("Error sending data:", e)