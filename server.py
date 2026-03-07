from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

sensor_points = []

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/data', methods=['POST'])
def receive_data():
    data = request.json
    sensor_points.append(data)
    if len(sensor_points) > 100:  # optional
        sensor_points.pop(0)
    return {"status": "ok"}

@app.route('/points', methods=['GET'])
def get_points():
    return jsonify(sensor_points)

if __name__ == '__main__':
    app.run(port=5000)