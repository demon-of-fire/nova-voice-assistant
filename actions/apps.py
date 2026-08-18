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
    # Never use shell=True — reject anything that isn't a plain command name
    if any(c in app_name for c in "|&;<>`$\"'()"):
        return f"Couldn't find an app called '{app_name}'. It might not be installed."
    try:
        subprocess.Popen([app_name], shell=False)
        return f"Opened {app_name}."
    except Exception:
        pass

    return f"Couldn't find an app called '{app_name}'. It might not be installed."


def close_app(app_name):
    """Kill a running application by process name — protects Nova and system processes."""
    search = app_name.lower().strip()
    if len(search) < 3:
        return "That app name is too short to be safe. Please be more specific."

    # Never kill these process names — they're system/Nova infrastructure
    # msedgewebview2 is shared by many apps (Nova, Spotify, Teams, etc.)
    # Killing it can crash ANY app using webview2, including Nova.
    protected_names = {
        "msedgewebview2.exe", "nova.exe", "python.exe", "pythonw.exe",
        "explorer.exe", "svchost.exe", "csrss.exe", "dwm.exe",
        "system", "system idle process", "lsass.exe", "services.exe",
        "conhost.exe", "bash.exe", "cmd.exe", "powershell.exe",
        "regedit.exe", "taskmgr.exe", "winlogon.exe", "wininit.exe",
    }

    killed = []
    main_procs = []

    def _stem(pname):
        """Strip common vendor prefixes so 'word' matches WINWORD, not WordPad."""
        base = pname[:-4] if pname.endswith(".exe") else pname
        for pre in ("win", "ms", "wps"):
            if base.startswith(pre) and len(base) > len(pre) + 2:
                return base[len(pre):]
        return base

    candidates = []
    for proc in psutil.process_iter(["name", "pid", "exe"]):
        try:
            pname = proc.info["name"].lower()
            pid = proc.info["pid"]
            if pname in protected_names:
                continue
            candidates.append((pid, proc.info["name"]))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Pass 1: exact name or stem-prefix match (WINWORD for 'word')
    for pid, name in candidates:
        pname = name.lower()
        if pname == search or _stem(pname).startswith(search):
            main_procs.append((pid, name))
    # Pass 2: only if nothing matched — substring (e.g. 'chrome' → msedge no)
    if not main_procs:
        for pid, name in candidates:
            if search in name.lower():
                main_procs.append((pid, name))

    if not main_procs:
        return f"Couldn't find '{app_name}' running."

    for pid, name in main_procs:
        try:
            p = psutil.Process(pid)
            # Terminate (graceful) first, then kill if it doesn't stop
            p.terminate()
            killed.append(name)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Give processes a moment to close gracefully
    import time
    time.sleep(0.5)

    # Force kill any that are still alive
    for pid, name in main_procs:
        try:
            p = psutil.Process(pid)
            if p.is_running():
                p.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if killed:
        return f"Closed {', '.join(set(killed))}."
    return f"Couldn't find '{app_name}' running."


def refresh_app_cache():
    """Manually refresh the Start Menu app cache."""
    _scan_start_menu()
    return f"Refreshed. Found {len(_APP_CACHE)} apps."
