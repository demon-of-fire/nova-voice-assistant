"""Network utilities: IP info, wifi, ping."""

import subprocess
import socket
import psutil


def get_network_info():
    """Get IP address, wifi name, and connection status."""
    try:
        info_parts = []

        # Local IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            info_parts.append(f"Local IP: {local_ip}")
        except Exception:
            info_parts.append("Local IP: not connected")

        # Wifi SSID (Windows)
        try:
            result = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True, text=True, timeout=10,
            )
            for line in result.stdout.splitlines():
                line = line.strip()
                if line.startswith("SSID") and "BSSID" not in line:
                    ssid = line.split(":", 1)[1].strip()
                    info_parts.append(f"WiFi network: {ssid}")
                    break
                if line.startswith("State"):
                    state = line.split(":", 1)[1].strip()
                    info_parts.append(f"Connection state: {state}")
        except Exception:
            pass

        # Network interfaces summary
        stats = psutil.net_if_stats()
        active = [name for name, s in stats.items() if s.isup and name != "Loopback Pseudo-Interface 1"]
        if active:
            info_parts.append(f"Active interfaces: {', '.join(active)}")

        return ". ".join(info_parts) + "." if info_parts else "Couldn't retrieve network info."
    except Exception as e:
        return f"Error getting network info: {e}"


def get_wifi_networks():
    """List available WiFi networks."""
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "networks", "mode=bssid"],
            capture_output=True, text=True, timeout=10,
        )
        networks = []
        current = {}
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("SSID") and "BSSID" not in line:
                if current:
                    networks.append(current)
                ssid = line.split(":", 1)[1].strip()
                current = {"ssid": ssid}
            elif line.startswith("Signal"):
                current["signal"] = line.split(":", 1)[1].strip()
            elif line.startswith("Authentication"):
                current["auth"] = line.split(":", 1)[1].strip()
        if current:
            networks.append(current)

        if not networks:
            return "No WiFi networks found."

        lines = [f"Found {len(networks)} WiFi networks:"]
        for n in networks[:15]:
            signal = n.get("signal", "?")
            auth = n.get("auth", "?")
            lines.append(f"  {n['ssid']} — Signal {signal}, {auth}")
        return "\n".join(lines)
    except FileNotFoundError:
        return "WiFi scanning not available."
    except subprocess.TimeoutExpired:
        return "WiFi scan timed out."
    except Exception as e:
        return f"Error scanning WiFi: {e}"


def ping(host):
    """Ping a host and return the result."""
    try:
        result = subprocess.run(
            ["ping", "-n", "4", host],
            capture_output=True, text=True, timeout=15,
        )
        output = result.stdout.strip()
        # Extract the summary line
        for line in output.splitlines():
            if "average" in line.lower() or "Average" in line:
                return f"Ping {host}: {line.strip()}"
            if "could not find host" in line.lower():
                return f"Could not reach {host}."
        # Return last few lines as summary
        summary = "\n".join(output.splitlines()[-3:])
        return f"Ping {host}:\n{summary}"
    except subprocess.TimeoutExpired:
        return f"Ping to {host} timed out."
    except Exception as e:
        return f"Error pinging {host}: {e}"


def get_public_ip():
    """Get the public IP address."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Invoke-WebRequest -Uri 'https://api.ipify.org' -UseBasicParsing).Content"],
            capture_output=True, text=True, timeout=10,
        )
        ip = result.stdout.strip()
        if ip and len(ip) < 50:
            return f"Your public IP is {ip}."
        return "Couldn't determine public IP."
    except subprocess.TimeoutExpired:
        return "Request timed out while getting public IP."
    except Exception as e:
        return f"Error getting public IP: {e}"
