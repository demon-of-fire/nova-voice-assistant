"""Confirmation dialog for dangerous actions — dark themed, NVDA accessible."""

import threading

DANGEROUS_ACTIONS = {
    "delete_file", "delete_folder",
    "write_file", "edit_file", "append_to_file", "move_file",
    "install_app", "uninstall_app",
    "run_command", "run_powershell",
    "kill_process",
    "shutdown_pc", "restart_pc",
    "run_python", "create_script",
}

_settings_ref = None

def set_settings(settings):
    """Store a reference to Settings so we can check confirm_actions."""
    global _settings_ref
    _settings_ref = settings

def needs_confirmation(action_name):
    """Return True if the action requires user confirmation before executing."""
    if _settings_ref and not _settings_ref.get("confirm_actions"):
        return False
    return action_name in DANGEROUS_ACTIONS


def ask_confirmation(action_description):
    """Show a topmost dark-themed confirmation dialog. Returns True if user confirms.

    Runs tkinter on a dedicated thread so it never blocks a non-main thread.
    """
    result = {"confirmed": False}
    event = threading.Event()

    def _show():
        try:
            import tkinter as tk

            root = tk.Tk()
            root.title("Nova — Confirm Action")
            root.configure(bg="#1e1e1e")
            root.attributes("-topmost", True)
            root.resizable(False, False)

            # Centre on screen
            w, h = 480, 220
            sx = root.winfo_screenwidth() // 2 - w // 2
            sy = root.winfo_screenheight() // 2 - h // 2
            root.geometry(f"{w}x{h}+{sx}+{sy}")

            # Make accessible — set role-like attributes NVDA can read
            root.option_add("*Font", "Segoe\\ UI 11")

            label_title = tk.Label(
                root, text="Confirmation Required",
                bg="#1e1e1e", fg="#ffffff", font=("Segoe UI", 14, "bold"),
            )
            label_title.pack(pady=(18, 6))

            label_desc = tk.Label(
                root, text=action_description, bg="#1e1e1e", fg="#cccccc",
                wraplength=440, justify="center", font=("Segoe UI", 10),
            )
            label_desc.pack(pady=(0, 18))

            btn_frame = tk.Frame(root, bg="#1e1e1e")
            btn_frame.pack(pady=(0, 12))

            def _confirm():
                result["confirmed"] = True
                root.destroy()

            def _cancel():
                root.destroy()

            btn_yes = tk.Button(
                btn_frame, text="Yes, do it", command=_confirm,
                bg="#d4380d", fg="#ffffff", activebackground="#e8541a",
                activeforeground="#ffffff", relief="flat", padx=20, pady=6,
                font=("Segoe UI", 10, "bold"), cursor="hand2",
            )
            btn_yes.pack(side="left", padx=8)

            btn_cancel = tk.Button(
                btn_frame, text="Cancel", command=_cancel,
                bg="#333333", fg="#ffffff", activebackground="#555555",
                activeforeground="#ffffff", relief="flat", padx=20, pady=6,
                font=("Segoe UI", 10), cursor="hand2",
            )
            btn_cancel.pack(side="left", padx=8)

            # Keyboard: Enter = confirm, Escape = cancel
            root.bind("<Return>", lambda e: _confirm())
            root.bind("<Escape>", lambda e: _cancel())

            # Focus the confirm button so NVDA reads it
            btn_yes.focus_set()

            root.protocol("WM_DELETE_WINDOW", _cancel)
            root.mainloop()
        except Exception:
            # If tkinter is unavailable, default to deny
            result["confirmed"] = False
        finally:
            event.set()

    t = threading.Thread(target=_show, daemon=True)
    t.start()
    event.wait(timeout=60)  # 60-second timeout
    return result["confirmed"]
