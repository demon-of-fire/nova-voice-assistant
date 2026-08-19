"""Nova — A lightweight Windows voice assistant powered by Google Gemini."""

import sys
import os
import traceback
import logging
import subprocess
import threading
import time
import ctypes

LOG_PATH = os.path.join(os.path.expanduser("~"), "nova_error.log")
DEBUG_LOG = os.path.join(os.path.expanduser("~"), "nova_debug.log")
PID_FILE = os.path.join(os.path.expanduser("~"), ".nova_pid")
CRASH_COUNT_FILE = os.path.join(os.path.expanduser("~"), ".nova_crash_count")


def _register_windows_search():
    """Register Nova in Windows Search so Win+S can find it."""
    try:
        import winreg
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\Nova.exe"
        exe_path = os.path.abspath(sys.argv[0])
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, exe_path)
            winreg.SetValueEx(key, "Path", 0, winreg.REG_SZ, os.path.dirname(exe_path))
    except Exception:
        pass


def _register_nova_hotkey():
    """Register Win+Shift+N as a dedicated Nova hotkey in Windows."""
    try:
        import winreg
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\Windows.Nova"
        cmd = f'"{os.path.abspath(sys.argv[0])}" --activate'
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValueEx(key, "ExplorerCommand", 0, winreg.REG_SZ, "Nova Voice Assistant")
            winreg.SetValueEx(key, "icon", 0, winreg.REG_SZ, os.path.abspath(sys.argv[0]))
    except Exception:
        pass


def _write_pid():
    """Write current PID to a file for crash detection."""
    try:
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))
    except Exception:
        pass


def _clean_pid():
    try:
        if os.path.isfile(PID_FILE):
            os.remove(PID_FILE)
    except Exception:
        pass


def run_nova(startup_mode=False, setup_complete=False, command_action=""):
    """Run Nova once."""
    logging.basicConfig(
        filename=DEBUG_LOG,
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s: %(message)s",
        filemode="a",
    )
    log = logging.getLogger("nova")

    import config
    from assistant.settings import Settings

    settings = Settings()
    if setup_complete:
        settings.set("start_minimized", True)

    from assistant.ui import AssistantUI
    from assistant.core import Assistant
    from assistant.tray import run_tray

    ui = AssistantUI(settings)

    api_key = settings.get("gemini_api_key") or config.GEMINI_API_KEY
    if not api_key:
        ui._needs_apikey = True
    else:
        ui._needs_apikey = False

    assistant = Assistant(ui, settings)

    def on_tray_show():
        ui.show()

    def on_tray_talk():
        if assistant._can_activate():
            threading.Thread(target=assistant.activate_silent, daemon=True).start()

    def on_tray_mute():
        threading.Thread(target=assistant.toggle_mute, daemon=True).start()

    def on_tray_settings():
        ui.show()
        try:
            ui._eval("showSettings();")
        except Exception:
            pass

    def on_tray_quit():
        assistant.stop()
        ui.quit()

    tray_icon = run_tray(on_tray_show, on_tray_talk, on_tray_mute, on_tray_settings, on_tray_quit)

    original_ready = ui._on_webview_ready

    def _extended_ready():
        original_ready()

        if ui._needs_apikey:
            def _apikey_flow():
                key = ui.show_apikey_setup()
                if not key:
                    ui.quit()
                    return
                os.environ["GEMINI_API_KEY"] = key
                settings.set("gemini_api_key", key)
                from assistant.brain import Brain
                assistant.brain = Brain(settings)
                ui._brain_ref = assistant.brain
                ui._eval("document.getElementById('apikey-view').classList.remove('active'); document.getElementById('main-view').classList.remove('hidden');")
                ui.set_state("idle", "Say 'Hey Nova' or Ctrl+Shift+T")
                assistant.start_background_services()

            threading.Thread(target=_apikey_flow, daemon=True).start()
        else:
            assistant.start_background_services()
            if startup_mode or settings.get("start_minimized"):
                ui._window.hide()
            _run_command_action(command_action, ui, assistant)

    ui._on_webview_ready = _extended_ready

    try:
        ui.run()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            assistant.stop()
        except Exception:
            pass
        try:
            tray_icon.stop()
        except Exception:
            pass

    log.info("Nova stopped")


def _command_from_args(args):
    from urllib.parse import urlparse

    for arg in args:
        lower = arg.lower()
        if lower in ("--talk", "--activate"):
            return "talk"
        if lower in ("--type", "--chat"):
            return "type"
        if lower in ("--settings", "--preferences"):
            return "settings"
        if lower in ("--show", "--open"):
            return "show"
        if lower.startswith("nova://"):
            parsed = urlparse(arg)
            action = (parsed.netloc or parsed.path.strip("/")).lower()
            if action in {"talk", "activate", "type", "chat", "settings", "show", "open"}:
                return {"activate": "talk", "chat": "type", "open": "show"}.get(action, action)
    return ""


