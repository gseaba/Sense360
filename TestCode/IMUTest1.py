import time
import math
import board
import busio

from adafruit_bno08x import BNO_REPORT_ROTATION_VECTOR
from adafruit_bno08x.i2c import BNO08X_I2C


# -----------------------------
# IMU Setup
# -----------------------------

i2c = busio.I2C(board.SCL, board.SDA)

# Your BNO085 is at 0x4B
bno = BNO08X_I2C(i2c, address=0x4B)

bno.enable_feature(BNO_REPORT_ROTATION_VECTOR)


# -----------------------------
# Quaternion -> Heading
# -----------------------------

def quaternion_to_yaw(qi, qj, qk, qr):

    siny_cosp = 2 * (qr * qk + qi * qj)
    cosy_cosp = 1 - 2 * (qj * qj + qk * qk)

    yaw = math.atan2(siny_cosp, cosy_cosp)

    yaw_deg = math.degrees(yaw)

    if yaw_deg < 0:
        yaw_deg += 360

    return yaw_deg


# -----------------------------
# Main Test
# -----------------------------

print("BNO085 IMU Test")
print("Press Ctrl+C to stop\n")

last_heading = None
last_valid_time = 0

error_count = 0
valid_count = 0

try:

    while True:

        try:

            qi, qj, qk, qr = bno.quaternion

            heading = quaternion_to_yaw(
                qi,
                qj,
                qk,
                qr
            )

            last_heading = heading
            last_valid_time = time.monotonic()

            valid_count += 1

            print(
                f"Heading: {heading:6.1f}°   |   "
                f"Valid: {valid_count}   "
                f"Errors: {error_count}"
            )

        except (KeyError, RuntimeError, OSError, ValueError) as error:

            error_count += 1

            age = time.monotonic() - last_valid_time

            # Use last valid reading if it is still recent
            if last_heading is not None and age <= 0.5:

                print(
                    f"Heading: {last_heading:6.1f}° "
                    f"(LAST VALID)   |   "
                    f"IMU Error: {error}   |   "
                    f"Errors: {error_count}"
                )

            else:

                print(
                    f"Heading: INVALID   |   "
                    f"IMU Error: {error}   |   "
                    f"Errors: {error_count}"
                )

        time.sleep(0.1)


except KeyboardInterrupt:

    print("\nIMU test stopped.")

    total = valid_count + error_count

    if total > 0:
        error_rate = 100 * error_count / total

        print(f"Valid readings: {valid_count}")
        print(f"Errors: {error_count}")
        print(f"Error rate: {error_rate:.1f}%")