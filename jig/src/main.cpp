#include "main.hpp"


void setup() {
  Serial.begin(115200);
  Serial.setTimeout(1000);
  Serial.println("hey");

  pinMode(ESC_GND, OUTPUT);
  digitalWrite(ESC_GND, LOW);
  
  Timer1.initialize(250);
  Timer1.pwm(ESC_PIN, 0);

  Accel.set_max_speed(1023);
  Accel.set_min_speed(1023/2);
  Accel.set_accel(50);
  Accel.set_decel(50);
  Accel.set_callback(&update_speed);
  Accel.constrain = true;
}

void update_speed(int speed)
{
  Timer1.pwm(ESC_PIN, speed);
}

void loop() {
  long x = Serial.parseInt();
  if(x)
  {
    Serial.println("\nPulseWidth set to: " + String(x-1) + "%");
    Accel.set_speed(x);
  }
}
