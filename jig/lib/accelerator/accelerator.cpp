#include "accelerator.hpp"


/* #region Setters and getters */


void Accelerator::m_init_timer2()
{
    TCCR2A |= _BV(WGM21); // CTC mode
    TCCR2B |= _BV(CS22) | _BV(CS20); // 2040uS period, 8uS steps
    TIMSK2 |= _BV(OCIE2A); // Generate an interrupt when timer2 matches OCR2A
}

void Accelerator::OCR2A_ISR()
{
    if (m_direction)
    {
        if (++m_current_speed >= m_max_speed)
        {
            m_current_speed = m_max_speed;
        }
        (*m_cb)(m_current_speed);
    }
    else
    {
        if (--m_current_speed <= m_min_speed)
        {
            m_current_speed = m_min_speed;
        }
        (*m_cb)(m_current_speed);
    }
}

ISR(TIMER2_COMPA_vect)
{
    Accelerator::OCR2A_ISR();
}

