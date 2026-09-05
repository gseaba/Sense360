"""
world_model.py

Stores Sense360's current understanding of the environment surrounding
the wearer.

The WorldModel receives sensor Observations and stores useful
information about different directions around the user.

Each portion of the world stores not only the measured distance, but
also when that information was last updated. This allows Sense360 to
recognize stale information and avoid trusting measurements that are
too old.

The WorldModel should not know whether its measurements came from an
HC-SR04, LiDAR, or another sensor. It works only with standardized
Observation objects.
"""

import time
from dataclasses import dataclass


@dataclass
class WorldCell:
    """Stores the current knowledge about one direction."""

    distance_m: float | None = None
    last_updated: float | None = None
    confidence: float = 0.0

    def age(self):
        """Return how many seconds have passed since this cell was updated."""

        if self.last_updated is None:
            return None

        return time.monotonic() - self.last_updated


class WorldModel:
    """Stores the current environmental data around the wearer."""

    def __init__(self, resolution_deg=45):
        self.resolution_deg = resolution_deg

        number_of_cells = int(360 / resolution_deg)

        self.cells = [
            WorldCell()
            for _ in range(number_of_cells)
        ]

    def update(self, observations, heading_deg):
        """Use new sensor observations to update the world model."""

        for observation in observations:

            world_angle = (
                heading_deg + observation.relative_angle_deg
            ) % 360

            cell_index = int(
                world_angle / self.resolution_deg
            ) % len(self.cells)

            cell = self.cells[cell_index]

            cell.distance_m = observation.distance_m
            cell.last_updated = observation.timestamp
            cell.confidence = observation.confidence

    def get_cell(self, index):
        """Return one section of the world model."""
        return self.cells[index]