"""Confirmation dialog for dangerous actions — dark themed, NVDA accessible.

All important text is in focusable tk.Button widgets so NVDA can read them.
"""

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
    All text is in focusable Buttons for NVDA screen reader support.
    """
    result = {"confirmed": False}
    event = threading.Event()

    def _show():
        try:
            import tkinter as tk

            def _nvda_say(msg):
                try:
                    from assistant.accessibility import announce
                    announce(msg)
                except Exception:
                    pass

            root = tk.Tk()
            root.title("Nova — Confirm Action")
            root.configure(bg="#1e1e1e")
            root.attributes("-topmost", True)
            root.resizable(False, False)

            w, h = 500, 260
            sx = root.winfo_screenwidth() // 2 - w // 2
            sy = root.winfo_screenheight() // 2 - h // 2
            root.geometry(f"{w}x{h}+{sx}+{sy}")

            # Title as focusable Button (NVDA reads button text)
            title_btn = tk.Button(
                root, text="Confirmation Required",
                bg="#1e1e1e", fg="#ffffff", font=("Segoe UI", 13, "bold"),
                activebackground="#1e1e1e", activeforeground="#ffffff",
                bd=0, takefocus=True, padx=12, pady=4,
            )
            title_btn.pack(fill="x", pady=(14, 4))

            # Description as focusable Button
            desc_btn = tk.Button(
                root, text=action_description,
                bg="#1e1e1e", fg="#cccccc", font=("Segoe UI", 10),
                activebackground="#1e1e1e", activeforeground="#cccccc",
                bd=0, takefocus=True, padx=12, pady=4,
                wraplength=460, anchor="w", justify="left",
            )
            desc_btn.pack(fill="x", pady=(0, 12))

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
                font=("Segoe UI", 10, "bold"), takefocus=True,
            )
            btn_yes.pack(side="left", padx=8)
            btn_yes.bind("<Return>", lambda e: btn_yes.invoke())
            btn_yes.bind("<FocusIn>",
                lambda e: _nvda_say("Yes do it button. Press Enter to confirm."), add="+")

            btn_cancel = tk.Button(
                btn_frame, text="Cancel", command=_cancel,
                bg="#333333", fg="#ffffff", activebackground="#555555",
                activeforeground="#ffffff", relief="flat", padx=20, pady=6,
                font=("Segoe UI", 10), takefocus=True,
            )
            btn_cancel.pack(side="left", padx=8)
            btn_cancel.bind("<Return>", lambda e: btn_cancel.invoke())
            btn_cancel.bind("<FocusIn>",
                lambda e: _nvda_say("Cancel button. Press Enter to cancel."), add="+")

            # Tab cycling
            focus_widgets = [title_btn, desc_btn, btn_yes, btn_cancel]
            for i, widget in enumerate(focus_widgets):
                nxt = focus_widgets[(i + 1) % len(focus_widgets)]
                prv = focus_widgets[(i - 1) % len(focus_widgets)]
                widget.bind("<Tab>", lambda e, w=nxt: (w.focus_set(), "break")[-1])
                widget.bind("<Shift-Tab>", lambda e, w=prv: (w.focus_set(), "break")[-1])

            root.bind("<Return>", lambda e: _confirm())
            root.bind("<Escape>", lambda e: _cancel())
            root.protocol("WM_DELETE_WINDOW", _cancel)

            def _init():
                title_btn.focus_set()
                _nvda_say(f"Confirmation required. {action_description}. "
                          "Press Enter to confirm, Escape to cancel.")

            root.after(200, _init)
            root.mainloop()
        except Exception:
            result["confirmed"] = False
        finally:
            event.set()

    t = threading.Thread(target=_show, daemon=True)
    t.start()
    event.wait(timeout=60)
    return result["confirmed"]
