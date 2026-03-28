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
    """Kill a process by name or PID."""
    if not ask_confirmation(f"Kill process: {name_or_pid}"):
        return "Action cancelled by user."

    killed = []

    # Try as PID first
    try:
        pid = int(name_or_pid)
        proc = psutil.Process(pid)
        proc_name = proc.name()
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
    for proc in psutil.process_iter(["name", "pid"]):
        try:
            if search in proc.info["name"].lower():
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
                created = datetime.datetime.fromtimestamp(info["create_time"]).strftime("%I:%M %p")
                mem_mb = (proc.memory_info().rss / (1024 * 1024)) if proc.is_running() else 0
                found.append(
                    f"{info['name']} (PID {info['pid']}): "
                    f"Status {info['status']}, CPU {info['cpu_percent']:.1f}%, "
                    f"Memory {mem_mb:.1f} MB, Threads {info['num_threads']}, "
                    f"Started at {created}"
                )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if found:
        return "\n".join(found[:10])
    return f"No process matching '{name}' found."
