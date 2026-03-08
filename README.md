## Problem Statement
Accessibility has long been an underaddressed challenge in municipal planning. The winter season compounds these barriers significantly: icy sidewalks, accumulating snow, reduced visibility, and cold-sensitive medical conditions all restrict mobility for people with disabilities, seniors, and other vulnerable residents. Traditional patrol-based inspection models are labour-intensive, reactive rather than preventive, and cannot scale to cover the region’s full pedestrian network in real time.

There is a clear need for a low-cost, data-driven solution that can detect hazardous surface conditions as they develop and communicate that intelligence directly to city operations staff.

## How we built it
### Embedded Hardware (Arduino)
- HC-SR04 ultrasonic sensor measures distance to surface obstructions in real time, outputting readings every 100 ms
- DHT11 / temperature sensor captures ambient temperature for ice-risk correlation
- LED warning system provides on-device visual alert — green (safe) or red (hazard) 
- Servo-based barrier protection for preventing entry into hazardous zones 

### Real-Time Flask Dashboard
- Leaflet.js map & municipality data sidebar with markers for green (safe), red (hazard) or purple (anomaly)
- Node Status panel: live distance, temperature, and GPS coordinates updated every 3 seconds
- AI Risk Score bar: logistic-regression-style sigmoid classifier scoring 0–100% based on distance, temperature, humidity, and snow depth
- Atmospheric Conditions panel: Open-Meteo API with OpenWeatherMap information 
- Live connection indicators for sensor network, map layer, weather API, AI risk model, and LOF anomaly model

### Anomaly Detection — Local Outlier Factor
The system implements unsupervised machine learning anomaly detection using scikit-learn’s LocalOutlierFactor. This approach requires no labelled training data and adapts automatically to the evolving baseline of a given sensor node’s environment.

### Feature Vector (4-Dimensional)

| Feature | Unit | 
|---------------|------------------|
| Distance | cm |
| Temperature | °C | 
| Δ Distance | cm / reading | 
| Δ Temperature | °C / reading |

## What Makes This Different
- Combines real-time IoT edge sensing with server-side unsupervised ML
- Zero labelled training data required: LOF adapts to each deployment location’s unique baseline automatically
- Scalable: 16-metre ultrasonic detection range means a single mobile unit can survey an entire sidewalk block in one pass
- Accessibility Outcomes: City operations staff receive real-time hazard maps without waiting for resident 311 complaints or scheduled inspections
- Anomaly detection catches sensor malfunctions before they produce false safe readings, improving reliability for vulnerable users
- Prioritizes snow removal: hazard data can be routed directly to dispatch systems to schedule clearing at curb ramps and crossings first

## What's next for SnowSense IoT Network
- Supervised ML upgrade: once labelled data accumulates from LOF-flagged events, train a RandomForestClassifier on [distance, temperature, Δdistance, Δtemperature, hour_of_day, humidity, snow_depth] to replace the Arduino threshold with a server-side model 
- Predictive pre-alerts: use Open-Meteo’s hourly forecast to push pre-emptive warnings when the temperature + humidity forecast crosses ice-formation thresholds

- <img width="1507" height="786" alt="Screenshot_2026-03-07_at_9 52 10_PM" src="https://github.com/user-attachments/assets/d9709c35-5346-4d50-a263-48b4e137dde6" />
- <img width="1503" height="780" alt="Screenshot_2026-03-07_at_9 52 57_PM" src="https://github.com/user-attachments/assets/1ec0f43a-07f5-455f-bb1c-bdab297cd8aa" />
![Uploading Screenshot_2026-03-07_at_9.54.21_PM.png…]()


