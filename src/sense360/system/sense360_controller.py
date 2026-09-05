"""
sense360_controller.py

Coordinates the major Sense360 software subsystems.

The Sense360Controller is the top-level coordinator for one complete
Sense360 operating cycle.

It connects:
    - MotionTracker
    - SensorManager
    - WorldModel
    - HapticSystem

The controller intentionally does NOT contain hardware-specific code.
It does not know:
    - Which GPIO pins are used.
    - How an HC-SR04 measures distance.
    - How the BNO085 communicates over I2C.
    - Which PCA9685 channels control the motors.
    - How WorldModel filtering works.
    - How motor intensity is calculated.

Instead, it tells each subsystem when to perform its job.

Current update sequence:

    1. Update wearer orientation and motion information.
    2. Read environmental sensors.
    3. Obtain the current wearer heading.
    4. Update the WorldModel using sensor observations and heading.
    5. Update haptic feedback using the WorldModel and wearer heading.

Keeping this control flow in one place makes the overall operation of
Sense360 easy to understand and allows individual subsystems to be
modified without rewriting the rest of the application.
"""


class Sense360Controller:
    """
    Coordinates the major Sense360 subsystems.
    """

    def __init__(
        self,
        sensor_manager,
        motion_tracker,
        world_model,
        haptic_system,
    ):
        """
        Create the Sense360Controller.

        Parameters
        ----------
        sensor_manager : SensorManager
            Manages environmental sensors and returns Observations.

        motion_tracker : MotionTracker
            Tracks wearer heading, orientation, and motion.

        world_model : WorldModel
            Stores and filters Sense360's understanding of the
            surrounding environment.

        haptic_system : HapticSystem
            Converts WorldModel information into vibration feedback.
        """

        self.sensor_manager = sensor_manager
        self.motion_tracker = motion_tracker
        self.world_model = world_model
        self.haptic_system = haptic_system

        self._running = False
        self.update_count = 0

    def update(self):
        """
        Run one complete Sense360 update cycle.

        Returns
        -------
        dict
            Basic information about the completed update.

            This is primarily useful during development and testing.

            Example:

                {
                    "heading_deg": 90.2,
                    "observation_count": 1,
                    "is_moving": False,
                }

        Notes
        -----
        Individual subsystems control their own update rates.

        For example:
            - MotionTracker may only read the BNO085 every 20 ms.
            - HC-SR04 may only fire every 60 ms.

        Therefore this method can be called repeatedly from main.py
        without needing to manually delay every subsystem here.
        """

        # =========================================================
        # 1. UPDATE MOTION / ORIENTATION
        # =========================================================

        self.motion_tracker.update()

        # Use the latest available heading.
        heading_deg = (
            self.motion_tracker.get_heading()
        )

        # =========================================================
        # 2. READ ENVIRONMENTAL SENSORS
        # =========================================================

        observations = (
            self.sensor_manager.update()
        )

        # =========================================================
        # 3. UPDATE THE WORLD MODEL
        # =========================================================

        # Even if observations is empty, WorldModel.update() is still
        # called so stale environmental data can be removed.
        self.world_model.update(
            observations=observations,
            heading_deg=heading_deg,
        )

        # =========================================================
        # 4. UPDATE HAPTIC FEEDBACK
        # =========================================================

        self.haptic_system.update(
            world_model=self.world_model,
            heading_deg=heading_deg,
        )

        self.update_count += 1

        # Return a small amount of diagnostic information.
        # main.py does not have to use this, but it will be useful
        # while testing the first prototype.
        return {
            "heading_deg": heading_deg,
            "observation_count": len(observations),
            "is_moving": (
                self.motion_tracker.get_is_moving()
            ),
        }

    def start(self):
        """
        Mark Sense360 as running.

        The controller does not create its own infinite loop.
        main.py remains responsible for repeatedly calling update().

        Keeping the loop outside the controller makes testing easier
        because individual update cycles can be run manually.
        """

        self._running = True

    def stop(self):
        """
        Mark Sense360 as stopped and disable all vibration motors.
        """

        self._running = False

        self.haptic_system.all_off()

    def is_running(self):
        """
        Return whether Sense360 is currently marked as running.
        """

        return self._running

    def get_update_count(self):
        """
        Return the number of complete update cycles that have run.
        """

        return self.update_count

    def shutdown(self):
        """
        Safely shut down every Sense360 subsystem.

        Cleanup order:
            1. Turn off vibration motors.
            2. Release sensor GPIO resources.
            3. Release IMU I2C resources.
            4. Release PCA9685 I2C resources.

        Cleanup methods are individually protected so an error while
        shutting down one subsystem does not prevent the others from
        being cleaned up.
        """

        self._running = False

        # ---------------------------------------------------------
        # Turn motors off immediately.
        # ---------------------------------------------------------

        try:
            self.haptic_system.all_off()
        except Exception:
            pass

        # ---------------------------------------------------------
        # Release sensor GPIO resources.
        # ---------------------------------------------------------

        try:
            self.sensor_manager.cleanup()
        except Exception:
            pass

        # ---------------------------------------------------------
        # Release BNO085 resources.
        # ---------------------------------------------------------

        try:
            self.motion_tracker.cleanup()
        except Exception:
            pass

        # ---------------------------------------------------------
        # Release PCA9685 resources.
        # ---------------------------------------------------------

        try:
            self.haptic_system.cleanup()
        except Exception:
            pass