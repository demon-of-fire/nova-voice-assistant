"""
Nova — A Windows voice assistant powered by Google Gemini.
"""

import sys
import os
import traceback


def main():
    # Log errors to file so --windowed exe doesn't silently die
    log_path = os.path.join(os.path.expanduser("~"), "nova_error.log")

    try:
        # Set up logging to file so we can trace issues
        import logging
        logging.basicConfig(
            filename=os.path.join(os.path.expanduser("~"), "nova_debug.log"),
            level=logging.INFO,
            format="%(asctime)s %(name)s %(levelname)s: %(message)s",
            filemode="w",
        )

        import config
        from assistant.settings import Settings

        settings = Settings()

        from assistant.ui import AssistantUI
        from assistant.core import Assistant
        from assistant.tray import run_tray

        ui = AssistantUI(settings)

        if not config.GEMINI_API_KEY:
            # The API key view will be shown once the webview is ready.
            # We set a flag so _on_webview_ready triggers it.
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
                # Show API key view — blocks in a thread until user saves
                def _apikey_flow():
                    key = ui.show_apikey_setup()
                    if not key:
                        ui.quit()
                        return
                    # Reload config
                    import importlib
                    importlib.reload(config)
                    # Re-init brain with new key
                    assistant.brain = __import__("assistant.brain", fromlist=["Brain"]).Brain(settings)
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
            assistant.stop()
            tray_icon.stop()

    except Exception:
        err = traceback.format_exc()
        try:
            with open(log_path, "w") as f:
                f.write(err)
        except Exception:
            pass
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0, f"Nova crashed.\n\nError log saved to:\n{log_path}\n\n{err[:800]}",
                "Nova Error", 0x10
            )
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
