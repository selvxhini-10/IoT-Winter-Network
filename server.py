"""
server.py  —  Region of Waterloo Winter Accessibility Dashboard
Enhanced with:
  - Rolling sensor history (in-memory + optional SQLite persistence)
  - LocalOutlierFactor anomaly detection (sklearn)
  - /anomaly endpoint returning latest LOF result
  - /history endpoint for chart data
"""

from flask import Flask, request, jsonify, render_template
import numpy as np
import pandas as pd
from collections import deque
from datetime import datetime

import openmeteo_requests
import requests_cache
from retry_requests import retry

from sklearn.neighbors import LocalOutlierFactor
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

app = Flask(__name__)

# ──────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────
HISTORY_MAXLEN   = 200    # rolling window of readings kept in memory
LOF_N_NEIGHBORS  = 5      # k for LOF
LOF_CONTAMINATION = 0.05  # expected fraction of outliers (5 %)
LOF_WARMUP       = 10     # min readings before LOF runs
LOF_THRESHOLD    = 1.8    # LOF score above this → anomaly

# ──────────────────────────────────────────────────────────────
# STATE
# ──────────────────────────────────────────────────────────────
sensor_point   = {}
sensor_history = deque(maxlen=HISTORY_MAXLEN)   # list of dicts
anomaly_result = {
    "is_anomaly": False,
    "lof_score": 1.0,
    "reason": "Warming up…",
    "feature_deviations": {},
    "timestamp": None,
    "n_readings": 0,
}

_prev_distance    = None
_prev_temperature = None


# ──────────────────────────────────────────────────────────────
# OPEN-METEO WEATHER
# ──────────────────────────────────────────────────────────────
cache_session  = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session  = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo      = openmeteo_requests.Client(session=retry_session)


def fetch_waterloo_weather():
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude":  43.4723,
        "longitude": -80.5449,
        "hourly": ["temperature_2m", "relative_humidity_2m", "snow_depth"],
        "timezone": "auto"
    }
    responses   = openmeteo.weather_api(url, params=params)
    response    = responses[0]
    hourly      = response.Hourly()
    temperature = hourly.Variables(0).ValuesAsNumpy()[0]
    humidity    = hourly.Variables(1).ValuesAsNumpy()[0]
    snow_depth  = hourly.Variables(2).ValuesAsNumpy()[0]
    return {
        "temperature": float(temperature),
        "humidity":    float(humidity),
        "snow_depth":  float(snow_depth),
    }


# ──────────────────────────────────────────────────────────────
# ANOMALY DETECTION — Local Outlier Factor
# Features: [distance, temperature, Δdistance, Δtemperature]
# ──────────────────────────────────────────────────────────────

def _extract_features(record):
    return [
        record["distance"],
        record["temperature"],
        record["delta_distance"],
        record["delta_temperature"],
    ]


def _compute_feature_deviations(query_vec, history_vecs):
    """Return z-scores for each feature relative to rolling baseline."""
    arr  = np.array(history_vecs)
    mean = arr.mean(axis=0)
    std  = arr.std(axis=0) + 1e-6
    z    = np.abs((np.array(query_vec) - mean) / std)
    return {
        "distance":         float(z[0]),
        "temperature":      float(z[1]),
        "delta_distance":   float(z[2]),
        "delta_temperature":float(z[3]),
    }


def _explain_anomaly(deviations):
    """Human-readable explanation of the dominant anomalous feature."""
    labels = {
        "distance":          "obstacle distance reading",
        "temperature":       "temperature",
        "delta_distance":    "distance change rate",
        "delta_temperature": "temperature change rate",
    }
    top_key = max(deviations, key=deviations.get)
    z       = deviations[top_key]
    return (
        f"Unusual {labels[top_key]} "
        f"(z={z:.1f}σ from baseline). "
        "May indicate sensor fault or sudden environmental change."
    )


def run_lof(query_record, history):
    """
    Fit LOF on all history readings (excluding the query) and score the query.
    Returns (lof_score: float, is_anomaly: bool).
    """
    global _prev_distance, _prev_temperature

    n = len(history)
    if n < LOF_WARMUP:
        return 1.0, False

    all_vecs = [_extract_features(r) for r in history]
    query_vec = _extract_features(query_record)

    # Fit LOF on history (novelty=True allows scoring unseen points)
    k = min(LOF_N_NEIGHBORS, n - 1)
    clf = LocalOutlierFactor(
        n_neighbors=k,
        contamination=LOF_CONTAMINATION,
        novelty=True
    )
    clf.fit(all_vecs)

    # score_samples returns negative LOF; invert for readability
    raw = clf.score_samples([query_vec])[0]
    lof_score = float(-raw)  # now > 1.0 = more anomalous

    is_anomaly = lof_score > LOF_THRESHOLD

    return lof_score, is_anomaly


