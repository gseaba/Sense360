"""
observation.py

Defines the standard format used to pass sensor measurements through
the Sense360 software.

All distance-sensing hardware should convert its raw measurements into
Observation objects. This keeps the WorldModel independent of the
specific sensor hardware being used.

For example:
    - An HC-SR04 may create one Observation per measurement.
    - A LiDAR may create hundreds of Observations per scan.

The rest of the system only needs to understand Observation objects,
not how the physical sensor generated them.
"""

from dataclasses import dataclass


@dataclass
class Observation:
    """Represents one distance measurement in a particular direction."""

    distance_m: float
    relative_angle_deg: float
    timestamp: float
    sensor_id: str
    confidence: float = 1.0