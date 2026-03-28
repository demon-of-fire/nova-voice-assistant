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
    Every interactive widget has a FocusIn announcement for screen readers.
    """
    import tkinter as tk

    BG = "#1a1a2e"
    FG = "#e0e0e0"
    ENTRY_BG = "#2a2a4e"
    BTN_BG = "#3a3a5e"

    got_key = {"value": ""}

    root = tk.Tk()
    root.title("Nova Setup — Enter Gemini API Key")
    root.configure(bg=BG)
    root.attributes("-topmost", True)
    root.resizable(False, False)

    w, h = 500, 280
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
                         bg=ENTRY_BG, fg=FG, insertbackground=FG, takefocus=True)
    key_entry.pack(padx=40, pady=(4, 16))

    btn_row = tk.Frame(root, bg=BG)
    btn_row.pack()

    def _ok():
        k = key_entry.get().strip()
        if k:
            got_key["value"] = k
            root.destroy()
        else:
            _nvda_say("No key entered. Please type your API key.")
            key_entry.focus_set()

    def _cancel():
        root.destroy()

    ok_btn = tk.Button(btn_row, text="OK — Save API key", font=("Segoe UI", 11, "bold"),
                       bg="#2e7d32", fg="white", activebackground="#388e3c",
                       padx=24, pady=4, command=_ok, takefocus=True)
    ok_btn.pack(side="left", padx=8)

    cancel_btn = tk.Button(btn_row, text="Cancel — Exit Nova", font=("Segoe UI", 11),
                           bg=BTN_BG, fg=FG, activebackground="#4a4a6e",
                           padx=16, pady=4, command=_cancel, takefocus=True)
    cancel_btn.pack(side="left", padx=8)

    # --- NVDA announcement helper ---
    def _nvda_say(msg):
        try:
            from assistant.accessibility import announce
            announce(msg)
        except Exception:
            pass

    # --- FocusIn announcements for NVDA ---
    key_entry.bind("<FocusIn>",
        lambda e: _nvda_say("API key entry field. Paste or type your Gemini API key here."), add="+")
    ok_btn.bind("<FocusIn>",
        lambda e: _nvda_say("OK button. Press Enter to save your API key and start Nova."), add="+")
    cancel_btn.bind("<FocusIn>",
        lambda e: _nvda_say("Cancel button. Press Enter to exit without saving."), add="+")

    # Tab order: entry -> OK -> Cancel -> entry
    focus_widgets = [key_entry, ok_btn, cancel_btn]
    for i, widget in enumerate(focus_widgets):
        nxt = focus_widgets[(i + 1) % len(focus_widgets)]
        prv = focus_widgets[(i - 1) % len(focus_widgets)]
        widget.bind("<Tab>", lambda e, w=nxt: (w.focus_set(), "break")[-1])
        widget.bind("<Shift-Tab>", lambda e, w=prv: (w.focus_set(), "break")[-1])

    root.bind("<Return>", lambda e: _ok())
    root.bind("<Escape>", lambda e: _cancel())
    root.protocol("WM_DELETE_WINDOW", _cancel)

    # Set initial focus and announce for NVDA
    def _init_focus():
        key_entry.focus_set()
        _nvda_say("Nova Setup. You need a Gemini API key to use Nova. "
                  "Get a free key at aistudio.google.com/apikey. "
                  "Tab to move between fields. Type your key and press Enter.")

    root.after(300, _init_focus)
    root.mainloop()

    if got_key["value"]:
        settings.set("gemini_api_key", got_key["value"])
        os.environ["GEMINI_API_KEY"] = got_key["value"]


if __name__ == "__main__":
    main()
