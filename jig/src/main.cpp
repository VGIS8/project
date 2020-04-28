#include "main.hpp"


void setup() {
  Serial.begin(115200);
  Serial.setTimeout(1000);
  Serial.println("hey");

  pinMode(ESC_GND, OUTPUT);
  //bitSet(DDRD, 2);
  digitalWrite(ESC_GND, LOW);
  
  Timer1.initialize(250);
  Timer1.pwm(ESC_PIN, 1023/2);

  Accel.set_max_speed(1023);
  Accel.set_min_speed(1023/2);
  Accel.set_accel(30);
  Accel.set_decel(30);
  Accel.set_callback(&update_speed);
  Accel.constrain = true;

  delay(10000);
}

void update_speed(int speed)
{
  Timer1.pwm(ESC_PIN, speed);
}

void loop() {

  if(1)
  {
    long x = Serial.parseInt();
    if(x)
    {
      Serial.println("\nPulseWidth set to: " + String(x-1) + "%");
      Accel.set_speed(map(x, 1, 101, 1023/2, 1023));
    }
  }
  else
  {  
    Accel.set_speed(1023);
    while(Accel.get_speed() != 1023)
    {
      delay(5);
    }
    delay(1000);

    unsigned long x = millis();
    Accel.set_speed(1023/2);
    while(Accel.get_speed() != 1023/2)
    {
      delay(5);
    }
    delay(1000);
  }
}
