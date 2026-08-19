"""Core orchestrator — ties listener, brain, speaker, and UI together."""

import time
import threading
import keyboard
import config
from assistant.listener import Listener
from assistant.speaker import Speaker
from assistant.brain import Brain
from actions.confirmation import set_settings as set_confirm_settings
from actions.confirmation import set_ui as set_confirm_ui


class Assistant:
    def __init__(self, ui, settings):
        self.ui = ui
        self.settings = settings
        self.listener = Listener(settings)
        self.speaker = Speaker(settings)
        self.brain = Brain(settings)
        self._services_started = False
        self._wake_processor_started = False
        self._hotkey_handles = []
        self._native_hotkeys = None
        self._activate_lock = threading.Lock()
        self._stopping = False
        set_confirm_settings(settings)
        set_confirm_ui(ui)

        # Wire UI callbacks
        self.ui.on_activate = self.activate
        self.ui.on_mute_toggle = self.toggle_mute
        self.ui.on_setting_changed = self.on_setting_changed
        self.ui._process_text_cb = self._process
        self.ui._brain_ref = self.brain

    def _can_activate(self):
        """Check if Nova can accept input right now."""
        if self._stopping:
            return False
        if self.ui._muted:
            return False
        if self.ui._state != "idle":
            return False
        return True

    def activate(self):
        """Full interaction cycle: listen -> think -> respond -> maybe follow up."""
        if not self._can_activate():
            return
        if not self._activate_lock.acquire(blocking=False):
            return

        try:
            self.listener.set_mute(True)
            self.ui.set_state("listening", "Listening...")

            from assistant import sounds
            sounds.play_sync("activate")
            time.sleep(0.3)
            self.listener.quick_calibrate()

            self.listener.set_mute(False)
            text = self.listener.listen_once()
            self.listener.set_mute(self.ui._muted)

            if not text:
                sounds.play("not_understood")
                self.ui.set_state("idle", "Ready. Ctrl+Shift+T to talk.", None)
                return

            self._process(text)
        finally:
            self._activate_lock.release()

    def activate_silent(self):
        """Activate without voice prompt (for hotkey)."""
        if not self._can_activate():
            return
        if not self._activate_lock.acquire(blocking=False):
            return

        try:
            self.listener.set_mute(True)
            self.ui.show()
            self.ui.set_state("listening", "Listening...")

            from assistant import sounds
            sounds.play_sync("activate")
            time.sleep(0.3)
            self.listener.quick_calibrate()

            self.listener.set_mute(False)
            text = self.listener.listen_once()
            self.listener.set_mute(self.ui._muted)

            if not text:
                sounds.play("not_understood")
                self.ui.set_state("idle", "Ready. Ctrl+Shift+T to talk.", None)
                return

            self._process(text)
        finally:
            self._activate_lock.release()

    def _process(self, text):
        """Send text to brain, speak the response, then optionally follow up."""
        import logging
        log = logging.getLogger("nova")
        from assistant import sounds

        try:
            self.ui.set_state("thinking", "Thinking...", f'"{text}"')
            sounds.play("thinking")

            response = self.brain.process(text)
            log.info("Brain response: %s", response[:200] if response else "None")

            self.ui.set_state("speaking", config.ASSISTANT_NAME, response)

            self.listener.set_mute(True)
            self.speaker.say_sync(response)
            self.listener.set_mute(self.ui._muted)

            # Check if quit was requested
            from actions.system import is_quit_requested
            if is_quit_requested():
                log.info("Quit requested — shutting down")
                time.sleep(1)
                self.stop()
                self.ui.quit()
                return
        except Exception as e:
            log.error("_process crashed: %s", e, exc_info=True)
            try:
                self.ui.set_state("error", f"Error: {e}")
                time.sleep(3)
                self.ui.set_state("idle", "Say 'Hey Nova' or press Ctrl+Shift+T")
            except Exception:
                pass
            return

        try:
            # Follow-up mode: keep listening for more input
            if self.settings.get("follow_up_mode"):
                self._follow_up_loop()
            else:
                sounds.play("deactivate")
                self.ui.set_state("idle", "Say 'Hey Nova' or press Ctrl+Shift+T", None)
        except Exception as e:
            log.error("Follow-up crashed: %s", e, exc_info=True)
            try:
                self.ui.set_state("idle", "Say 'Hey Nova' or press Ctrl+Shift+T")
            except Exception:
                pass

    def _follow_up_loop(self):
        """After responding, listen for a follow-up with echo protection."""
        import logging
        log = logging.getLogger("nova")
        from assistant import sounds

        # Wait for TTS to finish playing before listening
        # This prevents the assistant from hearing its own voice
        wait_start = time.time()
        while self.speaker.busy and time.time() - wait_start < 10:
            time.sleep(0.2)

        self.ui.set_state("listening", "Listening for follow-up...")
        self.listener.set_mute(True)
        self.listener.quick_calibrate()

        self.listener.set_mute(False)
        text = self.listener.listen_once()
        self.listener.set_mute(self.ui._muted)

        if not text:
            sounds.play("not_understood")
            self.ui.set_state("idle", "Ready. Ctrl+Shift+T to talk.")
            return

        self._process(text)

    def toggle_mute(self):
        """Toggle mute state."""
        from assistant import sounds

        muted = self.listener.toggle_mute()
        self.ui.set_muted(muted)

        if muted:
            sounds.play("mute")
            status = "Muted — I can't hear anything"
        else:
            sounds.play("unmute")
            status = "Say 'Hey Nova' or press Ctrl+Shift+T"

        self.ui.set_state("idle", status)

    def start_background_services(self):
        """Start wake word listener and register global hotkeys."""
        from assistant import sounds
        import logging
        log = logging.getLogger("nova")

        if self._services_started:
            return
        self._services_started = True

        if self.settings.get("wake_word_enabled"):
            self.listener.start()
            log.info("Wake word listener started")

        def _wake_word_processor():
            consecutive_errors = 0
            while not self._stopping:
                try:
                    cmd = self.listener.command_queue.get(timeout=0.5)
                    consecutive_errors = 0
                except Exception:
                    consecutive_errors += 1
                    if consecutive_errors > 100:
                        log.error("Wake word processor stalled for 50+ seconds")
                        consecutive_errors = 0
                    continue

                if not self._can_activate():
                    continue

                try:
                    if cmd == "__ACTIVATE__":
                        self.activate_silent()
                    else:
                        self.ui.show()
                        sounds.play_sync("activate")
                        time.sleep(0.3)
                        self._process(cmd)
                except Exception as e:
                    log.error("Wake word processor error: %s", e, exc_info=True)

        if not self._wake_processor_started:
            threading.Thread(target=_wake_word_processor, daemon=True).start()
            self._wake_processor_started = True

        self._register_hotkeys()

    def _register_hotkeys(self):
        import logging
        log = logging.getLogger("nova")

        hotkeys = [
            (config.HOTKEY_PUSH_TO_TALK, self._hotkey_activate),
            (config.HOTKEY_MUTE_TOGGLE, self._hotkey_mute),
            (config.HOTKEY_SETTINGS, self._hotkey_settings),
            (config.HOTKEY_SCREEN_SHARE, self._hotkey_screen_share),
            (config.HOTKEY_TYPE_INPUT, self._hotkey_type_input),
            (config.HOTKEY_QUIT, self._hotkey_quit),
        ]

        try:
            from assistant.native_hotkeys import NativeHotkeyManager
            self._native_hotkeys = NativeHotkeyManager()
            for key, callback in hotkeys:
                self._native_hotkeys.add(key, callback)
            self._native_hotkeys.start()
            log.info("Native hotkey manager started")
            return
        except Exception as exc:
            log.error("Native hotkeys unavailable, falling back to keyboard hooks: %s", exc)

        for key, callback in hotkeys:
            try:
                handle = keyboard.add_hotkey(key, callback, suppress=False)
                self._hotkey_handles.append(handle)
                log.info("Registered hotkey: %s", key)
            except Exception as exc:
                log.error("Failed to register hotkey %s: %s", key, exc)

    def on_setting_changed(self, key, value):
        if key == "wake_word_enabled":
            if value:
                self.listener.start()
            else:
                self.listener.stop()

    def _hotkey_activate(self):
        if self.ui._state == "idle" and not self.ui._muted:
            threading.Thread(target=self.activate_silent, daemon=True).start()
        elif self.ui._state == "listening":
            self.listener.set_mute(self.ui._muted)
            self.ui.set_state("idle", "Say 'Hey Nova' or press Ctrl+Shift+T")

    def _hotkey_mute(self):
        threading.Thread(target=self.toggle_mute, daemon=True).start()

    def _hotkey_quit(self):
        self.stop()
        self.ui.quit()

    def _hotkey_type_input(self):
        if self.ui._state != "idle":
            return
        self.ui.show()
        self.ui.show_type_dialog()

    def _hotkey_settings(self):
        self.ui.show()
        self.ui._eval("showSettings();")

    def _hotkey_screen_share(self):
        """Toggle screen sharing via hotkey."""
        if self.settings.get("allow_screen_control"):
            self.brain.screen_sharing = not self.brain.screen_sharing
            state = "on" if self.brain.screen_sharing else "off"
            self.ui._eval(f"""
                var btn = document.getElementById('btn-screen');
                if (btn) {{
                    btn.textContent = '{("Screen ON" if self.brain.screen_sharing else "Screen")}';
                    btn.classList.{'add' if self.brain.screen_sharing else 'remove'}('active');
                }}
                announce('Screen sharing {state}');
            """)

    def stop(self):
        self._stopping = True
        self.listener.stop()
        self.speaker.stop()
        if self._native_hotkeys:
            self._native_hotkeys.stop()
            self._native_hotkeys = None
        for handle in self._hotkey_handles:
            try:
                keyboard.remove_hotkey(handle)
            except Exception:
                pass
        self._hotkey_handles.clear()
