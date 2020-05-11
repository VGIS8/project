
#include "PacketCom.hpp"

PacketCom::PacketCom(uint8_t start_byte, bool ack)
{
    m_start_byte = start_byte;
    m_ack = ack;
}

uint8_t PacketCom::available(void)
{
    return m_avail;
}

/**
 * @return The next Packet in buffer if available, otherwise a dummy Packet with all fields 0
 */
Packet PacketCom::read()
{
    if(m_avail)
    {
        return m_buffer[--m_avail];
    }
    else
    {
        Packet x {0,0,0,0};
        return x;
    }
}

void PacketCom::poke()
{
    while(Serial.available())
    {
        char x = Serial.read();

        if (x == m_start_byte)
        {
            DEBUGPL("Start of packet");
            m_in_packet = true;
            m_current_byte = 0;
        }
        else if (m_in_packet)
        {
            DEBUGP("C: ");DEBUGPL(x);
            uint8_t * p = (uint8_t*) &m_buffer[m_avail];
            p[m_current_byte++] = (uint8_t) x;
        }

        if (m_current_byte > sizeof(Packet)-1)
        {
            DEBUGPL("Full packet");
            if (m_check_crc(m_buffer[m_avail]))
            {
                DEBUGPL("Valid CRC");
                m_avail++;
            };
            m_current_byte = 0;
            m_in_packet = false;
        }
    }
}

/* Private functions */
bool PacketCom::m_check_crc(Packet p)
{
    
    uint16_t crc = m_CRC16.ccitt((uint8_t *)&p.speed, sizeof(p)-sizeof(p.CRC));
    if (crc == p.CRC)
    {
        if (m_ack)
        {
            Serial.print('G');
        }
        DEBUGP(crc);DEBUGP("==");DEBUGPL(p.CRC);
        return true;
    }
    else
    {
        if (m_ack)
        {
            Serial.print('B');
        }
        DEBUGP(crc);DEBUGP("!=");DEBUGPL(p.CRC);
        return false;
    }
}