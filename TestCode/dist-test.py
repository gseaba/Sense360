import time
import statistics
import lgpio

TRIG_PIN = 17
ECHO_PIN = 27
SPEED_OF_SOUND_M_S = 343.0

class AsyncHCSR04:
    def __init__(self, trig_pin=17, echo_pin=27):
        self.trig_pin = trig_pin
        self.echo_pin = echo_pin
        
        try:
            self.chip = lgpio.gpiochip_open(4)
        except lgpio.error:
            self.chip = lgpio.gpiochip_open(0)

        # Claim Output for TRIG
        lgpio.gpio_claim_output(self.chip, self.trig_pin, 0)
        
        # Claim Input for ECHO
        lgpio.gpio_claim_input(self.chip, self.echo_pin)

        self.start_ns = None
        self.pulse_duration_s = None

        # lgpio.callback handles both claim and registration cleanly
        self.cb = lgpio.callback(
            self.chip, 
            self.echo_pin, 
            lgpio.BOTH_EDGES, 
            self._edge_callback
        )

    def _edge_callback(self, chip, gpio, level, timestamp_ns):
        """Callback signature: (chip, gpio, level, timestamp_ns)"""
        if level == 1:
            self.start_ns = timestamp_ns
        elif level == 0 and self.start_ns is not None:
            self.pulse_duration_s = (timestamp_ns - self.start_ns) / 1e9

    def trigger_ping(self):
        self.pulse_duration_s = None
        self.start_ns = None
        
        lgpio.gpio_write(self.chip, self.trig_pin, 1)
        time.sleep(0.00001)
        lgpio.gpio_write(self.chip, self.trig_pin, 0)

    def get_distance(self, timeout_s=0.03):
        self.trigger_ping()
        
        start = time.monotonic()
        while self.pulse_duration_s is None:
            if time.monotonic() - start > timeout_s:
                return None
            time.sleep(0.001)

        return (self.pulse_duration_s * SPEED_OF_SOUND_M_S) / 2.0

    def cleanup(self):
        if hasattr(self, 'cb') and self.cb:
            self.cb.cancel()
        lgpio.gpio_write(self.chip, self.trig_pin, 0)
        lgpio.gpio_free(self.chip, self.trig_pin)
        lgpio.gpio_free(self.chip, self.echo_pin)
        lgpio.gpiochip_close(self.chip)


# =========================================================
# Testing Script (Accuracy & 3-Ping Median)
# =========================================================
if __name__ == "__main__":
    sensor = AsyncHCSR04(trig_pin=TRIG_PIN, echo_pin=ECHO_PIN)
    print("Testing Asynchronous lgpio Driver... Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(5.0)
            # Gather 3 rapid pings for median filtering
            readings = []
            for _ in range(3):
                d = sensor.get_distance()
                if d is not None and 0.02 <= d <= 4.0:
                    readings.append(d * 100)  # Convert to cm
                time.sleep(0.01)  # Brief 10ms acoustic ring-down pause

            if readings:
                median_dist = statistics.median(readings)
                print(f"Distance: {median_dist:6.2f} cm  (Raw Pings: {[round(r, 1) for r in readings]})")
            else:
                print("Reading Timed Out / Out of Range")

    except KeyboardInterrupt:
        print("\nStopping test...")
    finally:
        sensor.cleanup()