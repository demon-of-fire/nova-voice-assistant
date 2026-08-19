"""Automation actions: pomodoro, caffeine, window layouts, macros, battery."""

import os
import json
import subprocess
import threading
import datetime
import ctypes
import time


AUTOMATION_DIR = os.path.join(os.path.expanduser("~"), ".nova_automation")
_keep_awake_thread = None
_keep_awake_running = False


def _ensure_dir():
    os.makedirs(AUTOMATION_DIR, exist_ok=True)


def _path(name):
    _ensure_dir()
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
    return os.path.join(AUTOMATION_DIR, f"{safe}.json")


def start_pomodoro(minutes=25):
    """Start a Pomodoro timer. After the timer, notifies and suggests a break."""
    minutes = max(1, min(180, int(minutes)))
    seconds = minutes * 60

    def _pomodoro_loop():
        import winsound
        import time as _time
        _time.sleep(seconds)
        for _ in range(3):
            try:
                winsound.PlaySound("SystemHand", winsound.SND_ALIAS | winsound.SND_ASYNC)
            except Exception:
                pass
            _time.sleep(1.5)
        subprocess.Popen(
            ["powershell", "-NoProfile", "-Command",
             f"[System.Windows.MessageBox]::Show('Pomodoro {minutes}min is done! Time for a 5min break.', 'Nova Pomodoro')"],
            close_fds=True,
        )

    threading.Thread(target=_pomodoro_loop, daemon=True).start()
    return f"Pomodoro timer set for {minutes} minutes. I'll let you know when it's done."


def keep_awake(minutes=60):
    """Prevent the PC from sleeping for N minutes using PowerShell."""
    global _keep_awake_running, _keep_awake_thread

    minutes = max(1, min(480, int(minutes)))

    if _keep_awake_running:
        return "Already keeping the PC awake. Say 'stop keeping awake' to disable."

    _keep_awake_running = True
    ps_command = (
        f"$end = (Get-Date).AddMinutes({minutes}); "
        f"while ((Get-Date) -lt $end) {{ "
        f"  [System.Windows.Forms.Application]::DoEvents(); "
        f"  Start-Sleep -Seconds 30; "
        f"}}"
    )

    def _caffeine():
        global _keep_awake_running
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 f"$null = Add-Type -AssemblyName System.Windows.Forms; "
                 f"while ($true) {{ "
                 f"  [System.Windows.Forms.Application]::DoEvents(); "
                 f"  Start-Sleep -Seconds 20; "
                 f"}}"],
                timeout=minutes * 60,
            )
        except subprocess.TimeoutExpired:
            pass
        except Exception:
            pass
        _keep_awake_running = False

    _keep_awake_thread = threading.Thread(target=_caffeine, daemon=True)
    _keep_awake_thread.start()

    # Also use SetThreadExecutionState to prevent sleep
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)

    return f"Keeping PC awake for {minutes} minutes."


def stop_keeping_awake():
    """Allow the PC to sleep normally again."""
    global _keep_awake_running
    _keep_awake_running = False
    ES_CONTINUOUS = 0x80000000
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
    return "PC can sleep normally now."


def save_window_layout(name):
    """Save the current window layout (positions/sizes) to a named profile."""
    try:
        import psutil
        import ctypes.wintypes as wt

        user32 = ctypes.windll.user32
        layouts = []

        @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        def callback(hwnd, _):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buf, length + 1)
                    title = buf.value
                    if title:
                        rect = wt.RECT()
                        user32.GetWindowRect(hwnd, ctypes.byref(rect))
                        layouts.append({
                            "title": title,
                            "left": rect.left, "top": rect.top,
                            "right": rect.right, "bottom": rect.bottom,
                        })
            return True

        user32.EnumWindows(callback, 0)
        data = {"saved": datetime.datetime.now().isoformat(), "windows": layouts}
        with open(_path(f"layout_{name}"), "w") as f:
            json.dump(data, f, indent=2)
        return f"Saved layout '{name}' with {len(layouts)} windows."
    except Exception as e:
        return f"Couldn't save layout: {e}"


def restore_window_layout(name):
    """Restore a saved window layout by name."""
    try:
        path = _path(f"layout_{name}")
        if not os.path.isfile(path):
            return f"Layout '{name}' not found."
        with open(path) as f:
            data = json.load(f)
        windows = data.get("windows", [])

        restored = 0
        user32 = ctypes.windll.user32
        for win in windows:
            hwnd = user32.FindWindowW(None, win["title"])
            if hwnd:
                user32.SetWindowPos(
                    hwnd, None,
                    win["left"], win["top"],
                    win["right"] - win["left"],
                    win["bottom"] - win["top"],
                    0x0004,  # SWP_NOZORDER
                )
                restored += 1
        return f"Restored layout '{name}' ({restored}/{len(windows)} windows)."
    except Exception as e:
        return f"Couldn't restore layout: {e}"


def list_layouts():
    """List saved window layouts."""
    _ensure_dir()
    try:
        layouts = [f[:-5].replace("layout_", "", 1) for f in os.listdir(AUTOMATION_DIR)
                   if f.startswith("layout_") and f.endswith(".json")]
        if not layouts:
            return "No saved layouts."
        return "Saved layouts: " + ", ".join(layouts)
    except Exception as e:
        return f"Error listing layouts: {e}"


def get_battery_report():
    """Generate and read a Windows battery report summary."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-WmiObject Win32_Battery | Select-Object EstimatedChargeRemaining, BatteryStatus, EstimatedRunTime"],
            capture_output=True, text=True, timeout=10,
        )
        output = result.stdout.strip()
        if not output:
            return "No battery detected on this system."

        lines = [l.strip() for l in output.splitlines() if l.strip()]
        for line in lines:
            if "EstimatedChargeRemaining" in line:
                continue
            if "--" in line:
                continue
            parts = line.split()
            if len(parts) >= 3:
                pct = parts[0]
                status_code = parts[1]
                runtime = parts[2]
                status_map = {"1": "discharging", "2": "on AC", "3": "charged",
                              "4": "low", "5": "critical", "6": "charging"}
                status = status_map.get(status_code, "unknown")
                runtime_str = f"{runtime} min remaining" if runtime != "0" else ""
                return f"Battery at {pct}%, {status}. {runtime_str}.".strip()

        return output[:300]
    except Exception as e:
        return f"Couldn't get battery info: {e}"
