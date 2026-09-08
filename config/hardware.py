"""
hardware.py

Describes the physical hardware configuration of the current Sense360
prototype.

This file contains information about WHAT hardware is installed and
HOW that hardware is physically connected.

Examples:
    - Raspberry Pi GPIO assignments
    - Ultrasonic sensor mounting directions
    - I2C bus assignments
    - I2C device addresses
    - PCA9685 motor channels
    - BNO085 connection information

Behavioral and algorithm-tuning values do NOT belong here.
Those values belong in:

    config/settings.py

Keeping hardware configuration separate from the device classes prevents
GPIO pins, I2C buses, addresses, and PWM channels from being hard-coded
throughout the Sense360 software.

Current prototype hardware:
    - Raspberry Pi 4 Model B
    - 1 HC-SR04 ultrasonic sensor
    - 1 BNO085 IMU
    - 1 PCA9685 PWM controller
    - 1 vibration motor
    - MOSFET motor driver circuit

The configuration can later be expanded to additional sensors and motors
without requiring major changes to the classes that operate them.
"""


# =====================================================================
# RASPBERRY PI GPIO
# =====================================================================

# GPIO chip used by the lgpio library.
#
# Raspberry Pi GPIO numbering throughout this configuration uses
# BCM GPIO numbers unless otherwise stated.
GPIO_CHIP = 0


# =====================================================================
# I2C BUSES
# =====================================================================

# The PCA9685 uses the Raspberry Pi's standard hardware I2C bus.
#
# Bus 1 wiring:
#     SDA -> BCM GPIO2
#            Physical Pin 3
#
#     SCL -> BCM GPIO3
#            Physical Pin 5
PCA9685_I2C_BUS = 1


# The BNO085 uses a separate software-created I2C bus.
#
# Bus 8 wiring:
#     SDA -> BCM GPIO20
#            Physical Pin 38
#
#     SCL -> BCM GPIO21
#            Physical Pin 40
BNO085_I2C_BUS = 8


# =====================================================================
# ULTRASONIC SENSORS
# =====================================================================

# Each dictionary describes one installed ultrasonic sensor.
#
# GPIO values use BCM numbering.
#
# Sensor-angle convention:
#
#     0 degrees   = front
#     90 degrees  = right
#     180 degrees = rear
#     270 degrees = left
#
# The angle describes the physical direction the sensor faces relative
# to the Sense360 belt.
#
# Current prototype Sensor 1:
#
#     TRIG:
#         BCM GPIO17
#         Physical Pin 11
#
#     ECHO:
#         BCM GPIO27
#         Physical Pin 13
#
# IMPORTANT:
#     The HC-SR04 ECHO signal is approximately 5 V.
#
#     The Raspberry Pi GPIO input must not receive this voltage directly.
#     ECHO must pass through the voltage-divider circuit before reaching
#     GPIO27.

ULTRASONIC_SENSORS = [
    {
        "sensor_id": "sensor_1",
        "trig_pin": 17,
        "echo_pin": 27,
        "relative_angle_deg": 0.0,
    },
]


# =====================================================================
# BNO085 IMU
# =====================================================================

# The BNO085 provides orientation and motion information to Sense360.
#
# Unlike the PCA9685, the BNO085 is connected to the separate software
# I2C bus.
#
# Current connection:
#
#     I2C Bus: 8
#
#     SDA:
#         BCM GPIO20
#         Physical Pin 38
#
#     SCL:
#         BCM GPIO21
#         Physical Pin 40
#
#     I2C Address:
#         0x4B

BNO085 = {
    "enabled": True,

    "i2c_bus": BNO085_I2C_BUS,
    "i2c_address": 0x4B,

    "sda_pin": 20,
    "scl_pin": 21,
}


# =====================================================================
# PCA9685 PWM CONTROLLER
# =====================================================================

# The PCA9685 generates PWM signals used to control the Sense360
# vibration motors.
#
# It is connected to the Raspberry Pi's normal hardware I2C bus.
#
# Current connection:
#
#     I2C Bus: 1
#
#     SDA:
#         BCM GPIO2
#         Physical Pin 3
#
#     SCL:
#         BCM GPIO3
#         Physical Pin 5
#
#     I2C Address:
#         0x40
#
# The PCA9685 does NOT directly power the vibration motors.
# Its PWM output drives the MOSFET motor-control circuit.

PCA9685 = {
    "enabled": True,

    "i2c_bus": PCA9685_I2C_BUS,
    "i2c_address": 0x40,

    "sda_pin": 2,
    "scl_pin": 3,
}


# =====================================================================
# HAPTIC MOTORS
# =====================================================================

# Each dictionary describes one installed vibration motor.
#
# Motor-angle convention matches the sensor-angle convention:
#
#     0 degrees   = front
#     90 degrees  = right
#     180 degrees = rear
#     270 degrees = left
#
# "pwm_channel" specifies the PCA9685 output channel connected to that
# motor's MOSFET driver circuit.
#
# Current prototype:
#
#     Motor 1
#         PCA9685 Channel 0
#         Mounted at the front position

HAPTIC_MOTORS = [
    {
        "motor_id": "motor_1",
        "pwm_channel": 0,
        "relative_angle_deg": 0.0,
    },
]


# =====================================================================
# HARDWARE COUNTS
# =====================================================================

# These values are calculated automatically from the hardware lists.
#
# Do not manually update these when additional sensors or motors are
# installed.

NUMBER_OF_ULTRASONIC_SENSORS = len(
    ULTRASONIC_SENSORS
)

NUMBER_OF_HAPTIC_MOTORS = len(
    HAPTIC_MOTORS
)