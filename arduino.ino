/*
   Temperature Sensor Code: https://www.geeksforgeeks.org/electronics-engineering/arduino-temperature-sensor/

   HC-SR04 example sketch

   https://create.arduino.cc/projecthub/Isaac100/getting-started-with-the-hc-sr04-ultrasonic-sensor-036380

   by Isaac100

*/

// -------- Ultrasonic Pins --------
const int trigPin = 9;
const int echoPin = 10;

// -------- TMP36 Pin --------
const int tempPin = A0;

// -------- LED Pins --------
const int redLED = 7;
const int whiteLED = 6;

// -------- Variables --------
float duration;
float distance;
float temperatureC;

// -------- Threshold --------
const float hazardDistance = 4.0; // cm

void setup() {
  Serial.begin(9600);

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  pinMode(redLED, OUTPUT);
  pinMode(whiteLED, OUTPUT);
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

  duration = pulseIn(echoPin, HIGH, 30000);  // timeout protection
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
  } else {
    digitalWrite(redLED, LOW);
    digitalWrite(whiteLED, HIGH);
    Serial.println("STATUS: SAFE");
  }

  Serial.println("-------------------");

  delay(500);
}