
#pragma once

#include <Arduino.h>
#include <FastCRC.h>

#ifdef DEBUG
    #define DEBUGP(s) (Serial.print(s))
    #define DEBUGPL(s) (Serial.println(s))
#else
    #define DEBUGP(s) do {} while(0)
    #define DEBUGPL(s) do {} while(0)
#endif


/**
 * A data packet. 
 * The structure is one start character, followed by 4 bytes of data and 2 bytes of CRC
 * !<data><data><data><data><data><data><crc><crc>
 * The start character isn't stored
 */
#pragma pack(push, 1)
struct Packet
{    
    int16_t speed;
    uint16_t acceleration;
    uint16_t deceleration;
    uint16_t CRC;
};
#pragma pack(pop)


class PacketCom
{
private:
    uint8_t m_start_byte;
    uint8_t m_current_byte = 0;
    bool m_in_packet;

    Packet m_buffer[10];
    uint8_t m_avail = 0;
    
    bool m_check_crc(Packet p);
    bool m_ack;

    FastCRC16 m_CRC16;

public:
    PacketCom(uint8_t start_byte='!', bool ack=false);

    uint8_t available(void);
    Packet read(void);
    void poke();
};