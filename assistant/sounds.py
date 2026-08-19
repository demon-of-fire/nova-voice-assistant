"""Tiny Windows sound-effect player using the standard library."""

import os
import sys
import threading
import time
import winsound


if getattr(sys, "frozen", False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SOUNDS_DIR = os.path.join(_base, "sounds")
_ambient = None


def _path(name):
    path = os.path.join(SOUNDS_DIR, f"{name}.wav")
    return path if os.path.exists(path) else None


def play(name):
    """Play a sound without blocking."""
    path = _path(name)
    if not path:
        return

    def _do():
        flags = winsound.SND_FILENAME | winsound.SND_ASYNC
        if name == "listening":
            flags |= winsound.SND_LOOP
        try:
            winsound.PlaySound(path, flags)
        except Exception:
            pass

    threading.Thread(target=_do, daemon=True).start()


def play_sync(name):
    """Play a sound and wait briefly for it to finish."""
    path = _path(name)
    if not path:
        return
    try:
        winsound.PlaySound(path, winsound.SND_FILENAME)
    except Exception:
        time.sleep(0.15)


def stop_ambient():
    """Stop any async/looped sound."""
    try:
        winsound.PlaySound(None, winsound.SND_PURGE)
    except Exception:
        pass
