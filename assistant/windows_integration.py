"""Small Windows integration helpers for Nova."""

import os
import shutil
import subprocess
import sys


APP_NAME = "Nova"
STARTUP_ARGUMENTS = "--startup"
PROTOCOL = "nova"
DESCRIPTION = "Nova Voice Assistant"


def _project_root():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def installed_dir():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base, APP_NAME)


def installed_exe_path():
    return os.path.join(installed_dir(), f"{APP_NAME}.exe")


def _shortcut_target():
    if getattr(sys, "frozen", False):
        return sys.executable
    exe_path = os.path.join(_project_root(), "Nova.exe")
    if os.path.exists(exe_path):
        return exe_path
    return sys.executable


def _shortcut_args():
    if getattr(sys, "frozen", False):
        return ""
    if os.path.exists(os.path.join(_project_root(), "Nova.exe")):
        return ""
    return f'"{os.path.join(_project_root(), "main.py")}"'


def _create_shortcut(path, target=None, arguments=None, working_dir=None):
    try:
        import comtypes.client
    except Exception as exc:
        return False, f"Windows shortcut support is unavailable: {exc}"

    try:
        shell = comtypes.client.CreateObject("WScript.Shell")
        shortcut = shell.CreateShortcut(path)
        shortcut.TargetPath = target or _shortcut_target()
        shortcut.Arguments = arguments if arguments is not None else _shortcut_args()
        shortcut.WorkingDirectory = working_dir or _project_root()
        shortcut.Description = DESCRIPTION
        shortcut.Save()
        return True, "Shortcut ready."
    except Exception as exc:
        return False, str(exc)


def startup_shortcut_path():
    appdata = os.environ.get("APPDATA", "")
    return os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs", "Startup", f"{APP_NAME}.lnk")


def desktop_shortcut_path():
    return os.path.join(os.path.expanduser("~"), "Desktop", f"{APP_NAME}.lnk")


def start_menu_shortcut_path():
    appdata = os.environ.get("APPDATA", "")
    return os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs", f"{APP_NAME}.lnk")


def create_desktop_shortcut():
    return _create_shortcut(desktop_shortcut_path())


def create_start_menu_shortcut():
    return _create_shortcut(start_menu_shortcut_path())


def create_startup_shortcut():
    target = installed_exe_path() if os.path.exists(installed_exe_path()) else _shortcut_target()
    working_dir = installed_dir() if os.path.exists(installed_exe_path()) else _project_root()
    return _create_shortcut(
        startup_shortcut_path(),
        target=target,
        arguments=STARTUP_ARGUMENTS,
        working_dir=working_dir,
    )


def _installed_target():
    return installed_exe_path() if os.path.exists(installed_exe_path()) else _shortcut_target()


def _installed_working_dir():
    return installed_dir() if os.path.exists(installed_exe_path()) else _project_root()


def _quote(value):
    return f'"{value}"'


def register_protocol_handler():
    """Register nova:// links for launchers, scripts, and future shell hooks."""
    if os.name != "nt":
        return False, "URI integration is only implemented for Windows here."
    try:
        import winreg

        target = _installed_target()
        command = f'{_quote(target)} "%1"'
        base = rf"Software\Classes\{PROTOCOL}"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, base) as key:
            winreg.SetValueEx(key, None, 0, winreg.REG_SZ, f"URL:{DESCRIPTION}")
            winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, base + r"\DefaultIcon") as key:
            winreg.SetValueEx(key, None, 0, winreg.REG_SZ, f"{target},0")
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, base + r"\shell\open\command") as key:
            winreg.SetValueEx(key, None, 0, winreg.REG_SZ, command)
        return True, f"{PROTOCOL}:// links registered."
    except Exception as exc:
        return False, str(exc)


def unregister_protocol_handler():
    try:
        import winreg

        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{PROTOCOL}\shell\open\command")
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{PROTOCOL}\shell\open")
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{PROTOCOL}\shell")
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{PROTOCOL}\DefaultIcon")
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{PROTOCOL}")
        return True, f"{PROTOCOL}:// links removed."
    except FileNotFoundError:
        return True, f"{PROTOCOL}:// links were not registered."
    except Exception as exc:
        return False, str(exc)


def register_app_path():
    """Let Win+R find Nova.exe from the installed location."""
    if os.name != "nt":
        return False, "App Paths integration is only implemented for Windows here."
    try:
        import winreg

        target = _installed_target()
        with winreg.CreateKey(
            winreg.HKEY_CURRENT_USER,
            rf"Software\Microsoft\Windows\CurrentVersion\App Paths\{APP_NAME}.exe",
        ) as key:
            winreg.SetValueEx(key, None, 0, winreg.REG_SZ, target)
            winreg.SetValueEx(key, "Path", 0, winreg.REG_SZ, _installed_working_dir())
        return True, "Win+R app alias registered."
    except Exception as exc:
        return False, str(exc)