def _run_command_action(action, ui, assistant):
    if not action:
        return

    def _dispatch():
        if action == "show":
            ui.show()
        elif action == "talk":
            assistant._hotkey_activate()
        elif action == "type":
            assistant._hotkey_type_input()
        elif action == "settings":
            assistant._hotkey_settings()

    threading.Timer(0.5, _dispatch).start()


MAX_CONSECUTIVE_CRASHES = 3


def _read_crash_count():
    try:
        if os.path.exists(CRASH_COUNT_FILE):
            with open(CRASH_COUNT_FILE) as f:
                return int(f.read().strip())
    except Exception:
        pass
    return 0


def _write_crash_count(count):
    try:
        with open(CRASH_COUNT_FILE, "w") as f:
            f.write(str(count))
    except Exception:
        pass


def _clear_crash_count():
    try:
        if os.path.exists(CRASH_COUNT_FILE):
            os.remove(CRASH_COUNT_FILE)
    except Exception:
        pass


def _cleanup_stale_hotkeys():
    """Unregister any hotkeys that a previous crashed Nova instance left behind."""
    try:
        user32 = ctypes.windll.user32
        for hotkey_id in range(1, 20):
            try:
                user32.UnregisterHotKey(None, hotkey_id)
            except Exception:
                pass
    except Exception:
        pass


def _relaunch_after_crash():
    """Relaunch Nova after an unexpected crash, with crash count limiting."""
    crash_count = _read_crash_count() + 1
    _write_crash_count(crash_count)

    if crash_count > MAX_CONSECUTIVE_CRASHES:
        try:
            ctypes.windll.user32.MessageBoxW(
                0,
                f"Nova has crashed {crash_count} times in a row.\n"
                f"Check the error log at: {LOG_PATH}\n\n"
                "Please fix the issue before relaunching.",
                "Nova — Too Many Crashes", 0x30,
            )
        except Exception:
            pass
        _clear_crash_count()
        return

    # Clean up any stale hotkeys from previous instance
    _cleanup_stale_hotkeys()

    executable = os.path.abspath(sys.argv[0])
    args = [arg for arg in sys.argv[1:] if arg.lower() not in ("--startup", "--background")]
    args.append("--startup")
    try:
        subprocess.Popen([executable] + args, close_fds=True)
    except Exception:
        pass


def main():
    _write_pid()
    crash_count = _read_crash_count()

    # Register Windows integration features
    try:
        _register_windows_search()
    except Exception:
        pass
    try:
        _register_nova_hotkey()
    except Exception:
        pass

    try:
        args_set = {arg.lower() for arg in sys.argv[1:]}
        startup_mode = "--startup" in args_set or "--background" in args_set
        setup_complete = "--setup-complete" in args_set
        command_action = _command_from_args(sys.argv[1:])

        # Self-install to %LOCALAPPDATA%\Nova\ if frozen as exe
        try:
            from assistant.platform_integration import install_current_exe
            if install_current_exe(startup=True):
                return
        except Exception:
            pass

        run_nova(
            startup_mode=startup_mode,
            setup_complete=setup_complete,
            command_action=command_action,
        )

        # Successful exit — clear crash counter
        _clear_crash_count()
        _clean_pid()

    except Exception:
        err = traceback.format_exc()
        try:
            with open(LOG_PATH, "a") as f:
                f.write(f"\n{'='*60}\n{err}\n")
        except Exception:
            pass

        _clean_pid()

        if crash_count < MAX_CONSECUTIVE_CRASHES:
            # Auto-restart: relaunch after 2 seconds
            try:
                has_clr = False
                try:
                    import clr
                    has_clr = True
                except ImportError:
                    pass
                if not has_clr:
                    err_hint = (
                        "PythonNET (clr) is missing — this is required for pywebview on Windows.\n"
                        "Run: pip install pythonnet\n"
                        "If building with PyInstaller, ensure --collect-all pythonnet is used."
                    )
                else:
                    err_hint = err[:500]

                ctypes.windll.user32.MessageBoxW(
                    0,
                    f"Nova crashed and will restart.\n\nError log: {LOG_PATH}\n\n{err_hint}",
                    "Nova Restarting", 0x30,
                )
            except Exception:
                pass

            time.sleep(2)
            _relaunch_after_crash()
        else:
            try:
                ctypes.windll.user32.MessageBoxW(
                    0,
                    f"Nova has crashed {crash_count + 1} times. "
                    "Giving up.\n\nCheck the error log:\n" + LOG_PATH,
                    "Nova — Too Many Crashes", 0x10,
                )
            except Exception:
                pass
            _clear_crash_count()


if __name__ == "__main__":
    main()
