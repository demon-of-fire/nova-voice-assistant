"""More system actions: services, audio devices, display info, env vars."""

import os
import subprocess
import ctypes
import json


def list_services(status="running"):
    """List Windows services by status: running, stopped, or all."""
    try:
        if status == "running":
            filter_cmd = "Where-Object { $_.State -eq 'Running' }"
        elif status == "stopped":
            filter_cmd = "Where-Object { $_.State -eq 'Stopped' }"
        else:
            filter_cmd = "Where-Object { $true }"

        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"Get-Service | {filter_cmd} | Select-Object -First 20 Name, DisplayName, Status "
             f"| Format-Table -AutoSize | Out-String -Width 4096"],
            capture_output=True, text=True, timeout=15,
        )
        output = result.stdout.strip()
        if not output:
            return f"No {status} services found."
        lines = [l.strip() for l in output.splitlines() if l.strip() and "--" not in l]
        # Skip header line
        services = [l for l in lines if l and not l.startswith("Name")][:15]
        if not services:
            return f"No {status} services found."
        return f"{status.capitalize()} services: " + "; ".join(services[:15])
    except Exception as e:
        return f"Couldn't list services: {e}"


def restart_service(service_name):
    """Restart a Windows service by name."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"Restart-Service -Name '{service_name}' -Force -ErrorAction Stop; "
             f"Write-Output 'Service restarted'"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return f"Service '{service_name}' restarted."
        return f"Couldn't restart service: {result.stderr[:200]}"
    except subprocess.TimeoutExpired:
        return f"Restart of '{service_name}' timed out."
    except Exception as e:
        return f"Error restarting service: {e}"


def start_service(service_name):
    """Start a stopped Windows service."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"Start-Service -Name '{service_name}' -ErrorAction Stop"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return f"Service '{service_name}' started."
        return f"Couldn't start service: {result.stderr[:200]}"
    except Exception as e:
        return f"Error starting service: {e}"


def stop_service(service_name):
    """Stop a running Windows service."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"Stop-Service -Name '{service_name}' -Force -ErrorAction Stop"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return f"Service '{service_name}' stopped."
        return f"Couldn't stop service: {result.stderr[:200]}"
    except Exception as e:
        return f"Error stopping service: {e}"


def get_audio_devices():
    """List audio input and output devices."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-PnPAudioDevice | Select-Object Name, DeviceType | Format-Table -AutoSize | Out-String -Width 4096"],
            capture_output=True, text=True, timeout=10,
        )
        output = result.stdout.strip()
        if not output:
            return "No audio devices found."
        lines = [l.strip() for l in output.splitlines() if l.strip() and "--" not in l]
        devices = [l for l in lines if l and not l.startswith("Name")][:10]
        if not devices:
            return "No audio devices found."
        return "Audio devices: " + "; ".join(devices)
    except Exception:
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "[System.Windows.Forms.AudioDevice]::GetDevices() | Select-Object Name, Role"],
                capture_output=True, text=True, timeout=10,
            )
            if result.stdout.strip():
                return "Audio devices: " + result.stdout.strip()[:300]
            return "Couldn't enumerate audio devices."
        except Exception as e:
            return f"Couldn't get audio devices: {e}"


def get_display_info():
    """Get display/monitor information."""
    try:
        user32 = ctypes.windll.user32
        primary_w = user32.GetSystemMetrics(0)
        primary_h = user32.GetSystemMetrics(1)
        virtual_w = user32.GetSystemMetrics(78)
        virtual_h = user32.GetSystemMetrics(79)
        monitors = user32.GetSystemMetrics(80)

        return (f"Display: {monitors} monitor(s), "
                f"primary resolution {primary_w}x{primary_h}, "
                f"virtual desktop {virtual_w}x{virtual_h}.")
    except Exception as e:
        return f"Couldn't get display info: {e}"


def get_env_var(name):
    """Get the value of an environment variable."""
    try:
        value = os.environ.get(name.strip(), "")
        if value:
            return f"{name} = {value[:500]}"
        return f"Environment variable '{name}' not set."
    except Exception as e:
        return f"Error reading env var: {e}"


def list_env_vars(pattern=""):
    """List environment variables, optionally filtered by pattern."""
    try:
        vars_list = []
        for key, value in sorted(os.environ.items()):
            if pattern.lower() in key.lower():
                vars_list.append(f"{key}={value[:80]}")
        if not vars_list:
            return f"No env vars matching '{pattern}'."
        return "Environment variables: " + "; ".join(vars_list[:20])
    except Exception as e:
        return f"Error listing env vars: {e}"


def list_startup_programs():
    """List programs that run at Windows startup."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_StartupCommand | "
             "Select-Object Name, Command, Location | Format-Table -AutoSize | Out-String -Width 4096"],
            capture_output=True, text=True, timeout=10,
        )
        output = result.stdout.strip()
        if not output:
            return "No startup programs found."
        lines = [l.strip() for l in output.splitlines() if l.strip() and "--" not in l]
        programs = [l for l in lines if l and not l.startswith("Name")][:15]
        if not programs:
            return "No startup programs found."
        return f"Startup programs ({len(programs)}): " + "; ".join(programs)
    except Exception as e:
        return f"Couldn't list startup programs: {e}"
