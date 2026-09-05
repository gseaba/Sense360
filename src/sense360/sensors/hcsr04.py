"""
hcsr04.py

Implements the Sensor interface for one HC-SR04 ultrasonic sensor.

This class is responsible only for hardware-specific ultrasonic
measurement tasks, including:
    - Controlling the TRIG pin
    - Reading the ECHO pin
    - Measuring echo travel time
    - Converting travel time into distance
    - Returning the result as an Observation

It should NOT decide how the measurement affects the world map or
how the vibration motors respond. Those responsibilities belong to
other parts of the Sense360 system.
"""

import time

from .sensor import Sensor
from ..models.observation import Observation


class HCSR04(Sensor):
    """Represents one HC-SR04 ultrasonic distance sensor."""

    def __init__(
        self,
        sensor_id: str,
        trig_pin: int,
        echo_pin: int,
        relative_angle_deg: float,
    ):
        self.sensor_id = sensor_id
        self.trig_pin = trig_pin
        self.echo_pin = echo_pin
        self.relative_angle_deg = relative_angle_deg

    def read_distance(self):
        """
        Read one distance measurement from the HC-SR04.

        The actual GPIO trigger/echo timing code will be added here.
        """

        # TODO: Move working HC-SR04 GPIO code here.
        raise NotImplementedError("HC-SR04 GPIO measurement code not added yet.")

    def get_observations(self):
        """Take one ultrasonic measurement and return it as an Observation."""

        distance = self.read_distance()

        observation = Observation(
            distance_m=distance,
            relative_angle_deg=self.relative_angle_deg,
            timestamp=time.monotonic(),
            sensor_id=self.sensor_id,
        )

        return [observation]