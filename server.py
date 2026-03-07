from flask import Flask, request, jsonify, render_template
import pandas as pd
import openmeteo_requests
import requests_cache
from retry_requests import retry

app = Flask(__name__)

# Latest sensor reading
sensor_point = {}

# -------- Open-Meteo setup --------
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

def fetch_waterloo_weather():
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 43.4723,
        "longitude": -80.5449,
        "hourly": ["temperature_2m", "relative_humidity_2m", "snow_depth"],
        "timezone": "auto"
    }
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    hourly = response.Hourly()
    temperature = hourly.Variables(0).ValuesAsNumpy()[0]  # current hour
    humidity = hourly.Variables(1).ValuesAsNumpy()[0]
    snow_depth = hourly.Variables(2).ValuesAsNumpy()[0]
    return {
        "temperature": float(temperature),
        "humidity": float(humidity),
        "snow_depth": float(snow_depth)
    }

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/data', methods=['POST'])
def receive_data():
    global sensor_point
    data = request.json
    sensor_point = data
    return {"status": "ok"}

@app.route('/points', methods=['GET'])
def get_points():
    if sensor_point:
        return jsonify([sensor_point])
    else:
        return jsonify([])

@app.route('/weather', methods=['GET'])
def weather():
    return jsonify(fetch_waterloo_weather())

if __name__ == '__main__':
    app.run(port=5000, debug=True)