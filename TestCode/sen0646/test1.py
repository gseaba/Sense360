
import serial

PORT = "/dev/serial0"
BAUD = 921600

def main():
    ser = serial.Serial(
        port=PORT,
        baudrate=BAUD,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=0.1
    )

    buffer = bytearray()

    print("SEN0646 distance test running...")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            data = ser.read(ser.in_waiting or 1)

            if not data:
                continue

            buffer.extend(data)

            while len(buffer) >= 16:
                idx = buffer.find(b'\x57\x00')

                if idx < 0:
                    buffer[:] = buffer[-1:]
                    break

                if idx > 0:
                    del buffer[:idx]

                if len(buffer) < 16:
                    break

                frame = buffer[:16]

                # Verify packet checksum
                if (sum(frame[:15]) & 0xFF) != frame[15]:
                    del buffer[0]
                    continue

                # Distance in millimeters
                distance_mm = (
                    frame[8]
                    | (frame[9] << 8)
                    | (frame[10] << 16)
                )

                distance_m = distance_mm / 1000.0

                print(f"Distance: {distance_m:.3f} m")

                del buffer[:16]

    except KeyboardInterrupt:
        print("\nTest stopped.")

    finally:
        ser.close()


if __name__ == "__main__":
    main()