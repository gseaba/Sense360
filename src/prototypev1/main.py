import time

from hcsr04 import HCSR04


front = HCSR04(
    trig_pin=17,
    echo_pin=27,
)

right = HCSR04(
    trig_pin=22,
    echo_pin=23,
)

left = HCSR04(
    trig_pin=24,
    echo_pin=25,
)


try:
    while True:

        # Start measurements.
        front.trigger()
        right.trigger()
        left.trigger()

        # Do other application work here.
        # --------------------------------------------------
        # navigation()
        # process_buttons()
        # update_display()
        # process_network()
        # etc.
        # --------------------------------------------------

        time.sleep(0.01)

        # Retrieve completed measurements.
        front_distance = front.get_distance()
        right_distance = right.get_distance()
        left_distance = left.get_distance()

        if front_distance is not None:
            print(f"Front: {front_distance:.2f} m")

        if right_distance is not None:
            print(f"Right: {right_distance:.2f} m")

        if left_distance is not None:
            print(f"Left: {left_distance:.2f} m")

finally:
    front.cleanup()
    right.cleanup()
    left.cleanup()