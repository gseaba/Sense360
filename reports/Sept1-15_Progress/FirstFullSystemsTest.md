[Back to README](./README.md)

## First Full-System Test

We completed the first full-system test using:

- 1 HC-SR04 ultrasonic sensor
- BNO085 IMU
- PCA9685 PWM driver
- MOSFET board
- Battery supply
- 1 vibration motor

The ultrasonic sensor successfully controlled the vibration motor while the system printed live heading, distance, and vibration information.

### Vibration Methods Tested

We tested three different haptic feedback methods:

1. **Amplitude Control**
   - The motor vibrated more strongly as objects got closer.

2. **Parking-Sensor Style Pulsing**
   - The motor pulsed slowly when objects were far away.
   - The pulse rate increased as objects got closer.
   - Very close objects caused continuous vibration.

3. **Frequency + Amplitude Control**
   - The motor stayed active continuously.
   - Both vibration strength and PWM frequency changed with distance.

### Ultrasonic Sensor Filtering

The HC-SR04 occasionally produced inconsistent or unrealistic measurements.

To improve stability, software outlier detection was added:

- Small changes from the stored distance are accepted immediately.
- Large sudden changes are treated as suspicious.
- A large change is only accepted after several similar measurements occur in a row.

This allows the system to ignore brief false readings while still responding when the actual environment changes.