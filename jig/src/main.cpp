#include "main.hpp"


void setup() 
{
  Serial.begin(115200);

  pinMode(ESC_GND, OUTPUT);
  digitalWrite(ESC_GND, LOW);
  
  Timer1.initialize(250);
  Timer1.pwm(ESC_PIN, 1023/2);

  Accel.set_max_speed(1000);
  Accel.set_min_speed(0);
  Accel.set_accel(125);
  Accel.set_decel(125);
  Accel.set_callback(&update_speed);
  Accel.constrain = true;
}


void update_speed(int speed)
{
  speed = map(speed, 0, 1000, 1023/2, 1023);
  Timer1.pwm(ESC_PIN, speed);
}


void loop() 
{
  com.poke();
  
  if (com.available())
  {
    Packet p = com.read();
    Accel.set_accel(p.acceleration);
    Accel.set_decel(p.deceleration);
    if(p.speed < 0)
    {
      p.speed *= -1;
    }

    Accel.set_speed(p.speed);

    //Serial.print("s:");Serial.print(p.speed); Serial.print(" a:");Serial.print(p.acceleration); Serial.print(" d:");Serial.print(p.deceleration); Serial.print(" c:");Serial.print(p.CRC, HEX);Serial.print('\n');
  }
}
