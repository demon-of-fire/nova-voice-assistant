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
        set_confirm_settings(settings)
        set_confirm_ui(ui)

        # Wire UI callbacks
        self.ui.on_activate = self.activate
        self.ui.on_mute_toggle = self.toggle_mute
        self.ui._process_text_cb = self._process
        self.ui._brain_ref = self.brain

    def activate(self):
        """Full interaction cycle: listen -> think -> respond -> maybe follow up."""
        if self.ui._muted:
            return
        if self.ui._state != "idle":
            return

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
            # Didn't understand — play a gentle sound and go back to idle
            sounds.play("not_understood")
            self.ui.set_state("idle", "Ready. Ctrl+Shift+T to talk.")
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

        from assistant import sounds
        sounds.play_sync("activate")
        time.sleep(0.3)
        self.listener.quick_calibrate()

        self.listener.set_mute(False)
        text = self.listener.listen_once()
        self.listener.set_mute(self.ui._muted)

        if not text:
            # Didn't understand — play a gentle sound and go back to idle
            sounds.play("not_understood")
            self.ui.set_state("idle", "Ready. Ctrl+Shift+T to talk.")
            return

        self._process(text)

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
                self.ui.set_state("idle", "Say 'Hey Nova' or Ctrl+Shift+T")
            except Exception:
                pass
            return

        try:
            # Follow-up mode: keep listening for more input
            if self.settings.get("follow_up_mode"):
                self._follow_up_loop()
            else:
                sounds.play("deactivate")
                self.ui.set_state("idle", "Say 'Hey Nova' or Ctrl+Shift+T")
        except Exception as e:
            log.error("Follow-up crashed: %s", e, exc_info=True)
            try:
                self.ui.set_state("idle", "Say 'Hey Nova' or Ctrl+Shift+T")
            except Exception:
                pass

    def _follow_up_loop(self):
        """After responding, listen for a follow-up. If silence, go idle."""
        from assistant import sounds

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

        # Got follow-up — process it (which will loop back here)
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
            status = "Say 'Hey Nova' or Ctrl+Shift+T"

        self.ui.set_state("idle", status)

    def start_background_services(self):
        """Start wake word listener and register global hotkeys."""
        from assistant import sounds

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
        keyboard.add_hotkey(config.HOTKEY_SCREEN_SHARE, self._hotkey_screen_share)

    def _hotkey_activate(self):
        if self.ui._state == "idle" and not self.ui._muted:
            threading.Thread(target=self.activate_silent, daemon=True).start()
        elif self.ui._state == "listening":
            self.listener.set_mute(self.ui._muted)
            self.ui.set_state("idle", "Say 'Hey Nova' or Ctrl+Shift+T")

    def _hotkey_mute(self):
        threading.Thread(target=self.toggle_mute, daemon=True).start()

    def _hotkey_quit(self):
        self.stop()
        self.ui.quit()

    def _hotkey_type_input(self):
        if self.ui._state != "idle":
            return
        self.ui.show_type_dialog()

    def _hotkey_screen_share(self):
        """Toggle screen sharing via hotkey."""
        if self.settings.get("allow_screen_control"):
            self.brain.screen_sharing = not self.brain.screen_sharing
            state = "on" if self.brain.screen_sharing else "off"
            self.ui._eval(f"""
                var btn = document.getElementById('btn-screen');
                if (btn) {{
                    btn.textContent = '{("Screen ON (F5)" if self.brain.screen_sharing else "Screen (F5)")}';
                    btn.classList.{'add' if self.brain.screen_sharing else 'remove'}('active');
                }}
                announce('Screen sharing {state}');
            """)

    def stop(self):
        self.listener.stop()
        keyboard.unhook_all()
