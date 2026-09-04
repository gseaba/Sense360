import time
import math
import RPi.GPIO as GPIO

from adafruit_extended_bus import ExtendedI2C as I2C
from adafruit_pca9685 import PCA9685
from adafruit_bno08x import BNO_REPORT_ROTATION_VECTOR
from adafruit_bno08x.i2c import BNO08X_I2C


# -----------------------------
# Ultrasonic Sensor
# -----------------------------

TRIG = 17
ECHO = 27

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

GPIO.output(TRIG, False)


# -----------------------------
# PCA9685
# -----------------------------

pca_i2c = I2C(1)

pca = PCA9685(pca_i2c, address=0x40)
pca.frequency = 200

motor = pca.channels[0]


# -----------------------------
# BNO085
# -----------------------------

imu_i2c = I2C(8)

bno = BNO08X_I2C(imu_i2c, address=0x4B)
bno.enable_feature(BNO_REPORT_ROTATION_VECTOR)


# -----------------------------
# Distance Filter Variables
# -----------------------------

stored_distance = None

candidate_distance = None
candidate_count = 0

CHANGE_THRESHOLD = 15       # cm
CANDIDATE_TOLERANCE = 10    # cm
REQUIRED_READINGS = 3


# -----------------------------
# Get Raw Distance
# -----------------------------

def get_distance():

    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    timeout = time.time() + 0.05

    while GPIO.input(ECHO) == 0:
        start = time.time()

        if time.time() > timeout:
            return None

    timeout = time.time() + 0.05

    while GPIO.input(ECHO) == 1:
        stop = time.time()

        if time.time() > timeout:
            return None

    duration = stop - start

    return duration * 34300 / 2


# -----------------------------
# Filter Distance
# -----------------------------

def filter_distance(new_distance):

    global stored_distance
    global candidate_distance
    global candidate_count

    # First reading
    if stored_distance is None:

        stored_distance = new_distance
        return stored_distance


    difference = abs(new_distance - stored_distance)


    # Reading makes sense
    if difference <= CHANGE_THRESHOLD:

        stored_distance = new_distance

        candidate_distance = None
        candidate_count = 0

        return stored_distance


    # Reading is very different
    else:

        # Start a new candidate
        if candidate_distance is None:

            candidate_distance = new_distance
            candidate_count = 1


        # New reading agrees with candidate
        elif abs(new_distance - candidate_distance) <= CANDIDATE_TOLERANCE:

            candidate_count += 1

            # Average candidate readings
            candidate_distance = (
                candidate_distance + new_distance
            ) / 2


        # New reading does not agree with candidate
        else:

            candidate_distance = new_distance
            candidate_count = 1


        # Enough readings agree with new distance
        if candidate_count >= REQUIRED_READINGS:

            stored_distance = candidate_distance

            candidate_distance = None
            candidate_count = 0


        return stored_distance


# -----------------------------
# Get Heading
# -----------------------------

def get_heading():

    qi, qj, qk, qr = bno.quaternion

    siny_cosp = 2 * (qr * qk + qi * qj)
    cosy_cosp = 1 - 2 * (qj * qj + qk * qk)

    yaw = math.atan2(siny_cosp, cosy_cosp)

    heading = math.degrees(yaw)

    if heading < 0:
        heading += 360

    return heading


# -----------------------------
# Distance -> Pulse Frequency
# -----------------------------

def get_frequency(distance):

    MAX_DISTANCE = 100
    MIN_DISTANCE = 10

    if distance >= MAX_DISTANCE:
        return 0

    if distance <= MIN_DISTANCE:
        return 100

    frequency = 0.5 + (
        (MAX_DISTANCE - distance)
        / (MAX_DISTANCE - MIN_DISTANCE)
        * 4.5
    )

    return frequency


# -----------------------------
# Main Loop
# -----------------------------

try:

    while True:

        raw_distance = get_distance()

        if raw_distance is None:

            motor.duty_cycle = 0
            continue


        # Filter the ultrasonic reading
        distance = filter_distance(raw_distance)

        heading = get_heading()

        frequency = get_frequency(distance)


        # -------------------------
        # No vibration
        # -------------------------

        if frequency == 0:

            motor.duty_cycle = 0

            print(
                f"Heading {heading:.1f} "
                f"Distance {distance:.1f} cm "
                f"Vibration 0%"
            )

            time.sleep(0.1)


        # -------------------------
        # Continuous vibration
        # -------------------------

        elif frequency == 100:

            motor.duty_cycle = 0xFFFF

            print(
                f"Heading {heading:.1f} "
                f"Distance {distance:.1f} cm "
                f"Vibration 100%"
            )

            time.sleep(0.1)


        # -------------------------
        # Pulsing vibration
        # -------------------------

        else:

            period = 1 / frequency

            motor.duty_cycle = 0xFFFF

            print(
                f"Heading {heading:.1f} "
                f"Distance {distance:.1f} cm "
                f"Vibration 100%"
            )

            time.sleep(0.1)

            motor.duty_cycle = 0

            time.sleep(max(0, period - 0.1))


except KeyboardInterrupt:

    print("\nStopping...")


finally:

    motor.duty_cycle = 0
    pca.deinit()
    GPIO.cleanup()