import time
import math
import board
import busio

from adafruit_bno08x import BNO_REPORT_ROTATION_VECTOR
from adafruit_bno08x.i2c import BNO08X_I2C


# -----------------------------
# I2C / BNO085 Setup
# -----------------------------

i2c = busio.I2C(board.SCL, board.SDA)

# Your BNO085 is at address 0x4B
bno = BNO08X_I2C(i2c, address=0x4B)

# Enable fused orientation output
bno.enable_feature(BNO_REPORT_ROTATION_VECTOR)


# -----------------------------
# Quaternion -> Heading
# -----------------------------

def quaternion_to_yaw(qi, qj, qk, qr):
    """
    Convert the BNO085 quaternion into a yaw/heading angle
    from 0 to 360 degrees.
    """

    siny_cosp = 2.0 * (qr * qk + qi * qj)
    cosy_cosp = 1.0 - 2.0 * (qj * qj + qk * qk)

    yaw_rad = math.atan2(siny_cosp, cosy_cosp)

    yaw_deg = math.degrees(yaw_rad)

    # Convert -180...180 into 0...360
    if yaw_deg < 0:
        yaw_deg += 360.0

    return yaw_deg


# -----------------------------
# State Variables
# -----------------------------

last_heading = None
last_valid_time = None

valid_count = 0
error_count = 0

# Consider IMU data stale if no good reading has
# been received for this long.
MAX_STALE_TIME = 0.5


# -----------------------------
# Main Loop
# -----------------------------

print("BNO085 IMU Test")
print("Press Ctrl+C to stop\n")

try:

    while True:

        try:

            # Read quaternion from IMU
            qi, qj, qk, qr = bno.quaternion

            # Convert quaternion into heading
            heading = quaternion_to_yaw(
                qi,
                qj,
                qk,
                qr
            )

            # Save this as the newest valid heading
            last_heading = heading
            last_valid_time = time.time()

            valid_count += 1

            print(
                f"Heading: {heading:6.1f}°   |   "
                f"Valid: {valid_count}   "
                f"Errors: {error_count}"
            )


        except (
            KeyError,
            IndexError,
            RuntimeError,
            OSError,
            ValueError
        ) as error:

            error_count += 1

            # Decide whether the last heading is still fresh enough
            # to use.
            if (
                last_heading is not None
                and last_valid_time is not None
                and time.time() - last_valid_time <= MAX_STALE_TIME
            ):

                print(
                    f"Heading: {last_heading:6.1f}° "
                    f"(LAST VALID)   |   "
                    f"IMU Error: {error}   |   "
                    f"Errors: {error_count}"
                )

            else:

                print(
                    f"Heading: NO VALID DATA   |   "
                    f"IMU Error: {error}   |   "
                    f"Errors: {error_count}"
                )

        # Approximately 10 readings per second
        time.sleep(0.1)


except KeyboardInterrupt:

    print("\nIMU test stopped.")


finally:

    print("\nResults:")
    print(f"Valid readings: {valid_count}")
    print(f"Errors:         {error_count}")

    total = valid_count + error_count

    if total > 0:
        success_rate = valid_count / total * 100

        print(
            f"Success rate:   "
            f"{success_rate:.1f}%"
        )