"""
motion_tracker.py

Tracks the orientation and motion of the Sense360 wearer.

Initially, this class will obtain orientation information from the
BNO085 IMU, especially the user's heading. This information allows
sensor measurements to be converted from directions relative to the
belt into directions relative to the surrounding environment.

Future versions may also use:
    - Pitch and roll
    - Angular velocity
    - Linear acceleration
    - Movement detection
    - Additional motion or position estimation

Keeping this logic here prevents the WorldModel from depending
directly on BNO085-specific code.
"""


class MotionTracker:
    """Stores and updates the current orientation/motion of the wearer."""

    def __init__(self):
        self.heading_deg = 0.0
        self.pitch_deg = 0.0
        self.roll_deg = 0.0
        self.is_moving = False

    def update(self):
        """
        Read new motion/orientation information.

        BNO085 communication code will eventually be placed here.
        """

        # TODO: Read BNO085 data.
        pass

    def get_heading(self):
        """Return the current heading in degrees."""
        return self.heading_deg