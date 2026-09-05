# Sense360

Senior Design class project repository.

## Links

Reports found [here](./reports/README.md)  

Hardware information found [here](./hardware/README.md)

Project TODO found [here](./TODO.md)


## Repository Structure

```text
Senior-Project
├── reports/
│   ├── README.md                  # Instructions & submission log
│   ├── 2026-08-25_biweekly-01.md
│   ├── images_biweekly-01
|   └── Sept1-15_Progress
|       └── FirstFullSystemsTest.md
├── hardware/
│   ├── README.md                  # Hardware overview & specs
│   ├── bom.md                     # Bill of Materials & component costs
│   ├── pinoutsPT1.md              # MCU pin mapping & hardware interfaces for first prototype
│   └── schematics/                # Schematic files, SVGs, or PNG renders
|—— src/
|    └── sense360/
|        │
|        ├── sensors/
|        │   ├── hcsr04.py
|        │   └── sensor_manager.py
|        │
|        ├── motion/
|        │   └── motion_tracker.py
|        │
|        ├── world/
|        │   └── world_model.py
|        │
|        ├── haptics/
|        │   └── haptic_system.py
|        │
|        ├── system/
|        │   └── sense360_controller.py
|        │
|        └── models/
|            └── observation.py
|
|—— config/
|        hardware.yaml
|
|—— TestCode/
    └── TODO.md                        # Master task list & status
```