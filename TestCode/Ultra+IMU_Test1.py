import time
import math
import board
import busio
import RPi.GPIO as GPIO

from adafruit_bno08x import BNO_REPORT_ROTATION_VECTOR
from adafruit_bno08x.i2c import BNO08X_I2C


# -----------------------------
# Ultrasonic Sensor GPIO
# -----------------------------

TRIG = 17
ECHO = 27

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

GPIO.output(TRIG, GPIO.LOW)


# -----------------------------
# BNO085 IMU
# -----------------------------

i2c = busio.I2C(board.SCL, board.SDA)

# Your BNO085 was detected at address 0x4B
bno = BNO08X_I2C(i2c, address=0x4B)

# Enable orientation quaternion output
bno.enable_feature(BNO_REPORT_ROTATION_VECTOR)


# -----------------------------
# Ultrasonic Measurement
# -----------------------------

def get_distance():

    # Trigger 10 us ultrasonic pulse
    GPIO.output(TRIG, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG, GPIO.LOW)

    # Wait for ECHO rising edge
    timeout = time.perf_counter() + 0.03

    while GPIO.input(ECHO) == GPIO.LOW:
        if time.perf_counter() > timeout:
            return None

    pulse_start = time.perf_counter()

    # Wait for ECHO falling edge
    timeout = time.perf_counter() + 0.03

    while GPIO.input(ECHO) == GPIO.HIGH:
        if time.perf_counter() > timeout:
            return None

    pulse_end = time.perf_counter()

    pulse_duration = pulse_end - pulse_start

    # Speed of sound = ~34300 cm/s
    distance_cm = pulse_duration * 34300 / 2

    return distance_cm


# -----------------------------
# Quaternion -> Yaw
# -----------------------------

def quaternion_to_yaw(qi, qj, qk, qr):

    # Convert quaternion to yaw angle
    siny_cosp = 2 * (qr * qk + qi * qj)
    cosy_cosp = 1 - 2 * (qj * qj + qk * qk)

    yaw = math.atan2(siny_cosp, cosy_cosp)

    # Convert radians to degrees
    yaw_deg = math.degrees(yaw)

    # Convert -180...180 to 0...360
    if yaw_deg < 0:
        yaw_deg += 360

    return yaw_deg


# -----------------------------
# Main Test Loop
# -----------------------------

print("Ultrasonic + BNO085 Test")
print("Press Ctrl+C to stop\n")

time.sleep(1)

try:

    while True:

        # -------------------------
        # Trigger ultrasonic sensor
        # -------------------------

        distance = get_distance()

        # -------------------------
        # Read IMU orientation
        # -------------------------

        qi, qj, qk, qr = bno.quaternion

        heading = quaternion_to_yaw(
            qi,
            qj,
            qk,
            qr
        )

        # -------------------------
        # Print results together
        # -------------------------

        if distance is None:

            print(
                f"Distance: NO ECHO   |   "
                f"Heading: {heading:6.1f}°"
            )

        else:

            print(
                f"Distance: {distance:6.1f} cm   |   "
                f"Heading: {heading:6.1f}°"
            )

        # Avoid retriggering ultrasonic sensor too quickly
        time.sleep(0.1)


except KeyboardInterrupt:

    print("\nTest stopped.")


finally:

    GPIO.cleanup()