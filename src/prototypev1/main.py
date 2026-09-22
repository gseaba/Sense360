from collections import deque
import statistics
import time

from hcsr04 import HCSR04


front = HCSR04(trig_pin=17, echo_pin=27)
right = HCSR04(trig_pin=22, echo_pin=23)
left = HCSR04(trig_pin=24, echo_pin=25)


# Keep the three most recent valid measurements.
front_buffer = deque(maxlen=3)
right_buffer = deque(maxlen=3)
left_buffer = deque(maxlen=3)


try:
    while True:

        # ---------------------------------------------------------
        # Start measurements
        # ---------------------------------------------------------

        front.trigger()

        time.sleep(0.01)

        right.trigger()

        time.sleep(0.01)

        left.trigger()

        # ---------------------------------------------------------
        # Do other application work here
        # ---------------------------------------------------------

        # ...

        # ---------------------------------------------------------
        # Collect completed measurements
        # ---------------------------------------------------------

        front_distance = front.get_distance()
        right_distance = right.get_distance()
        left_distance = left.get_distance()

        if front_distance is not None:
            front_buffer.append(front_distance)

        if right_distance is not None:
            right_buffer.append(right_distance)

        if left_distance is not None:
            left_buffer.append(left_distance)

        # ---------------------------------------------------------
        # Later, when you actually need the filtered distances:
        # ---------------------------------------------------------

        if front_buffer:
            front_median = statistics.median(front_buffer)

        if right_buffer:
            right_median = statistics.median(right_buffer)

        if left_buffer:
            left_median = statistics.median(left_buffer)

        # Continue doing other work...

finally:
    front.cleanup()
    right.cleanup()
    left.cleanup()