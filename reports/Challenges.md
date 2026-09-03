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
