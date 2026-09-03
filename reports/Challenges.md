# Challenges and Obstacles

## Pi Setup

During the initial setup of the Raspberry Pi 4 Model B, several challenges were encountered while attempting to establish a headless SSH connection.

### Initial Connection

The Raspberry Pi was being configured without a dedicated monitor or keyboard. Initially, the Pi was connected directly to a MacBook Pro through USB-C. Although the Pi powered on and the green activity LED indicated that it was reading from the microSD card, the Mac did not recognize the Pi as a USB network device.

This indicated that the existing Raspberry Pi OS installation was not configured for USB gadget mode. Therefore, the USB-C connection was providing power but could not be used to SSH into the Pi.

### University Network Connection

The Pi was then connected to the University of Iowa network using Ethernet. An attempt was made to locate the Pi from the Mac using:

```bash
ping raspberrypi.local
```

The Mac returned:

```text
ping: cannot resolve raspberrypi.local: Unknown host
```

Because the university uses a managed network, local hostname discovery between devices may not always function as it would on a typical home network.

As a workaround, a Dell computer that was also connected through Ethernet was used. From this computer:

```bash
ping raspberrypi.local
```

successfully received replies from the Raspberry Pi. This confirmed that the Pi was booting correctly, had connected to the network, and was reachable from another device.

### SSH Host Key Conflict

When attempting to SSH into the Pi from the Dell computer, SSH reported that the host key had changed and refused the connection.

The previously stored SSH key was removed using:

```bash
ssh-keygen -R raspberrypi.local
```

After removing the old key, a new SSH connection could be established and the Raspberry Pi prompted for a password.

### Unknown Login Credentials

The next challenge was authentication. The Raspberry Pi came as part of a RasTech kit with a preconfigured microSD card, but the username and password associated with the existing installation were unknown.

The older default Raspberry Pi credentials were attempted but did not work. After several attempts, SSH returned:

```text
Permission denied (publickey,password)
```

At this point, network communication and SSH functionality had both been confirmed. The remaining issue was that the login credentials for the existing Raspberry Pi installation were unknown.

### Re-Imaging the Raspberry Pi

Rather than continuing to guess the credentials, the decision was made to re-image the microSD card using Raspberry Pi Imager.

The new configuration uses:

- **Device:** Raspberry Pi 4 Model B
- **Operating System:** Raspberry Pi OS (64-bit)
- **Hostname:** `raspi`
- **Time Zone:** `America/Chicago`
- **SSH:** Enabled
- **Pi Connect:** Disabled

A known username and password were also configured during imaging. This provides complete control over the Raspberry Pi configuration and eliminates the unknown credentials from the original installation.

After imaging, the Raspberry Pi should be accessible over SSH using:

```bash
ssh sense@raspi.local
```

Overall, the setup process demonstrated several potential challenges with headless Raspberry Pi configuration, including USB networking limitations, managed university network behavior, stored SSH host keys, and unknown factory credentials. Re-imaging the microSD card with a known configuration provided the most reliable solution.

## BNO085 IMU Integration Notes

### Initial Setup

The BNO085 was first connected to the Raspberry Pi hardware I2C bus.

| BNO085 Pin | Raspberry Pi |
| :--- | :--- |
| VCC | 3.3 V - Pin 1 |
| GND | GND - Pin 6 |
| SDA | GPIO2 - Pin 3 |
| SCL | GPIO3 - Pin 5 |

The IMU was detected at address `0x4B`.

### Problems Encountered

The required Python libraries initially failed to install because `swig` and the `lgpio` system library were missing.

```bash
sudo apt install swig python3-dev build-essential
sudo apt install liblgpio-dev
```

After installation, the BNO085 communicated with the Pi but produced frequent corrupted I2C packets.

Common errors included:

```text
KeyError: 123
KeyError: 255
IndexError: list assignment index out of range
```

Increasing the hardware I2C speed to 400 kHz improved communication slightly, but errors still occurred too frequently.

The code was also modified to ignore corrupted packets and reuse the last valid heading. This kept the program from crashing but did not solve the underlying communication problem.

### Final Solution

The BNO085 was moved to a separate software I2C bus.

| BNO085 Pin | BCM GPIO | Physical Pin |
| :--- | :---: | ---: |
| VCC | - | 1 |
| GND | - | 6 |
| SDA | GPIO20 | 38 |
| SCL | GPIO21 | 40 |

The following line was added to `/boot/firmware/config.txt`:

```text
dtoverlay=i2c-gpio,bus=8,i2c_gpio_sda=20,i2c_gpio_scl=21
```

The Python code was changed to use software I2C bus 8:

```python
from adafruit_extended_bus import ExtendedI2C as I2C

i2c = I2C(8)
bno = BNO08X_I2C(i2c, address=0x4B)
```

### Final I2C Architecture

| Device | Bus | SDA | SCL | Address |
| :--- | :--- | :--- | :--- | :--- |
| PCA9685 | Hardware I2C Bus 1 | GPIO2 / Pin 3 | GPIO3 / Pin 5 | `0x40` |
| BNO085 | Software I2C Bus 8 | GPIO20 / Pin 38 | GPIO21 / Pin 40 | `0x4B` |

Moving the BNO085 to software I2C eliminated the frequent corrupted-packet errors and provided stable IMU communication.