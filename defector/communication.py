import serial
import platform

from crcmod.predefined import Crc

port = 'COM3'
if 'linux' in platform.system().lower():
    port = '/dev/ttyUSB0'


def set_speed(speed, acceleration, deceleration=None):
    """Set the speed of the vial spinner

    Args:
        speed (int): The permille to spin the vial at (-1000 to 1000)
        acceleration: The acceleration in units/s^2
        deceleration: The deceleration in units/s^2
            Default acceleration
    """

    if deceleration is None:
        deceleration = acceleration

    if not (-1000 <= speed <= 1000):
        raise ValueError(f'{speed} is outside the permitted range (-1000 to 1000)')

    speed = speed.to_bytes(2, byteorder='little', signed=True)
    acceleration = acceleration.to_bytes(2, byteorder='little')
    deceleration = deceleration.to_bytes(2, byteorder='little')

    packet = speed + acceleration + deceleration

    crc16 = Crc('crc-ccitt-false')
    crc16.update(packet)
    packet += crc16.crcValue.to_bytes(2, byteorder='little')

    ser = serial.Serial()
    ser.baudrate = 115200
    ser.port = port
    ser.timeout = 0.1
    ser.dtr = None

    with ser as com:
        com.write(b'!' + packet)
        line = com.read(1)
        print(line.decode())
