"""Persistent settings stored in a JSON file in the user's home directory.

API keys are obfuscated in the settings file so they don't appear as
plain text if someone opens the JSON. This is NOT encryption — it's
base64 encoding to prevent casual shoulder-surfing and accidental leaks
in screenshots. For real security, use environment variables.
"""

import json
import os
import base64

SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".nova_settings.json")

_OBFUSCATED_KEYS = {"gemini_api_key"}

def _obfuscate(value):
    if not value:
        return ""
    return "b64:" + base64.b64encode(value.encode("utf-8")).decode("ascii")

def _deobfuscate(value):
    if not value or not isinstance(value, str):
        return value
    if value.startswith("b64:"):
        try:
            return base64.b64decode(value[4:]).decode("utf-8")
        except Exception:
            return value
    return value

DEFAULTS = {
    "gemini_api_key": "",
    "allow_typing": True,          # let Nova type text into documents
    "allow_keyboard_control": True, # let Nova press hotkeys
    "allow_app_launch": True,       # let Nova open apps
    "allow_system_control": True,   # shutdown/restart/lock
    "allow_web_search": True,       # open browser / search
    "allow_file_access": True,      # find files / open folders
    "allow_shell_commands": False,  # run cmd/powershell commands (dangerous)
    "allow_file_write": True,       # write/edit/append to files
    "allow_file_delete": False,     # delete files and folders (dangerous)
    "allow_install_apps": False,    # install/uninstall apps via winget (dangerous)
    "allow_process_control": True,  # list/kill processes
    "allow_network": True,          # network info, wifi scan, ping
    "allow_code_execution": False,  # run arbitrary Python code (dangerous)
    "allow_screen_control": False,  # screen sharing + mouse control
    "gemini_model": "gemini-2.5-flash",  # which Gemini model to use
    "tts_rate": 160,
    "tts_volume": 1.0,
    "tts_voice": "",                # Windows SAPI voice token id; blank uses default
    "stt_engine": "google",       # "google" (online), "sphinx" (offline/light), "whisper" (offline/accurate)
    "wake_word_enabled": False,
    "start_minimized": False,
    "confirm_actions": True,      # show "are you sure?" before dangerous actions
    "follow_up_mode": True,       # keep listening after responding for follow-ups
    "dark_mode": True,            # dark mode UI (default on)
    "orb_position": "bottom-right",  # floating orb: bottom-right, bottom-left, top-right, top-left
}


# Models that are known dead / deprecated — auto-migrate to working ones
_DEAD_MODELS = {
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-2.5-pro-preview-05-06",
    "gemini-2.5-flash-preview-05-20",
}
_FALLBACK_MODEL = "gemini-2.5-flash"


class Settings:
    def __init__(self):
        self._data = dict(DEFAULTS)
        self._load()

    def _load(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f:
                    saved = json.load(f)
                # Deobfuscate sensitive keys on load
                for key in _OBFUSCATED_KEYS:
                    if key in saved:
                        saved[key] = _deobfuscate(saved[key])
                self._data.update(saved)
            except (json.JSONDecodeError, IOError):
                pass

        # Auto-migrate dead Gemini models
        model = self._data.get("gemini_model", "")
        if model in _DEAD_MODELS or "preview" in model:
            self._data["gemini_model"] = _FALLBACK_MODEL
            self._save()

    def _save(self):
        try:
            # Copy data and obfuscate sensitive keys for storage
            to_save = dict(self._data)
            for key in _OBFUSCATED_KEYS:
                if key in to_save and to_save[key]:
                    to_save[key] = _obfuscate(to_save[key])
            with open(SETTINGS_FILE, "w") as f:
                json.dump(to_save, f, indent=2)
        except IOError:
            pass

    def get(self, key):
        return self._data.get(key, DEFAULTS.get(key))

    def set(self, key, value):
        self._data[key] = value
        self._save()

    def toggle(self, key):
        """Toggle a boolean setting. Returns the new value."""
        current = self._data.get(key, DEFAULTS.get(key, False))
        self._data[key] = not current
        self._save()
        return self._data[key]

    def all(self):
        return dict(self._data)
