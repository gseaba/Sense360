"""
main.py

Main entry point for the Sense360 application.

This file builds the complete Sense360 system using the physical hardware
configuration from config/hardware.py and the tunable behavior parameters
from config/settings.py.

Responsibilities:
    - Create all configured HC-SR04 sensor objects.
    - Create the SensorManager.
    - Create the BNO085 MotionTracker.
    - Create the WorldModel.
    - Create the PCA9685 HapticSystem.
    - Connect all subsystems through the Sense360Controller.
    - Run the main Sense360 update loop.
    - Print useful diagnostic information during development.
    - Safely shut down all hardware when the program stops.

Hardware-specific details such as GPIO pins and I2C addresses should NOT
be hard-coded here.

Algorithm tuning values should also NOT be hard-coded here.

Instead:

    config/hardware.py
        describes what hardware is installed and how it is connected.

    config/settings.py
        describes how Sense360 should behave.

The main program simply uses those configurations to construct the
appropriate objects.
"""

import time

from config import hardware
from config import settings

from sense360.sensors.hcsr04 import HCSR04
from sense360.sensors.sensor_manager import SensorManager
from sense360.motion.motion_tracker import MotionTracker
from sense360.world.world_model import WorldModel
from sense360.haptics.haptic_system import HapticSystem
from sense360.system.sense360_controller import Sense360Controller


def create_sensors():
    """
    Create all ultrasonic sensors listed in hardware.py.

    Returns
    -------
    list
        List of initialized HCSR04 objects.

    Notes
    -----
    The current prototype creates one sensor.

    Later, adding more HC-SR04 sensors should normally require only
    adding additional entries to:

        hardware.ULTRASONIC_SENSORS

    This function will automatically create them.
    """

    sensors = []

    for sensor_config in hardware.ULTRASONIC_SENSORS:

        sensor = HCSR04(
            sensor_id=sensor_config["sensor_id"],
            trig_pin=sensor_config["trig_pin"],
            echo_pin=sensor_config["echo_pin"],
            relative_angle_deg=(
                sensor_config["relative_angle_deg"]
            ),

            min_distance_m=(
                settings.HC_SR04_MIN_DISTANCE_M
            ),

            max_distance_m=(
                settings.HC_SR04_MAX_DISTANCE_M
            ),

            timeout_s=(
                settings.HC_SR04_TIMEOUT_S
            ),

            min_measurement_interval_s=(
                settings.HC_SR04_MIN_MEASUREMENT_INTERVAL_S
            ),
        )

        sensors.append(sensor)

    return sensors


def create_sensor_manager(sensors):
    """
    Create the SensorManager that coordinates environmental sensors.
    """

    return SensorManager(
        sensors=sensors,

        delay_between_sensors_s=(
            settings.SENSOR_DELAY_BETWEEN_SENSORS_S
        ),
    )


def create_motion_tracker():
    """
    Create the BNO085 MotionTracker using hardware and software settings.
    """

    if not hardware.BNO085["enabled"]:
        raise RuntimeError(
            "BNO085 is disabled in hardware.py."
        )

    return MotionTracker(
        i2c_bus=hardware.BNO085["i2c_bus"],
        i2c_address=hardware.BNO085["i2c_address"],

        min_update_interval_s=(
            settings.MOTION_MIN_UPDATE_INTERVAL_S
        ),

        moving_acceleration_threshold_m_s2=(
            settings.MOTION_ACCELERATION_THRESHOLD_M_S2
        ),

        moving_gyro_threshold_rad_s=(
            settings.MOTION_GYRO_THRESHOLD_RAD_S
        ),

        heading_offset_deg=(
            settings.MOTION_HEADING_OFFSET_DEG
        ),
    )


def create_world_model():
    """
    Create the Sense360 WorldModel using filtering settings.
    """

    return WorldModel(
        resolution_deg=(
            settings.WORLD_RESOLUTION_DEG
        ),

        stale_after_s=(
            settings.WORLD_STALE_AFTER_S
        ),

        base_allowed_change_m=(
            settings.WORLD_BASE_ALLOWED_CHANGE_M
        ),

        allowed_change_rate_m_per_s=(
            settings.WORLD_ALLOWED_CHANGE_RATE_M_PER_S
        ),

        min_smoothing_alpha=(
            settings.WORLD_MIN_SMOOTHING_ALPHA
        ),

        max_smoothing_alpha=(
            settings.WORLD_MAX_SMOOTHING_ALPHA
        ),

        candidate_similarity_m=(
            settings.WORLD_CANDIDATE_SIMILARITY_M
        ),

        candidate_required_count=(
            settings.WORLD_CANDIDATE_REQUIRED_COUNT
        ),

        candidate_timeout_s=(
            settings.WORLD_CANDIDATE_TIMEOUT_S
        ),
    )


