#include <Wire.h>
#include <Adafruit_Si7021.h>

Adafruit_Si7021 sensor;

void setup() {
  Serial.begin(9600);
  if (!sensor.begin()) {
    Serial.println("Couldn't find a valid Si7021 sensor, check the pinout!");
    while (1);
  }
}

void loop() {
  if (Serial.available() > 0) {
    char request = Serial.read();
    float data;
    if (request == 't') {
      data = sensor.readTemperature();
      Serial.println(data, 2);
    } else if (request == 'h') {
      data = sensor.readHumidity();
      Serial.println(data, 2);
    }
  }
}