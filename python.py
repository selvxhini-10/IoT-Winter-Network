"""
python.py  —  Region of Waterloo Winter Accessibility IoT Reader
Reads ultrasonic distance + temperature from Arduino over serial,
posts to Flask server, and prints live anomaly detection results.
"""

import serial
import requests
import time

# ── CONFIG ──────────────────────────────────────
SERIAL_PORT  = '/dev/tty.usbmodem101'
BAUD_RATE    = 9600
SERVER_URL   = 'http://localhost:5000'

# Fixed GPS coordinates for this sensor node
LAT = 43.4723
LON = -80.5449
# ────────────────────────────────────────────────

ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
print(f"[Serial] Connected to {SERIAL_PORT} at {BAUD_RATE} baud")

distance    = None
temperature = None


def post_reading(distance, temperature, status):
    """Send sensor reading to Flask server."""
    data = {
        "lat":         LAT,
        "lon":         LON,
        "distance":    distance,
        "temperature": temperature,
        "status":      status,
    }
    try:
        resp = requests.post(f"{SERVER_URL}/data", json=data, timeout=2)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[HTTP] Error sending data: {e}")


def fetch_anomaly():
    """Fetch and display the latest LOF anomaly result from server."""
    try:
        resp = requests.get(f"{SERVER_URL}/anomaly", timeout=2)
        resp.raise_for_status()
        result = resp.json()

        n        = result.get("n_readings", 0)
        warmup   = result.get("warmup_remaining", 0)
        score    = result.get("lof_score", 1.0)
        is_anom  = result.get("is_anomaly", False)
        reason   = result.get("reason", "")
        devs     = result.get("feature_deviations", {})

        if warmup > 0:
            print(f"[LOF]  Warming up — {n} readings collected, {warmup} more needed")
        else:
            flag = "⚠  ANOMALY" if is_anom else "✓  Normal"
            print(f"[LOF]  {flag}  |  score={score:.3f}  |  n={n}")
            if is_anom:
                print(f"       Reason: {reason}")
            if devs:
                print(f"       z-scores → dist:{devs.get('distance',0):.2f}  "
                      f"temp:{devs.get('temperature',0):.2f}  "
                      f"Δdist:{devs.get('delta_distance',0):.2f}  "
                      f"Δtemp:{devs.get('delta_temperature',0):.2f}")

    except requests.exceptions.RequestException as e:
        print(f"[HTTP] Could not fetch anomaly result: {e}")


# ── MAIN LOOP ────────────────────────────────────
print("[Reader] Listening for sensor data…\n")

reading_count = 0

while True:
    try:
        line = ser.readline().decode().strip()

        # Parse combined distance + temperature line
        # Expected format: "Distance: 42.3 cm | Temp: -3.1 C"
        if "Distance" in line and "Temp" in line:
            parts       = line.split('|')
            distance    = float(parts[0].split(':')[1].strip().replace(' cm', ''))
            temperature = float(parts[1].split(':')[1].strip().replace(' C', '').replace(' °C', ''))

        # Parse STATUS line from Arduino
        elif "STATUS" in line:
            if distance is None or temperature is None:
                continue  # wait until first sensor values are in

            status = "HAZARD" if "HAZARD" in line else "SAFE"
            print(f"[Sensor] dist={distance:.1f}cm  temp={temperature:.1f}°C  status={status}")

            # Post to server (triggers LOF on server side)
            post_reading(distance, temperature, status)
            reading_count += 1

            # Fetch anomaly result every reading
            fetch_anomaly()

        time.sleep(0.1)

    except UnicodeDecodeError:
        continue  # occasional serial noise
    except Exception as e:
        print(f"[Error] {e}")
        continue
