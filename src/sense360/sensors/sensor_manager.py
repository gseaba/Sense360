"""
sensor_manager.py

Coordinates all environmental sensors used by Sense360.

The SensorManager is responsible for:
    - Storing all active sensor objects.
    - Reading each sensor.
    - Collecting all Observation objects into one list.
    - Handling simple timing between sensor readings.

The rest of Sense360 should communicate with the SensorManager instead
of directly reading individual sensors.

This makes it easier to scale the system from one sensor to many sensors.
For example, the same SensorManager can work with:
    - 1 HC-SR04
    - 4 HC-SR04 sensors
    - 8 HC-SR04 sensors
    - Future LiDAR or other sensor types

Each sensor only needs to implement the get_observations() method
defined by the Sensor base class.

For now, sensors are read sequentially. This is useful for HC-SR04
ultrasonic sensors because firing them too closely together can cause
cross-talk between sensors.

If future hardware requires more advanced scheduling or asynchronous
operation, that logic can be added here without changing the rest of
the Sense360 system.
"""

import time


class SensorManager:
    """
    Manages all environmental sensors and collects their observations.
    """

    def __init__(self, sensors=None, delay_between_sensors_s=0.02):
        """
        Create a SensorManager.

        Parameters
        ----------
        sensors : list, optional
            List of Sensor objects managed by the system.

        delay_between_sensors_s : float
            Delay between reading individual sensors.

            This is primarily intended to reduce ultrasonic cross-talk
            between multiple HC-SR04 sensors.
        """

        if sensors is None:
            sensors = []

        self.sensors = sensors
        self.delay_between_sensors_s = delay_between_sensors_s

    def add_sensor(self, sensor):
        """
        Add a new sensor to the manager.

        Parameters
        ----------
        sensor
            Any object that implements get_observations().
        """

        self.sensors.append(sensor)

    def remove_sensor(self, sensor):
        """
        Remove a sensor from the manager.

        Parameters
        ----------
        sensor
            Sensor object to remove.
        """

        if sensor in self.sensors:
            self.sensors.remove(sensor)

    def update(self):
        """
        Read all sensors and collect their observations.

        Returns
        -------
        list
            Combined list of Observation objects from every sensor.

        If a sensor produces no valid data, it should return an empty
        list. The SensorManager simply continues to the next sensor.
        """

        observations = []

        for index, sensor in enumerate(self.sensors):

            new_observations = sensor.get_observations()

            if new_observations:
                observations.extend(new_observations)

            # Do not delay after the final sensor.
            if index < len(self.sensors) - 1:
                time.sleep(self.delay_between_sensors_s)

        return observations

    def get_sensor_count(self):
        """
        Return the number of sensors currently managed.
        """

        return len(self.sensors)

    def cleanup(self):
        """
        Clean up hardware resources used by all sensors.

        If a sensor defines a cleanup() method, call it.

        This allows hardware-specific sensors such as the HC-SR04
        to release GPIO resources when Sense360 shuts down.
        """

        for sensor in self.sensors:

            cleanup_method = getattr(sensor, "cleanup", None)

            if callable(cleanup_method):
                cleanup_method()