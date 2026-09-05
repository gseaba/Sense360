"""
sense360_controller.py

Coordinates the major Sense360 software subsystems.

The Sense360Controller acts as the top-level coordinator. It does not
perform low-level hardware operations itself. Instead, it tells each
subsystem when to perform its job.

A typical update cycle is:

    1. Read the wearer's orientation/motion.
    2. Collect new environmental sensor observations.
    3. Update the WorldModel.
    4. Update the haptic feedback.

Keeping the main control flow here makes the behavior of the entire
device easy to understand while keeping hardware-specific details
inside their appropriate modules.
"""


class Sense360Controller:
    """Coordinates one complete update cycle of Sense360."""

    def __init__(
        self,
        sensor_manager,
        motion_tracker,
        world_model,
        haptic_system,
    ):
        self.sensor_manager = sensor_manager
        self.motion_tracker = motion_tracker
        self.world_model = world_model
        self.haptic_system = haptic_system

    def update(self):
        """Run one complete Sense360 update cycle."""

        # Update orientation/motion information.
        self.motion_tracker.update()

        # Collect new environmental measurements.
        observations = self.sensor_manager.update()

        # Determine the wearer's current heading.
        heading = self.motion_tracker.get_heading()

        # Update our understanding of the surroundings.
        self.world_model.update(
            observations,
            heading,
        )

        # Update vibration feedback.
        self.haptic_system.update(
            self.world_model
        )

    def shutdown(self):
        """Safely shut down Sense360 hardware."""

        self.haptic_system.all_off()