# Voice Recognition Door Opener for Raspberry Pi & macOS

## Project Overview

This project creates an automated voice recognition system for door access control using a Raspberry Pi 4 or macOS. The system connects to a Bluetooth handsfree device (on Pi), listens for a button press (on Pi) or Enter key (on macOS), prompts for a password via audio, processes voice input using the VOSK engine, and publishes MQTT messages to control smart home door locks.

---

## Architecture

- **Shared core logic**: All business logic, audio, password, and MQTT code is in `voice_recognizer_base.py`.
- **Platform-specific entry points**:
  - `main.py` (Raspberry Pi): Handles GPIO, Bluetooth, and button events.
  - `run_macos.py` (macOS): Handles interactive mode for development/testing.
- **Add new features and bugfixes in the base class** for both platforms.
- **macOS and Raspberry Pi behave identically** except for hardware integration.
- See also: [`README-macos.md`](./README-macos.md)

---

## System Requirements

### Hardware (Raspberry Pi)
- **Raspberry Pi 4** (2GB RAM minimum, 4GB recommended)
- **Bluetooth handsfree device** (headset, speakerphone, etc.)
- **Push button** (GPIO connected)
- **Microphone** (built into handsfree or separate USB microphone)
- **Speaker** (built into handsfree or separate audio output)
- **Power supply** (5V/3A recommended for Pi 4)

### Software
- **Raspberry Pi OS** (64-bit recommended for better performance)
- **macOS 10.15+** (for development/testing)
- **Python 3.8+**
- **VOSK** (Czech or English language model)
- **PyAudio** (audio processing)
- **Paho MQTT** (MQTT client)
- **RPi.GPIO** (button handling, Pi only)

---

## System Architecture

```
+-------------------+    +-------------------+    +-------------------+
|   Push Button     |--->|  Raspberry Pi     |--->|   MQTT Broker     |
|   (GPIO Input)    |    |  (Python App)     |    |  (Smart Home)     |
+-------------------+    +-------------------+    +-------------------+
                            |
                            v
                   +-------------------+
                   | Bluetooth Audio   |
                   |   (Handsfree)     |
                   +-------------------+

Or on macOS:

+-------------------+
|   macOS App       |
| (Python, Enter)   |
+-------------------+
        |
        v
+-------------------+
|  System Microphone|
+-------------------+
```

---

## File Structure

```
voice-recognizer/
├── README.md
├── README-macos.md
├── requirements.txt
├── requirements-macos.txt
├── config.yaml
├── voice_recognizer_base.py   # Shared core logic (all platforms)
├── main.py                    # Raspberry Pi entry point (GPIO, Bluetooth)
├── run_macos.py               # macOS entry point (interactive mode)
├── bluetooth_manager.py
├── audio_manager.py
├── voice_processor.py
├── mqtt_client.py
├── button_handler.py
├── passwords.txt
├── sounds/
├── vosk-model-cs/ (or vosk-model-en/)
├── systemd/
└── ...
```

---

## Development Workflow

- **Add new features and bugfixes in `voice_recognizer_base.py`**
- Platform-specific code (GPIO, Bluetooth, button) is only in `main.py` (Pi) or `run_macos.py` (macOS)
- Test on macOS with `python run_macos.py` (no GPIO/Bluetooth)
- Deploy to Raspberry Pi with `python main.py` (full hardware support)

---

## Installation & Usage (Raspberry Pi)

1. Flash Raspberry Pi OS 64-bit to SD card
2. Enable SSH and configure network
3. Install system dependencies
4. Install Python requirements
5. Configure Bluetooth pairing
6. Set up MQTT broker connection
7. Configure systemd service for auto-start

```bash
# Start the service
sudo systemctl start voice-recognizer

# Check status
sudo systemctl status voice-recognizer

# View logs
sudo journalctl -u voice-recognizer -f
```

---

## Security & Troubleshooting

- Use strong passwords in the password list
- Secure MQTT broker with authentication
- Regular security updates for Raspberry Pi OS
- See `README-macos.md` for macOS-specific notes

---

## See Also
- [`README-macos.md`](./README-macos.md) for macOS development/testing 