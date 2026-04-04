"""Nova UI — pywebview + HTML/CSS for native NVDA accessibility.

All UI is rendered in a real browser engine (EdgeChromium/MSHTML) so
NVDA reads headings, buttons, inputs, and ARIA live regions natively.
Python ↔ JavaScript communication via pywebview's js_api bridge.
"""

import os
import threading
import webview
import config

_WEB_DIR = os.path.join(os.path.dirname(__file__), "web")


class Api:
    """Python API exposed to JavaScript via pywebview.api.*"""

    def __init__(self, ui):
        self._ui = ui

    # --- Main actions ---

    def activate(self):
        if self._ui.on_activate and self._ui._state == "idle" and not self._ui._muted:
            threading.Thread(target=self._ui.on_activate, daemon=True).start()

    def toggle_mute(self):
        if self._ui.on_mute_toggle:
            self._ui.on_mute_toggle()

    def minimize_to_tray(self):
        self._ui._window.hide()

    def resize_for_settings(self, opening):
        """Resize and reposition the window for settings (large, centered) or back to pill."""
        try:
            win = self._ui._window
            if opening:
                # Save current position/size so we can restore later
                self._ui._saved_x = win.x
                self._ui._saved_y = win.y
                self._ui._saved_w = win.width
                self._ui._saved_h = win.height
                # Get screen size — use a reasonable default
                sw, sh = 1920, 1080
                try:
                    import ctypes
                    user32 = ctypes.windll.user32
                    sw = user32.GetSystemMetrics(0)
                    sh = user32.GetSystemMetrics(1)
                except Exception:
                    pass
                w, h = 750, 560
                x = (sw - w) // 2
                y = (sh - h) // 2
                win.resize(w, h)
                win.move(x, y)
            else:
                # Restore to pill size and position
                w = getattr(self._ui, '_saved_w', config.PILL_WIDTH)
                h = getattr(self._ui, '_saved_h', config.PILL_HEIGHT)
                x = getattr(self._ui, '_saved_x', None)
                y = getattr(self._ui, '_saved_y', None)
                win.resize(w, h)
                if x is not None and y is not None:
                    win.move(x, y)
        except Exception:
            pass

    def process_text(self, text):
        """Called from the type-to-chat modal."""
        if self._ui._process_text_cb:
            threading.Thread(
                target=self._ui._process_text_cb, args=(text,), daemon=True
            ).start()

    # --- Settings ---

    def get_settings(self):
        return self._ui._settings.all()

    def set_setting(self, key, value):
        self._ui._settings.set(key, value)
        if key == "gemini_api_key":
            os.environ["GEMINI_API_KEY"] = value

    def toggle_setting(self, key):
        return self._ui._settings.toggle(key)

    def get_voices(self):
        try:
            from assistant.speaker import list_voices
            return list_voices()
        except Exception:
            return []

    def get_stt_engines(self):
        try:
            from assistant.listener import get_available_stt_engines
            engines = get_available_stt_engines()
            return [[eid, f"{en} — {ed}"] for eid, en, ed in engines
                    if "not installed" not in en]
        except Exception:
            return [["google", "Google (online) — Needs internet"]]

    # --- Screen sharing ---

    def toggle_screen_share(self):
        """Toggle screen sharing mode. Returns new state."""
        if not self._ui._settings.get("allow_screen_control"):
            from assistant.accessibility import announce
            try:
                announce("Screen control is disabled. Enable it in Settings, Permissions.")
            except Exception:
                pass
            return False
        brain = self._ui._brain_ref
        if brain:
            brain.screen_sharing = not brain.screen_sharing
            return brain.screen_sharing
        return False

    # --- Confirmation ---

    def confirm_response(self, confirmed):
        self._ui._confirm_result = confirmed
        self._ui._confirm_event.set()

    # --- API key setup ---

    def save_api_key(self, key):
        # Strip whitespace, quotes, and invisible characters
        key = key.strip().strip('"').strip("'").strip()
        if not key:
            return {"ok": False, "error": "Key is empty"}

        # Quick validation — try a simple Gemini API call
        try:
            from google import genai
            client = genai.Client(api_key=key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents="Say hi in one word.",
            )
            # If we get here, the key works
        except Exception as e:
            err = str(e).lower()
            if "api key" in err or "invalid" in err or "403" in err or "unauthorized" in err:
                return {"ok": False, "error": "Invalid API key. Check that you copied the full key."}
            # Other errors (network, quota) — key might still be valid, allow it
            pass

        self._ui._settings.set("gemini_api_key", key)
        os.environ["GEMINI_API_KEY"] = key
        self._ui._apikey_result = key
        self._ui._apikey_event.set()
        return {"ok": True}

    def exit_app(self):
        self._ui._apikey_result = ""
        self._ui._apikey_event.set()

    # --- Lifecycle ---

    def ui_ready(self):
        """Called by JS when pywebview bridge is ready."""
        self._ui._on_webview_ready()


