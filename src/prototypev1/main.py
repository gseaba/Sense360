from collections import deque
import statistics
import time
from gpiozero import PWMOutputDevice  # Standard library for PWM motor control
from hcsr04 import HCSR04  # Assuming custom class or wrapper

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------
MAX_DISTANCE_CM = 150  # Distance where vibration starts (1.5 m)
MIN_DISTANCE_CM = 10   # Distance for maximum vibration intensity (10 cm)

# Define each direction with unique GPIO pins
# Adjust trig, echo, and motor GPIO pin numbers for your wiring set up
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

# ---------------------------------------------------------
# Hardware Initialization
# ---------------------------------------------------------
devices = []

for cfg in SENSORS_CONFIG:
    devices.append({
        "name": cfg["name"],
        "sensor": HCSR04(trig_pin=cfg["trig"], echo_pin=cfg["echo"]),
        "motor": PWMOutputDevice(cfg["motor_pin"]),
        "buffer": deque(maxlen=3)
    })

def calculate_vibration_intensity(distance_cm):
    """Maps distance to a PWM value between 0.0 (off) and 1.0 (full speed)."""
    if distance_cm >= MAX_DISTANCE_CM:
        return 0.0
    if distance_cm <= MIN_DISTANCE_CM:
        return 1.0
    
    # Closer distance = Higher intensity (inverse linear mapping)
    intensity = 1.0 - ((distance_cm - MIN_DISTANCE_CM) / (MAX_DISTANCE_CM - MIN_DISTANCE_CM))
    return max(0.0, min(1.0, intensity))

# Fire opposing/staggered sensors rather than adjacent ones to minimize crosstalk risk
STAGGERED_KEYS = [
    "front", "back", 
    "right", "left", 
    "front_right", "back_left", 
    "back_right", "front_left"
]

# Create a lookup dictionary for quick retrieval by key
device_dict = {dev["name"]: dev for dev in devices}

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

            # Trigger measurement
            sensor.trigger()
            time.sleep(0.025)  # Brief delay to prevent ultrasonic signal cross-talk

            # Read distance
            dist = sensor.get_distance()
            if dist is not None:
                buffer.append(dist)

            # Apply median filter and update motor intensity
            if buffer:
                filtered_dist = statistics.median(buffer)
                intensity = calculate_vibration_intensity(filtered_dist)
                motor.value = intensity
            else:
                motor.value = 0.0

finally:
    # Safely turn off motors and release sensor resources
    for dev in devices:
        dev["motor"].value = 0
        dev["motor"].close()
        if hasattr(dev["sensor"], "cleanup"):
            dev["sensor"].cleanup()