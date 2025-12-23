# Gesture Music Player

A gesture-controlled music player that uses hand gestures detected through your webcam to control music playback. Now with a simple web interface!

## Features

- **Hand Gesture Controls**: Control music playback with simple hand gestures
- **Face Detection**: Automatically pauses when no face is detected
- **Web Interface**: Clean, modern web UI to monitor playback
- **Playlist Management**: View and manage your music playlist
- **Favorites**: Mark favorite songs with a pinch gesture

## Gesture Controls

| Gesture | Action |
|---------|--------|
| ✊ Fist (0 fingers) | Play music |
| ✋ Open palm (4+ fingers) | Pause music |
| ☝️ One finger up | Control volume (hand height = volume level) |
| 👈👉 Swipe left/right | Previous/Next track |
| 🤏 Pinch (thumb + index) | Toggle favorite |

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `music` folder in the project directory and add your music files (.mp3, .wav, or .ogg)

## Usage

### Option 1: Web Interface (Recommended)

Run the Flask web application:
```bash
python app.py
```

Then open your browser and go to:
```
http://localhost:5000
```

The web interface shows:
- Live camera feed with gesture recognition
- Current track information
- Playlist with favorites marked
- Volume display
- Gesture guide
- Keyboard shortcuts

### Option 2: Standalone Application

Run the original standalone version:
```bash
python music.py
```

Press 'q' to quit the application.

## Keyboard Shortcuts

- **Q**: Quit application
- **N**: Next track
- **P**: Previous track

## Requirements

- Python 3.7+
- Webcam
- Music files in the `music` folder

## Project Structure

```
masooma music project/
├── app.py                  # Flask web application
├── music.py                # Standalone version
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── music/                 # Music files folder
├── templates/
│   └── index.html         # Web interface HTML
└── static/
    ├── style.css          # Styling
    └── script.js          # JavaScript for updates
```

## Troubleshooting

- **No music files found**: Make sure you have a `music` folder with .mp3, .wav, or .ogg files
- **Camera not working**: Check if your webcam is connected and not being used by another application
- **Gestures not detected**: Make sure you have good lighting and your hand is visible to the camera
- **Port 5000 already in use**: Change the port in `app.py` (last line)
