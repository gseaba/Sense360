from collections import deque
import statistics
import time
import lgpio
from gpiozero import PWMOutputDevice
from hcsr04 import HCSR04

# ---------------------------------------------------------
# Configuration (Values in METERS)
# ---------------------------------------------------------
MAX_DISTANCE_M = 1.5  # Distance where vibration starts (1.5 m)
MIN_DISTANCE_M = 0.1  # Distance for max vibration intensity (0.1 m / 10 cm)

# Define each direction with unique GPIO pins
SENSORS_CONFIG = [
    {"name": "front",       "trig": 17, "echo": 27, "motor_pin": 18},
    {"name": "front_right", "trig": 22, "echo": 23, "motor_pin": 24},
    {"name": "right",       "trig": 24, "echo": 25, "motor_pin": 12},
    {"name": "back_right",  "trig": 5,  "echo": 6,  "motor_pin": 13},
    {"name": "back",        "trig": 13, "echo": 19, "motor_pin": 19},
    {"name": "back_left",   "trig": 26, "echo": 21, "motor_pin": 20},
    {"name": "left",        "trig": 20, "echo": 16, "motor_pin": 21},
    {"name": "front_left",  "trig": 16, "echo": 12, "motor_pin": 6},
]

# Stagger sensor triggering order to minimize ultrasonic crosstalk
STAGGERED_KEYS = [
    "front", "back", 
    "right", "left", 
    "front_right", "back_left", 
    "back_right", "front_left"
]

# ---------------------------------------------------------
# Hardware Initialization
# ---------------------------------------------------------
# Open a single shared chip handle for all 8 sensors
try:
    chip_handle = lgpio.gpiochip_open(4)
except lgpio.error:
    chip_handle = lgpio.gpiochip_open(0)

devices = []

for cfg in SENSORS_CONFIG:
    devices.append({
        "name": cfg["name"],
        "sensor": HCSR04(
            trig_pin=cfg["trig"], 
            echo_pin=cfg["echo"], 
            chip_handle=chip_handle
        ),
        "motor": PWMOutputDevice(cfg["motor_pin"]),
        "buffer": deque(maxlen=3)
    })

device_dict = {dev["name"]: dev for dev in devices}

def calculate_vibration_intensity(distance_m):
    """Maps distance in meters to a PWM value between 0.0 and 1.0."""
    if distance_m >= MAX_DISTANCE_M:
        return 0.0
    if distance_m <= MIN_DISTANCE_M:
        return 1.0
    
    intensity = 1.0 - ((distance_m - MIN_DISTANCE_M) / (MAX_DISTANCE_M - MIN_DISTANCE_M))
    return max(0.0, min(1.0, intensity))

# ---------------------------------------------------------
# Main Control Loop
# ---------------------------------------------------------
try:
    while True:
        for name in STAGGERED_KEYS:
            dev = device_dict[name]
            sensor = dev["sensor"]
            motor = dev["motor"]
            buffer = dev["buffer"]

            # 1. Start trigger pulse
            sensor.trigger()

            # 2. Delay to allow echo measurement + decay time (prevents crosstalk)
            time.sleep(0.025)

            # 3. Read distance (returns meters or None)
            dist_m = sensor.get_distance()
            if dist_m is not None:
                buffer.append(dist_m)

            # 4. Filter reading and set motor intensity
            if buffer:
                filtered_dist = statistics.median(buffer)
                motor.value = calculate_vibration_intensity(filtered_dist)
            else:
                motor.value = 0.0

finally:
    # Safely turn off motors and release sensor resources
    for dev in devices:
        dev["motor"].value = 0
        dev["motor"].close()
        dev["sensor"].cleanup()
        
    try:
        lgpio.gpiochip_close(chip_handle)
    except lgpio.error:
        pass