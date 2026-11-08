
import board
import busio
from adafruit_pca9685 import PCA9685
import time

# Motor names and PCA9685 channels
MOTORS = {
    "1": ("front", 7),
    "2": ("front_right", 6),
    "3": ("right", 5),
    "4": ("back_right", 4),
    "5": ("back", 3),
    "6": ("back_left", 2),
    "7": ("left", 1),
    "8": ("front_left", 0),
}

i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 200

try:
    # Ensure all motors start off
    for _, channel in MOTORS.values():
        pca.channels[channel].duty_cycle = 0

    while True:
        print("\nSelect a motor:")
        for key, (name, channel) in MOTORS.items():
            print(f"  {key}: {name} (channel {channel})")
        print("  q: Quit")

        choice = input("Enter selection: ").strip().lower()

        if choice == "q":
            break

        if choice not in MOTORS:
            print("Invalid selection.")
            continue

        name, channel = MOTORS[choice]
        print(f"Activating {name}...")

        pca.channels[channel].duty_cycle = 65535
        time.sleep(1)
        pca.channels[channel].duty_cycle = 0

        print(f"{name} finished.")

finally:
    # Ensure all motors are off when exiting
    for _, channel in MOTORS.values():
        pca.channels[channel].duty_cycle = 0

    pca.deinit()
    print("All motors off. Exiting.")
