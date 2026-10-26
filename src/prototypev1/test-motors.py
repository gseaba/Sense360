
import time
import board
import busio
from adafruit_pca9685 import PCA9685

# Motor names and PCA9685 channels from main.py
MOTORS = [
    ("front",       7),
    ("front_right", 6),
    ("right",       5),
    ("back_right",  4),
    ("back",        3),
    ("back_left",   2),
    ("left",        1),
    ("front_left",  0),
]

# Initialize PCA9685
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 200

try:
    # Ensure all motors start off
    for _, channel in MOTORS:
        pca.channels[channel].duty_cycle = 0

    for name, channel in MOTORS:
        print(f"Testing {name} (channel {channel})")

        # Turn motor on at full power
        pca.channels[channel].duty_cycle = 65535
        time.sleep(1)

        # Turn motor off
        pca.channels[channel].duty_cycle = 0

        print(f"{name} OFF")
        time.sleep(1)

    print("Motor test complete.")

finally:
    # Turn off every motor even if an error occurs
    for _, channel in MOTORS:
        pca.channels[channel].duty_cycle = 0

    pca.deinit()
