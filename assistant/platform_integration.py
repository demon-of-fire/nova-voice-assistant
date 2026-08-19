"""Platform integration facade for Nova.

Windows has the full implementation today. The Linux functions below mirror the
same API with freedesktop-style paths so the app does not need a redesign later.
"""

import os
import sys


if os.name == "nt":
    from assistant.windows_integration import *  # noqa: F401,F403
else:
    APP_NAME = "Nova"
    PROTOCOL = "nova"
    DESCRIPTION = "Nova Voice Assistant"

    def _project_root():
        return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def installed_dir():
        return os.path.join(os.path.expanduser("~"), ".local", "share", APP_NAME)

    def installed_exe_path():
        return os.path.join(installed_dir(), APP_NAME.lower())

    def _main_command(args=""):
        main_py = os.path.join(_project_root(), "main.py")
        return f'{sys.executable} "{main_py}" {args}'.strip()

    def _desktop_file(args=""):
        return "\n".join([
            "[Desktop Entry]",
            "Type=Application",
            f"Name={APP_NAME}",
            f"Comment={DESCRIPTION}",
            f"Exec={_main_command(args)}",
            "Terminal=false",
            "Categories=Utility;Accessibility;",
            "",
        ])

    def _write_file(path, content):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        try:
            os.chmod(path, 0o755)
        except Exception:
            pass
        return True, "Desktop entry ready."

    def startup_shortcut_path():
        return os.path.join(os.path.expanduser("~"), ".config", "autostart", "nova.desktop")

    def desktop_shortcut_path():
        return os.path.join(os.path.expanduser("~"), "Desktop", "nova.desktop")

    def start_menu_shortcut_path():
        return os.path.join(os.path.expanduser("~"), ".local", "share", "applications", "nova.desktop")

    def create_desktop_shortcut():
        return _write_file(desktop_shortcut_path(), _desktop_file())

    def create_start_menu_shortcut():
        return _write_file(start_menu_shortcut_path(), _desktop_file())

    def create_startup_shortcut():
        return _write_file(startup_shortcut_path(), _desktop_file("--startup"))

    def install_current_exe(startup=True):
        return False

    def set_start_with_windows(enabled):
        if enabled:
            return create_startup_shortcut()
        try:
            os.remove(startup_shortcut_path())
            return True, "Startup entry removed."
        except FileNotFoundError:
            return True, "Startup entry was not present."
        except Exception as exc:
            return False, str(exc)

    def register_protocol_handler():
        path = os.path.join(os.path.expanduser("~"), ".local", "share", "applications", "nova-url.desktop")
        content = _desktop_file("%u").replace("Type=Application", "Type=Application\nMimeType=x-scheme-handler/nova;")
        return _write_file(path, content)

    def unregister_protocol_handler():
        try:
            os.remove(os.path.join(os.path.expanduser("~"), ".local", "share", "applications", "nova-url.desktop"))
            return True, "nova:// links removed."
        except FileNotFoundError:
            return True, "nova:// links were not registered."
        except Exception as exc:
            return False, str(exc)

    def register_app_path():
        return create_start_menu_shortcut()

    def unregister_app_path():
        return True, "No separate Linux app alias is registered."

    def repair_native_integration(settings=None):
        results = [create_desktop_shortcut(), create_start_menu_shortcut(), create_startup_shortcut(), register_protocol_handler()]
        if settings is not None:
            settings.set("start_minimized", True)
        failed = [message for ok, message in results if not ok]
        if failed:
            return False, "; ".join(failed)
        return True, "Native integration repaired."

    def disconnect_native_integration():
        ok, message = set_start_with_windows(False)
        uri_ok, uri_message = unregister_protocol_handler()
        if ok and uri_ok:
            return True, "Startup and URI integration removed."
        return False, "; ".join([m for good, m in [(ok, message), (uri_ok, uri_message)] if not good])

    def open_install_location():
        return False, "Open-folder integration is not implemented for Linux yet."

    def open_startup_folder():
        return False, "Open-folder integration is not implemented for Linux yet."

    def open_logs_folder():
        return False, "Open-folder integration is not implemented for Linux yet."

    def status(settings):
        return {
            "platform": sys.platform,
            "installed_exe": installed_exe_path(),
            "installed": os.path.exists(installed_exe_path()),
            "desktop_shortcut": os.path.exists(desktop_shortcut_path()),
            "start_menu_shortcut": os.path.exists(start_menu_shortcut_path()),
            "start_with_windows": os.path.exists(startup_shortcut_path()),
            "uri_protocol": os.path.exists(os.path.join(os.path.expanduser("~"), ".local", "share", "applications", "nova-url.desktop")),
            "app_path_alias": os.path.exists(start_menu_shortcut_path()),
            "startup_shortcut": startup_shortcut_path(),
            "install_dir": installed_dir(),
            "start_minimized": bool(settings.get("start_minimized")),
            "wake_word_enabled": bool(settings.get("wake_word_enabled")),
        }
