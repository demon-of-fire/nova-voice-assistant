"""Core orchestrator — ties listener, brain, speaker, and UI together."""

import time
import threading
import keyboard
import config
from assistant.listener import Listener
from assistant.speaker import Speaker
from assistant.brain import Brain
from assistant import sounds
from actions.confirmation import set_settings as set_confirm_settings


class Assistant:
    def __init__(self, ui, settings):
        self.ui = ui
        self.settings = settings
        self.listener = Listener(settings)
        self.speaker = Speaker(settings)
        self.brain = Brain(settings)
        set_confirm_settings(settings)

        # Wire UI callbacks
        self.ui.on_activate = self.activate
        self.ui.on_mute_toggle = self.toggle_mute

    def activate(self):
        """Full interaction cycle: listen -> think -> respond -> maybe follow up."""
        if self.ui._muted:
            return
        if self.ui._state != "idle":
            return

        self.listener.set_mute(True)
        self.ui.set_state("listening", "Listening...")
        sounds.play_sync("activate")
        time.sleep(0.3)
        self.listener.quick_calibrate()

        self.listener.set_mute(False)
        text = self.listener.listen_once()
        self.listener.set_mute(self.ui._muted)

        if not text:
            err = self.listener.last_error
            if err and err not in ("no_speech", "not_understood"):
                self.ui.set_state("error", err)
                time.sleep(3)
            sounds.play("deactivate")
            self.ui.set_state("idle", "Say 'Hey Nova' or Ctrl+Shift+T")
            return

        self._process(text)

    def activate_silent(self):
        """Activate without voice prompt (for hotkey)."""
        if self.ui._muted:
            return
        if self.ui._state != "idle":
            return

        self.listener.set_mute(True)
        self.ui.show()
        self.ui.set_state("listening", "Listening...")
        sounds.play_sync("activate")
        time.sleep(0.3)
        self.listener.quick_calibrate()

        self.listener.set_mute(False)
        text = self.listener.listen_once()
        self.listener.set_mute(self.ui._muted)

        if not text:
            err = self.listener.last_error
            if err and err not in ("no_speech", "not_understood"):
                self.ui.set_state("error", err)
                time.sleep(3)
            sounds.play("deactivate")
            self.ui.set_state("idle", "Say 'Hey Nova' or Ctrl+Shift+T")
            return

        self._process(text)

    def _process(self, text):
        """Send text to brain, speak the response, then optionally follow up."""
        self.ui.set_state("thinking", "Thinking...", f'"{text}"')
        sounds.play("thinking")

        response = self.brain.process(text)

        self.ui.set_state("speaking", config.ASSISTANT_NAME, response)

        self.listener.set_mute(True)
        self.speaker.say_sync(response)
        self.listener.set_mute(self.ui._muted)

        # Follow-up mode: keep listening for more input
        if self.settings.get("follow_up_mode"):
            self._follow_up_loop()
        else:
            sounds.play("deactivate")
            self.ui.set_state("idle", "Say 'Hey Nova' or Ctrl+Shift+T")

    def _follow_up_loop(self):
        """After responding, listen for a follow-up. If silence, go idle."""
        self.ui.set_state("listening", "Listening for follow-up...")
        self.listener.set_mute(True)
        self.listener.quick_calibrate()

        self.listener.set_mute(False)
        text = self.listener.listen_once()
        self.listener.set_mute(self.ui._muted)

        if not text:
            sounds.play("deactivate")
            self.ui.set_state("idle", "Say 'Hey Nova' or Ctrl+Shift+T")
            return

        # Got follow-up — process it (which will loop back here)
        self._process(text)

    def toggle_mute(self):
        """Toggle mute state."""
        muted = self.listener.toggle_mute()
        self.ui.set_muted(muted)

        if muted:
            sounds.play("mute")
            status = "Muted — I can't hear anything"
        else:
            sounds.play("unmute")
            status = "Say 'Hey Nova' or Ctrl+Shift+T"

        self.ui.set_state("idle", status)

    def start_background_services(self):
        """Start wake word listener and register global hotkeys."""
        if self.settings.get("wake_word_enabled"):
            self.listener.start()

        def _wake_word_processor():
            while True:
                try:
                    cmd = self.listener.command_queue.get(timeout=0.5)
                except Exception:
                    continue

                if self.ui._state != "idle":
                    continue

                if cmd == "__ACTIVATE__":
                    self.activate()
                else:
                    sounds.play_sync("activate")
                    time.sleep(0.3)
                    self._process(cmd)

        threading.Thread(target=_wake_word_processor, daemon=True).start()

        keyboard.add_hotkey(config.HOTKEY_PUSH_TO_TALK, self._hotkey_activate)
        keyboard.add_hotkey(config.HOTKEY_MUTE_TOGGLE, self._hotkey_mute)
        keyboard.add_hotkey(config.HOTKEY_QUIT, self._hotkey_quit)
        keyboard.add_hotkey(config.HOTKEY_TYPE_INPUT, self._hotkey_type_input)

    def _hotkey_activate(self):
        if self.ui._state == "idle" and not self.ui._muted:
            threading.Thread(target=self.activate_silent, daemon=True).start()
        elif self.ui._state == "listening":
            self.listener.set_mute(self.ui._muted)
            self.ui.set_state("idle", "Say 'Hey Nova' or Ctrl+Shift+T")

    def _hotkey_mute(self):
        self.ui.root.after(0, self.toggle_mute)

    def _hotkey_quit(self):
        self.stop()
        self.ui.root.after(0, self.ui.quit)

    def _hotkey_type_input(self):
        if self.ui._state != "idle":
            return
        self.ui.root.after(0, self._show_type_dialog)

    def _show_type_dialog(self):
        """Show a text input dialog so the user can type a message to Nova.
        Fully NVDA accessible — all widgets labeled and keyboard navigable."""
        import tkinter as tk
        from assistant.accessibility import announce

        dark = self.settings.get("dark_mode")
        if dark is None:
            dark = True
        BG = "#1a1a2e" if dark else "#f0f0f0"
        FG = "#e0e0e0" if dark else "#1a1a1a"
        ENTRY_BG = "#2a2a4e" if dark else "#ffffff"
        BTN_BG = "#2a2a4e" if dark else "#d0d0d0"

        win = tk.Toplevel(self.ui.root)
        win.title("Type a message to Nova")
        win.attributes("-topmost", True)
        win.configure(bg=BG)
        win.resizable(False, False)

        w, h = 500, 160
        sx = win.winfo_screenwidth() // 2 - w // 2
        sy = win.winfo_screenheight() // 2 - h // 2
        win.geometry(f"{w}x{h}+{sx}+{sy}")

        # Use a Button for the instruction so NVDA can read it
        info_btn = tk.Button(win, text="Type your message below and press Enter to send",
                             font=("Segoe UI", 10), bg=BG, fg=FG,
                             activebackground=BG, activeforeground=FG,
                             bd=0, takefocus=True, anchor="w", padx=16, pady=4)
        info_btn.pack(fill="x", pady=(8, 2))

        entry = tk.Entry(win, font=("Segoe UI", 12), width=50,
                         bg=ENTRY_BG, fg=FG, insertbackground=FG, takefocus=True)
        entry.pack(padx=16, pady=(0, 8))
        entry.bind("<FocusIn>",
            lambda e: announce("Message field. Type your message and press Enter."), add="+")

        btn_row = tk.Frame(win, bg=BG)
        btn_row.pack()

        def _send():
            text = entry.get().strip()
            if text:
                win.destroy()
                threading.Thread(target=self._process, args=(text,), daemon=True).start()
            else:
                announce("Please type a message first.")
                entry.focus_set()

        def _cancel():
            win.destroy()

        send_btn = tk.Button(btn_row, text="Send message", font=("Segoe UI", 10, "bold"),
                             bg="#2e7d32", fg="white", activebackground="#388e3c",
                             padx=16, pady=3, command=_send, takefocus=True)
        send_btn.pack(side="left", padx=6)
        send_btn.bind("<Return>", lambda e: send_btn.invoke())
        send_btn.bind("<FocusIn>",
            lambda e: announce("Send message button. Press Enter to send."), add="+")

        cancel_btn = tk.Button(btn_row, text="Cancel", font=("Segoe UI", 10),
                               bg=BTN_BG, fg=FG, activebackground="#3a3a5e",
                               padx=12, pady=3, command=_cancel, takefocus=True)
        cancel_btn.pack(side="left", padx=6)
        cancel_btn.bind("<Return>", lambda e: cancel_btn.invoke())
        cancel_btn.bind("<FocusIn>",
            lambda e: announce("Cancel button. Press Enter to close."), add="+")

        focus_widgets = [info_btn, entry, send_btn, cancel_btn]
        for i, widget in enumerate(focus_widgets):
            nxt = focus_widgets[(i + 1) % len(focus_widgets)]
            prv = focus_widgets[(i - 1) % len(focus_widgets)]
            widget.bind("<Tab>", lambda e, w=nxt: (w.focus_set(), "break")[-1])
            widget.bind("<Shift-Tab>", lambda e, w=prv: (w.focus_set(), "break")[-1])

        win.bind("<Return>", lambda e: _send())
        win.bind("<Escape>", lambda e: _cancel())
        win.protocol("WM_DELETE_WINDOW", _cancel)

        def _init():
            entry.focus_set()
            announce("Type your message to Nova. Press Enter to send, Escape to cancel.")

        win.after(200, _init)

    def stop(self):
        self.listener.stop()
        keyboard.unhook_all()
