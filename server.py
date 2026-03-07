# server.py
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Keep only the latest reading
sensor_point = {}

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/data', methods=['POST'])
def receive_data():
    global sensor_point
    data = request.json
    sensor_point = data  # always store latest
    return {"status": "ok"}

@app.route('/points', methods=['GET'])
def get_points():
    if sensor_point:
        return jsonify([sensor_point])
    else:
        return jsonify([])

if __name__ == '__main__':
    app.run(port=5000, debug=True)