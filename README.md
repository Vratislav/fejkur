# Voice Recognition Door Opener for Raspberry Pi

## Project Overview

This project creates an automated voice recognition system for door access control using a Raspberry Pi 4. The system automatically connects to a Bluetooth handsfree device, listens for a button press, prompts for a password via audio, processes voice input using the Czech VOSK engine, and publishes MQTT messages to control smart home door locks.

## System Requirements

### Hardware
- **Raspberry Pi 4** (2GB RAM minimum, 4GB recommended)
- **Bluetooth handsfree device** (headset, speakerphone, etc.)
- **Push button** (GPIO connected)
- **Microphone** (built into handsfree or separate USB microphone)
- **Speaker** (built into handsfree or separate audio output)
- **Power supply** (5V/3A recommended for Pi 4)

### Software
- **Raspberry Pi OS** (64-bit recommended for better performance)
- **Python 3.8+**
- **VOSK** (Czech language model)
- **PyAudio** (audio processing)
- **PyBluez** (Bluetooth connectivity)
- **Paho MQTT** (MQTT client)
- **GPIO Zero** (button handling)

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Push Button   │───▶│  Raspberry Pi   │───▶│   MQTT Broker   │
│   (GPIO Input)  │    │   (Python App)  │    │  (Smart Home)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ Bluetooth Audio │
                       │   (Handsfree)   │
                       └─────────────────┘
```

## Workflow

1. **Startup**: System boots and automatically connects to paired Bluetooth handsfree
2. **Standby**: System waits for button press while monitoring audio
3. **Activation**: Button press triggers password prompt audio
4. **Listening**: System records audio from microphone
5. **Processing**: VOSK engine processes Czech speech to text
6. **Validation**: Compares recognized text against password list
7. **Action**: If password matches, publishes MQTT message to unlock door
8. **Feedback**: Provides audio confirmation of success/failure

## File Structure

```
voice-recognizer/
├── README.md
├── requirements.txt
├── config.yaml
├── main.py
├── bluetooth_manager.py
├── audio_manager.py
├── voice_processor.py
├── mqtt_client.py
├── button_handler.py
├── passwords.txt
├── audio/
│   ├── password_prompt.wav
│   ├── success.wav
│   └── failure.wav
└── systemd/
    └── voice-recognizer.service
```

## Configuration

### Audio Settings
- Sample rate: 16000 Hz
- Channels: 1 (mono)
- Format: 16-bit PCM
- Recording duration: 5 seconds (configurable)

### MQTT Settings
- Broker: Local or cloud MQTT broker
- Topic: `home/door/unlock`
- Message: `{"action": "unlock", "timestamp": "..."}`

### Security
- Password list stored locally
- Audio recordings not stored (privacy)
- MQTT authentication required

## Installation

1. Flash Raspberry Pi OS 64-bit to SD card
2. Enable SSH and configure network
3. Install system dependencies
4. Install Python requirements
5. Configure Bluetooth pairing
6. Set up MQTT broker connection
7. Configure systemd service for auto-start

## Usage

The system runs automatically at startup. Manual operation:

```bash
# Start the service
sudo systemctl start voice-recognizer

# Check status
sudo systemctl status voice-recognizer

# View logs
sudo journalctl -u voice-recognizer -f
```

## Troubleshooting

- **Bluetooth issues**: Check pairing status, restart bluetooth service
- **Audio problems**: Verify audio device selection, check volume levels
- **VOSK errors**: Ensure Czech model is downloaded and accessible
- **MQTT failures**: Verify broker connectivity and credentials

## Security Considerations

- Use strong passwords in the password list
- Secure MQTT broker with authentication
- Consider encrypting password file
- Regular security updates for Raspberry Pi OS
- Physical security of the device

## Performance Optimization

- Use 64-bit OS for better memory management
- Optimize audio buffer sizes
- Minimize background processes
- Use SSD storage for better I/O performance 