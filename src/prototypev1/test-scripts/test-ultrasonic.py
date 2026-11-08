
import time
import lgpio
from HCSR04 import HCSR04

# Sensor names and GPIO pins from main.py
SENSORS = {
    "1": ("front",       15, 10),
    "2": ("front_right", 18, 17),
    "3": ("right",       23, 27),
    "4": ("back_right",  24, 22),
    "5": ("back",        25, 9),
    "6": ("back_left",   8, 11),
    "7": ("left",        7, 5),
    "8": ("front_left",  12, 6),
}

# Open GPIO chip, matching main.py
try:
    chip_handle = lgpio.gpiochip_open(4)
except lgpio.error:
    chip_handle = lgpio.gpiochip_open(0)

sensors = {}

try:
    # Initialize each sensor
    for key, (name, trig, echo) in SENSORS.items():
        sensors[key] = HCSR04(
            trig_pin=trig,
            echo_pin=echo,
            chip_handle=chip_handle
        )

    while True:
        print("\nSelect a distance sensor:")
        for key, (name, trig, echo) in SENSORS.items():
            print(f"  {key}: {name} (TRIG={trig}, ECHO={echo})")
        print("  q: Quit")

        choice = input("Enter selection: ").strip().lower()

        if choice == "q":
            break

        if choice not in sensors:
            print("Invalid selection.")
            continue

        name = SENSORS[choice][0]
        sensor = sensors[choice]

        print(f"Reading {name} sensor...")

        sensor.trigger()
        time.sleep(0.025)
        distance_m = sensor.get_distance()

        if distance_m is None or distance_m <= 0:
            print("No valid distance reading.")
        else:
            print(f"Distance: {distance_m:.3f} m "
                  f"({distance_m * 100:.1f} cm)")

finally:
    for sensor in sensors.values():
        sensor.cleanup()

    try:
        lgpio.gpiochip_close(chip_handle)
    except lgpio.error:
        pass

    print("Sensor test ended.")
