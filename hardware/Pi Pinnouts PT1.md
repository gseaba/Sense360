# Raspberry Pi Pinout

The first prototype uses four HC-SR04 ultrasonic sensors, four vibration motors, an IMU/accelerometer, a PCA9685 PWM controller, and MOSFET motor drivers.

The Raspberry Pi communicates with the PCA9685 and IMU over the shared I2C bus. Each ultrasonic sensor uses its own TRIG and ECHO GPIO pins.

## Raspberry Pi GPIO Assignments

| Physical Pin | BCM GPIO | Connection | Function |
|---:|---:|---|---|
| 1 | - | PCA9685 VCC, IMU VCC | 3.3 V logic power |
| 3 | GPIO 2 | PCA9685 SDA, IMU SDA | I2C Data |
| 5 | GPIO 3 | PCA9685 SCL, IMU SCL | I2C Clock |
| 6 | - | Ground Rail | Common Ground |
| 11 | GPIO 17 | Ultrasonic Sensor 1 TRIG | Trigger Output |
| 13 | GPIO 27 | Ultrasonic Sensor 1 ECHO | Echo Input |
| 15 | GPIO 22 | Ultrasonic Sensor 2 TRIG | Trigger Output |
| 16 | GPIO 23 | Ultrasonic Sensor 2 ECHO | Echo Input |
| 18 | GPIO 24 | Ultrasonic Sensor 3 TRIG | Trigger Output |
| 22 | GPIO 25 | Ultrasonic Sensor 3 ECHO | Echo Input |
| 29 | GPIO 5 | Ultrasonic Sensor 4 TRIG | Trigger Output |
| 31 | GPIO 6 | Ultrasonic Sensor 4 ECHO | Echo Input |

## Software GPIO Definitions

BCM GPIO numbering is used in software.

```python
TRIG_PINS = [17, 22, 24, 5]
ECHO_PINS = [27, 23, 25, 6]
