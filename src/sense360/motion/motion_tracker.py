"""
motion_tracker.py

Tracks the orientation and motion of the Sense360 wearer using the
BNO085 IMU.

The MotionTracker provides the rest of Sense360 with information about
how the belt is oriented and whether it appears to be moving.

Current responsibilities:
    - Communicate with the BNO085 over its dedicated I2C bus.
    - Read the BNO085 rotation-vector quaternion.
    - Convert the quaternion into heading, pitch, and roll.
    - Read linear acceleration with gravity removed.
    - Read gyroscope data.
    - Estimate whether the wearer is currently moving.
    - Limit how frequently the IMU is read.
    - Keep BNO085-specific code out of the WorldModel.

The WorldModel should not communicate with the BNO085 directly.
Instead, it asks the MotionTracker for information such as:

    motion_tracker.get_heading()

The BNO085 can detect short-term motion through acceleration and
rotation, but this class does NOT attempt to determine the wearer's
absolute X/Y position by integrating acceleration.

IMU-only position estimates accumulate error too quickly for that to
be reliable over long periods.

Current Sense360 hardware:
    BNO085
        I2C bus: 8
        Address: 0x4B
        SDA: GPIO20 / physical pin 38
        SCL: GPIO21 / physical pin 40
"""

import math
import time

from adafruit_extended_bus import ExtendedI2C as I2C

from adafruit_bno08x import (
    BNO_REPORT_ROTATION_VECTOR,
    BNO_REPORT_LINEAR_ACCELERATION,
    BNO_REPORT_GYROSCOPE,
)

from adafruit_bno08x.i2c import BNO08X_I2C


