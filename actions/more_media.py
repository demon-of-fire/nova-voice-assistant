"""Media actions: now playing info, per-app volume, region screenshot, color picker, magnifier."""

import subprocess
import ctypes
import os
import re
import tempfile
from actions.confirmation import ask_confirmation


def get_now_playing():
    """Get info about currently playing media using PowerShell."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Add-Type -AssemblyName System.Runtime.WindowsRuntime; "
             "$null = [Windows.Media.MediaControl,Windows.Media,ContentType=WindowsRuntime]; "
             "$media = [Windows.Media.MediaControl]::Get(); "
             "Write-Output \"$($media.Title)|$($media.Artist)|$($media.PlaybackStatus)\""],
            capture_output=True, text=True, timeout=10,
        )
        output = result.stdout.strip()
        if output and "|" in output:
            parts = output.split("|")
            title = parts[0].strip() if parts[0].strip() else "Unknown"
            artist = parts[1].strip() if len(parts) > 1 and parts[1].strip() else "Unknown"
            status = parts[2].strip() if len(parts) > 2 else "Unknown"
            return f"Now playing: {title} by {artist} ({status.lower()})."
        return "No media is currently playing."
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-Process | Where-Object { $_.MainWindowTitle -ne '' } | "
             "Select-Object -First 5 MainWindowTitle, ProcessName | "
             "Format-Table -AutoSize | Out-String -Width 4096"],
            capture_output=True, text=True, timeout=10,
        )
        output = result.stdout.strip()
        if output:
            return f"No media detected. Active windows: {output[:200]}"
        return "No media is currently playing."
    except Exception as e:
        return f"Couldn't get media info: {e}"


def set_app_volume(app_name, level):
    """Set volume level for a specific application using PowerShell."""
    level = max(0, min(100, int(level)))
    try:
        ps_cmd = (
            f"$app = Get-Process | Where-Object {{ $_.ProcessName -like '*{app_name}*' }} | "
            f"Select-Object -First 1; "
            f"if ($app -and $app.Id) {{ "
            f"  try {{ "
            f"    $sessions = [AudioSwitcher.Audio.Session]::GetAudioSessions($app.Id); "
            f"    if ($sessions -and $sessions.Count -gt 0) {{ "
            f"      $sessions.Volume = {level} / 100.0; "
            f"      Write-Output 'Set volume for {app_name} to {level}%'; "
            f"    }} "
            f"  }} catch {{ "
            f"    Write-Output 'AudioSwitcher not available'; "
            f"  }} "
            f"}} else {{ Write-Output 'Could not find process {app_name}' }}"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=10,
        )
        output = result.stdout.strip()
        if output and "AudioSwitcher not available" not in output:
            return output
    except Exception:
        pass

    return f"Couldn't set per-app volume for '{app_name}'. The AudioSwitcher module is not installed. Try asking me to set the system volume instead."


def take_region_screenshot(x1, y1, x2, y2):
    """Take a screenshot of a specific screen region."""
    try:
        from actions.screen import take_screenshot
        from PIL import Image
        img_data = take_screenshot()
        temp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        temp_path = temp.name
        temp.close()

        with open(temp_path, "wb") as f:
            f.write(img_data)

        img = Image.open(temp_path)
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        left = min(x1, x2)
        upper = min(y1, y2)
        right = max(x1, x2)
        lower = max(y1, y2)
        cropped = img.crop((left, upper, right, lower))

        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        filename = f"region_{os.urandom(4).hex()}.png"
        out_path = os.path.join(desktop, filename)
        cropped.save(out_path)
        os.unlink(temp_path)
        return f"Region screenshot saved to Desktop as {filename}."
    except ImportError:
        return "PIL/Pillow is required for region screenshots."
    except Exception as e:
        return f"Couldn't capture region: {e}"


def pick_color():
    """Open a color picker dialog using PowerShell."""
    try:
        ps_cmd = (
            'Add-Type -AssemblyName System.Drawing; '
            'Add-Type -AssemblyName System.Windows.Forms; '
            '$colorDialog = New-Object System.Windows.Forms.ColorDialog; '
            '$result = $colorDialog.ShowDialog(); '
            'if ($result -eq "OK") { '
            '  $color = $colorDialog.Color; '
            '  Write-Output "$($color.R),$($color.G),$($color.B),#$($color.R.ToString(\'X2\') + $color.G.ToString(\'X2\') + $color.B.ToString(\'X2\'))" '
            '} else { Write-Output "cancelled" }'
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=30,
        )
        output = result.stdout.strip()
        if output and "," in output:
            parts = output.split(",")
            if len(parts) >= 4:
                r, g, b, hex_color = parts[0], parts[1], parts[2], parts[3]
                return f"Selected color: RGB({r}, {g}, {b}), hex {hex_color}."
        return "No color was selected."
    except subprocess.TimeoutExpired:
        return "Color picker timed out."
    except Exception as e:
        return f"Couldn't open color picker: {e}"


def toggle_magnifier(state=""):
    """Toggle Windows Magnifier on/off."""
    try:
        shell = ctypes.windll.user32
        if state.lower() in ("on", "enable", "start"):
            # Launch Magnifier
            subprocess.Popen(["magnify.exe"], close_fds=True)
            return "Magnifier started."
        elif state.lower() in ("off", "disable", "stop"):
            # Kill Magnifier
            subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "Stop-Process -Name 'Magnify' -Force -ErrorAction SilentlyContinue"],
                capture_output=True, text=True, timeout=5,
            )
            return "Magnifier stopped."
        else:
            # Toggle: check if running
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "Get-Process -Name 'Magnify' -ErrorAction SilentlyContinue"],
                capture_output=True, text=True, timeout=5,
            )
            if result.stdout.strip():
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command",
                     "Stop-Process -Name 'Magnify' -Force -ErrorAction SilentlyContinue"],
                    capture_output=True, text=True, timeout=5,
                )
                return "Magnifier stopped."
            else:
                subprocess.Popen(["magnify.exe"], close_fds=True)
                return "Magnifier started."
    except Exception as e:
        return f"Couldn't toggle magnifier: {e}"


def set_magnifier_zoom(level=200):
    """Set Magnifier zoom level (100-1000%). Requires Magnifier to be running."""
    try:
        level = max(100, min(1000, int(level)))
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW(None, "Magnifier")
        if not hwnd:
            return "Magnifier is not running. Start it first."

        # Use PowerShell to set zoom via UI automation
        subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"[System.Windows.Forms.SendKeys]::SendWait('%({level})')"],
            capture_output=True, text=True, timeout=5,
        )
        return f"Magnifier zoom set to {level}%."
    except Exception as e:
        return f"Couldn't set magnifier zoom: {e}"
