"""
haptic_system.py

Controls the vibration feedback presented to the Sense360 wearer.

The HapticSystem is responsible for converting desired motor
intensities into commands sent to the physical haptic hardware.

Initially, this will control the coin vibration motors through the
PCA9685 PWM controller and MOSFET driver circuits.

The rest of the program should not need to know which PCA9685 channel
or physical circuit controls a particular motor.

Future versions can change the haptic hardware while keeping the
higher-level Sense360 logic mostly unchanged.
"""


class HapticSystem:
    """Manages all vibration motors used for user feedback."""

    def __init__(self, motor_channels=None):
        self.motor_channels = motor_channels or []

    def set_motor(self, motor_index, intensity):
        """
        Set one motor's vibration intensity.

        intensity should eventually be limited between 0.0 and 1.0.
        """

        intensity = max(0.0, min(1.0, intensity))

        # TODO:
        # Convert intensity into a PCA9685 PWM duty cycle.
        # Send that duty cycle to the correct PCA9685 channel.
        pass

    def all_off(self):
        """Turn all vibration motors off."""

        for motor_index in range(len(self.motor_channels)):
            self.set_motor(motor_index, 0.0)

    def update(self, world_model):
        """
        Update vibration feedback using the current WorldModel.

        The first feedback algorithm will eventually be implemented here
        or delegated to a separate strategy if the algorithms become
        complicated enough to justify another class.
        """

        # TODO: Convert world distances into vibration feedback.
        pass