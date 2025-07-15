# Voice Recognition Door Opener - macOS Version

This is the macOS development version of the voice recognition door opener. It allows you to test and develop the voice recognition system on macOS without needing a Raspberry Pi.

## Features

- ✅ **Voice Recognition**: Uses VOSK for Czech speech recognition
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

### Porting to Raspberry Pi

When ready to deploy on Raspberry Pi:
1. Use the original `main.py` (includes GPIO and Bluetooth)
2. Run `./install.sh` on the Pi
3. Configure systemd service

## File Structure

```
voice-recognizer/
├── run_macos.py              # macOS main app
├── setup_macos.sh            # macOS setup script
├── requirements-macos.txt     # macOS dependencies
├── test_sounds.py            # Sound system test
├── sounds/                   # Sound effects
│   ├── prompt-0.mp3
│   ├── prompt-10pm-0.mp3
│   ├── success-0.mp3
│   └── fail-0.mp3
├── vosk-model-cs/            # VOSK model
├── passwords.txt             # Password list
└── config.yaml              # Configuration
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