class AssistantUI:
    def __init__(self, settings):
        self._state = "idle"
        self._muted = False
        self._settings = settings
        self._window = None
        self._ready_event = threading.Event()
        self._force_quit = False  # Only True when user explicitly quits

        # Callbacks (set by core.py)
        self.on_activate = None
        self.on_mute_toggle = None
        self._process_text_cb = None
        self._brain_ref = None  # Set by core.py for screen sharing toggle

        # Confirmation dialog state
        self._confirm_result = False
        self._confirm_event = threading.Event()

        # API key dialog state
        self._apikey_result = ""
        self._apikey_event = threading.Event()

        # Build the API bridge
        self._api = Api(self)

        # Create the webview window
        dark = self._settings.get("dark_mode")
        if dark is None:
            dark = True

        index_path = os.path.join(_WEB_DIR, "index.html")

        self._window = webview.create_window(
            "Nova Voice Assistant",
            url=index_path,
            js_api=self._api,
            width=config.PILL_WIDTH,
            height=config.PILL_HEIGHT,
            x=(1920 // 2 - config.PILL_WIDTH // 2),
            y=30,
            resizable=True,
            on_top=True,
            frameless=False,
            easy_drag=True,
            min_size=(320, 90),
        )

        # Intercept window close — hide instead of quit
        self._window.events.closing += self._on_closing

    def _on_closing(self):
        """Called when someone tries to close the window (X button, Alt+F4, etc).
        Returns False to PREVENT closing — hides the window instead.
        Only allows closing when _force_quit is True."""
        if self._force_quit:
            return True  # Allow the window to actually close
        # Hide instead of close
        try:
            self._window.hide()
        except Exception:
            pass
        return False  # Prevent the window from closing

    def _on_webview_ready(self):
        """Called when JS bridge is available."""
        dark = self._settings.get("dark_mode")
        if dark is not None and not dark:
            self._eval("document.body.classList.add('light');")
        self._ready_event.set()

    def _eval(self, js):
        """Evaluate JavaScript in the webview. Safe to call from any thread."""
        try:
            if self._window:
                self._window.evaluate_js(js)
        except Exception:
            pass

    # --- Public API (called by core.py) ---

    def set_state(self, state, status=None, response=None):
        self._state = state
        status_js = _js_str(status) if status else "null"
        response_js = _js_str(response) if response is not None else "null"
        self._eval(f"updateState({_js_str(state)}, {status_js}, {response_js});")

        # Resize window when showing response
        if response and state in ("speaking", "idle"):
            try:
                self._window.resize(config.PILL_WIDTH, config.PILL_EXPANDED_HEIGHT)
            except Exception:
                pass
        elif state == "idle" and response is None:
            try:
                self._window.resize(config.PILL_WIDTH, config.PILL_HEIGHT)
            except Exception:
                pass

    def set_muted(self, muted):
        self._muted = muted
        self._eval(f"updateMuted({'true' if muted else 'false'});")

    def show(self):
        try:
            self._window.show()
            self._window.on_top = True
        except Exception:
            pass

    def quit(self):
        """Actually destroy the window and exit. Only called on explicit quit."""
        self._force_quit = True
        try:
            self._window.destroy()
        except Exception:
            pass

    def run(self):
        """Start the webview event loop. Blocks until window is closed."""
        webview.start(debug=False)

    # --- Confirmation dialog (called from brain.py via confirmation.py) ---

    def ask_confirmation(self, description):
        """Show confirmation modal and block until user responds. Thread-safe."""
        self._confirm_result = False
        self._confirm_event.clear()
        # Bring window to front so the user can see the confirmation
        try:
            self._window.show()
            self._window.on_top = True
        except Exception:
            pass
        self._eval(f"showConfirmation({_js_str(description)});")
        # Wait up to 30 seconds for user response
        got_response = self._confirm_event.wait(timeout=30)
        if not got_response:
            # Timed out — dismiss the modal
            self._eval("hideConfirmation();")
            return False
        return self._confirm_result

    # --- Type-to-chat (called from core.py) ---

    def show_type_dialog(self):
        self._eval("showTypeChat();")

    # --- API key setup ---

    def show_apikey_setup(self):
        """Show the API key entry view. Blocks until user saves or cancels."""
        self._apikey_result = ""
        self._apikey_event.clear()
        self._eval("showApiKeyView();")
        self._apikey_event.wait()
        return self._apikey_result

    @property
    def root(self):
        """Compatibility shim — core.py uses root.after() for thread-safe calls.
        We replace this with a simple object that just runs functions directly."""
        return _RootCompat(self)


class _RootCompat:
    """Minimal compatibility layer so core.py's root.after(0, fn) still works."""

    def __init__(self, ui):
        self._ui = ui

    def after(self, ms, fn, *args):
        if ms == 0:
            threading.Thread(target=fn, args=args, daemon=True).start()
        else:
            def _delayed():
                import time
                time.sleep(ms / 1000.0)
                fn(*args)
            threading.Thread(target=_delayed, daemon=True).start()


def _js_str(s):
    """Escape a Python string for safe embedding in JavaScript."""
    if s is None:
        return "null"
    escaped = str(s).replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "")
    return f"'{escaped}'"
