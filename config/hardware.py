
"""
Sense360 Hardware Configuration

Defines the physical wiring and component placement for the
8-sensor, 8-motor Sense360 wearable belt.

All Raspberry Pi GPIO numbers use BCM numbering.

Physical arrangement:
    0 degrees   = Front
    90 degrees  = Right
    180 degrees = Rear
    270 degrees = Left

All sensors and motors are spaced 45 degrees apart.
"""

# =========================================================
# RASPBERRY PI GPIO CONFIGURATION
# =========================================================

# Raspberry Pi 4 GPIO chip used by lgpio
GPIO_CHIP = 0


# =========================================================
# I2C BUS CONFIGURATION
# =========================================================

# PCA9685: Hardware I2C bus 1
# SDA = GPIO2  (Physical pin 3)
# SCL = GPIO3  (Physical pin 5)

PCA9685_I2C_BUS = 1

# BNO085: Software I2C bus 8
# SDA = GPIO20 (Physical pin 38)
# SCL = GPIO21 (Physical pin 40)

BNO085_I2C_BUS = 8


# =========================================================
# HC-SR04 ULTRASONIC SENSORS
# =========================================================

# Each sensor uses an independent TRIG and ECHO GPIO.
#
# IMPORTANT:
# Every ECHO line passes through its own voltage divider
# before reaching the Raspberry Pi.
#
# GPIO numbering is BCM, not physical pin numbering.
#
# Sensor | TRIG GPIO | ECHO GPIO | Angle
# -------|-----------|-----------|------
#    1   |    15     |    10     |   0
#    2   |    18     |    17     |  45
#    3   |    23     |    27     |  90
#    4   |    24     |    22     | 135
#    5   |    25     |     9     | 180
#    6   |     8     |    11     | 225
#    7   |     7     |     5     | 270
#    8   |    12     |     6     | 315

ULTRASONIC_SENSORS = [
    {
        "sensor_id": "sensor_1",
        "trig_pin": 15,
        "echo_pin": 10,
        "relative_angle_deg": 0.0,
    },
    {
        "sensor_id": "sensor_2",
        "trig_pin": 18,
        "echo_pin": 17,
        "relative_angle_deg": 45.0,
    },
    {
        "sensor_id": "sensor_3",
        "trig_pin": 23,
        "echo_pin": 27,
        "relative_angle_deg": 90.0,
    },
    {
        "sensor_id": "sensor_4",
        "trig_pin": 24,
        "echo_pin": 22,
        "relative_angle_deg": 135.0,
    },
    {
        "sensor_id": "sensor_5",
        "trig_pin": 25,
        "echo_pin": 9,
        "relative_angle_deg": 180.0,
    },
    {
        "sensor_id": "sensor_6",
        "trig_pin": 8,
        "echo_pin": 11,
        "relative_angle_deg": 225.0,
    },
    {
        "sensor_id": "sensor_7",
        "trig_pin": 7,
        "echo_pin": 5,
        "relative_angle_deg": 270.0,
    },
    {
        "sensor_id": "sensor_8",
        "trig_pin": 12,
        "echo_pin": 6,
        "relative_angle_deg": 315.0,
    },
]


# =========================================================
# BNO085 IMU
# =========================================================

# Software I2C bus 8
#
# VCC = Pi 3.3V
# GND = Pi GND
# SDA = GPIO20 (Physical pin 38)
# SCL = GPIO21 (Physical pin 40)

BNO085 = {
    "enabled": True,
    "i2c_bus": BNO085_I2C_BUS,
    "i2c_address": 0x4B,
    "sda_pin": 20,
    "scl_pin": 21,
}


# =========================================================
# PCA9685 PWM CONTROLLER
# =========================================================

# Hardware I2C bus 1
#
# VCC = Pi 3.3V
# GND = Pi GND
# SDA = GPIO2 (Physical pin 3)
# SCL = GPIO3 (Physical pin 5)
#
# PWM frequency is configured in config/settings.py
# and should be 200 Hz.

PCA9685 = {
    "enabled": True,
    "i2c_bus": PCA9685_I2C_BUS,
    "i2c_address": 0x40,
    "sda_pin": 2,
    "scl_pin": 3,
}


# =========================================================
# HAPTIC VIBRATION MOTORS
# =========================================================

# Eight vibration motors connected through two
# F5305S 4-channel MOSFET driver boards.
#
# Each motor is located next to its corresponding sensor.
#
# PCA9685 channel order is reversed relative to the
# ultrasonic sensor numbering.
#
# Motor | PCA Channel | Angle | Sensor
# ------|-------------|-------|-------
#   1   |      7      |   0   |   1
#   2   |      6      |  45   |   2
#   3   |      5      |  90   |   3
#   4   |      4      | 135   |   4
#   5   |      3      | 180   |   5
#   6   |      2      | 225   |   6
#   7   |      1      | 270   |   7
#   8   |      0      | 315   |   8

HAPTIC_MOTORS = [
    {
        "motor_id": "motor_1",
        "pwm_channel": 7,
        "relative_angle_deg": 0.0,
    },
    {
        "motor_id": "motor_2",
        "pwm_channel": 6,
        "relative_angle_deg": 45.0,
    },
    {
        "motor_id": "motor_3",
        "pwm_channel": 5,
        "relative_angle_deg": 90.0,
    },
    {
        "motor_id": "motor_4",
        "pwm_channel": 4,
        "relative_angle_deg": 135.0,
    },
    {
        "motor_id": "motor_5",
        "pwm_channel": 3,
        "relative_angle_deg": 180.0,
    },
    {
        "motor_id": "motor_6",
        "pwm_channel": 2,
        "relative_angle_deg": 225.0,
    },
    {
        "motor_id": "motor_7",
        "pwm_channel": 1,
        "relative_angle_deg": 270.0,
    },
    {
        "motor_id": "motor_8",
        "pwm_channel": 0,
        "relative_angle_deg": 315.0,
    },
]


# =========================================================
# HARDWARE COUNTS
# =========================================================

NUMBER_OF_ULTRASONIC_SENSORS = len(ULTRASONIC_SENSORS)

NUMBER_OF_HAPTIC_MOTORS = len(HAPTIC_MOTORS)
