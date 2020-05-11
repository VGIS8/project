

#pragma once

#include <Arduino.h>

class Accelerator
{
    public:        
        void set_callback(void (*ptr)(int)) __attribute__((always_inline))
        {
            m_cb = ptr;
        }

        /**
         * Set the acceleration used when changing speed
         * @param accel The acceleration [unit/s^2]
         */
        void set_accel(int accel) __attribute__((always_inline))
        {
            m_us_per_unit_per_s[1] = 1000000 / accel;
        }

        /**
         * Get the current acceleration used when changing speed
         * @return The acceleration in unit/s^2
         */
        int get_accel() __attribute__((always_inline))
        {
            return m_us_per_unit_per_s[1] * 1000000;
        }

        /**
         * Set the deceleration used when changing speed
         * @param decel The deceleration [unit/s^2]
         */
        void set_decel(int decel) __attribute__((always_inline))
        {
            m_us_per_unit_per_s[0] = 1000000 / decel;
        }

        /**
         * Get the current deceleration used when changing speed
         * @return The deceleration in unit/s^2
         */
        int get_decel() __attribute__((always_inline))
        {
            return m_us_per_unit_per_s[0] * 1000000;
        }

        /**
         * Set the min allowed speed.
         * Only used if ::constrain is true
         * @param min_speed minimum allowed speed [unit/s]
         */
        void set_min_speed(int min_speed) __attribute__((always_inline))
        {
            m_min_speed = min_speed;
        }

        /**
         * Get the min allowed speed.
         * @return The minimum allowed speed [unit/s]
         */
        int get_min_speed() __attribute__((always_inline))
        {
            return m_min_speed;
        }

        /**
         * Set the max allowed speed.
         * Only used if ::constrain is true
         * @param max_speed maximum allowed speed [unit/s]
         */
        void set_max_speed(int max_speed) __attribute__((always_inline))
        {
            m_max_speed = max_speed;
        }
       
        /**
         * Get the max allowed speed.
         * @return The maximum allowed speed [unit/s]
         */
        int get_max_speed() __attribute__((always_inline))
        {
            return m_max_speed;
        }

        /**
         * Set the desired speed
         * @param speed The speed to accelerate to [unit/s]
         */
        void set_speed(int speed) __attribute__((always_inline))
        {
            if (speed < m_current_speed)
            {
                // Use deceleration value
                OCR2A = m_us_per_unit_per_s[0] / m_counter_step_size;
                m_direction = 0;
            }
            else if (speed > m_current_speed)
            {
                // Use the acceleration value
                OCR2A = m_us_per_unit_per_s[1] / m_counter_step_size;
                m_direction = 1;
            }
            //Serial.println(OCR2A);
            m_target_speed = speed;

            if (constrain)
            {
                m_target_speed = constrain(m_target_speed, m_min_speed, m_max_speed);
                m_current_speed = constrain(m_current_speed, m_min_speed, m_max_speed);
            }

            timer_start();
        }

        /**
         * Get the current target speed
         * @return The current target speed [unit/s]
         */
        int get_speed() __attribute__((always_inline))
        {
            return m_current_speed;
        }

        /**
         * Constrain the min/max speed?
         */
        static bool constrain;

        /**
         * Static ISR handler with access to static members
         */

        static void OCR2A_ISR()
        {
           if (m_direction)
           {
               ++m_current_speed;
               if (m_current_speed >= m_max_speed && constrain)
               {
                   m_current_speed = m_max_speed;
                   timer_stop();
               }
               if (m_current_speed >= m_target_speed)
               {
                   timer_stop();
               }
               (*m_cb)(m_current_speed);
           }
           else
           {
               if (--m_current_speed <= m_min_speed)
               {
                   m_current_speed = m_min_speed;
                   timer_stop();
               }
               if (m_current_speed <= m_target_speed)
               {
                   timer_stop();
               }
               (*m_cb)(m_current_speed);
           }
        }

    
    protected:
        static int 
            m_target_speed,
            m_current_speed,
            m_min_speed, 
            m_max_speed;

        /**
         * If we're currently accelerating(1) or decelerating(0)
         */
        static bool m_direction;

        /**
         * The callback function to call with the new speed
         */
        static void (*m_cb)(int);
        
        /**
         * Start the timer
         */
        static void timer_start() __attribute__((always_inline))
        {
            TCNT2 = 0; // Clear the timer
            TCCR2A |= _BV(WGM21); // CTC mode
            TCCR2B |= _BV(CS22) | _BV(CS21) | _BV(CS20); // 2040uS period, 8uS steps
            TIMSK2 |= _BV(OCIE2A); // Intterupt on compare match
        }

        /**
         * Stop the timer from running
         */
        static void timer_stop() __attribute__((always_inline))
        {
            TCCR2B &= ~(_BV(CS22) | _BV(CS21) | _BV(CS20));
            TIMSK2 &= ~_BV(OCIE2A);
        }

    private:
        
        unsigned long m_us_per_unit_per_s[2];

        /**
         * The time per count in timer2 [uS]
         */
        const int m_counter_step_size = 32; 
};

Accelerator Accel;

bool Accelerator::constrain = false;
bool Accelerator::m_direction = false;

int Accelerator::m_target_speed = 0;
int Accelerator::m_current_speed = 0;
int Accelerator::m_min_speed = 0;
int Accelerator::m_max_speed = 0;

void (*Accelerator::m_cb)(int) = NULL;

ISR(TIMER2_COMPA_vect)
{
    // bitSet(PORTD, 2);
    // delayMicroseconds(10);
    // bitClear(PORTD, 2);
    Accelerator::OCR2A_ISR();
}
