"""
hcsr04.py

Implements the Sensor interface for an HC-SR04 ultrasonic distance sensor.

This class is responsible for all hardware-specific behavior required
to obtain a distance measurement from one HC-SR04 sensor.

Responsibilities:
    - Configure the TRIG GPIO as an output.
    - Configure the ECHO GPIO as an input.
    - Generate the 10 microsecond trigger pulse required by the HC-SR04.
    - Measure the duration of the returned echo pulse.
    - Convert echo travel time into distance.
    - Detect measurements that time out or fall outside the useful
      operating range of the sensor.
    - Convert successful measurements into the standard Sense360
      Observation format.
    - Release GPIO resources when the sensor is shut down.

This class intentionally does NOT:
    - Filter temporary obstacles such as the wearer's arm.
    - Decide whether an observation should modify the WorldModel.
    - Control vibration motors.
    - Perform navigation logic.

Those responsibilities belong elsewhere in the Sense360 software.

The HC-SR04 ECHO output is approximately 5 V and MUST be reduced before
being connected to a Raspberry Pi GPIO input. Sense360 currently uses
a resistor voltage divider on the ECHO connection.
"""

import time
import lgpio

from .sensor import Sensor
from ..models.observation import Observation


class HCSR04(Sensor):
    """
    Represents one physical HC-SR04 ultrasonic distance sensor.
    """

    # Approximate speed of sound at room temperature.
    SPEED_OF_SOUND_M_S = 343.0

    def __init__(
        self,
        sensor_id: str,
        trig_pin: int,
        echo_pin: int,
        relative_angle_deg: float,
        min_distance_m: float = 0.02,
        max_distance_m: float = 4.0,
        timeout_s: float = 0.03,
        chip_handle=None,
    ):
        """
        Create an HC-SR04 sensor.

        Parameters
        ----------
        sensor_id:
            Human-readable identifier for the sensor.
            Example: "front" or "sensor_1"

        trig_pin:
            BCM GPIO number connected to HC-SR04 TRIG.

        echo_pin:
            BCM GPIO number connected to HC-SR04 ECHO through
            the voltage divider.

        relative_angle_deg:
            Direction the sensor faces relative to the belt.

            Suggested convention:
                0 degrees   = front
                90 degrees  = right
                180 degrees = rear
                270 degrees = left

        min_distance_m:
            Minimum distance that will be accepted as physically valid.

        max_distance_m:
            Maximum distance that will be accepted as physically valid.

        timeout_s:
            Maximum amount of time to wait for the ECHO signal.

        chip_handle:
            Optional existing lgpio chip handle.

            If no handle is supplied, this object opens gpiochip0 itself.
            A shared handle can later be supplied if multiple sensors are
            managed through one GPIO connection.
        """

        self.sensor_id = sensor_id
        self.trig_pin = trig_pin
        self.echo_pin = echo_pin
        self.relative_angle_deg = relative_angle_deg

        self.min_distance_m = min_distance_m
        self.max_distance_m = max_distance_m
        self.timeout_s = timeout_s

        self._closed = False

        # If no GPIO chip was supplied, open gpiochip0 ourselves.
        if chip_handle is None:
            self.chip = lgpio.gpiochip_open(0)
            self._owns_chip = True
        else:
            self.chip = chip_handle
            self._owns_chip = False

        # Configure TRIG as an output initially LOW.
        lgpio.gpio_claim_output(
            self.chip,
            self.trig_pin,
            0
        )

        # Configure ECHO as an input.
        lgpio.gpio_claim_input(
            self.chip,
            self.echo_pin
        )

        # Give the sensor a moment to settle after initialization.
        time.sleep(0.05)

    def _send_trigger_pulse(self):
        """
        Send the trigger pulse that begins an HC-SR04 measurement.

        The HC-SR04 requires a HIGH pulse of at least approximately
        10 microseconds on the TRIG input.
        """

        # Make certain TRIG starts LOW.
        lgpio.gpio_write(
            self.chip,
            self.trig_pin,
            0
        )

        time.sleep(0.000002)

        # Send 10 microsecond HIGH pulse.
        lgpio.gpio_write(
            self.chip,
            self.trig_pin,
            1
        )

        time.sleep(0.000010)

        # Return TRIG LOW.
        lgpio.gpio_write(
            self.chip,
            self.trig_pin,
            0
        )

    def read_distance(self):
        """
        Perform one ultrasonic measurement.

        Returns
        -------
        float | None

        Distance in meters when a valid echo is received.

        Returns None when:
            - ECHO never rises.
            - ECHO never falls.
            - The calculated distance is outside the accepted range.

        A failed measurement is not treated as a new world measurement.
        This allows previously stored WorldModel data to remain in place
        and naturally become older instead of being overwritten by bad
        sensor data.
        """

        if self._closed:
            raise RuntimeError(
                f"{self.sensor_id} cannot be read after cleanup()."
            )

        self._send_trigger_pulse()

        # -------------------------------------------------------------
        # Wait for the beginning of the ECHO pulse.
        # -------------------------------------------------------------

        wait_start = time.monotonic()

        while lgpio.gpio_read(self.chip, self.echo_pin) == 0:

            if time.monotonic() - wait_start > self.timeout_s:
                return None

        # ECHO just went HIGH.
        pulse_start_ns = time.monotonic_ns()

        # -------------------------------------------------------------
        # Wait for the end of the ECHO pulse.
        # -------------------------------------------------------------

        while lgpio.gpio_read(self.chip, self.echo_pin) == 1:

            if (
                time.monotonic_ns() - pulse_start_ns
            ) / 1_000_000_000 > self.timeout_s:

                return None

        # ECHO just went LOW.
        pulse_end_ns = time.monotonic_ns()

        # -------------------------------------------------------------
        # Calculate distance.
        # -------------------------------------------------------------

        pulse_duration_s = (
            pulse_end_ns - pulse_start_ns
        ) / 1_000_000_000

        # Sound travels to the object AND back to the sensor,
        # so divide the total travel distance by two.
        distance_m = (
            pulse_duration_s
            * self.SPEED_OF_SOUND_M_S
            / 2.0
        )

        # Reject measurements outside the expected physical range.
        if not (
            self.min_distance_m
            <= distance_m
            <= self.max_distance_m
        ):
            return None

        return distance_m

    def get_observations(self):
        """
        Perform one measurement and return standardized Sense360 data.

        HC-SR04 produces one directional distance measurement at a time,
        so a successful measurement returns a list containing exactly
        one Observation.

        A failed measurement returns an empty list.

        Returning a list keeps this sensor compatible with future sensor
        types such as LiDAR, which may return hundreds of observations
        from a single scan.
        """

        distance_m = self.read_distance()

        if distance_m is None:
            return []

        observation = Observation(
            distance_m=distance_m,
            relative_angle_deg=self.relative_angle_deg,
            timestamp=time.monotonic(),
            sensor_id=self.sensor_id,
            confidence=1.0,
        )

        return [observation]

    def cleanup(self):
        """
        Release GPIO resources used by this sensor.

        This should be called when Sense360 shuts down.

        If this sensor opened its own GPIO chip, the chip is also closed.
        If the GPIO chip was supplied externally, only this sensor's GPIO
        pins are released.
        """

        if self._closed:
            return

        # Make sure TRIG is LOW before releasing it.
        try:
            lgpio.gpio_write(
                self.chip,
                self.trig_pin,
                0
            )
        except lgpio.error:
            pass

        # Release both GPIO lines.
        try:
            lgpio.gpio_free(
                self.chip,
                self.trig_pin
            )
        except lgpio.error:
            pass

        try:
            lgpio.gpio_free(
                self.chip,
                self.echo_pin
            )
        except lgpio.error:
            pass

        # Only close the entire GPIO chip if this object opened it.
        if self._owns_chip:
            try:
                lgpio.gpiochip_close(
                    self.chip
                )
            except lgpio.error:
                pass

        self._closed = True

    def __enter__(self):
        """
        Allow the sensor to optionally be used with a Python 'with' block.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Automatically clean up GPIO when leaving a 'with' block.
        """
        self.cleanup()