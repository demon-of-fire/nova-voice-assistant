# Changelog

## v1.0.0 — 2026-03-28

Initial release.

### Features
- Voice-controlled Windows PC assistant powered by Google Gemini
- 40+ tool actions: apps, windows, volume, brightness, media, files, shell, web, processes, network, code execution
- Wake word detection ("Hey Nova") with fuzzy matching
- Follow-up conversation mode — keep talking without re-triggering wake word
- Type-to-chat input (Ctrl+Shift+Y)
- Quick web search — answers questions by voice without opening a browser
- Media controls — play/pause, next, previous, stop (works with Spotify, YouTube, VLC, etc.)
- Quit assistant by voice command
- Neural TTS voices via Microsoft Edge (15 natural-sounding voices)
- pyttsx3 SAPI5 fallback for offline use
- Full NVDA screen reader accessibility — all UI uses plain tk.Button widgets
- Dark mode (default) and light mode with toggle
- Floating orb when minimized (like Siri) — click to start listening, customizable position
- System tray integration
- Ollama support for local/free AI conversations
- Gemini model selection (2.5 Flash, 2.5 Pro, 2.5 Flash Lite, 3.0 previews)
- Ollama model picker with popular models + manual entry
- API key obfuscation (base64) in settings file
- Confirmation dialogs before dangerous actions
- Configurable permissions for all action categories
- Global keyboard shortcuts: Ctrl+Shift+T (talk), Ctrl+Shift+M (mute), Ctrl+Shift+Y (type), Ctrl+Shift+Q (quit)
- Auto-migration of deprecated Gemini models
- Error logging to ~/nova_error.log
- PyInstaller build script for standalone .exe
