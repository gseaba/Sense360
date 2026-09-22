import time
import lgpio


class HCSR04:
    """
    Nonblocking HC-SR04 ultrasonic sensor.

    The sensor uses GPIO edge callbacks to measure the ECHO pulse.
    The application is responsible for deciding when to trigger a
    measurement and when to retrieve the result.
    """

    SPEED_OF_SOUND_M_S = 343.0

    def __init__(
        self,
        trig_pin: int,
        echo_pin: int,
        min_distance_m: float = 0.02,
        max_distance_m: float = 4.0,
        chip_handle=None,
    ):
        self.trig_pin = trig_pin
        self.echo_pin = echo_pin

        self.min_distance_m = min_distance_m
        self.max_distance_m = max_distance_m

        # ---------------------------------------------------------
        # GPIO chip
        # ---------------------------------------------------------

        if chip_handle is None:
            try:
                self.chip = lgpio.gpiochip_open(4)
            except lgpio.error:
                self.chip = lgpio.gpiochip_open(0)

            self._owns_chip = True
        else:
            self.chip = chip_handle
            self._owns_chip = False

        # ---------------------------------------------------------
        # GPIO configuration
        # ---------------------------------------------------------

        # TRIG starts LOW.
        lgpio.gpio_claim_output(
            self.chip,
            self.trig_pin,
            0,
        )

        # ECHO generates callbacks on both rising and falling edges.
        lgpio.gpio_claim_alert(
            self.chip,
            self.echo_pin,
            3,  # BOTH_EDGES
        )

        # ---------------------------------------------------------
        # Measurement state
        # ---------------------------------------------------------

        self._echo_start_ns = None
        self._pulse_duration_s = None

        self._callback = lgpio.callback(
            self.chip,
            self.echo_pin,
            3,  # BOTH_EDGES
            self._edge_callback,
        )

        self._closed = False

        # Give the GPIO time to settle.
        time.sleep(0.05)

    def _edge_callback(self, chip, gpio, level, timestamp_ns):
        """
        Called by lgpio whenever ECHO changes state.
        """

        if level == 1:
            # Rising edge: beginning of echo pulse.
            self._echo_start_ns = timestamp_ns

        elif level == 0 and self._echo_start_ns is not None:
            # Falling edge: end of echo pulse.
            self._pulse_duration_s = (
                timestamp_ns - self._echo_start_ns
            ) / 1_000_000_000

            self._echo_start_ns = None

    def trigger(self):
        """
        Start a new distance measurement.

        This function does NOT wait for the measurement to finish.
        """

        if self._closed:
            raise RuntimeError("Sensor has been cleaned up.")

        # Clear previous measurement.
        self._echo_start_ns = None
        self._pulse_duration_s = None

        # Send 10 us trigger pulse.
        lgpio.gpio_write(
            self.chip,
            self.trig_pin,
            1,
        )

        time.sleep(0.000010)

        lgpio.gpio_write(
            self.chip,
            self.trig_pin,
            0,
        )

    def get_distance(self):
        """
        Return the most recently completed distance measurement.

        Returns:
            Distance in meters, or None if no measurement is available.
        """

        if self._pulse_duration_s is None:
            return None

        distance_m = (
            self._pulse_duration_s
            * self.SPEED_OF_SOUND_M_S
            / 2.0
        )

        # Consume the measurement so the same result isn't returned
        # repeatedly.
        self._pulse_duration_s = None

        if not (
            self.min_distance_m
            <= distance_m
            <= self.max_distance_m
        ):
            return None

        return distance_m

    def measurement_ready(self):
        """
        Return True when a new measurement is available.
        """

        return self._pulse_duration_s is not None

    def cleanup(self):
        """
        Release GPIO resources.
        """

        if self._closed:
            return

        try:
            self._callback.cancel()
        except lgpio.error:
            pass

        try:
            lgpio.gpio_write(
                self.chip,
                self.trig_pin,
                0,
            )
        except lgpio.error:
            pass

        try:
            lgpio.gpio_free(
                self.chip,
                self.trig_pin,
            )
        except lgpio.error:
            pass

        try:
            lgpio.gpio_free(
                self.chip,
                self.echo_pin,
            )
        except lgpio.error:
            pass

        if self._owns_chip:
            try:
                lgpio.gpiochip_close(self.chip)
            except lgpio.error:
                pass

        self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()