def unregister_app_path():
    try:
        import winreg

        winreg.DeleteKey(
            winreg.HKEY_CURRENT_USER,
            rf"Software\Microsoft\Windows\CurrentVersion\App Paths\{APP_NAME}.exe",
        )
        return True, "Win+R app alias removed."
    except FileNotFoundError:
        return True, "Win+R app alias was not registered."
    except Exception as exc:
        return False, str(exc)


def _registry_key_exists(root, path):
    if os.name != "nt":
        return False
    try:
        import winreg

        with winreg.OpenKey(root, path):
            return True
    except Exception:
        return False


def install_current_exe(startup=True):
    """Install a downloaded one-file exe into the user's profile and relaunch it.

    Returns True when the current process should exit because the installed copy
    has been started.
    """
    if not getattr(sys, "frozen", False):
        return False

    current = os.path.abspath(sys.executable)
    target = installed_exe_path()
    if os.path.normcase(current) == os.path.normcase(target):
        create_start_menu_shortcut()
        create_desktop_shortcut()
        if startup:
            create_startup_shortcut()
        register_protocol_handler()
        register_app_path()
        return False

    os.makedirs(installed_dir(), exist_ok=True)
    shutil.copy2(current, target)
    _create_shortcut(start_menu_shortcut_path(), target=target, arguments="", working_dir=installed_dir())
    _create_shortcut(desktop_shortcut_path(), target=target, arguments="", working_dir=installed_dir())
    if startup:
        create_startup_shortcut()
    register_protocol_handler()
    register_app_path()
    subprocess.Popen([target, "--setup-complete"], cwd=installed_dir(), close_fds=True)
    return True


def set_start_with_windows(enabled):
    path = startup_shortcut_path()
    if enabled:
        return create_startup_shortcut()
    try:
        if os.path.exists(path):
            os.remove(path)
        return True, "Startup shortcut removed."
    except Exception as exc:
        return False, str(exc)


def repair_native_integration(settings=None):
    """Re-apply all per-user OS integration that does not require admin rights."""
    results = []
    for action in (
        create_desktop_shortcut,
        create_start_menu_shortcut,
        create_startup_shortcut,
        register_protocol_handler,
        register_app_path,
    ):
        ok, message = action()
        results.append((ok, message))
    if settings is not None:
        try:
            settings.set("start_minimized", True)
        except Exception:
            pass
    failed = [message for ok, message in results if not ok]
    if failed:
        return False, "Some integration steps failed: " + "; ".join(failed)
    return True, "Native integration repaired."


def disconnect_native_integration():
    results = []
    for action in (
        lambda: set_start_with_windows(False),
        unregister_protocol_handler,
        unregister_app_path,
    ):
        ok, message = action()
        results.append((ok, message))
    failed = [message for ok, message in results if not ok]
    if failed:
        return False, "Some integration cleanup failed: " + "; ".join(failed)
    return True, "Startup, URI, and Win+R integration removed."


def open_install_location():
    try:
        path = installed_dir() if os.path.exists(installed_dir()) else _project_root()
        os.startfile(path)
        return True, path
    except Exception as exc:
        return False, str(exc)


def open_startup_folder():
    try:
        os.startfile(os.path.dirname(startup_shortcut_path()))
        return True, os.path.dirname(startup_shortcut_path())
    except Exception as exc:
        return False, str(exc)


def open_logs_folder():
    try:
        os.startfile(os.path.expanduser("~"))
        return True, os.path.expanduser("~")
    except Exception as exc:
        return False, str(exc)


def status(settings):
    if os.name == "nt":
        import winreg
        uri_protocol = _registry_key_exists(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{PROTOCOL}")
        app_path_alias = _registry_key_exists(
            winreg.HKEY_CURRENT_USER,
            rf"Software\Microsoft\Windows\CurrentVersion\App Paths\{APP_NAME}.exe",
        )
    else:
        uri_protocol = False
        app_path_alias = False

    return {
        "platform": sys.platform,
        "installed_exe": installed_exe_path(),
        "installed": os.path.exists(installed_exe_path()),
        "desktop_shortcut": os.path.exists(desktop_shortcut_path()),
        "start_menu_shortcut": os.path.exists(start_menu_shortcut_path()),
        "start_with_windows": os.path.exists(startup_shortcut_path()),
        "uri_protocol": uri_protocol,
        "app_path_alias": app_path_alias,
        "startup_shortcut": startup_shortcut_path(),
        "install_dir": installed_dir(),
        "start_minimized": bool(settings.get("start_minimized")),
        "wake_word_enabled": bool(settings.get("wake_word_enabled")),
    }
