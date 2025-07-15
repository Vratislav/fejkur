# Voice Recognition Door Opener - macOS Version

This is the macOS development version of the voice recognition door opener. It allows you to test and develop the voice recognition system on macOS without needing a Raspberry Pi.

---

## Architecture

- **Shared core logic**: All business logic, audio, password, and MQTT code is in `voice_recognizer_base.py`.
- **Platform-specific entry points**:
  - `run_macos.py` (macOS): Handles interactive mode for development/testing.
  - `main.py` (Raspberry Pi): Handles GPIO, Bluetooth, and button events.
- **Add new features and bugfixes in the base class** for both platforms.
- **macOS and Raspberry Pi behave identically** except for hardware integration.
- See also: [`README.md`](./README.md)

---

## Features

- ✅ **Voice Recognition**: Uses VOSK for Czech or English speech recognition
- ✅ **Sound Effects**: Time-based sound selection with cycling
- ✅ **Password Management**: Configurable password matching
- ✅ **MQTT Integration**: Optional MQTT messaging
- ✅ **Interactive Mode**: Easy testing interface
- ❌ **No GPIO**: Button handling not available on macOS
- ❌ **No Bluetooth**: Bluetooth audio not available on macOS

## Prerequisites

- macOS 10.15 or later
- Python 3.8 or later
- Homebrew (for installing dependencies)

## Quick Setup

1. **Install Homebrew** (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Run the setup script**:
   ```bash
   ./setup_macos.sh
   ```

3. **Test the sound system**:
   ```bash
   source venv/bin/activate
   python test_sounds.py
   ```

4. **Run the voice recognizer**:
   ```bash
   source venv/bin/activate
   python run_macos.py
   ```

## Usage

### Interactive Mode

The macOS version runs in interactive mode:

1. **Start the app**: `python run_macos.py`
2. **Press Enter** to start voice recognition
3. **Say a password** from `passwords.txt`
4. **Press 'q'** to quit

### Sample Passwords

The setup script creates sample passwords in `passwords.txt`:
- `v sklo`
- `otevři dveře`
- `heslo`

You can edit this file to add your own passwords.

### Sound System

The app uses the enhanced sound system:
- **Normal hours (6 AM - 10 PM)**: Uses regular sound files
- **After 10 PM**: Uses quieter "10pm" sound files
- **Multiple files**: Cycles through available sound files
- **MP3 support**: Plays your custom sound effects

## Configuration

### MQTT (Optional)

To enable MQTT messaging, edit `config.yaml`:

```yaml
mqtt:
  broker: "192.168.1.64"
  port: 1883
  username: "homey"
  password: "homey"
  topic: "home/door/unlock"
```

### Audio Settings

Audio settings can be adjusted in `config.yaml`:

```yaml
audio:
  sample_rate: 16000
  channels: 1
  chunk_size: 1024
  silence_threshold: 0.01
```

## Troubleshooting

### Audio Issues

1. **Check microphone permissions**:
   - System Preferences → Security & Privacy → Microphone
   - Enable Terminal/Python access

2. **Test audio devices**:
   ```bash
   python -c "import pyaudio; p = pyaudio.PyAudio(); print([p.get_device_info_by_index(i)['name'] for i in range(p.get_device_count())])"
   ```

### VOSK Model Issues

1. **Download manually**: Visit https://alphacephei.com/vosk/models/
2. **Extract to `vosk-model-cs/`** directory
3. **Verify model structure**:
   ```
   vosk-model-cs/
   ├── am/
   ├── conf/
   ├── graph/
   └── ivector/
   ```

### Import Errors

1. **Activate virtual environment**:
   ```bash
   source venv/bin/activate
   ```

2. **Reinstall dependencies**:
   ```bash
   pip install -r requirements-macos.txt
   ```

## Development

### Code Structure

- **All core logic is in `voice_recognizer_base.py`** (shared by both platforms)
- **macOS entry point**: `run_macos.py` (just a thin wrapper)
- **Raspberry Pi entry point**: `main.py` (handles GPIO, Bluetooth, button)
- **Add new features and bugfixes in the base class** for both platforms
- See [`README.md`](./README.md) for Pi-specific and deployment notes

### Testing Components

- **Sound system**: `python test_sounds.py`
- **Voice recognition**: `python test_vosk.py`
- **Password matching**: `python test_system.py`

### Adding Features

The macOS version is designed for development. You can:
- Test voice recognition logic
- Develop password matching algorithms
- Test sound system features
- Develop MQTT integration
- All improvements should be made in `voice_recognizer_base.py` for both platforms

### Porting to Raspberry Pi

When ready to deploy on Raspberry Pi:
1. Use the same codebase (shared base class)
2. Run `./install.sh` on the Pi
3. Configure systemd service

## File Structure

```
voice-recognizer/
├── run_macos.py              # macOS main app (thin wrapper)
├── main.py                   # Raspberry Pi main app (GPIO, Bluetooth)
├── voice_recognizer_base.py  # Shared core logic (all platforms)
├── setup_macos.sh            # macOS setup script
├── requirements-macos.txt    # macOS dependencies
├── requirements.txt          # Pi dependencies
├── test_sounds.py            # Sound system test
├── sounds/                   # Sound effects
│   ├── prompt-0.mp3
│   ├── prompt-10pm-0.mp3
│   ├── success-0.mp3
│   └── fail-0.mp3
├── vosk-model-cs/            # VOSK model
├── passwords.txt             # Password list
├── config.yaml               # Configuration
└── ...
```

## Logs

The app creates logs in:
- `voice-recognizer-macos.log` - Application logs
- Console output - Real-time logging

## Security Notes

- This is a development version
- No GPIO access (no physical button)
- No Bluetooth audio (uses system microphone)
- MQTT is optional and can be disabled
- Passwords are stored in plain text for testing

---

## See Also
- [`README.md`](./README.md) for Raspberry Pi and deployment details 