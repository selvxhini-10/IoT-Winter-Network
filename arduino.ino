#include <Arduino.h>

// -------- Ultrasonic Pins --------
const int trigPin = 9;
const int echoPin = 10;

// -------- TMP36 Pin --------
const int tempPin = A0;

// -------- LED Pins --------
const int redLED = 7;
const int whiteLED = 6;

// -------- Servo Pin --------
const int servoPin = 11;

// -------- Variables --------
float duration;
float distance;
float temperatureC;

// -------- Threshold --------
const float hazardDistance = 4.0; // cm

// -------- Hazard Timer --------
unsigned long hazardStartTime = 0;
bool hazardActive = false;

// -----------------------------
// Servo helper function using PWM (UNO R4 compatible)
// -----------------------------
void setServoAngle(int angle) {
  // Convert 0-180° to 1000-2000 µs pulse
  int pulse = map(angle, 0, 180, 1000, 2000);

  // Generate a single pulse
  digitalWrite(servoPin, HIGH);
  delayMicroseconds(pulse);
  digitalWrite(servoPin, LOW);

  // Wait remainder of 20ms period
  int delayMs = 20 - pulse / 1000;
  if (delayMs > 0) delay(delayMs); // <-- FIXED here
}

void setup() {
  Serial.begin(9600);

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  pinMode(redLED, OUTPUT);
  pinMode(whiteLED, OUTPUT);

  pinMode(servoPin, OUTPUT);
}

void loop() {
  // ==========================
  // ULTRASONIC SENSOR
  // ==========================
  digitalWrite(trigPin, LOW);
  delayMicroseconds(5);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  duration = pulseIn(echoPin, HIGH, 30000); // timeout protection
  distance = duration * 0.0343 / 2.0;

  // ==========================
  // TMP36 TEMPERATURE SENSOR
  // ==========================
  int sensorValue = analogRead(tempPin);
  float voltage = sensorValue * (5.0 / 1023.0);
  temperatureC = (voltage - 0.5) * 100.0;

  // ==========================
  // SERIAL DEBUG
  // ==========================
  Serial.print("Distance (cm): ");
  Serial.print(distance);
  Serial.print(" | Temp (C): ");
  Serial.println(temperatureC);

  // ==========================
  // HAZARD LOGIC
  // ==========================
  if (distance < hazardDistance) {
    digitalWrite(redLED, HIGH);
    digitalWrite(whiteLED, LOW);
    Serial.println("STATUS: HAZARD DETECTED");

    // start timer if hazard just started
    if (!hazardActive) {
      hazardActive = true;
      hazardStartTime = millis();
    }

    // tilt servo if hazard has been active for 10 seconds
    if (millis() - hazardStartTime >= 5000) {
      setServoAngle(0); // tilt
    }

  } else {
    digitalWrite(redLED, LOW);
    digitalWrite(whiteLED, HIGH);
    Serial.println("STATUS: SAFE");

    // reset hazard timer
    hazardActive = false;

    // reset servo upright
    setServoAngle(60);
  }

  Serial.println("-------------------");

  delay(500);
}
