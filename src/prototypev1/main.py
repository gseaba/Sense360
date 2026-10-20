from collections import deque
import statistics
import time
import lgpio
from adafruit_pca9685 import PCA9685
import board
import busio
from hcsr04 import HCSR04

# ---------------------------------------------------------
# Configuration (Values in METERS)
# ---------------------------------------------------------
MAX_DISTANCE_M = 1.5  # Distance where vibration starts (1.5 m)
MIN_DISTANCE_M = 0.1  # Distance for max vibration intensity (0.1 m / 10 cm)

# Define each direction with unique GPIO pins
SENSORS_CONFIG = [
    {"name": "front",       "trig": 15, "echo": 10, "motor_channel": 7},
    {"name": "front_right", "trig": 18, "echo": 17, "motor_channel": 6},
    {"name": "right",       "trig": 23, "echo": 27, "motor_channel": 5},
    {"name": "back_right",  "trig": 24,  "echo": 22,  "motor_channel": 4},
    {"name": "back",        "trig": 25, "echo": 9, "motor_channel": 3},
    {"name": "back_left",   "trig": 8, "echo": 11, "motor_channel": 2},
    {"name": "left",        "trig": 7, "echo": 5, "motor_channel": 1},
    {"name": "front_left",  "trig": 12, "echo": 6, "motor_channel": 0},
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


i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 1000

devices = []

for cfg in SENSORS_CONFIG:
    devices.append({
        "name": cfg["name"],
        "sensor": HCSR04(
            trig_pin=cfg["trig"], 
            echo_pin=cfg["echo"], 
            chip_handle=chip_handle
        ),
        "motor": pca.channels[cfg["motor_channel"]],
        "buffer": deque(maxlen=3)
    })

device_dict = {dev["name"]: dev for dev in devices}

def calculate_vibration_intensity(distance_m):
    """Maps distance in meters to PWM value (0.0 to 1.0)."""
    # Treat invalid/out-of-bounds readings as off
    if distance_m <= 0 or distance_m >= MAX_DISTANCE_M:
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

            # If measurement failed/out-of-range, append -1 as a placeholder
            if dist_m is None:
                buffer.append(-1)
            else:
                buffer.append(dist_m)

            # 4. Filter reading and set motor intensity
            if buffer:
                filtered_dist = statistics.median(buffer)
                intensity = calculate_vibration_intensity(filtered_dist)
                motor.duty_cycle = int(intensity * 65535)
            else:
                motor.duty_cycle = 0

finally:
    # Safely turn off motors and release sensor resources
    for dev in devices:
        dev["motor"].duty_cycle = 0
        dev["sensor"].cleanup()
        dev["sensor"].cleanup()

    pca.deinit()
        
    try:
        lgpio.gpiochip_close(chip_handle)
    except lgpio.error:
        pass