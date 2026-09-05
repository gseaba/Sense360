"""
settings.py

Contains tunable software settings for the Sense360 system.

These values control how Sense360 behaves rather than describing how
the physical hardware is wired.

The purpose of keeping these settings in one place is to make testing
and calibration easier. Parameters can be adjusted here without editing
the internal implementation of classes such as HCSR04, SensorManager,
or WorldModel.

Examples of values that belong here:
    - Ultrasonic sensor timing limits
    - Sensor scheduling delays
    - WorldModel filtering thresholds
    - Stale-data timing
    - Smoothing behavior
    - Candidate-measurement behavior

Physical configuration such as GPIO pins, sensor mounting angles, and
PCA9685 motor channels belongs in hardware.py instead.
"""


# =====================================================================
# HC-SR04 SETTINGS
# =====================================================================

# Minimum accepted HC-SR04 measurement.
HC_SR04_MIN_DISTANCE_M = 0.02

# Maximum accepted HC-SR04 measurement.
#
# The HC-SR04 may technically report distances near this range, although
# the useful Sense360 range may later be reduced after physical testing.
HC_SR04_MAX_DISTANCE_M = 4.0

# Maximum amount of time to wait for an ECHO transition before treating
# the measurement as failed.
HC_SR04_TIMEOUT_S = 0.03

# Minimum time between trigger pulses from the SAME HC-SR04 sensor.
#
# This prevents an individual sensor from being triggered too rapidly.
HC_SR04_MIN_MEASUREMENT_INTERVAL_S = 0.06


# =====================================================================
# SENSOR MANAGER SETTINGS
# =====================================================================

# Minimum delay placed between reading DIFFERENT sensors.
#
# This primarily helps reduce ultrasonic cross-talk when several
# HC-SR04 sensors are installed around the belt.
#
# This is different from HC_SR04_MIN_MEASUREMENT_INTERVAL_S:
#
#     HC_SR04_MIN_MEASUREMENT_INTERVAL_S
#         protects one individual sensor from firing too often.
#
#     SENSOR_DELAY_BETWEEN_SENSORS_S
#         separates different sensors from one another.
SENSOR_DELAY_BETWEEN_SENSORS_S = 0.02


# =====================================================================
# WORLD MODEL STRUCTURE
# =====================================================================

# Angular width of each world cell.
#
# Examples:
#     90 degrees -> 4 cells
#     45 degrees -> 8 cells
#     30 degrees -> 12 cells
#     10 degrees -> 36 cells
#      5 degrees -> 72 cells
#
# This value must divide evenly into 360.
WORLD_RESOLUTION_DEG = 45


# =====================================================================
# WORLD MODEL DATA AGE
# =====================================================================

# Once accepted world data becomes older than this value, the old
# information is completely discarded.
WORLD_STALE_AFTER_S = 1.0


# =====================================================================
# WORLD MODEL AGE-DEPENDENT REJECTION
# =====================================================================

# Minimum difference that is always allowed between the current world
# value and a new observation.
#
# 0.15 m = 15 cm
WORLD_BASE_ALLOWED_CHANGE_M = 0.15

# Determines how rapidly the allowed difference increases as the
# currently stored measurement gets older.
#
# Default:
#     1.0 meter of additional allowed difference per second of age.
#
# Examples with the current settings:
#
#     age = 0.00 s
#         allowed difference = 0.15 m
#
#     age = 0.10 s
#         allowed difference = 0.25 m
#
#     age = 0.50 s
#         allowed difference = 0.65 m
WORLD_ALLOWED_CHANGE_RATE_M_PER_S = 1.0


# =====================================================================
# WORLD MODEL SMOOTHING
# =====================================================================

# Smoothing alpha determines how far the stored world distance moves
# toward an accepted new measurement.
#
# Example:
#
#     old distance = 1.00 m
#     new distance = 0.90 m
#     alpha = 0.20
#
#     stored distance becomes:
#         1.00 + 0.20 * (0.90 - 1.00)
#         = 0.98 m
#
# Young world data uses the minimum alpha.
WORLD_MIN_SMOOTHING_ALPHA = 0.20

# As stored data gets older, the smoothing alpha increases toward this
# value so new observations influence the world more strongly.
WORLD_MAX_SMOOTHING_ALPHA = 0.80


# =====================================================================
# WORLD MODEL UNEXPECTED-MEASUREMENT CANDIDATES
# =====================================================================

# When a measurement is rejected because it differs greatly from recent
# world data, it becomes a candidate.
#
# Additional rejected measurements must be within this distance of the
# candidate to count as evidence of the same environmental change.
#
# 0.10 m = 10 cm
WORLD_CANDIDATE_SIMILARITY_M = 0.10

# Number of similar unexpected measurements required before the candidate
# is considered real and replaces the old world measurement.
WORLD_CANDIDATE_REQUIRED_COUNT = 3

# Maximum time allowed between candidate observations.
#
# If another supporting observation does not arrive within this period,
# the candidate is forgotten and the process starts over.
WORLD_CANDIDATE_TIMEOUT_S = 0.30

# =====================================================================
# MOTION TRACKER SETTINGS
# =====================================================================

# Maximum MotionTracker update rate.
#
# 0.02 seconds corresponds to approximately 50 Hz.
MOTION_MIN_UPDATE_INTERVAL_S = 0.02


# Linear acceleration magnitude required before Sense360 considers
# the wearer to be moving.
#
# This is a starting value and should be tuned experimentally.
MOTION_ACCELERATION_THRESHOLD_M_S2 = 0.35


# Angular velocity required before Sense360 considers the wearer to
# be turning/moving.
#
# 0.15 rad/s is approximately 8.6 degrees per second.
MOTION_GYRO_THRESHOLD_RAD_S = 0.15


# Heading correction used to account for the physical mounting
# orientation of the BNO085 on the Sense360 belt.
MOTION_HEADING_OFFSET_DEG = 0.0

# =====================================================================
# HAPTIC SYSTEM SETTINGS
# =====================================================================

# PWM frequency generated by the PCA9685 for the vibration motors.
HAPTIC_PWM_FREQUENCY_HZ = 200


# Distance at which vibration reaches maximum intensity.
HAPTIC_MIN_FEEDBACK_DISTANCE_M = 0.20


# Obstacles farther away than this do not generate vibration.
HAPTIC_MAX_FEEDBACK_DISTANCE_M = 2.00


# Lowest non-zero vibration command.
#
# This may need adjustment depending on the minimum duty cycle that
# reliably starts the physical coin vibration motors.
HAPTIC_MIN_ACTIVE_INTENSITY = 0.25


# Maximum allowed motor intensity.
HAPTIC_MAX_INTENSITY = 1.00


# Controls the shape of the distance-to-vibration curve.
#
# 1.0 = linear
#
# > 1.0 keeps vibration weaker at longer distances and causes it to
# increase more rapidly as an obstacle gets closer.
HAPTIC_INTENSITY_CURVE_POWER = 1.0