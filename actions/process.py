"""Process management: list, kill, inspect processes."""

import psutil
from actions.confirmation import ask_confirmation


def list_processes():
    """List the top 20 processes by CPU and memory usage."""
    try:
        procs = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                info = p.info
                procs.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Sort by CPU + memory combined
        procs.sort(key=lambda x: (x.get("cpu_percent") or 0) + (x.get("memory_percent") or 0), reverse=True)
        top = procs[:20]

        lines = ["Top 20 processes by resource usage:"]
        for p in top:
            cpu = p.get("cpu_percent", 0) or 0
            mem = p.get("memory_percent", 0) or 0
            lines.append(f"  {p['name']} (PID {p['pid']}): CPU {cpu:.1f}%, Memory {mem:.1f}%")
        return "\n".join(lines)
    except Exception as e:
        return f"Error listing processes: {e}"


def kill_process(name_or_pid):
    """Kill a process by name or PID. Refuses to kill Nova or system processes."""
    if not ask_confirmation(f"Kill process: {name_or_pid}"):
        return "Action cancelled by user."

    protected_names = {
        "nova.exe", "python.exe", "pythonw.exe", "msedgewebview2.exe",
        "explorer.exe", "svchost.exe", "csrss.exe", "dwm.exe",
        "system", "system idle process", "lsass.exe", "services.exe",
        "conhost.exe", "cmd.exe", "powershell.exe", "winlogon.exe",
    }

    killed = []

    # Try as PID first
    try:
        pid = int(name_or_pid)
        proc = psutil.Process(pid)
        proc_name = proc.name()
        if proc_name.lower() in protected_names:
            return f"Refusing to kill protected process {proc_name}."
        proc.kill()
        return f"Killed {proc_name} (PID {pid})."
    except (ValueError, TypeError):
        pass  # Not a PID, treat as name
    except psutil.NoSuchProcess:
        return f"No process found with PID {name_or_pid}."
    except psutil.AccessDenied:
        return f"Access denied — cannot kill PID {name_or_pid}."
    except Exception as e:
        return f"Error killing process: {e}"

    # Search by name
    search = str(name_or_pid).lower().strip()
    if len(search) < 3:
        return "That name is too short to be safe. Please be more specific."
    for proc in psutil.process_iter(["name", "pid"]):
        try:
            pname = proc.info["name"].lower()
            if pname in protected_names:
                continue
            if search in pname:
                proc.kill()
                killed.append(f"{proc.info['name']} (PID {proc.info['pid']})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if killed:
        return f"Killed: {', '.join(killed)}."
    return f"No running process matching '{name_or_pid}'."


def get_process_info(name):
    """Get detailed info about a process by name."""
    search = name.lower().strip()
    found = []

    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent",
                                      "status", "create_time", "num_threads"]):
        try:
            if search in proc.info["name"].lower():
                info = proc.info
                import datetime
                created = info.get("create_time")
                created_str = (datetime.datetime.fromtimestamp(created).strftime("%I:%M %p")
                               if created else "unknown")
                try:
                    mem_mb = proc.memory_info().rss / (1024 * 1024)
                except Exception:
                    mem_mb = 0
                found.append(
                    f"{info['name']} (PID {info['pid']}): "
                    f"Status {info['status']}, CPU {info['cpu_percent'] or 0:.1f}%, "
                    f"Memory {mem_mb:.1f} MB, Threads {info.get('num_threads') or 0}, "
                    f"Started at {created_str}"
                )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if found:
        return "\n".join(found[:10])
    return f"No process matching '{name}' found."
