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
    """Fully NVDA-accessible API key entry dialog.

    Every piece of information is a focusable tk.Button with clear text
    that NVDA reads aloud when you Tab to it.  No tk.Label — those render
    as graphics and are invisible to screen readers.
    """
    import tkinter as tk

    BG = "#1a1a2e"
    FG = "#e0e0e0"
    ENTRY_BG = "#2a2a4e"

    got_key = {"value": ""}

    root = tk.Tk()
    root.title("Nova — First Time Setup")
    root.configure(bg=BG)
    root.attributes("-topmost", True)
    root.resizable(False, False)

    w, h = 560, 380
    sx = root.winfo_screenwidth() // 2 - w // 2
    sy = root.winfo_screenheight() // 2 - h // 2
    root.geometry(f"{w}x{h}+{sx}+{sy}")

    # --- NVDA announcement helper ---
    def _nvda_say(msg):
        try:
            from assistant.accessibility import announce
            announce(msg)
        except Exception:
            pass

    focus_order = []

    # Step 1: Tell the user what this is
    step1 = tk.Button(
        root, text="Step 1: You need a free Gemini API key to use Nova",
        font=("Segoe UI", 12, "bold"), takefocus=True,
        bg=BG, fg=FG, activebackground=BG, activeforeground=FG,
        bd=0, anchor="w", padx=16, pady=6)
    step1.pack(fill="x", pady=(20, 0))
    focus_order.append(step1)

    # Step 2: Where to get the key
    step2 = tk.Button(
        root, text="Step 2: Go to aistudio.google.com/apikey to get your free key",
        font=("Segoe UI", 11), takefocus=True,
        bg=BG, fg="#8888cc", activebackground=BG, activeforeground="#8888cc",
        bd=0, anchor="w", padx=16, pady=6)
    step2.pack(fill="x")
    focus_order.append(step2)

    # Step 3: Paste it here
    step3 = tk.Button(
        root, text="Step 3: Paste your API key in the text field below and press Enter",
        font=("Segoe UI", 11), takefocus=True,
        bg=BG, fg=FG, activebackground=BG, activeforeground=FG,
        bd=0, anchor="w", padx=16, pady=6)
    step3.pack(fill="x", pady=(0, 8))
    focus_order.append(step3)

    # API key text field
    key_entry = tk.Entry(root, font=("Segoe UI", 13), show="*", width=44,
                         bg=ENTRY_BG, fg=FG, insertbackground=FG, takefocus=True)
    key_entry.pack(padx=16, pady=(4, 20))
    key_entry.bind("<FocusIn>",
        lambda e: _nvda_say("API key text field. Paste or type your Gemini API key here, then press Enter."),
        add="+")
    focus_order.append(key_entry)

    def _ok():
        k = key_entry.get().strip()
        if k:
            got_key["value"] = k
            root.destroy()
        else:
            _nvda_say("The field is empty. Please paste your API key first.")
            key_entry.focus_set()

    def _cancel():
        root.destroy()

    # Save button — very clear label
    save_btn = tk.Button(
        root, text="Save API key and start Nova",
        font=("Segoe UI", 12, "bold"), takefocus=True,
        bg="#2e7d32", fg="white", activebackground="#388e3c",
        padx=20, pady=8, command=_ok)
    save_btn.pack(pady=(0, 6))
    save_btn.bind("<FocusIn>",
        lambda e: _nvda_say("Save API key and start Nova button."), add="+")
    focus_order.append(save_btn)

    # Cancel button — very clear label
    exit_btn = tk.Button(
        root, text="Exit without saving",
        font=("Segoe UI", 11), takefocus=True,
        bg="#3a2222", fg="#cc8888", activebackground="#5a3333",
        padx=16, pady=6, command=_cancel)
    exit_btn.pack(pady=(0, 12))
    exit_btn.bind("<FocusIn>",
        lambda e: _nvda_say("Exit without saving button."), add="+")
    focus_order.append(exit_btn)

    # Tab / Shift-Tab cycling
    for i, widget in enumerate(focus_order):
        nxt = focus_order[(i + 1) % len(focus_order)]
        prv = focus_order[(i - 1) % len(focus_order)]
        widget.bind("<Tab>", lambda e, w=nxt: (w.focus_set(), "break")[-1])
        widget.bind("<Shift-Tab>", lambda e, w=prv: (w.focus_set(), "break")[-1])

    root.bind("<Return>", lambda e: _ok())
    root.bind("<Escape>", lambda e: _cancel())
    root.protocol("WM_DELETE_WINDOW", _cancel)

    def _init_focus():
        step1.focus_set()
        _nvda_say("Nova first time setup. Use Tab to read each step. "
                  "You need a Gemini API key. Tab through for instructions.")

    root.after(300, _init_focus)
    root.mainloop()

    if got_key["value"]:
        settings.set("gemini_api_key", got_key["value"])
        os.environ["GEMINI_API_KEY"] = got_key["value"]


if __name__ == "__main__":
    main()
