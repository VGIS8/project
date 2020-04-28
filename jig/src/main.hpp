#pragma once

#include <Arduino.h>
#include <TimerOne.h>
#include <accelerator.hpp>

#define ESC_PIN 10
#define ESC_GND 12


// Prototypes
void update_speed(int);