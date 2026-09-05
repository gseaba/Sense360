"""
hcsr04.py

Implements the Sensor interface for an HC-SR04 ultrasonic distance sensor.

This class is responsible for all hardware-specific behavior required
to obtain distance measurements from one HC-SR04.

Responsibilities:
    - Configure the TRIG and ECHO GPIO pins.
    - Generate the ultrasonic trigger pulse.
    - Measure the returned echo pulse.
    - Convert echo travel time into distance.
    - Prevent the sensor from firing too frequently.
    - Detect timeouts and invalid measurements.
    - Convert successful measurements into Observation objects.
    - Release GPIO resources during shutdown.

This class does NOT:
    - Decide whether a measurement belongs in the WorldModel.
    - Reject transient obstacles such as the wearer's arm.
    - Control vibration motors.
    - Perform navigation or mapping logic.

The HC-SR04 ECHO signal is approximately 5 V and must pass through
a voltage divider before reaching the Raspberry Pi GPIO input.
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
        min_measurement_interval_s: float = 0.06,
        chip_handle=None,
    ):
        """
        Create an HC-SR04 sensor.

        Parameters
        ----------
        sensor_id : str
            Unique name for this sensor.

        trig_pin : int
            BCM GPIO number connected to TRIG.

        echo_pin : int
            BCM GPIO number connected to ECHO through the voltage divider.

        relative_angle_deg : float
            Direction the sensor faces relative to the belt.

            Convention:
                0 degrees   = front
                90 degrees  = right
                180 degrees = rear
                270 degrees = left

        min_distance_m : float
            Minimum accepted distance.

        max_distance_m : float
            Maximum accepted distance.

        timeout_s : float
            Maximum amount of time to wait for an echo transition.

        min_measurement_interval_s : float
            Minimum time allowed between ultrasonic trigger pulses.

        chip_handle
            Optional existing lgpio GPIO chip handle.

            If no handle is supplied, this sensor opens gpiochip0 itself.
        """

        self.sensor_id = sensor_id
        self.trig_pin = trig_pin
        self.echo_pin = echo_pin
        self.relative_angle_deg = relative_angle_deg

        self.min_distance_m = min_distance_m
        self.max_distance_m = max_distance_m
        self.timeout_s = timeout_s
        self.min_measurement_interval_s = min_measurement_interval_s

        self.last_measurement_time = None
        self._closed = False

        # Open gpiochip0 if a shared handle was not supplied.
        if chip_handle is None:
            self.chip = lgpio.gpiochip_open(0)
            self._owns_chip = True
        else:
            self.chip = chip_handle
            self._owns_chip = False

        # Configure TRIG as an output starting LOW.
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

        # Allow the sensor to stabilize after initialization.
        time.sleep(0.05)

    def _ready_for_measurement(self):
        """
        Determine whether enough time has passed to fire again.

        Returns
        -------
        bool
            True if the sensor may take another measurement.
            False if it must wait longer.
        """

        if self.last_measurement_time is None:
            return True

        elapsed_time = (
            time.monotonic()
            - self.last_measurement_time
        )

        return elapsed_time >= self.min_measurement_interval_s

    def _send_trigger_pulse(self):
        """
        Send the trigger pulse required by the HC-SR04.

        The HC-SR04 begins a measurement when TRIG is held HIGH
        for approximately 10 microseconds.
        """

        # Ensure TRIG begins LOW.
        lgpio.gpio_write(
            self.chip,
            self.trig_pin,
            0
        )

        time.sleep(0.000002)

        # Send the 10 microsecond trigger pulse.
        lgpio.gpio_write(
            self.chip,
            self.trig_pin,
            1
        )

        time.sleep(0.000010)

        lgpio.gpio_write(
            self.chip,
            self.trig_pin,
            0
        )

    def read_distance(self):
        """
        Perform one ultrasonic distance measurement.

        Returns
        -------
        float | None
            Distance in meters if a valid measurement is received.

            Returns None when:
                - The sensor is not yet allowed to fire again.
                - ECHO never rises.
                - ECHO never falls.
                - The measured distance is outside the accepted range.
        """

        if self._closed:
            raise RuntimeError(
                f"{self.sensor_id} cannot be read after cleanup()."
            )

        # Prevent the HC-SR04 from firing too frequently.
        if not self._ready_for_measurement():
            return None

        # Record the firing time before starting the measurement.
        self.last_measurement_time = time.monotonic()

        self._send_trigger_pulse()

        # ---------------------------------------------------------
        # Wait for ECHO to go HIGH.
        # ---------------------------------------------------------

        wait_start = time.monotonic()

        while lgpio.gpio_read(self.chip, self.echo_pin) == 0:

            if time.monotonic() - wait_start > self.timeout_s:
                return None

        pulse_start_ns = time.monotonic_ns()

        # ---------------------------------------------------------
        # Wait for ECHO to return LOW.
        # ---------------------------------------------------------

        while lgpio.gpio_read(self.chip, self.echo_pin) == 1:

            elapsed_echo_time = (
                time.monotonic_ns() - pulse_start_ns
            ) / 1_000_000_000

            if elapsed_echo_time > self.timeout_s:
                return None

        pulse_end_ns = time.monotonic_ns()

        # ---------------------------------------------------------
        # Convert echo duration into distance.
        # ---------------------------------------------------------

        pulse_duration_s = (
            pulse_end_ns - pulse_start_ns
        ) / 1_000_000_000

        # Sound travels to the object and then back to the sensor,
        # therefore the total distance traveled is divided by two.
        distance_m = (
            pulse_duration_s
            * self.SPEED_OF_SOUND_M_S
            / 2.0
        )

        # Reject physically unreasonable measurements.
        if not (
            self.min_distance_m
            <= distance_m
            <= self.max_distance_m
        ):
            return None

        return distance_m

    def get_observations(self):
        """
        Attempt to obtain a new environmental observation.

        Returns
        -------
        list
            One Observation when a valid measurement is available.

            An empty list is returned when:
                - The sensor is waiting for its next allowed firing time.
                - The measurement times out.
                - The measured distance is invalid.

        Returning a list allows this sensor to use the same interface
        as future sensors such as LiDAR scanners, which may return many
        observations from a single scan.
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
        """

        if self._closed:
            return

        # Ensure TRIG is LOW before releasing the GPIO.
        try:
            lgpio.gpio_write(
                self.chip,
                self.trig_pin,
                0
            )
        except lgpio.error:
            pass

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

        # Only close the GPIO chip if this object opened it.
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
        Allow use of the sensor inside a Python 'with' block.
        """

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Automatically release GPIO resources when leaving a 'with' block.
        """

        self.cleanup()