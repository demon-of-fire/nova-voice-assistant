"""Nova UI — fully NVDA accessible.

No menus (tkinter menus are broken with NVDA). Instead:
- Keyboard shortcuts for all actions
- Settings opens as a proper dialog with labeled widgets
- All buttons are real tk.Button with descriptive text
- Window title announces state changes
"""

import math
import threading
import tkinter as tk
import config
from assistant.accessibility import announce, announce_state


class AssistantUI:
    def __init__(self, settings):
        self._state = "idle"
        self._muted = False
        self._pulse_phase = 0.0
        self._status_text = "Ready. Ctrl+Shift+T to talk."
        self._response_text = ""
        self._expanded = False
        self._settings = settings
        self._orb_win = None

        # Callbacks (set by core)
        self.on_activate = None
        self.on_mute_toggle = None
        self._settings_win = None

        # -- Theme from settings --
        dark = self._settings.get("dark_mode")
        if dark is None:
            dark = True
        self._bg = "#1a1a2e" if dark else "#f0f0f0"
        self._fg = "#e0e0e0" if dark else "#1a1a1a"
        self._btn_bg = "#2a2a4e" if dark else "#d0d0d0"
        self._btn_fg = "#e0e0e0" if dark else "#1a1a1a"
        self._subtle_fg = "#555577" if dark else "#777799"

        # --- Window ---
        self.root = tk.Tk()
        self.root.title("Nova Voice Assistant — Ready")
        self.root.attributes("-topmost", True)
        self.root.configure(bg=self._bg)
        self.root.resizable(False, False)

        screen_w = self.root.winfo_screenwidth()
        x = (screen_w - config.PILL_WIDTH) // 2
        self.root.geometry(f"{config.PILL_WIDTH}x{config.PILL_HEIGHT}+{x}+30")
        self.root.minsize(config.PILL_WIDTH, config.PILL_HEIGHT)

        # --- Keyboard shortcuts ---
        self.root.bind("<F2>", lambda e: self._on_activate_key())
        self.root.bind("<F3>", lambda e: self._on_mute_click())
        self.root.bind("<F4>", lambda e: self._open_settings())
        self.root.bind("<Escape>", lambda e: self._minimize_to_tray())

        self.root.protocol("WM_DELETE_WINDOW", self._minimize_to_tray)

        # ===== MAIN FRAME =====
        self.frame = tk.Frame(self.root, bg=self._bg,
                              width=config.PILL_WIDTH, height=config.PILL_HEIGHT)
        self.frame.pack(fill="both", expand=True)
        self.frame.pack_propagate(False)
        self.frame.bind("<Button-1>", self._start_drag)
        self.frame.bind("<B1-Motion>", self._on_drag)

        # ===== TOP ROW =====
        self.top_row = tk.Frame(self.frame, bg=self._bg)
        self.top_row.pack(fill="x", padx=4, pady=4)

        # Orb (decorative, not focusable)
        self.canvas = tk.Canvas(
            self.top_row, width=46, height=46,
            bg=self._bg, highlightthickness=0, takefocus=False,
        )
        self.canvas.pack(side="left", padx=(2, 6))
        self.canvas.bind("<Button-1>", self._on_orb_click)

        # Text column (middle)
        text_col = tk.Frame(self.top_row, bg=self._bg)
        text_col.pack(side="left", fill="x", expand=True)

        self.status_label = tk.Label(
            text_col, text=self._status_text,
            font=("Segoe UI", 9, "bold"),
            bg=self._bg, fg=self._fg, anchor="w",
        )
        self.status_label.pack(anchor="w")

        self.name_label = tk.Label(
            text_col, text="F2:Talk  F3:Mute  F4:Settings",
            font=("Segoe UI", 7),
            bg=self._bg, fg=self._subtle_fg, anchor="w",
        )
        self.name_label.pack(anchor="w")

        # Buttons row — packed directly into frame (not nested) for NVDA
        btn_row = tk.Frame(self.frame, bg=self._bg)
        btn_row.pack(fill="x", padx=6, pady=(0, 4))

        # Talk button (F2)
        self.talk_btn = tk.Button(
            btn_row, text="Talk (F2)",
            font=("Segoe UI", 9), takefocus=True,
            bg="#2a4a2a", fg="#88cc88",
            activebackground="#3a5a3a", activeforeground="white",
            bd=0, padx=6, pady=3,
            command=lambda: self._on_activate_key(),
        )
        self.talk_btn.pack(side="left", padx=2)
        self.talk_btn.bind("<FocusIn>",
            lambda e: announce("Talk button. Press Enter or F2 to start listening."), add="+")

        # Mute button (F3)
        self.mute_btn = tk.Button(
            btn_row, text="Mic on (F3)",
            font=("Segoe UI", 9), takefocus=True,
            bg="#2a3a2a", fg="#88cc88",
            activebackground="#3a4a3a", activeforeground="white",
            bd=0, padx=6, pady=3,
            command=self._on_mute_click,
        )
        self.mute_btn.pack(side="left", padx=2)
        self.mute_btn.bind("<FocusIn>",
            lambda e: announce(f"{'Muted' if self._muted else 'Mic on'}. Press Enter or F3 to toggle."), add="+")

        # Settings button (F4)
        self.settings_btn = tk.Button(
            btn_row, text="Settings (F4)",
            font=("Segoe UI", 9), takefocus=True,
            bg=self._btn_bg, fg=self._btn_fg,
            activebackground="#3a3a5e", activeforeground="white",
            bd=0, padx=6, pady=3,
            command=self._open_settings,
        )
        self.settings_btn.pack(side="left", padx=2)
        self.settings_btn.bind("<FocusIn>",
            lambda e: announce("Settings button. Press Enter or F4 to open settings."), add="+")

        # Hide button (Esc)
        self.close_btn = tk.Button(
            btn_row, text="Hide (Esc)",
            font=("Segoe UI", 9), takefocus=True,
            bg="#3a2222", fg="#cc8888",
            activebackground="#5a3333", activeforeground="white",
            bd=0, padx=6, pady=3,
            command=self._minimize_to_tray,
        )
        self.close_btn.pack(side="left", padx=2)
        self.close_btn.bind("<FocusIn>",
            lambda e: announce("Hide button. Press Enter or Escape to minimize to tray."), add="+")

        # -- Tab loops: last -> first, first -> last --
        main_btns = [self.talk_btn, self.mute_btn, self.settings_btn, self.close_btn]
        for i, btn in enumerate(main_btns):
            nxt = main_btns[(i + 1) % len(main_btns)]
            prv = main_btns[(i - 1) % len(main_btns)]
            btn.bind("<Tab>", lambda e, w=nxt: (w.focus_set(), "break")[-1])
            btn.bind("<Shift-Tab>", lambda e, w=prv: (w.focus_set(), "break")[-1])

        # Give initial focus to the first button so NVDA finds it
        self.root.after(300, lambda: self.talk_btn.focus_set())

        # Response area (hidden until expanded)
        self.response_label = tk.Label(
            self.frame, text="",
            font=("Segoe UI", 10),
            bg=self._bg, fg=self._fg,
            anchor="nw", justify="left",
            wraplength=config.PILL_WIDTH - 30,
        )

        self._animate()

    def _open_settings(self):
        """Settings dialog — fully dark mode, NVDA accessible, plain tk.Button only."""
        try:
            if self._settings_win and self._settings_win.winfo_exists():
                self._settings_win.focus()
                return
        except Exception:
            self._settings_win = None

        # -- Theme colors based on dark/light mode ---
        dark = self._settings.get("dark_mode")
        if dark is None:
            dark = True
        BG = "#1a1a2e" if dark else "#f0f0f0"
        FG = "#e0e0e0" if dark else "#1a1a1a"
        BTN_BG = "#2a2a4e" if dark else "#d8d8d8"
        BTN_FG = "#e0e0e0" if dark else "#1a1a1a"
        BTN_ACTIVE_BG = "#3a3a5e" if dark else "#c0c0c0"
        ENTRY_BG = "#2a2a4e" if dark else "#ffffff"
        ENTRY_FG = "#e0e0e0" if dark else "#1a1a1a"
        HEADING_FG = "#8888cc" if dark else "#333399"
        SEL_FG = "#88ff88" if dark else "#006600"

        win = tk.Toplevel(self.root)
        win.title("Nova Settings")
        win.geometry("520x720")
        win.resizable(True, True)
        win.attributes("-topmost", True)
        win.configure(bg=BG)
        win.grab_set()
        self._settings_win = win

        main_frame = tk.Frame(win, bg=BG)
        main_frame.pack(fill="both", expand=True, padx=6, pady=6)

        def _on_close():
            self._settings_win = None
            win.grab_release()
            win.destroy()

        focus_order = []

        # -- Helpers -----------------------------------------------------------

        def _label(text):
            tk.Label(main_frame, text=text, font=("Segoe UI", 11, "bold"),
                     bg=BG, fg=HEADING_FG, anchor="w").pack(fill="x", padx=8, pady=(12, 2))

        def _toggle_btn(label_text, setting_key):
            state = "ON" if self._settings.get(setting_key) else "OFF"
            btn = tk.Button(main_frame, text=f"{label_text}: {state}",
                            font=("Segoe UI", 10), anchor="w", takefocus=True,
                            bg=BTN_BG, fg=BTN_FG, activebackground=BTN_ACTIVE_BG,
                            activeforeground=BTN_FG, bd=0, padx=8, pady=3)
            btn.pack(fill="x", padx=16, pady=1)

            def _on_click():
                new_val = not self._settings.get(setting_key)
                self._settings.set(setting_key, new_val)
                s = "ON" if new_val else "OFF"
                btn.configure(text=f"{label_text}: {s}")
                announce(f"{label_text}, {s}")

            btn.configure(command=_on_click)
            def _on_focus(event, txt=label_text, key=setting_key):
                s = "ON" if self._settings.get(key) else "OFF"
                announce(f"{txt}, {s}. Press Enter to toggle.")
            btn.bind("<FocusIn>", _on_focus, add="+")
            focus_order.append(btn)
            return btn

        def _choice_btn(parent, label_text, setting_key, value, group_btns):
            current = self._settings.get(setting_key)
            marker = "[selected] " if current == value else ""
            btn = tk.Button(parent, text=f"{marker}{label_text}",
                            font=("Segoe UI", 10), anchor="w", takefocus=True,
                            bg=BTN_BG, fg=SEL_FG if current == value else BTN_FG,
                            activebackground=BTN_ACTIVE_BG, activeforeground=BTN_FG,
                            bd=0, padx=8, pady=3)
            btn.pack(fill="x", padx=16, pady=1)
            group_btns.append((btn, label_text, value))

            def _on_click():
                self._settings.set(setting_key, value)
                for b, txt, val in group_btns:
                    m = "[selected] " if val == value else ""
                    b.configure(text=f"{m}{txt}",
                                fg=SEL_FG if val == value else BTN_FG)
                announce(f"{label_text}, selected")

            btn.configure(command=_on_click)
            def _on_focus(event, txt=label_text, key=setting_key, val=value):
                sel = "selected" if self._settings.get(key) == val else "not selected"
                announce(f"{txt}, {sel}. Press Enter to select.")
            btn.bind("<FocusIn>", _on_focus, add="+")
            focus_order.append(btn)
            return btn

        # == AI Backend ========================================================
        _label("AI Backend")
        ai_group = []
        _choice_btn(main_frame, "Auto mode, Gemini for actions, Ollama for chat",
                     "ai_mode", "auto", ai_group)
        _choice_btn(main_frame, "Gemini only, cloud AI, can do PC actions",
                     "ai_mode", "gemini_only", ai_group)
        _choice_btn(main_frame, "Ollama only, local AI, free, chat only",
                     "ai_mode", "ollama_only", ai_group)

        # -- Gemini model picker --
        _label("Gemini Model")
        gemini_models = [
            ("gemini-2.5-flash", "Gemini 2.5 Flash, fast and smart, recommended"),
            ("gemini-2.5-pro", "Gemini 2.5 Pro, smartest, best for complex tasks"),
            ("gemini-2.5-flash-lite", "Gemini 2.5 Flash Lite, fastest, lightweight"),
            ("gemini-3-flash-preview", "Gemini 3.0 Flash Preview, newest, experimental"),
            ("gemini-3-pro-preview", "Gemini 3.0 Pro Preview, newest, most capable"),
        ]
        gemini_group = []
        for mid, mdesc in gemini_models:
            _choice_btn(main_frame, mdesc, "gemini_model", mid, gemini_group)

        # -- Ollama model picker --
        _label("Ollama Model")
        ollama_models = []
        try:
            import urllib.request
            import json as _json
            req = urllib.request.Request("http://localhost:11434/api/tags")
            resp = urllib.request.urlopen(req, timeout=2)
            data = _json.loads(resp.read())
            ollama_models = [m["name"] for m in data.get("models", [])]
        except Exception:
            pass

        if ollama_models:
            ollama_group = []
            for m in ollama_models:
                short = m.split(":")[0]
                _choice_btn(main_frame, short, "ollama_model", short, ollama_group)
        else:
            # Show popular Ollama models as buttons + manual entry
            popular_ollama = [
                "llama3.2", "llama3.1", "llama3",
                "mistral", "mixtral", "phi3",
                "gemma2", "codellama", "deepseek-coder",
                "qwen2.5", "llava",
            ]
            ollama_group = []
            for m in popular_ollama:
                _choice_btn(main_frame, m, "ollama_model", m, ollama_group)

            # Also allow manual entry
            model_row = tk.Frame(main_frame, bg=BG)
            model_row.pack(fill="x", padx=16, pady=(4, 1))
            model_entry = tk.Entry(model_row, font=("Segoe UI", 10), width=20,
                                   bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=ENTRY_FG)
            model_entry.insert(0, self._settings.get("ollama_model") or "llama3.2")
            model_entry.pack(side="left", padx=(0, 4))
            def _on_model_focus(event):
                announce(f"Ollama model name, current value {model_entry.get()}. Type a name and Tab to Save.")
            model_entry.bind("<FocusIn>", _on_model_focus, add="+")
            focus_order.append(model_entry)

            def _save_model():
                val = model_entry.get().strip()
                self._settings.set("ollama_model", val)
                announce(f"Saved Ollama model as {val}")
            save_btn = tk.Button(model_row, text="Save model", font=("Segoe UI", 9),
                                 bg=BTN_BG, fg=BTN_FG, activebackground=BTN_ACTIVE_BG,
                                 bd=0, command=_save_model)
            save_btn.pack(side="left")
            save_btn.bind("<FocusIn>", lambda e: announce("Save model name button."), add="+")
            focus_order.append(save_btn)

        # -- Gemini API key --
        _label("Gemini API Key")
        current_key = self._settings.get("gemini_api_key") or config.GEMINI_API_KEY
        masked = "key saved" if current_key else "not set"
        key_row = tk.Frame(main_frame, bg=BG)
        key_row.pack(fill="x", padx=16, pady=(4, 1))
        key_entry = tk.Entry(key_row, show="*", font=("Segoe UI", 10), width=28,
                             bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=ENTRY_FG)
        key_entry.pack(side="left", padx=(0, 4))
        key_entry.bind("<FocusIn>",
                       lambda e: announce(f"Gemini API key field. Current: {masked}. Type your key."),
                       add="+")
        focus_order.append(key_entry)

        def _save_key():
            k = key_entry.get().strip()
            if k:
                self._settings.set("gemini_api_key", k)
                import os
                os.environ["GEMINI_API_KEY"] = k
                key_entry.delete(0, "end")
                announce("API key saved securely")
            else:
                announce("No key entered")
        save_key_btn = tk.Button(key_row, text="Save key", font=("Segoe UI", 9),
                                 bg=BTN_BG, fg=BTN_FG, activebackground=BTN_ACTIVE_BG,
                                 bd=0, command=_save_key)
        save_key_btn.pack(side="left")
        save_key_btn.bind("<FocusIn>", lambda e: announce("Save API key button."), add="+")
        focus_order.append(save_key_btn)

        # == Permissions =======================================================
        _label("Basic Permissions")
        for key, label in [
            ("allow_typing", "Allow typing in documents"),
            ("allow_keyboard_control", "Allow keyboard shortcuts and window control"),
            ("allow_app_launch", "Allow launching and closing apps"),
            ("allow_system_control", "Allow volume, brightness, shutdown, restart"),
            ("allow_web_search", "Allow web search and opening URLs"),
            ("allow_file_access", "Allow reading files and listing folders"),
            ("allow_process_control", "Allow listing and managing processes"),
            ("allow_network", "Allow network info, wifi scan, ping"),
        ]:
            _toggle_btn(label, key)

        _label("Advanced Permissions")
        for key, label in [
            ("allow_file_write", "Allow writing, editing, and moving files"),
            ("allow_file_delete", "Allow deleting files and folders"),
            ("allow_shell_commands", "Allow running shell commands"),
            ("allow_install_apps", "Allow installing and uninstalling apps"),
            ("allow_code_execution", "Allow running Python code"),
        ]:
            _toggle_btn(label, key)

        # == Voice =============================================================
        _label("Text to Speech Voice")
        try:
            from assistant.speaker import list_voices
            available_voices = list_voices()
        except Exception:
            available_voices = []

        if available_voices:
            voice_group = []
            for vid, vname in available_voices:
                _choice_btn(main_frame, vname, "tts_voice", vid, voice_group)

        # == Speech Speed ======================================================
        _label("Speech Speed")

        speed_btn_slower = tk.Button(main_frame, anchor="w", takefocus=True,
                                     font=("Segoe UI", 10), bg=BTN_BG, fg=BTN_FG,
                                     activebackground=BTN_ACTIVE_BG, bd=0, padx=8, pady=3)
        speed_btn_slower.pack(fill="x", padx=16, pady=1)
        speed_btn_faster = tk.Button(main_frame, anchor="w", takefocus=True,
                                     font=("Segoe UI", 10), bg=BTN_BG, fg=BTN_FG,
                                     activebackground=BTN_ACTIVE_BG, bd=0, padx=8, pady=3)
        speed_btn_faster.pack(fill="x", padx=16, pady=1)

        def _update_speed():
            r = self._settings.get("tts_rate") or 160
            speed_btn_slower.configure(text=f"Speed: {r} wpm. Press to slow down.")
            speed_btn_faster.configure(text=f"Speed: {r} wpm. Press to speed up.")
        _update_speed()

        def _slower():
            r = max(80, (self._settings.get("tts_rate") or 160) - 20)
            self._settings.set("tts_rate", r)
            _update_speed()
            announce(f"Speed {r}")
        def _faster():
            r = min(300, (self._settings.get("tts_rate") or 160) + 20)
            self._settings.set("tts_rate", r)
            _update_speed()
            announce(f"Speed {r}")

        speed_btn_slower.configure(command=_slower)
        speed_btn_faster.configure(command=_faster)
        speed_btn_slower.bind("<FocusIn>", lambda e: announce(
            f"Speech speed {self._settings.get('tts_rate')} words per minute. Enter to slow down."), add="+")
        speed_btn_faster.bind("<FocusIn>", lambda e: announce(
            f"Speech speed {self._settings.get('tts_rate')} words per minute. Enter to speed up."), add="+")
        focus_order.extend([speed_btn_slower, speed_btn_faster])

        # == Speech Recognition Engine =========================================
        _label("Speech Recognition Engine")
        try:
            from assistant.listener import get_available_stt_engines
            stt_engines = get_available_stt_engines()
        except Exception:
            stt_engines = [("google", "Google (online)", "Needs internet")]

        stt_group = []
        for eng_id, eng_name, eng_desc in stt_engines:
            if "not installed" not in eng_name:
                _choice_btn(main_frame, f"{eng_name}, {eng_desc}",
                            "stt_engine", eng_id, stt_group)

        # == General ===========================================================
        _label("General")
        _toggle_btn("Enable wake word, say Hey Nova to activate", "wake_word_enabled")
        _toggle_btn("Start minimized to system tray", "start_minimized")
        _toggle_btn("Ask for confirmation before dangerous actions", "confirm_actions")
        _toggle_btn("Follow-up mode, keep listening after each response", "follow_up_mode")

        # -- Dark/light mode toggle --
        _label("Appearance")

        def _toggle_theme():
            new_dark = not self._settings.get("dark_mode")
            self._settings.set("dark_mode", new_dark)
            announce(f"{'Dark' if new_dark else 'Light'} mode. Reopen settings to see change.")

        theme_state = "Dark mode" if dark else "Light mode"
        theme_btn = tk.Button(main_frame, text=f"Theme: {theme_state}. Press to switch.",
                              font=("Segoe UI", 10), anchor="w", takefocus=True,
                              bg=BTN_BG, fg=BTN_FG, activebackground=BTN_ACTIVE_BG,
                              bd=0, padx=8, pady=3, command=_toggle_theme)
        theme_btn.pack(fill="x", padx=16, pady=1)
        theme_btn.bind("<FocusIn>", lambda e: announce(
            f"Theme is {'dark mode' if self._settings.get('dark_mode') else 'light mode'}. Enter to switch."), add="+")
        focus_order.append(theme_btn)

        # -- Orb position --
        _label("Floating Orb Position")
        orb_positions = [
            ("bottom-right", "Bottom right"),
            ("bottom-left", "Bottom left"),
            ("top-right", "Top right"),
            ("top-left", "Top left"),
        ]
        orb_group = []
        for pos_val, pos_label in orb_positions:
            _choice_btn(main_frame, pos_label, "orb_position", pos_val, orb_group)

        # == Close =============================================================
        close_btn = tk.Button(main_frame, text="Close Settings",
                              font=("Segoe UI", 12, "bold"), bg="#2e7d32", fg="white",
                              activebackground="#388e3c", bd=0, padx=12, pady=6,
                              command=_on_close, takefocus=True)
        close_btn.pack(pady=(12, 8))
        close_btn.bind("<FocusIn>",
                       lambda e: announce("Close Settings button. Enter to close."), add="+")
        focus_order.append(close_btn)

        # -- Tab / Shift-Tab cycling -------------------------------------------
        for i, widget in enumerate(focus_order):
            nxt = focus_order[(i + 1) % len(focus_order)]
            prv = focus_order[(i - 1) % len(focus_order)]
            widget.bind("<Tab>", lambda e, w=nxt: (w.focus_set(), "break")[-1])
            widget.bind("<Shift-Tab>", lambda e, w=prv: (w.focus_set(), "break")[-1])

        win.protocol("WM_DELETE_WINDOW", _on_close)
        win.bind("<Escape>", lambda e: _on_close())

        def _init_focus():
            announce("Nova Settings. Tab to move between buttons. "
                     "Enter to toggle or select. Escape to close.")
            if focus_order:
                focus_order[0].focus_set()

        win.after(200, _init_focus)

    # --- State ---

    def set_state(self, state, status=None, response=None):
        self._state = state
        if status is not None:
            self._status_text = status
        if response is not None:
            self._response_text = response

        def _update():
            self.status_label.configure(text=self._status_text)

            titles = {
                "listening": "Nova — Listening",
                "thinking": "Nova — Processing",
                "speaking": "Nova — Speaking",
            }
            self.root.title(titles.get(state, "Nova Voice Assistant — Ready"))

            if state == "listening":
                announce_state("listening")
            elif state == "thinking" and response:
                announce_state("thinking", response)
            elif state == "speaking" and response:
                announce(response)

            if self._response_text and state in ("speaking", "idle") and response:
                self._expand(self._response_text)
            elif state == "idle" and not response:
                self._collapse()
            self._update_mute_btn()

        self.root.after(0, _update)

    def set_muted(self, muted):
        self._muted = muted
        self.root.after(0, self._update_mute_btn)
        announce_state("muted" if muted else "unmuted")

    def _update_mute_btn(self):
        if self._muted:
            self.mute_btn.configure(text="Muted (F3)", bg="#3a2222", fg="#cc6666")
        else:
            self.mute_btn.configure(text="Mic on (F3)", bg="#2a3a2a", fg="#88cc88")

    # --- Expand / Collapse ---

    def _expand(self, text):
        if not self._expanded:
            self._expanded = True
            x, y = self.root.winfo_x(), self.root.winfo_y()
            self.root.geometry(f"{config.PILL_WIDTH}x{config.PILL_EXPANDED_HEIGHT}+{x}+{y}")
            self.response_label.pack(fill="x", padx=16, pady=(0, 8))
        self.response_label.configure(text=text)
        self.root.after(8000, self._collapse)

    def _collapse(self):
        if self._expanded:
            self._expanded = False
            self.response_label.pack_forget()
            x, y = self.root.winfo_x(), self.root.winfo_y()
            self.root.geometry(f"{config.PILL_WIDTH}x{config.PILL_HEIGHT}+{x}+{y}")

    # --- Orb animation ---

    def _get_color(self):
        if self._muted:
            return config.ORB_COLOR_MUTED
        return {
            "idle": config.ORB_COLOR_IDLE,
            "listening": config.ORB_COLOR_LISTENING,
            "thinking": config.ORB_COLOR_THINKING,
            "speaking": config.ORB_COLOR_SPEAKING,
            "error": config.ORB_COLOR_ERROR,
        }.get(self._state, config.ORB_COLOR_IDLE)

    def _animate(self):
        self.canvas.delete("all")
        cx, cy = 23, 23
        color = self._get_color()
        self._pulse_phase += 0.1

        for i in range(3, 0, -1):
            pulse = math.sin(self._pulse_phase + i * 0.6) * 3
            if self._state == "listening":
                pulse *= 2
            elif self._state == "thinking":
                pulse = math.sin(self._pulse_phase * 2 + i) * 5
            r = 10 + i * 4 + pulse
            frac = i / 4.0
            r_c = int(int(color[1:3], 16) * (1 - frac) + 26 * frac)
            g_c = int(int(color[3:5], 16) * (1 - frac) + 26 * frac)
            b_c = int(int(color[5:7], 16) * (1 - frac) + 46 * frac)
            c = f"#{r_c:02x}{g_c:02x}{b_c:02x}"
            self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill=c, outline="")

        cr = 10 + math.sin(self._pulse_phase) * 2
        self.canvas.create_oval(cx-cr, cy-cr, cx+cr, cy+cr, fill=color, outline="")
        self.root.after(33, self._animate)

    # --- Drag ---

    def _start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_drag(self, event):
        x = self.root.winfo_x() + event.x - self._drag_x
        y = self.root.winfo_y() + event.y - self._drag_y
        w = config.PILL_WIDTH
        h = config.PILL_EXPANDED_HEIGHT if self._expanded else config.PILL_HEIGHT
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    # --- Events ---

    def _on_orb_click(self, event):
        if self.on_activate and self._state == "idle" and not self._muted:
            threading.Thread(target=self.on_activate, daemon=True).start()

    def _on_activate_key(self):
        if self.on_activate and self._state == "idle" and not self._muted:
            threading.Thread(target=self.on_activate, daemon=True).start()

    def _on_mute_click(self):
        if self.on_mute_toggle:
            self.on_mute_toggle()

    def _minimize_to_tray(self):
        self.root.withdraw()
        self._show_floating_orb()

    def _show_floating_orb(self):
        """Show a small floating orb button when the main window is hidden."""
        if self._orb_win:
            try:
                if self._orb_win.winfo_exists():
                    return
            except Exception:
                pass

        orb = tk.Toplevel(self.root)
        orb.overrideredirect(True)
        orb.attributes("-topmost", True)
        orb.configure(bg=self._bg)
        self._orb_win = orb

        size = 48
        pos = self._settings.get("orb_position") or "bottom-right"
        sw = orb.winfo_screenwidth()
        sh = orb.winfo_screenheight()
        margin = 16

        positions = {
            "bottom-right": (sw - size - margin, sh - size - margin - 40),
            "bottom-left": (margin, sh - size - margin - 40),
            "top-right": (sw - size - margin, margin),
            "top-left": (margin, margin),
        }
        ox, oy = positions.get(pos, positions["bottom-right"])
        orb.geometry(f"{size}x{size}+{ox}+{oy}")

        orb_canvas = tk.Canvas(orb, width=size, height=size,
                               bg=self._bg, highlightthickness=0)
        orb_canvas.pack()

        color = self._get_color()
        cx, cy = size // 2, size // 2
        r = 18
        orb_canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill=color, outline="")

        def _on_click(event):
            self._hide_floating_orb()
            self.show()
            if self.on_activate and not self._muted:
                import threading
                threading.Thread(target=self.on_activate, daemon=True).start()

        orb_canvas.bind("<Button-1>", _on_click)

        # Drag support for the floating orb
        def _orb_start_drag(event):
            orb._drag_x = event.x
            orb._drag_y = event.y
        def _orb_on_drag(event):
            x = orb.winfo_x() + event.x - orb._drag_x
            y = orb.winfo_y() + event.y - orb._drag_y
            orb.geometry(f"{size}x{size}+{x}+{y}")
        orb_canvas.bind("<Button-3>", _orb_start_drag)
        orb_canvas.bind("<B3-Motion>", _orb_on_drag)

    def _hide_floating_orb(self):
        if self._orb_win:
            try:
                self._orb_win.destroy()
            except Exception:
                pass
            self._orb_win = None

    def _quit_from_menu(self):
        self.root.quit()

    def show(self):
        self._hide_floating_orb()
        self.root.deiconify()
        self.root.lift()

    def quit(self):
        self.root.quit()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
