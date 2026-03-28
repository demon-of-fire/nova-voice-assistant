"""Sound effects player using pygame.mixer.

Loads WAV files from the 'sounds' directory. If WAV not found,
falls back to MP3. Supports both bundled (PyInstaller) and dev mode.
"""

import os
import sys
import threading
import time

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# Find sounds directory
if getattr(sys, "frozen", False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SOUNDS_DIR = os.path.join(_base, "sounds")

# Preload
_sounds = {}
_NAMES = ["activate", "deactivate", "listening", "thinking", "mute", "unmute", "error"]

for name in _NAMES:
    # Prefer WAV, fall back to MP3
    for ext in (".wav", ".mp3"):
        path = os.path.join(SOUNDS_DIR, f"{name}{ext}")
        if os.path.exists(path):
            try:
                _sounds[name] = pygame.mixer.Sound(path)
                break
            except Exception:
                pass

_channel = pygame.mixer.Channel(0)
_bg_channel = pygame.mixer.Channel(1)


def play(name):
    """Play a sound (non-blocking)."""
    sound = _sounds.get(name)
    if not sound:
        return

    def _do():
        try:
            if name == "listening":
                _bg_channel.play(sound)
            else:
                _channel.play(sound)
        except Exception:
            pass

    threading.Thread(target=_do, daemon=True).start()


def play_sync(name):
    """Play a sound and block until done."""
    sound = _sounds.get(name)
    if not sound:
        return
    try:
        _channel.play(sound)
        while _channel.get_busy():
            time.sleep(0.05)
    except Exception:
        pass


def stop_ambient():
    """Stop the listening ambient sound."""
    try:
        _bg_channel.stop()
    except Exception:
        pass
