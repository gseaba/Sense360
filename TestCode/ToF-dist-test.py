import time
import board
import busio
import adafruit_vl53l4cd

def main():
    # Initialize the I2C bus using GPIO 3 (SCL) and GPIO 2 (SDA)
    # On the Raspberry Pi 4, board.SCL and board.SDA map to GPIO 3 and GPIO 2 by default.
    i2c = busio.I2C(board.SCL, board.SDA)

    print("Initializing VL53L4CX sensor...")
    
    # Initialize the sensor driver
    sensor = adafruit_vl53l4cd.VL53L4CD(i2c)

    # Optional: Print model/firmware info if supported
    print(f"Sensor initialized successfully!")

    # Begin taking measurements
    sensor.start_ranging()

    print("Starting distance measurements. Press Ctrl+C to exit.\n")

    try:
        while True:
            # Check if a new measurement is available
            if sensor.data_ready:
                # Read distance in centimeters (or millimeters depending on library implementation)
                distance_cm = sensor.distance
                print(f"Distance: {distance_cm:.1f} cm")
                
                # Clear the interrupt to ready the sensor for the next reading
                sensor.clear_interrupt()
                
            time.sleep(2)  # Small delay to prevent hammering the CPU

    except KeyboardInterrupt:
        print("\nStopping sensor...")
        sensor.stop_ranging()
        print("Test finished.")

if __name__ == "__main__":
    main()