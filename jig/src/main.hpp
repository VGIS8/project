#pragma once
// #define DEBUG

#include <Arduino.h>

#include <TimerOne.h>

#include <accelerator.hpp>
#include <packetCom.hpp>

#define ESC_PIN 10
#define ESC_GND 12

PacketCom com('!', true);

// Prototypes
void update_speed(int);