"""
sensor_manager.py

Coordinates all environmental sensors installed on Sense360.

The SensorManager owns the sensor objects and is responsible for:
    - Keeping track of installed sensors
    - Deciding when sensors are read
    - Collecting observations from every sensor
    - Controlling timing between ultrasonic measurements to reduce
      interference between sensors

The rest of the system asks the SensorManager for observations instead
of communicating with individual sensors directly.

Adding more sensors should normally require adding another Sensor
object to the manager rather than changing the manager's logic.
"""

import time


class SensorManager:
    """Coordinates all environmental sensors."""

    def __init__(self, sensors=None, ultrasonic_delay_s=0.02):
        self.sensors = sensors or []
        self.ultrasonic_delay_s = ultrasonic_delay_s

    def add_sensor(self, sensor):
        """Add another sensor to the system."""
        self.sensors.append(sensor)

    def update(self):
        """Read all sensors and return all new observations."""

        observations = []

        for sensor in self.sensors:
            new_observations = sensor.get_observations()
            observations.extend(new_observations)

            # Temporary simple scheduling method.
            # Helps prevent ultrasonic sensors from interfering
            # with one another.
            time.sleep(self.ultrasonic_delay_s)

        return observations