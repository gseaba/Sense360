# Sense360

Senior Design class project repository.

## Links

Reports found [here](./reports/README.md)  

Hardware information found [here](./hardware/README.md)

Project TODO found [here](./TODO.md)


## Repository Structure

```text
Sense360/
├── README.md
├── TODO.md
├── main.py                         # Application entry point
├── pyproject.toml                  # Python package configuration
├── config/
│   ├── __init__.py
│   ├── hardware.py                 # Wiring, buses, and hardware assignments
│   └── settings.py                 # Tunable system behavior
├── src/
│   └── sense360/
│       ├── __init__.py
│       ├── sensors/
│       │   ├── __init__.py
│       │   ├── sensor.py           # Base sensor interface
│       │   ├── hcsr04.py           # Ultrasonic sensor driver
│       │   └── sensor_manager.py   # Coordinates sensor readings
│       ├── motion/
│       │   ├── __init__.py
│       │   └── motion_tracker.py   # BNO085 orientation and motion
│       ├── world/
│       │   ├── __init__.py
│       │   └── world_model.py      # Directional memory and filtering
│       ├── haptics/
│       │   ├── __init__.py
│       │   └── haptic_system.py    # Vibration motor control
│       ├── system/
│       │   ├── __init__.py
│       │   └── sense360_controller.py
│       └── models/
│           ├── __init__.py
│           └── observation.py     # Shared measurement format
├── TestCode/
│   ├── FT1.py
│   ├── FT2.py
│   ├── FT3.py
│   ├── FT4.py
│   ├── IMUTest1.py
│   ├── PCA-VibrationsTEST1.py
│   ├── Ultra+IMU_Test1.py
│   └── Ultrasonic_test1.py
├── hardware/
│   ├── README.md
│   ├── bom.md
│   ├── PinnoutsPT1.md
│   └── Planning Photos.pdf
├── reports/
│   ├── README.md
│   ├── 2026-08-25_biweekly-01.md
│   ├── Challenges.md
│   ├── Sept1-15_Progress/
│   │   └── FirstFullSystemsTest.md
│   └── images_biweekly-01/
│       ├── belt-mounting-and-software-concept.png
│       ├── haptic-imu-direction-mapping.png
│       └── i2c-circuit-and-layout.png
└── minutes/
    └── 2026-08-26_minutes.md
```
