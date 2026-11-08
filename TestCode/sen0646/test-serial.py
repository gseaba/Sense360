
import serial
import time

PORT = "/dev/serial0"
BAUD = 921600

print(f"Opening {PORT} at {BAUD} baud...")

try:
    with serial.Serial(PORT, BAUD, timeout=1) as ser:
        ser.reset_input_buffer()
        print("Listening for sensor data for 10 seconds...")

        start = time.time()
        total_bytes = 0

        while time.time() - start < 10:
            data = ser.read(ser.in_waiting or 1)

            if data:
                total_bytes += len(data)
                print("Received:", data.hex(" "))

        print(f"\nTotal bytes received: {total_bytes}")

except serial.SerialException as e:
    print("Serial error:", e)