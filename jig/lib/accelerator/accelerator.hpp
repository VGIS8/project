

#pragma once

#include <Arduino.h>

class Accelerator
{
    public:
        
        void set_callback(void (*ptr)(int))
        {
            m_cb = ptr;
            TIMSK2 = _BV(OCIE2A);
        }

        /**
         * Set the acceleration used when changing speed
         * @param accel The acceleration [unit/s^2]
         */
        void set_accel(int accel)
        {
            m_us_per_unit_per_s[1] = 1000000 / accel;
        }

        /**
         * Get the current acceleration used when changing speed
         * @return The acceleration in rpm/s^2
         */
        int get_accel()
        {
            return m_us_per_unit_per_s[1] * 1000000;
        }

        /**
         * Set the deceleration used when changing speed
         * @param decel The deceleration [unit/s^2]
         */
        void set_decel(int decel)
        {
            m_us_per_unit_per_s[0] = 1000000 / decel;
        }

        /**
         * Get the current deceleration used when changing speed
         * @return The deceleration in rpm/s^2
         */
        int get_decel()
        {
            return m_us_per_unit_per_s[0] * 1000000;
        }

        /**
         * Set the min allowed speed.
         * Only used if ::constrain is true
         * @param min_speed minimum allowed speed [unit/s]
         */
        void set_min_speed(int min_speed)
        {
            m_min_speed = min_speed;
        }

        /**
         * Get the min allowed speed.
         * @return The minimum allowed speed [unit/s]
         */
        int get_min_speed()
        {
            return m_min_speed;
        }

        /**
         * Set the max allowed speed.
         * Only used if ::constrain is true
         * @param max_speed maximum allowed speed [unit/s]
         */
        void set_max_speed(int max_speed)
        {
            m_max_speed = max_speed;
        }
       
        /**
         * Get the max allowed speed.
         * @return The maximum allowed speed [unit/s]
         */
        int get_max_speed()
        {
            return m_max_speed;
        }

        /**
         * Set the desired speed
         * @param speed The speed to accelerate to [unit/s]
         */
        void set_speed(int speed)
        {
            if (speed < m_target_speed)
            {
                // Use deceleration value
                OCR2A = m_us_per_unit_per_s[1] / m_counter_step_size;
            }
            else
            {
                // Use the acceleration value
                OCR2A = m_us_per_unit_per_s[0] / m_counter_step_size;
            }
            m_target_speed = speed;
        }

        /**
         * Get the current target speed
         * @return The current target speed [unit/s]
         */
        int get_speed()
        {
            return m_target_speed;
        }

        /**
         * Static ISR handler with access to static members
         */
        static void OCR2A_ISR();
        
        /**
         * Constrain the min/max speed?
         */
        bool constrain;
    
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

    private:
        
        unsigned long m_us_per_unit_per_s[2];

        /**
         * The time per count in timer2 [uS]
         */
        const int m_counter_step_size = 8; 

        void m_init_timer2();
};