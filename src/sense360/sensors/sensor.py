"""
sensor.py

Defines the common interface for environmental sensors used by
Sense360.

Any sensor that measures the surrounding environment should provide
a get_observations() method. This allows the SensorManager to work
with different hardware without needing to know exactly how that
hardware operates.

Examples of future implementations include:
    - HC-SR04 ultrasonic sensors
    - Time-of-flight sensors
    - 360-degree LiDAR scanners

Each sensor converts its hardware-specific data into Observation
objects before returning it to the rest of the system.
"""

from abc import ABC, abstractmethod


class Sensor(ABC):
    """Base interface for sensors that observe the environment."""

    @abstractmethod
    def get_observations(self):
        """Read the sensor and return a list of Observation objects."""
        pass