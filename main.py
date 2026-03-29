"""
Nova — A Windows voice assistant powered by Google Gemini.
Auto-restarts if it crashes. Only exits on explicit quit (Ctrl+Shift+Q).
"""

import sys
import os
import time
import traceback
import logging

LOG_PATH = os.path.join(os.path.expanduser("~"), "nova_error.log")
DEBUG_LOG = os.path.join(os.path.expanduser("~"), "nova_debug.log")
MAX_RESTARTS = 50  # Max restarts before giving up (resets on successful run)
RESTART_DELAY = 2  # Seconds between restarts


def run_nova():
    """Run Nova. Returns True if it should restart, False if it quit intentionally."""
    logging.basicConfig(
        filename=DEBUG_LOG,
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s: %(message)s",
        filemode="a",  # Append so we keep logs across restarts
    )
    log = logging.getLogger("nova")

    import config
    from assistant.settings import Settings

    settings = Settings()

    from assistant.ui import AssistantUI
    from assistant.core import Assistant
    from assistant.tray import run_tray

    ui = AssistantUI(settings)

    # Check if API key is set — also check settings directly (not just config cache)
    api_key = settings.get("gemini_api_key") or config.GEMINI_API_KEY
    if not api_key:
        ui._needs_apikey = True
    else:
        ui._needs_apikey = False

    assistant = Assistant(ui, settings)

    def on_tray_show():
        ui.show()

    def on_tray_quit():
        assistant.stop()
        ui.quit()

    tray_icon = run_tray(on_tray_show, on_tray_quit)

    # Override _on_webview_ready to handle API key setup + start services
    original_ready = ui._on_webview_ready

    def _extended_ready():
        original_ready()

        if ui._needs_apikey:
            def _apikey_flow():
                key = ui.show_apikey_setup()
                if not key:
                    ui.quit()
                    return
                # Update the env var and settings
                os.environ["GEMINI_API_KEY"] = key
                settings.set("gemini_api_key", key)
                # Re-init brain with new key
                from assistant.brain import Brain
                assistant.brain = Brain(settings)
                ui._brain_ref = assistant.brain
                # Switch back to main view
                ui._eval("document.getElementById('apikey-view').classList.remove('active'); document.getElementById('main-view').classList.remove('hidden');")
                ui.set_state("idle", "Say 'Hey Nova' or Ctrl+Shift+T")
                assistant.start_background_services()

            import threading
            threading.Thread(target=_apikey_flow, daemon=True).start()
        else:
            assistant.start_background_services()

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

    # If force_quit was set, the user explicitly quit — don't restart
    if ui._force_quit:
        log.info("User quit Nova — not restarting")
        return False

    log.info("Nova window closed unexpectedly — will restart")
    return True


def main():
    restart_count = 0
    last_success = time.time()

    while restart_count < MAX_RESTARTS:
        try:
            should_restart = run_nova()

            if not should_restart:
                # Clean exit — user explicitly quit
                return

            # If it ran for more than 30 seconds, reset the restart counter
            if time.time() - last_success > 30:
                restart_count = 0

            restart_count += 1
            last_success = time.time()

            logging.getLogger("nova").warning(
                "Restarting Nova (attempt %d/%d)...", restart_count, MAX_RESTARTS
            )
            time.sleep(RESTART_DELAY)

        except Exception:
            err = traceback.format_exc()
            try:
                with open(LOG_PATH, "a") as f:
                    f.write(f"\n{'='*60}\n{time.strftime('%Y-%m-%d %H:%M:%S')}\n{err}\n")
            except Exception:
                pass

            restart_count += 1
            if restart_count >= MAX_RESTARTS:
                try:
                    import ctypes
                    ctypes.windll.user32.MessageBoxW(
                        0,
                        f"Nova keeps crashing.\n\nError log: {LOG_PATH}\n\n{err[:500]}",
                        "Nova Error", 0x10,
                    )
                except Exception:
                    pass
                return

            time.sleep(RESTART_DELAY)


if __name__ == "__main__":
    main()
