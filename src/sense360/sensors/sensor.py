"""
sensor.py

Defines the common interface for environmental sensors used by Sense360.

Every sensor that observes the surrounding environment should inherit
from the Sensor class and implement the get_observations() method.

The purpose of this interface is to keep the rest of the Sense360
software independent from specific hardware.

For example:
    - An HC-SR04 ultrasonic sensor may return one Observation.
    - A future LiDAR scanner may return hundreds of Observations.
    - A future time-of-flight sensor could also use the same interface.

The SensorManager only needs to know that every Sensor can provide
observations. It does not need to know how each physical device works.
"""

from abc import ABC, abstractmethod


class Sensor(ABC):
    """
    Base class for any sensor that measures the environment around
    the Sense360 wearer.
    """

    @abstractmethod
    def get_observations(self):
        """
        Read the sensor and return a list of Observation objects.

        Returns
        -------
        list
            A list containing zero or more Observation objects.

            An empty list means that no valid measurement was produced.

        Examples
        --------
        HC-SR04:
            [Observation(...)]

        Failed HC-SR04 reading:
            []

        360-degree LiDAR:
            [
                Observation(...),
                Observation(...),
                Observation(...),
                ...
            ]
        """
        pass