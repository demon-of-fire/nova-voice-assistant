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
- **Native TTS** — Uses installed Windows voices through SAPI, with no extra speech player
- **Floating Orb** — Minimizes to a small orb like Siri. Click to start listening. Customizable position
- **Windows Integration** — Desktop shortcut, optional start-with-Windows, tray behavior, global hotkeys
- **System Tray** — Runs quietly in the background

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| Ctrl+Shift+T | Start/stop talking |
| Ctrl+Shift+M | Mute/unmute |
| Ctrl+Shift+Y | Type a message |
| Ctrl+Shift+S | Toggle screen sharing |
| Ctrl+Shift+, | Open settings |
| Ctrl+Shift+Q | Quit Nova |
| Escape | Minimize to tray |

## Wake Word

Say **"Hey Nova"** to activate hands-free.

## Setup

### Requirements
- Windows 10/11
- A Gemini API key (free at [aistudio.google.com/apikey](https://aistudio.google.com/apikey))
- Microphone

### Install

Download `Nova Setup.exe` from the GitHub release and open it.

On first run, Nova copies the bundled app to `%LOCALAPPDATA%\Nova\Nova.exe`,
creates Desktop and Start Menu shortcuts, registers a Startup shortcut, and
opens from the installed copy. The Startup shortcut launches Nova in background
mode so Ctrl+Shift+T and Ctrl+Shift+Y are registered automatically when Windows
starts, even when the main window is hidden. Nova will then ask for your Gemini
API key.

Nova also registers per-user shell integration: `nova://` links for launchers
and scripts, a Win+R `Nova.exe` app path alias, and a Settings button that can
repair all native integration after an update or moved build. The shared
integration API lives in `assistant/platform_integration.py`, with Windows in
`assistant/windows_integration.py` and Linux-ready `.desktop`/autostart hooks
stubbed for future ports.

For development from source:

```bash
git clone https://github.com/demon-of-fire/nova-voice-assistant.git
cd nova-voice-assistant
pip install -r requirements.txt
python main.py
```

### Build Standalone EXE

```bash
python build.py
```

Creates `Nova Setup.exe` in the project folder. Upload that file for releases;
users only need to open it once.

## Settings

Open Settings from Nova or press Ctrl+Shift+, to configure:
- **Windows** — Create/repair desktop and Start Menu shortcuts, start with Windows, start minimized, wake word
- **AI Model** — Gemini 2.5 Flash (default), 2.5 Pro, or Flash Lite
- **Permissions** — Toggle what Nova can do (typing, app control, shell commands, etc.)
- **Voice** — Installed Windows voices to choose from
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
  brain.py           — Gemini function-calling brain
  listener.py        — Speech recognition + wake word detection
  speaker.py         — Native Windows SAPI speech
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
