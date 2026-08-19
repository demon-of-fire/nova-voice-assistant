"""System tools: power plans, storage, cleanup, startup management, restore points."""

import os
import subprocess
import ctypes
import json


def set_power_plan(plan):
    """Change the Windows power plan: balanced, power saver, high performance."""
    plans = {
        "balanced": "381b4222-f694-41f0-9685-ff5bb260df2e",
        "power saver": "a1841308-3541-4fab-bc81-f71556f20b4a",
        "power_saver": "a1841308-3541-4fab-bc81-f71556f20b4a",
        "powersaver": "a1841308-3541-4fab-bc81-f71556f20b4a",
        "high performance": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
        "high_performance": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
        "highperformance": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
        "ultimate performance": "e9a42b02-d5df-448d-aa00-03f14749eb61",
        "ultimate_performance": "e9a42b02-d5df-448d-aa00-03f14749eb61",
    }
    guid = plans.get(plan.lower().strip())
    if not guid:
        return (f"Unknown power plan '{plan}'. "
                f"Options: balanced, power saver, high performance, ultimate performance.")

    try:
        subprocess.run(
            ["powercfg", "/s", guid],
            capture_output=True, text=True, timeout=10, check=True,
        )
        return f"Power plan changed to '{plan}'."
    except subprocess.CalledProcessError as e:
        return f"Couldn't change power plan: {e.stderr[:200]}"
    except FileNotFoundError:
        return "Powercfg not available on this system."
    except Exception as e:
        return f"Error: {e}"


def get_power_plan():
    """Get the current active power plan."""
    try:
        result = subprocess.run(
            ["powercfg", "/getactivescheme"],
            capture_output=True, text=True, timeout=10,
        )
        output = result.stdout.strip()
        name = output.split("(", 1)[-1].rstrip(")") if "(" in output else output
        return f"Current power plan: {name}"
    except Exception as e:
        return f"Couldn't get power plan: {e}"


def get_storage_usage(drive=""):
    """Get disk storage usage for a drive (e.g. C:)."""
    try:
        if not drive:
            drive = os.path.splitdrive(os.path.expanduser("~"))[0]
        drive = drive.rstrip("\\") + "\\"

        free = ctypes.c_ulonglong(0)
        total = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            drive, None, ctypes.byref(total), ctypes.byref(free)
        )

        total_gb = total.value / (1024**3)
        free_gb = free.value / (1024**3)
        used_gb = total_gb - free_gb
        pct = (used_gb / total_gb * 100) if total_gb > 0 else 0

        return (f"Drive {drive}: {used_gb:.1f} GB used of {total_gb:.1f} GB "
                f"({pct:.0f}% full, {free_gb:.1f} GB free).")
    except Exception as e:
        return f"Couldn't get storage info: {e}"


def list_drives():
    """List all available drives with type and free space."""
    try:
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        drives = []
        for i in range(26):
            if bitmask & (1 << i):
                letter = f"{chr(65 + i)}:\\"
                dtype = ctypes.windll.kernel32.GetDriveTypeW(letter)
                type_names = {2: "Removable", 3: "Fixed", 4: "Network", 5: "CD/DVD"}
                dtype_str = type_names.get(dtype, "Unknown")

                free = ctypes.c_ulonglong(0)
                total = ctypes.c_ulonglong(0)
                if ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    letter, None, ctypes.byref(total), ctypes.byref(free)
                ):
                    total_gb = total.value / (1024**3)
                    free_gb = free.value / (1024**3)
                    drives.append(f"{letter} ({dtype_str}, {total_gb:.0f} GB, "
                                  f"{free_gb:.1f} GB free)")
                else:
                    drives.append(f"{letter} ({dtype_str})")
        if drives:
            return "Drives: " + "; ".join(drives)
        return "No drives found."
    except Exception as e:
        return f"Error listing drives: {e}"


def empty_recycle_bin():
    """Empty the Windows Recycle Bin."""
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(New-Object -ComObject Shell.Application).NameSpace(0xa).Items() | "
             "ForEach-Object { $_.InvokeVerb('delete') }"],
            capture_output=True, text=True, timeout=15,
        )
        return "Recycle Bin emptied."
    except subprocess.TimeoutExpired:
        return "Recycle Bin cleanup timed out."
    except Exception as e:
        return f"Couldn't empty Recycle Bin: {e}"


def manage_startup_app(action, name):
    """Enable or disable a startup application via Task Manager."""
    action = action.lower().strip()
    name = name.strip()

    try:
        # Get the startup entry path
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"Get-CimInstance Win32_StartupCommand | "
             f"Where-Object {{ $_.Name -like '*{name}*' }} | "
             f"Select-Object -First 1 Name, Command, Location"],
            capture_output=True, text=True, timeout=10,
        )
        if not result.stdout.strip():
            return f"Couldn't find startup entry matching '{name}'."

        if action in ("enable", "disable"):
            # Use registry to enable/disable
            toggle = "Disable" if action == "disable" else "Enable"
            subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 f"Get-CimInstance Win32_StartupCommand | "
                 f"Where-Object {{ $_.Name -like '*{name}*' }} | "
                 f"ForEach-Object {{ "
                 f"  $regPath = $_.Location.TrimStart('HKU\\').Replace('HKEY_CURRENT_USER\\', "
                 f"'HKEY_USERS\\').Replace('HKEY_LOCAL_MACHINE\\', 'HKLM:\\'); "
                 f"  Remove-ItemProperty -Path $regPath -Name $_.Command -ErrorAction SilentlyContinue"
                 f"}}"],
                capture_output=True, text=True, timeout=10,
            )
            return f"Startup entry '{name}' {action}d."
        return "Action must be 'enable' or 'disable'."
    except Exception as e:
        return f"Couldn't manage startup app: {e}"


def create_restore_point(description):
    """Create a Windows system restore point."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"Checkpoint-Computer -Description '{description}' -RestorePointType MODIFY_SETTINGS"],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0:
            return f"Restore point '{description}' created."
        return f"Couldn't create restore point: {result.stderr[:300]}"
    except subprocess.TimeoutExpired:
        return "Restore point creation timed out (may still be processing)."
    except Exception as e:
        return f"Error: {e}"


def disk_cleanup():
    """Run Windows Disk Cleanup utility."""
    try:
        subprocess.Popen(["cleanmgr.exe"], close_fds=True)
        return "Opening Disk Cleanup."
    except FileNotFoundError:
        return "Disk Cleanup not available."
    except Exception as e:
        return f"Couldn't open Disk Cleanup: {e}"


def get_system_uptime():
    """Get how long the system has been running."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance Win32_OperatingSystem).LastBootUpTime"],
            capture_output=True, text=True, timeout=10,
        )
        boot_str = result.stdout.strip()
        if boot_str:
            import datetime as dt
            boot = dt.datetime.strptime(boot_str.split(".")[0], "%Y%m%d%H%M%S")
            uptime = dt.datetime.now() - boot
            days = uptime.days
            hours = uptime.seconds // 3600
            minutes = (uptime.seconds % 3600) // 60
            parts = []
            if days > 0:
                parts.append(f"{days} day(s)")
            if hours > 0:
                parts.append(f"{hours} hour(s)")
            parts.append(f"{minutes} minute(s)")
            return f"System uptime: {' '.join(parts)}."
        return "Couldn't determine uptime."
    except Exception as e:
        return f"Error: {e}"
