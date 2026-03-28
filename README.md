# Nova Voice Assistant

A Windows voice assistant powered by Google Gemini with full PC control and NVDA screen reader accessibility.

## Features

- **Voice Control** — Talk to Nova to control your PC, search the web, manage files, and more
- **Natural Language** — Just say what you want: "close chrome", "play next song", "what's the score of the game"
- **40+ Actions** — Open/close apps, media controls, volume, brightness, file management, shell commands, web search, and more
- **Follow-Up Mode** — Keep talking back and forth without re-triggering the wake word
- **Type Input** — Ctrl+Shift+Y to type a message instead of speaking
- **Quick Search** — Answers questions, scores, weather by searching in the background (no browser opens)
- **NVDA Accessible** — Every UI element is screen reader compatible. Built for blind and low-vision users
- **Dark/Light Mode** — Fully themed UI with toggle in settings
- **Neural TTS** — Natural-sounding Microsoft Edge neural voices (not robotic SAPI5)
- **Floating Orb** — Minimizes to a small orb like Siri. Click to start listening. Customizable position
- **Ollama Support** — Use local AI models for free, private conversations
- **System Tray** — Runs quietly in the background

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| Ctrl+Shift+T | Start/stop talking |
| Ctrl+Shift+M | Mute/unmute |
| Ctrl+Shift+Y | Type a message |
| Ctrl+Shift+Q | Quit Nova |
| F2 | Talk (in Nova window) |
| F3 | Mute (in Nova window) |
| F4 | Settings (in Nova window) |
| Escape | Minimize to tray |

## Wake Word

Say **"Hey Nova"** to activate hands-free.

## Setup

### Requirements
- Windows 10/11
- Python 3.10+
- A Gemini API key (free at [aistudio.google.com/apikey](https://aistudio.google.com/apikey))
- Microphone

### Install

```bash
# Clone the repo
git clone https://github.com/demon-of-fire/nova-voice-assistant.git
cd nova-voice-assistant

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

On first launch, Nova will ask for your Gemini API key.

### Build Standalone EXE

```bash
python build.py
```

Creates `Nova.exe` in the project folder — no Python needed to run it.

## Settings

Open Settings (F4) to configure:
- **AI Model** — Gemini 2.5 Flash (default), 2.5 Pro, 3.0 Preview, or Ollama models
- **Permissions** — Toggle what Nova can do (typing, app control, shell commands, etc.)
- **Voice** — 15 neural voices to choose from
- **Speech Speed** — Adjustable WPM
- **STT Engine** — Google (online), Sphinx (offline), or Whisper (offline)
- **Follow-Up Mode** — Keep conversation going after each response
- **Confirm Actions** — Ask before dangerous operations
- **Dark/Light Mode**
- **Orb Position** — Bottom-right, bottom-left, top-right, top-left

## Architecture

```
main.py              — Entry point, API key dialog
config.py            — All constants and system prompt
assistant/
  core.py            — Orchestrator (listen -> think -> speak loop)
  brain.py           — Gemini + Ollama AI routing
  listener.py        — Speech recognition + wake word detection
  speaker.py         — Edge TTS neural voices + pyttsx3 fallback
  ui.py              — Tkinter UI (NVDA accessible)
  settings.py        — Persistent settings with API key obfuscation
  accessibility.py   — NVDA announcement helpers
  tray.py            — System tray icon
  sounds.py          — Sound effects
actions/
  apps.py            — Launch/close apps
  windows.py         — Window management
  input_control.py   — Keyboard/mouse control
  system.py          — Volume, brightness, power, media controls
  web.py             — Web search, quick search, URLs
  files.py           — File/folder operations
  filesystem.py      — Read/write/edit files
  shell.py           — Shell commands, winget
  process.py         — Process management
  network.py         — Network info, WiFi, ping
  code.py            — Python execution
  confirmation.py    — Confirmation dialogs
```

## License

MIT
