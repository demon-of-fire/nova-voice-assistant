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
        import config
        from assistant.settings import Settings

        settings = Settings()

        if not config.GEMINI_API_KEY:
            # Show a GUI dialog instead of printing to console
            _ask_api_key(settings)
            # Reload config after key is set
            import importlib
            importlib.reload(config)
            if not config.GEMINI_API_KEY:
                sys.exit(1)

        from assistant.ui import AssistantUI
        from assistant.core import Assistant
        from assistant.tray import run_tray

        ui = AssistantUI(settings)
        assistant = Assistant(ui, settings)

        def on_tray_show():
            ui.root.after(0, ui.show)

        def on_tray_quit():
            assistant.stop()
            ui.root.after(0, ui.quit)

        tray_icon = run_tray(on_tray_show, on_tray_quit)
        assistant.start_background_services()

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


def _ask_api_key(settings):
    """Accessible dark-mode dialog to collect the Gemini API key.

    Uses only plain tk.Button, tk.Entry, tk.Label — NVDA reads these.
    """
    import tkinter as tk

    BG = "#1a1a2e"
    FG = "#e0e0e0"
    ENTRY_BG = "#2a2a4e"
    BTN_BG = "#3a3a5e"

    got_key = {"value": ""}

    root = tk.Tk()
    root.title("Nova Setup — Enter API Key")
    root.configure(bg=BG)
    root.attributes("-topmost", True)
    root.resizable(False, False)

    w, h = 500, 260
    sx = root.winfo_screenwidth() // 2 - w // 2
    sy = root.winfo_screenheight() // 2 - h // 2
    root.geometry(f"{w}x{h}+{sx}+{sy}")

    tk.Label(root, text="Nova needs a Gemini API key to work.",
             font=("Segoe UI", 13, "bold"), bg=BG, fg=FG).pack(pady=(20, 4))
    tk.Label(root, text="Get a free key at: aistudio.google.com/apikey",
             font=("Segoe UI", 10), bg=BG, fg="#8888bb").pack(pady=(0, 12))
    tk.Label(root, text="Enter your Gemini API key:",
             font=("Segoe UI", 10), bg=BG, fg=FG, anchor="w").pack(fill="x", padx=40)

    key_entry = tk.Entry(root, font=("Segoe UI", 12), show="*", width=40,
                         bg=ENTRY_BG, fg=FG, insertbackground=FG)
    key_entry.pack(padx=40, pady=(4, 16))

    btn_row = tk.Frame(root, bg=BG)
    btn_row.pack()

    def _ok():
        k = key_entry.get().strip()
        if k:
            got_key["value"] = k
            root.destroy()
        else:
            key_entry.focus_set()

    def _cancel():
        root.destroy()

    ok_btn = tk.Button(btn_row, text="OK", font=("Segoe UI", 11, "bold"),
                       bg="#2e7d32", fg="white", activebackground="#388e3c",
                       padx=24, pady=4, command=_ok)
    ok_btn.pack(side="left", padx=8)

    cancel_btn = tk.Button(btn_row, text="Cancel", font=("Segoe UI", 11),
                           bg=BTN_BG, fg=FG, activebackground="#4a4a6e",
                           padx=16, pady=4, command=_cancel)
    cancel_btn.pack(side="left", padx=8)

    # Tab order: entry -> OK -> Cancel -> entry
    key_entry.bind("<Tab>", lambda e: (ok_btn.focus_set(), "break")[-1])
    ok_btn.bind("<Tab>", lambda e: (cancel_btn.focus_set(), "break")[-1])
    cancel_btn.bind("<Tab>", lambda e: (key_entry.focus_set(), "break")[-1])
    cancel_btn.bind("<Shift-Tab>", lambda e: (ok_btn.focus_set(), "break")[-1])
    ok_btn.bind("<Shift-Tab>", lambda e: (key_entry.focus_set(), "break")[-1])
    key_entry.bind("<Shift-Tab>", lambda e: (cancel_btn.focus_set(), "break")[-1])

    root.bind("<Return>", lambda e: _ok())
    root.bind("<Escape>", lambda e: _cancel())
    root.protocol("WM_DELETE_WINDOW", _cancel)

    key_entry.focus_set()
    root.mainloop()

    if got_key["value"]:
        settings.set("gemini_api_key", got_key["value"])
        os.environ["GEMINI_API_KEY"] = got_key["value"]


if __name__ == "__main__":
    main()
