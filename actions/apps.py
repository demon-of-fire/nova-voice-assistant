"""App launcher — scans Start Menu to find and launch any installed app."""

import os
import glob
import subprocess
import psutil
from difflib import SequenceMatcher

_APP_CACHE = {}


def _scan_start_menu():
    """Build index of all Start Menu shortcuts."""
    global _APP_CACHE
    _APP_CACHE = {}
    dirs = [
        r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
        os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
    ]
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for lnk in glob.glob(os.path.join(d, "**", "*.lnk"), recursive=True):
            name = os.path.splitext(os.path.basename(lnk))[0].lower()
            # Skip uninstallers and update entries
            if any(skip in name for skip in ("uninstall", "update", "readme", "help", "manual")):
                continue
            _APP_CACHE[name] = lnk


def _find_app(app_name):
    """Find the best matching .lnk file for an app name."""
    if not _APP_CACHE:
        _scan_start_menu()

    key = app_name.lower().strip()

    # Exact match
    if key in _APP_CACHE:
        return _APP_CACHE[key]

    # Substring match (prefer shorter names — more likely to be the main app)
    substring_matches = []
    for name, path in _APP_CACHE.items():
        if key in name or name in key:
            substring_matches.append((name, path))
    if substring_matches:
        substring_matches.sort(key=lambda x: len(x[0]))
        return substring_matches[0][1]

    # Fuzzy match
    best_path, best_score = None, 0
    for name, path in _APP_CACHE.items():
        score = SequenceMatcher(None, key, name).ratio()
        if score > best_score:
            best_path, best_score = path, score
    if best_score > 0.55:
        return best_path

    return None


def launch_app(app_name):
    """Launch an application by name."""
    lnk = _find_app(app_name)
    if lnk:
        try:
            os.startfile(lnk)
            display = os.path.splitext(os.path.basename(lnk))[0]
            return f"Opened {display}."
        except Exception as e:
            return f"Found {app_name} but couldn't open it: {e}"

    # Fallback: try running it directly (for PATH-accessible commands like 'code')
    try:
        subprocess.Popen(app_name, shell=True)
        return f"Opened {app_name}."
    except Exception:
        pass

    return f"Couldn't find an app called '{app_name}'. It might not be installed."


def close_app(app_name):
    """Kill a running application by process name."""
    search = app_name.lower().strip()
    killed = []
    for proc in psutil.process_iter(["name", "pid"]):
        try:
            pname = proc.info["name"].lower()
            if search in pname:
                proc.kill()
                killed.append(proc.info["name"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if killed:
        return f"Closed {', '.join(set(killed))}."
    return f"Couldn't find '{app_name}' running."


def refresh_app_cache():
    """Manually refresh the Start Menu app cache."""
    _scan_start_menu()
    return f"Refreshed. Found {len(_APP_CACHE)} apps."