class MotionTracker:
    """
    Tracks the current orientation and motion of the Sense360 wearer.
    """

    def __init__(
        self,
        i2c_bus: int,
        i2c_address: int,
        min_update_interval_s: float = 0.02,
        moving_acceleration_threshold_m_s2: float = 0.35,
        moving_gyro_threshold_rad_s: float = 0.15,
        heading_offset_deg: float = 0.0,
    ):
        """
        Create the MotionTracker.

        Parameters
        ----------
        i2c_bus : int
            Linux I2C bus number used by the BNO085.

            Current Sense360 hardware:
                8 -> /dev/i2c-8

        i2c_address : int
            BNO085 I2C address.

            Current Sense360 hardware:
                0x4B

        min_update_interval_s : float
            Minimum amount of time between MotionTracker updates.

            Default:
                0.02 seconds = maximum update rate of about 50 Hz.

        moving_acceleration_threshold_m_s2 : float
            Linear acceleration magnitude above which the wearer is
            considered to be moving.

        moving_gyro_threshold_rad_s : float
            Angular velocity magnitude above which the wearer is
            considered to be moving or turning.

        heading_offset_deg : float
            Constant angular correction applied to the calculated
            heading.

            This can later compensate for the physical orientation of
            the BNO085 when it is mounted on the belt.
        """

        self.i2c_bus = i2c_bus
        self.i2c_address = i2c_address

        self.min_update_interval_s = min_update_interval_s

        self.moving_acceleration_threshold_m_s2 = (
            moving_acceleration_threshold_m_s2
        )

        self.moving_gyro_threshold_rad_s = (
            moving_gyro_threshold_rad_s
        )

        self.heading_offset_deg = heading_offset_deg

        # ---------------------------------------------------------
        # Current orientation
        # ---------------------------------------------------------

        self.heading_deg = 0.0
        self.pitch_deg = 0.0
        self.roll_deg = 0.0

        # ---------------------------------------------------------
        # Current linear acceleration
        #
        # Gravity has already been removed by the BNO085.
        # Units: meters per second squared.
        # ---------------------------------------------------------

        self.linear_acceleration = (
            0.0,
            0.0,
            0.0,
        )

        # ---------------------------------------------------------
        # Current angular velocity.
        #
        # Units: radians per second.
        # ---------------------------------------------------------

        self.gyro = (
            0.0,
            0.0,
            0.0,
        )

        self.is_moving = False

        # Timestamp of the last successful update.
        self.last_updated = None

        self._closed = False

        # ---------------------------------------------------------
        # Open the BNO085's dedicated Linux I2C bus.
        # ---------------------------------------------------------

        self.i2c = I2C(
            self.i2c_bus
        )

        self.bno = BNO08X_I2C(
            self.i2c,
            address=self.i2c_address,
        )

        # ---------------------------------------------------------
        # Enable the BNO085 reports Sense360 currently needs.
        # ---------------------------------------------------------

        self.bno.enable_feature(
            BNO_REPORT_ROTATION_VECTOR
        )

        self.bno.enable_feature(
            BNO_REPORT_LINEAR_ACCELERATION
        )

        self.bno.enable_feature(
            BNO_REPORT_GYROSCOPE
        )

    def _ready_for_update(self):
        """
        Determine whether enough time has passed for another IMU update.

        Returns
        -------
        bool
            True if the MotionTracker should read the BNO085.
        """

        if self.last_updated is None:
            return True

        elapsed_time = (
            time.monotonic()
            - self.last_updated
        )

        return (
            elapsed_time
            >= self.min_update_interval_s
        )

    def _quaternion_to_euler(
        self,
        quat_i,
        quat_j,
        quat_k,
        quat_real,
    ):
        """
        Convert a quaternion into heading, pitch, and roll.

        The BNO085 rotation-vector report returns the quaternion as:

            i, j, k, real

        These correspond to the conventional quaternion components:

            x, y, z, w

        Returns
        -------
        tuple
            heading_deg, pitch_deg, roll_deg
        """

        x = quat_i
        y = quat_j
        z = quat_k
        w = quat_real

        # ---------------------------------------------------------
        # Roll
        # ---------------------------------------------------------

        sin_roll_cos_pitch = (
            2.0
            * (
                w * x
                + y * z
            )
        )

        cos_roll_cos_pitch = (
            1.0
            - 2.0
            * (
                x * x
                + y * y
            )
        )

        roll_rad = math.atan2(
            sin_roll_cos_pitch,
            cos_roll_cos_pitch,
        )

        # ---------------------------------------------------------
        # Pitch
        # ---------------------------------------------------------

        sin_pitch = (
            2.0
            * (
                w * y
                - z * x
            )
        )

        # Protect against small numerical errors that could place
        # sin_pitch slightly outside the valid asin range.
        sin_pitch = max(
            -1.0,
            min(
                1.0,
                sin_pitch,
            ),
        )

        pitch_rad = math.asin(
            sin_pitch
        )

        # ---------------------------------------------------------
        # Heading / yaw
        # ---------------------------------------------------------

        sin_yaw_cos_pitch = (
            2.0
            * (
                w * z
                + x * y
            )
        )

        cos_yaw_cos_pitch = (
            1.0
            - 2.0
            * (
                y * y
                + z * z
            )
        )

        yaw_rad = math.atan2(
            sin_yaw_cos_pitch,
            cos_yaw_cos_pitch,
        )

        roll_deg = math.degrees(
            roll_rad
        )

        pitch_deg = math.degrees(
            pitch_rad
        )

        heading_deg = (
            math.degrees(yaw_rad)
            + self.heading_offset_deg
        ) % 360.0

        return (
            heading_deg,
            pitch_deg,
            roll_deg,
        )

    def _calculate_motion_state(self):
        """
        Estimate whether the Sense360 wearer is currently moving.

        Movement is detected using both:

            - Linear acceleration
            - Angular velocity

        This means the wearer may be considered moving if they are:

            - Walking
            - Accelerating
            - Turning
            - Rotating the belt

        This is intentionally a simple first version.

        The thresholds should be tuned using real Sense360 test data.
        """

        accel_x, accel_y, accel_z = (
            self.linear_acceleration
        )

        gyro_x, gyro_y, gyro_z = (
            self.gyro
        )

        acceleration_magnitude = math.sqrt(
            accel_x ** 2
            + accel_y ** 2
            + accel_z ** 2
        )

        gyro_magnitude = math.sqrt(
            gyro_x ** 2
            + gyro_y ** 2
            + gyro_z ** 2
        )

        acceleration_motion = (
            acceleration_magnitude
            >= self.moving_acceleration_threshold_m_s2
        )

        rotation_motion = (
            gyro_magnitude
            >= self.moving_gyro_threshold_rad_s
        )

        self.is_moving = (
            acceleration_motion
            or rotation_motion
        )

    def update(self):
        """
        Read the latest BNO085 orientation and motion data.

        Returns
        -------
        bool
            True if new IMU data was successfully processed.

            False if:
                - The minimum update interval has not elapsed.
                - The BNO085 has not produced the required data yet.

        Existing MotionTracker values remain unchanged when no new data
        is available.
        """

        if self._closed:
            raise RuntimeError(
                "MotionTracker cannot be updated after cleanup()."
            )

        if not self._ready_for_update():
            return False

        # ---------------------------------------------------------
        # Read quaternion.
        # ---------------------------------------------------------

        quaternion = self.bno.quaternion

        if quaternion is None:
            return False

        (
            quat_i,
            quat_j,
            quat_k,
            quat_real,
        ) = quaternion

        (
            self.heading_deg,
            self.pitch_deg,
            self.roll_deg,
        ) = self._quaternion_to_euler(
            quat_i,
            quat_j,
            quat_k,
            quat_real,
        )

        # ---------------------------------------------------------
        # Read linear acceleration.
        # ---------------------------------------------------------

        linear_acceleration = (
            self.bno.linear_acceleration
        )

        if linear_acceleration is not None:
            self.linear_acceleration = (
                linear_acceleration
            )

        # ---------------------------------------------------------
        # Read gyroscope.
        # ---------------------------------------------------------

        gyro = self.bno.gyro

        if gyro is not None:
            self.gyro = gyro

        # Determine whether the wearer appears to be moving.
        self._calculate_motion_state()

        self.last_updated = time.monotonic()

        return True

    def get_heading(self):
        """
        Return the current heading in degrees.

        Returns
        -------
        float
            Heading normalized to:

                0 <= heading < 360
        """

        return self.heading_deg

    def get_orientation(self):
        """
        Return the current heading, pitch, and roll.

        Returns
        -------
        tuple
            heading_deg, pitch_deg, roll_deg
        """

        return (
            self.heading_deg,
            self.pitch_deg,
            self.roll_deg,
        )

    def get_linear_acceleration(self):
        """
        Return current gravity-compensated linear acceleration.

        Returns
        -------
        tuple
            x, y, z acceleration in meters per second squared.
        """

        return self.linear_acceleration

    def get_gyro(self):
        """
        Return current angular velocity.

        Returns
        -------
        tuple
            x, y, z angular velocity in radians per second.
        """

        return self.gyro

    def get_is_moving(self):
        """
        Return whether the wearer currently appears to be moving.
        """

        return self.is_moving

    def get_data_age(self):
        """
        Return the age of the most recent successful IMU update.

        Returns
        -------
        float | None
            Age in seconds.

            None means no successful IMU update has occurred yet.
        """

        if self.last_updated is None:
            return None

        return (
            time.monotonic()
            - self.last_updated
        )

    def cleanup(self):
        """
        Release the BNO085 I2C bus.

        This should be called when Sense360 shuts down.
        """

        if self._closed:
            return

        try:
            self.i2c.deinit()
        except Exception:
            pass

        self._closed = True