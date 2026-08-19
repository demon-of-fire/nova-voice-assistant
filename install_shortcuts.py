"""Create Windows entry points for Nova after setup or build."""

from assistant.settings import Settings
from assistant.windows_integration import (
    create_desktop_shortcut,
    create_start_menu_shortcut,
    set_start_with_windows,
)


def _ask_yes_no(prompt, default=False):
    suffix = "Y/n" if default else "y/N"
    answer = input(f"{prompt} [{suffix}]: ").strip().lower()
    if not answer:
        return default
    return answer in {"y", "yes"}


def main():
    settings = Settings()

    ok, message = create_desktop_shortcut()
    print(("Desktop shortcut ready." if ok else "Desktop shortcut failed.") + f" {message}")

    ok, message = create_start_menu_shortcut()
    print(("Start Menu shortcut ready." if ok else "Start Menu shortcut failed.") + f" {message}")

    start_with_windows = _ask_yes_no("Start Nova when Windows starts?", default=False)
    ok, message = set_start_with_windows(start_with_windows)
    print(("Startup setting saved." if ok else "Startup setting failed.") + f" {message}")

    if start_with_windows:
        settings.set("start_minimized", True)
        print("Nova will start minimized to the tray.")


if __name__ == "__main__":
    main()
