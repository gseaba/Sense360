"""
observation.py

Defines the standard data format used for environmental sensor
measurements throughout Sense360.

Every environmental sensor should convert its hardware-specific output
into one or more Observation objects before passing data to the rest of
the system.

This creates a common interface between sensors and the WorldModel.

Examples:
    - An HC-SR04 may generate one Observation per measurement.
    - A LiDAR scanner may generate hundreds of Observations per scan.
    - A future time-of-flight sensor can use the same format.

The WorldModel should not need to know which type of sensor created an
Observation. It only needs the measurement data contained within it.
"""

from dataclasses import dataclass


@dataclass
class Observation:
    """
    Represents one measurement of an object in the environment.

    Attributes
    ----------
    distance_m : float
        Measured distance to the object in meters.

    relative_angle_deg : float
        Direction of the measurement relative to the Sense360 belt.

        Suggested convention:
            0 degrees   = directly forward
            90 degrees  = right
            180 degrees = behind
            270 degrees = left

        The WorldModel can combine this relative angle with the wearer's
        heading from the MotionTracker to determine the measurement's
        direction in the surrounding environment.

    timestamp : float
        Time when the measurement was taken.

        Sense360 uses time.monotonic() timestamps so the age of sensor
        data can be calculated reliably without being affected by changes
        to the Raspberry Pi's system clock.

    sensor_id : str
        Identifier for the sensor that produced the measurement.

        Examples:
            "sensor_1"
            "front_ultrasonic"
            "lidar_1"

    confidence : float
        Estimate of how trustworthy the measurement is.

        Expected range:
            0.0 = no confidence
            1.0 = full confidence

        HC-SR04 measurements can initially use 1.0 for valid readings.
        More advanced confidence calculations can be added later.
    """

    distance_m: float
    relative_angle_deg: float
    timestamp: float
    sensor_id: str
    confidence: float = 1.0