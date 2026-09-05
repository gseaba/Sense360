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
# Get Distance
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

    distance = duration * 34300 / 2

    return distance


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
# Distance → Vibration %
# -----------------------------

def get_vibration(distance):

    MAX_DISTANCE = 100
    MIN_DISTANCE = 10

    if distance >= MAX_DISTANCE:
        vibration = 0

    elif distance <= MIN_DISTANCE:
        vibration = 100

    else:
        vibration = (
            (MAX_DISTANCE - distance)
            / (MAX_DISTANCE - MIN_DISTANCE)
            * 100
        )

    return vibration


# -----------------------------
# Main Loop
# -----------------------------

try:

    while True:

        distance = get_distance()

        if distance is not None:

            heading = get_heading()

            vibration = get_vibration(distance)

            motor.duty_cycle = int(
                vibration / 100 * 65535
            )

            print(
                f"Heading {heading:.1f} "
                f"Distance {distance:.1f} cm "
                f"Vibration {vibration:.0f}%"
            )

        else:

            motor.duty_cycle = 0

        time.sleep(0.1)


except KeyboardInterrupt:

    print("\nStopping...")


finally:

    motor.duty_cycle = 0
    pca.deinit()
    GPIO.cleanup()