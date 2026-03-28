"""Keyboard and mouse input control."""

import keyboard as kb
import pyautogui
import time


def type_text(text):
    """Type text as if the user typed it."""
    time.sleep(0.2)  # small delay to let focus settle
    kb.write(text, delay=0.02)
    preview = text[:50] + "..." if len(text) > 50 else text
    return f'Typed "{preview}".'


def press_keys(keys):
    """Press a keyboard shortcut like 'ctrl+c', 'alt+tab', 'win+d'."""
    # Normalize common spoken forms
    mapping = {
        "control": "ctrl",
        "windows": "win",
        "escape": "esc",
        "delete": "del",
        "return": "enter",
    }
    parts = keys.lower().replace(" ", "").split("+")
    normalized = "+".join(mapping.get(p, p) for p in parts)

    try:
        kb.send(normalized)
        return f"Pressed {normalized}."
    except Exception as e:
        return f"Couldn't press {keys}: {e}"
