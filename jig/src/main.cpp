#include "main.hpp"


void setup() {
  Serial.begin(115200);
  Serial.setTimeout(1000);
  Serial.println("hey");

  pinMode(ESC_GND, OUTPUT);
  digitalWrite(ESC_GND, LOW);
  
  Timer1.initialize(250);
  Timer1.pwm(ESC_PIN, 0);
}

void loop() {
  long x = Serial.parseInt();
  if(x)
  {
    Serial.println("\nPulseWidth set to: " + String(x-1) + "%");
    Timer1.pwm(ESC_PIN, map(x, 1, 101, 1023/2, 1023));
  }
}
