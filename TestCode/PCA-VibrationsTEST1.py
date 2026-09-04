import time
from adafruit_pca9685 import PCA9685
from adafruit_extended_bus import ExtendedI2C as I2C

# Use Raspberry Pi hardware I2C bus 1
i2c = I2C(1)

# PCA9685 at default address 0x40
pca = PCA9685(i2c, address=0x40)

# PWM frequency
pca.frequency = 1000

# Use Channel 0
motor = pca.channels[0]

try:
    while True:
        print("Motor ON")
        motor.duty_cycle = 0xFFFF   # 100% duty cycle
        time.sleep(2)

        print("Motor OFF")
        motor.duty_cycle = 0x0000   # 0% duty cycle
        time.sleep(2)

except KeyboardInterrupt:
    print("\nStopping motor...")

finally:
    motor.duty_cycle = 0
    pca.deinit()