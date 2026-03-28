"""Shell command execution, app install/uninstall via winget."""

import subprocess
from actions.confirmation import ask_confirmation


def run_command(command, shell="cmd"):
    """Run a cmd or powershell command and return the output."""
    if not ask_confirmation(f"Run {shell} command:\n{command}"):
        return "Action cancelled by user."

    try:
        if shell == "powershell":
            full_cmd = ["powershell", "-NoProfile", "-Command", command]
        else:
            full_cmd = ["cmd", "/c", command]

        result = subprocess.run(
            full_cmd, capture_output=True, text=True, timeout=30,
        )
        output = result.stdout.strip() or result.stderr.strip() or "(no output)"
        if len(output) > 2000:
            output = output[:2000] + "\n... (truncated)"
        return output
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds."
    except Exception as e:
        return f"Error running command: {e}"


def run_powershell(command):
    """Run a PowerShell command (shorthand)."""
    return run_command(command, shell="powershell")


def install_app(app_name):
    """Install an application using winget."""
    if not ask_confirmation(f"Install application: {app_name}"):
        return "Installation cancelled by user."

    try:
        result = subprocess.run(
            ["winget", "install", "--accept-package-agreements",
             "--accept-source-agreements", "-e", "--name", app_name],
            capture_output=True, text=True, timeout=120,
        )
        output = result.stdout.strip() + result.stderr.strip()
        if "successfully installed" in output.lower() or result.returncode == 0:
            return f"Successfully installed {app_name}."
        if "already installed" in output.lower():
            return f"{app_name} is already installed."
        return f"Installation result: {output[:500]}"
    except subprocess.TimeoutExpired:
        return "Installation timed out. It may still be running in the background."
    except FileNotFoundError:
        return "Winget is not available on this system."
    except Exception as e:
        return f"Error installing {app_name}: {e}"


def uninstall_app(app_name):
    """Uninstall an application using winget."""
    if not ask_confirmation(f"Uninstall application: {app_name}"):
        return "Uninstall cancelled by user."

    try:
        result = subprocess.run(
            ["winget", "uninstall", "--accept-source-agreements", "-e", "--name", app_name],
            capture_output=True, text=True, timeout=120,
        )
        output = result.stdout.strip() + result.stderr.strip()
        if "successfully uninstalled" in output.lower() or result.returncode == 0:
            return f"Successfully uninstalled {app_name}."
        return f"Uninstall result: {output[:500]}"
    except subprocess.TimeoutExpired:
        return "Uninstall timed out. It may still be running in the background."
    except FileNotFoundError:
        return "Winget is not available on this system."
    except Exception as e:
        return f"Error uninstalling {app_name}: {e}"


def list_installed_apps():
    """List installed applications using winget."""
    try:
        result = subprocess.run(
            ["winget", "list", "--accept-source-agreements"],
            capture_output=True, text=True, timeout=30,
        )
        output = result.stdout.strip()
        if not output:
            return "Couldn't retrieve installed apps."

        lines = output.splitlines()
        # winget list has a header; grab a summary
        app_lines = [l for l in lines if l.strip() and not l.startswith("-")]
        count = max(0, len(app_lines) - 2)  # subtract header lines
        # Return first 20 app names for brevity
        summary_lines = app_lines[:22]
        summary = "\n".join(summary_lines)
        if len(summary) > 2000:
            summary = summary[:2000] + "\n... (truncated)"
        return f"Found approximately {count} installed apps:\n{summary}"
    except subprocess.TimeoutExpired:
        return "Listing timed out after 30 seconds."
    except FileNotFoundError:
        return "Winget is not available on this system."
    except Exception as e:
        return f"Error listing apps: {e}"