def update_anomaly_state(new_point):
    """Called every time a new sensor reading arrives."""
    global _prev_distance, _prev_temperature, anomaly_result

    dist   = new_point["distance"]
    temp   = new_point["temperature"]
    ddist  = (dist - _prev_distance)   if _prev_distance  is not None else 0.0
    dtemp  = (temp - _prev_temperature) if _prev_temperature is not None else 0.0

    _prev_distance    = dist
    _prev_temperature = temp

    record = {
        "distance":          dist,
        "temperature":       temp,
        "delta_distance":    ddist,
        "delta_temperature": dtemp,
        "status":            new_point.get("status", "SAFE"),
        "timestamp":         datetime.utcnow().isoformat(),
    }

    # Add to history BEFORE scoring (LOF uses history[-1:] excluded for fresh score)
    history_snapshot = list(sensor_history)   # snapshot before append

    sensor_history.append(record)

    lof_score, is_anomaly = run_lof(record, history_snapshot)

    reason = "Sensor readings within expected range." if not is_anomaly else ""
    deviations = {}
    if len(history_snapshot) >= LOF_WARMUP:
        history_vecs = [_extract_features(r) for r in history_snapshot]
        query_vec    = _extract_features(record)
        deviations   = _compute_feature_deviations(query_vec, history_vecs)
        if is_anomaly:
            reason = _explain_anomaly(deviations)

    anomaly_result.update({
        "is_anomaly":          is_anomaly,
        "lof_score":           round(lof_score, 4),
        "reason":              reason if reason else "No deviations detected.",
        "feature_deviations":  deviations,
        "timestamp":           record["timestamp"],
        "n_readings":          len(sensor_history),
        "warmup_remaining":    max(0, LOF_WARMUP - len(sensor_history)),
    })

    print(
        f"[LOF] dist={dist:.1f}cm  temp={temp:.1f}°C  "
        f"Δd={ddist:.1f}  Δt={dtemp:.2f}  "
        f"lof={lof_score:.3f}  anomaly={is_anomaly}"
    )


# ──────────────────────────────────────────────────────────────
# ROUTES
# ──────────────────────────────────────────────────────────────

@app.route('/')
def dashboard():
    return render_template('dashboard.html')


@app.route('/data', methods=['POST'])
def receive_data():
    global sensor_point
    data        = request.json
    sensor_point = data
    update_anomaly_state(data)
    return {"status": "ok"}


@app.route('/points', methods=['GET'])
def get_points():
    if sensor_point:
        return jsonify([sensor_point])
    return jsonify([])


@app.route('/anomaly', methods=['GET'])
def get_anomaly():
    """
    Returns the latest LOF anomaly detection result.

    Response schema:
    {
        "is_anomaly":         bool,
        "lof_score":          float,   # ~1.0 = normal, >1.8 = anomaly
        "reason":             str,
        "feature_deviations": {        # z-scores per feature
            "distance":          float,
            "temperature":       float,
            "delta_distance":    float,
            "delta_temperature": float,
        },
        "timestamp":          str (ISO 8601),
        "n_readings":         int,
        "warmup_remaining":   int,
    }
    """
    return jsonify(anomaly_result)


@app.route('/history', methods=['GET'])
def get_history():
    """
    Returns last N readings (default 60) for trend charts.
    Query param: ?n=60
    """
    n       = min(int(request.args.get('n', 60)), HISTORY_MAXLEN)
    records = list(sensor_history)[-n:]
    return jsonify(records)


@app.route('/weather', methods=['GET'])
def weather():
    try:
        return jsonify(fetch_waterloo_weather())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 55)
    print("  Region of Waterloo — Winter Accessibility Server")
    print(f"  LOF: k={LOF_N_NEIGHBORS}, threshold={LOF_THRESHOLD}, warmup={LOF_WARMUP}")
    print("=" * 55)
    app.run(port=5000, debug=True)
