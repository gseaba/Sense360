
from collections import deque
import statistics
import time
import lgpio
from adafruit_pca9685 import PCA9685
import board
import busio
from HCSR04 import HCSR04

from communication.ipc import SensorPublisher


# ---------------------------------------------------------
# Configuration (Values in METERS)
# ---------------------------------------------------------

MAX_DISTANCE_M = 1.5
MIN_DISTANCE_M = 0.1

# Sensor configuration
SENSORS_CONFIG = [
    {"name": "front",       "trig": 15, "echo": 10, "motor_channel": 7},
    {"name": "front_right", "trig": 18, "echo": 17, "motor_channel": 6},
    {"name": "right",       "trig": 23, "echo": 27, "motor_channel": 5},
    {"name": "back_right",  "trig": 24, "echo": 22, "motor_channel": 4},
    {"name": "back",        "trig": 25, "echo": 9,  "motor_channel": 3},
    {"name": "back_left",   "trig": 8,  "echo": 11, "motor_channel": 2},
    {"name": "left",        "trig": 7,  "echo": 5,  "motor_channel": 1},
    {"name": "front_left",  "trig": 12, "echo": 6,  "motor_channel": 0},
]

# Sensor directions relative to the wearer
DIRECTION_ANGLES = {
    "front": 0,
    "front_right": 45,
    "right": 90,
    "back_right": 135,
    "back": 180,
    "back_left": 225,
    "left": 270,
    "front_left": 315,
}

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

try:
    chip_handle = lgpio.gpiochip_open(4)
except lgpio.error:
    chip_handle = lgpio.gpiochip_open(0)


i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 200

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


# Initialize dashboard communication
publisher = SensorPublisher()


# ---------------------------------------------------------
# Vibration Control
# ---------------------------------------------------------

def calculate_vibration_intensity(distance_m):
    """Maps distance in meters to PWM value (0.0 to 1.0)."""

    if distance_m <= 0 or distance_m >= MAX_DISTANCE_M:
        return 0.0

    if distance_m <= MIN_DISTANCE_M:
        return 1.0

    intensity = 1.0 - (
        (distance_m - MIN_DISTANCE_M) /
        (MAX_DISTANCE_M - MIN_DISTANCE_M)
    )

    return max(0.0, min(1.0, intensity))


# ---------------------------------------------------------
# Dashboard Data Generation
# ---------------------------------------------------------

def create_dashboard_snapshot(readings):
    """
    Creates a complete snapshot of the current sensor state.

    readings:
        Dictionary containing filtered sensor distances.
    """

    objects = []

    for name, angle in DIRECTION_ANGLES.items():

        distance = readings[name]

        # Only include valid detections within the
        # dashboard's operating distance.
        if distance is not None and 0 < distance < MAX_DISTANCE_M:

            objects.append({
                "sensor": name,
                "sector": round(angle / 20) % 18,
                "angle": angle,
                "distance": distance
            })

    return {
        "timestamp": time.time(),

        "sensors": readings,

        "objects": objects
    }


# ---------------------------------------------------------
# Main Control Loop
# ---------------------------------------------------------

try:

    while True:

        # Store the latest filtered reading from each sensor
        current_readings = {}

        for name in STAGGERED_KEYS:

            dev = device_dict[name]

            sensor = dev["sensor"]
            motor = dev["motor"]
            buffer = dev["buffer"]

            # 1. Start trigger pulse
            sensor.trigger()

            # 2. Delay to minimize ultrasonic crosstalk
            time.sleep(0.025)

            # 3. Read distance
            dist_m = sensor.get_distance()

            if dist_m is None:
                buffer.append(-1)
            else:
                buffer.append(dist_m)

            # 4. Filter reading
            filtered_dist = statistics.median(buffer)

            # Store valid readings for the dashboard.
            # None indicates an invalid measurement.
            if filtered_dist > 0:
                current_readings[name] = filtered_dist
            else:
                current_readings[name] = None

            # 5. Set motor intensity
            intensity = calculate_vibration_intensity(
                filtered_dist
            )

            motor.duty_cycle = int(intensity * 65535)

        # -------------------------------------------------
        # Publish sensor snapshot to dashboard server
        # -------------------------------------------------

        snapshot = create_dashboard_snapshot(current_readings)

        publisher.publish(snapshot)


finally:

    # Turn off motors and release sensor resources
    for dev in devices:
        dev["motor"].duty_cycle = 0
        dev["sensor"].cleanup()

    publisher.close()

    pca.deinit()

    try:
        lgpio.gpiochip_close(chip_handle)
    except lgpio.error:
        pass
