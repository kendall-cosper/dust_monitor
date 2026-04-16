import serial
from sense_hat import SenseHat

sense = SenseHat()
print(f"SenseHat Temp: {sense.get_temperature()}")

ser = serial.Serial('/dev/serial0', baudrate=9600, timeout=2)
while True:
    data = ser.read(32)
    print(f"Raw Serial Data Length: {len(data)}")
    if len(data) == 32:
        print("Success! Data received from PMS7003M.")
        break
