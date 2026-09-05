import time
import math
import RPi.GPIO as GPIO

from adafruit_extended_bus import ExtendedI2C as I2C
from adafruit_pca9685 import PCA9685
from adafruit_bno08x import BNO_REPORT_ROTATION_VECTOR
from adafruit_bno08x.i2c import BNO08X_I2C


# =========================================================
# Ultrasonic Sensor
# =========================================================

TRIG = 17
ECHO = 27

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

GPIO.output(TRIG, False)


# =========================================================
# PCA9685 + Motor
# =========================================================

pca_i2c = I2C(1)

pca = PCA9685(pca_i2c, address=0x40)

motor = pca.channels[0]


# =========================================================
# BNO085
# =========================================================

imu_i2c = I2C(8)

bno = BNO08X_I2C(imu_i2c, address=0x4B)

bno.enable_feature(BNO_REPORT_ROTATION_VECTOR)


# =========================================================
# Distance Filter Variables
# =========================================================

stored_distance = None

candidate_distance = None
candidate_count = 0

CHANGE_THRESHOLD = 15       # cm
CANDIDATE_TOLERANCE = 10    # cm
REQUIRED_READINGS = 3


# =========================================================
# Get Raw Ultrasonic Distance
# =========================================================

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


# =========================================================
# Outlier Detection
# =========================================================

def filter_distance(new_distance):

    global stored_distance
    global candidate_distance
    global candidate_count

    # First measurement
    if stored_distance is None:

        stored_distance = new_distance
        return stored_distance


    difference = abs(new_distance - stored_distance)


    # Normal believable change
    if difference <= CHANGE_THRESHOLD:

        stored_distance = new_distance

        candidate_distance = None
        candidate_count = 0

        return stored_distance


    # Large change - suspicious
    if candidate_distance is None:

        candidate_distance = new_distance
        candidate_count = 1


    # New reading agrees with suspicious reading
    elif abs(new_distance - candidate_distance) <= CANDIDATE_TOLERANCE:

        candidate_count += 1

        candidate_distance = (
            candidate_distance + new_distance
        ) / 2


    # Doesn't agree - restart candidate
    else:

        candidate_distance = new_distance
        candidate_count = 1


    # Enough repeated readings to trust new distance
    if candidate_count >= REQUIRED_READINGS:

        stored_distance = candidate_distance

        candidate_distance = None
        candidate_count = 0


    return stored_distance


# =========================================================
# Get Heading
# =========================================================

def get_heading():

    qi, qj, qk, qr = bno.quaternion

    siny_cosp = 2 * (qr * qk + qi * qj)
    cosy_cosp = 1 - 2 * (qj * qj + qk * qk)

    yaw = math.atan2(siny_cosp, cosy_cosp)

    heading = math.degrees(yaw)

    if heading < 0:
        heading += 360

    return heading


# =========================================================
# Distance -> Vibration
# =========================================================

def get_vibration(distance):

    MAX_DISTANCE = 100
    MIN_DISTANCE = 10

    MIN_AMPLITUDE = 20
    MAX_AMPLITUDE = 100

    MIN_FREQUENCY = 50
    MAX_FREQUENCY = 300


    # Too far away
    if distance >= MAX_DISTANCE:

        return 0, MIN_FREQUENCY


    # Extremely close
    if distance <= MIN_DISTANCE:

        return 100, MAX_FREQUENCY


    # Convert distance to 0 - 1
    closeness = (
        MAX_DISTANCE - distance
    ) / (
        MAX_DISTANCE - MIN_DISTANCE
    )


    # Amplitude
    amplitude = (
        MIN_AMPLITUDE
        + closeness
        * (MAX_AMPLITUDE - MIN_AMPLITUDE)
    )


    # Frequency
    frequency = (
        MIN_FREQUENCY
        + closeness
        * (MAX_FREQUENCY - MIN_FREQUENCY)
    )


    return amplitude, frequency


# =========================================================
# Main Loop
# =========================================================

try:

    while True:

        raw_distance = get_distance()

        if raw_distance is None:

            motor.duty_cycle = 0
            continue


        # Filter bad ultrasonic readings
        distance = filter_distance(raw_distance)

        # Get heading
        heading = get_heading()

        # Calculate motor settings
        amplitude, frequency = get_vibration(distance)


        # Motor OFF
        if amplitude == 0:

            motor.duty_cycle = 0


        # Motor ON
        else:

            # Change PWM frequency
            pca.frequency = int(frequency)

            # Change PWM amplitude
            motor.duty_cycle = int(
                amplitude / 100 * 65535
            )

        # Print status
        print(
            f"Heading {heading:.1f} "
            f"Distance {distance:.1f} cm "
            f"Vibration {amplitude:.0f}% "
            f"Frequency {frequency:.0f} Hz"
        )


        time.sleep(0.1)


except KeyboardInterrupt:

    print("\nStopping...")


finally:

    motor.duty_cycle = 0
    pca.deinit()
    GPIO.cleanup()
