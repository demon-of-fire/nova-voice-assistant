"""System controls: volume, brightness, power, info."""

import os
import datetime
import platform
import ctypes
import psutil


def get_time():
    return datetime.datetime.now().strftime("It's %I:%M %p.")


def get_date():
    return datetime.datetime.now().strftime("Today is %A, %B %d, %Y.")


def set_volume(level):
    """Set system volume (0-100)."""
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        scalar = max(0.0, min(1.0, int(level) / 100.0))
        volume.SetMasterVolumeLevelScalar(scalar, None)
        return f"Volume set to {level}%."
    except Exception as e:
        return f"Couldn't set volume: {e}"


def get_volume():
    """Get current system volume level."""
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        level = round(volume.GetMasterVolumeLevelScalar() * 100)
        return f"Volume is at {level}%."
    except Exception as e:
        return f"Couldn't read volume: {e}"


def set_brightness(level):
    """Set screen brightness (0-100)."""
    try:
        import screen_brightness_control as sbc
        sbc.set_brightness(int(level))
        return f"Brightness set to {level}%."
    except Exception as e:
        return f"Couldn't set brightness: {e}"


def get_system_info():
    """Return CPU, RAM, battery, OS info."""
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    info = f"CPU is at {cpu}%. "
    info += f"Memory: {mem.percent}% used of {round(mem.total / (1024**3), 1)} GB. "

    battery = psutil.sensors_battery()
    if battery:
        info += f"Battery at {round(battery.percent)}%"
        info += " and charging." if battery.power_plugged else "."
    else:
        info += "No battery detected (desktop)."

    info += f" Windows {platform.version()}."
    return info


def shutdown_pc(delay_seconds=60):
    os.system(f"shutdown /s /t {int(delay_seconds)}")
    return f"Shutting down in {delay_seconds} seconds. Say 'cancel shutdown' to abort."


def restart_pc(delay_seconds=60):
    os.system(f"shutdown /r /t {int(delay_seconds)}")
    return f"Restarting in {delay_seconds} seconds."


def cancel_shutdown():
    os.system("shutdown /a")
    return "Shutdown cancelled."


def lock_pc():
    ctypes.windll.user32.LockWorkStation()
    return "Locking your PC."


# ── Media controls ─────────────────────────────────────────────────────────

def media_play_pause():
    """Press the system media play/pause key."""
    import keyboard as kb
    kb.send("play/pause media")
    return "Toggled play/pause."


def media_next():
    """Press the system media next track key."""
    import keyboard as kb
    kb.send("next track")
    return "Skipped to next track."


def media_previous():
    """Press the system media previous track key."""
    import keyboard as kb
    kb.send("previous track")
    return "Went back to previous track."


def media_stop():
    """Press the system media stop key."""
    import keyboard as kb
    kb.send("stop media")
    return "Stopped media playback."


# ── Assistant self-control ─────────────────────────────────────────────────

def quit_assistant():
    """Quit the Nova assistant. The brain will speak the response first, then this runs."""
    import threading
    # Delay exit slightly so the TTS response can play
    threading.Timer(2.0, lambda: os._exit(0)).start()
    return "Goodbye! Shutting down Nova."
