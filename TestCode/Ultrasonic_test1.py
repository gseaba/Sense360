import RPi.GPIO as GPIO
import time

# BCM GPIO numbers
TRIG = 17
ECHO = 27

GPIO.setmode(GPIO.BCM)

GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# Make sure trigger starts LOW
GPIO.output(TRIG, GPIO.LOW)
time.sleep(2)

print("HC-SR04 Distance Test")
print("Press Ctrl+C to stop")

try:
    while True:

        # Send a 10 microsecond trigger pulse
        GPIO.output(TRIG, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(TRIG, GPIO.LOW)

        # Wait for ECHO to go HIGH
        timeout = time.time() + 0.05

        while GPIO.input(ECHO) == GPIO.LOW:
            pulse_start = time.time()

            if time.time() > timeout:
                raise TimeoutError("No echo received")

        # Wait for ECHO to go LOW
        timeout = time.time() + 0.05

        while GPIO.input(ECHO) == GPIO.HIGH:
            pulse_end = time.time()

            if time.time() > timeout:
                raise TimeoutError("Echo pulse timed out")

        # Echo pulse represents the round-trip travel time
        pulse_duration = pulse_end - pulse_start

        # Speed of sound ≈ 34300 cm/s.
        # Divide by 2 because sound travels to the object and back.
        distance_cm = pulse_duration * 34300 / 2

        print(f"Distance: {distance_cm:.1f} cm")

        time.sleep(1)

except KeyboardInterrupt:
    print("\nTest stopped.")

except TimeoutError as error:
    print(f"\nError: {error}")

finally:
    GPIO.cleanup()