def create_haptic_system():
    """
    Create the PCA9685-based HapticSystem.

    Motor channel assignments and mounting angles come from hardware.py.
    """

    if not hardware.PCA9685["enabled"]:
        raise RuntimeError(
            "PCA9685 is disabled in hardware.py."
        )

    return HapticSystem(
        i2c_bus=hardware.PCA9685["i2c_bus"],
        i2c_address=hardware.PCA9685["i2c_address"],
        motors=hardware.HAPTIC_MOTORS,

        pwm_frequency_hz=(
            settings.HAPTIC_PWM_FREQUENCY_HZ
        ),

        feedback_min_distance_m=(
            settings.HAPTIC_MIN_FEEDBACK_DISTANCE_M
        ),

        feedback_max_distance_m=(
            settings.HAPTIC_MAX_FEEDBACK_DISTANCE_M
        ),

        min_active_intensity=(
            settings.HAPTIC_MIN_ACTIVE_INTENSITY
        ),

        max_intensity=(
            settings.HAPTIC_MAX_INTENSITY
        ),

        intensity_curve_power=(
            settings.HAPTIC_INTENSITY_CURVE_POWER
        ),
    )


def create_controller():
    """
    Construct the complete Sense360 software system.

    Returns
    -------
    Sense360Controller
        Fully initialized Sense360 controller.
    """

    sensors = create_sensors()

    sensor_manager = create_sensor_manager(
        sensors
    )

    motion_tracker = create_motion_tracker()

    world_model = create_world_model()

    haptic_system = create_haptic_system()

    return Sense360Controller(
        sensor_manager=sensor_manager,
        motion_tracker=motion_tracker,
        world_model=world_model,
        haptic_system=haptic_system,
    )


def print_status(
    controller,
    status,
):
    """
    Print useful development information about the running system.

    This is intentionally separate from the controller so debugging
    output does not become part of the core Sense360 logic.
    """

    heading = status["heading_deg"]

    observation_count = (
        status["observation_count"]
    )

    is_moving = status["is_moving"]

    nearest_obstacle = (
        controller.world_model.get_nearest_obstacle()
    )

    # -------------------------------------------------------------
    # Format obstacle distance.
    # -------------------------------------------------------------

    if nearest_obstacle is None:
        distance_text = "No current obstacle data"

    else:
        distance_text = (
            f"{nearest_obstacle:.2f} m"
        )

    # -------------------------------------------------------------
    # Format motor outputs.
    # -------------------------------------------------------------

    motor_status = []

    for motor in hardware.HAPTIC_MOTORS:

        motor_id = motor["motor_id"]

        intensity = (
            controller.haptic_system.get_motor_intensity(
                motor_id
            )
        )

        motor_status.append(
            f"{motor_id}: {intensity * 100:.0f}%"
        )

    motors_text = " | ".join(
        motor_status
    )

    print(
        f"Heading: {heading:6.1f}° | "
        f"Observations: {observation_count} | "
        f"Moving: {is_moving} | "
        f"Nearest: {distance_text} | "
        f"{motors_text}"
    )


def main():
    """
    Initialize and run Sense360 until the user stops the program.
    """

    controller = None

    print()
    print("========================================")
    print("          Sense360 Starting")
    print("========================================")
    print()

    try:
        # ---------------------------------------------------------
        # Build the entire Sense360 system.
        # ---------------------------------------------------------

        print("Initializing hardware...")

        controller = create_controller()

        controller.start()

        print("Sense360 initialized successfully.")
        print()
        print(
            f"Ultrasonic sensors: "
            f"{hardware.NUMBER_OF_ULTRASONIC_SENSORS}"
        )

        print(
            f"Haptic motors: "
            f"{hardware.NUMBER_OF_HAPTIC_MOTORS}"
        )

        print(
            f"World cells: "
            f"{len(controller.world_model)}"
        )

        print()
        print("Sense360 running.")
        print("Press Ctrl+C to stop.")
        print()

        # ---------------------------------------------------------
        # Diagnostic printing does not need to happen every loop.
        # ---------------------------------------------------------

        last_status_print = 0.0

        # ---------------------------------------------------------
        # Main Sense360 operating loop.
        # ---------------------------------------------------------

        while controller.is_running():

            status = controller.update()

            current_time = time.monotonic()

            if (
                current_time - last_status_print
                >= settings.DEBUG_PRINT_INTERVAL_S
            ):
                print_status(
                    controller,
                    status,
                )

                last_status_print = current_time

            # Prevent the main loop from consuming an entire CPU core.
            #
            # Individual subsystems still enforce their own update rates.
            time.sleep(
                settings.MAIN_LOOP_SLEEP_S
            )

    except KeyboardInterrupt:

        print()
        print("Sense360 stopped by user.")

    except Exception as error:

        print()
        print("Sense360 encountered an error:")
        print(
            f"{type(error).__name__}: {error}"
        )

        # Re-raise so Python still shows the traceback.
        raise

    finally:

        print()
        print("Shutting down Sense360...")

        if controller is not None:

            controller.shutdown()

        print("Shutdown complete.")
        print()


if __name__ == "__main__":
    main()