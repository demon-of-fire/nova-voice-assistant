"""Speech recognition with wake word detection, mute support, and engine selection.

Supported engines:
- google: Google Speech API (online, free, accurate, needs internet)
- sphinx: CMU Sphinx (offline, lightweight, less accurate)
- whisper: OpenAI Whisper via whisper library (offline, accurate, needs GPU for speed)
"""

import logging
import threading
import queue
import speech_recognition as sr
import config

log = logging.getLogger("nova")


def get_available_stt_engines():
    """Return list of (id, name, description) for available STT engines."""
    engines = [
        ("google", "Google (online)", "Free, accurate, requires internet — best for most users"),
    ]

    # Check if pocketsphinx is installed
    try:
        import pocketsphinx  # noqa: F401
        engines.append(("sphinx", "Sphinx (offline)", "Lightweight, works without internet — lower accuracy"))
    except ImportError:
        engines.append(("sphinx", "Sphinx (offline) — not installed", "Install: pip install pocketsphinx"))

    # Check if whisper is installed
    try:
        import whisper  # noqa: F401
        engines.append(("whisper", "Whisper (offline)", "Very accurate, needs decent GPU — large download first time"))
    except ImportError:
        engines.append(("whisper", "Whisper (offline) — not installed", "Install: pip install openai-whisper"))

    return engines


class Listener:
    def __init__(self, settings=None):
        self.recognizer = sr.Recognizer()

        # Pause detection: how long of silence = "they stopped talking"
        self.recognizer.pause_threshold = config.PAUSE_THRESHOLD
        self.recognizer.non_speaking_duration = config.NON_SPEAKING_DURATION
        self.recognizer.operation_timeout = 15  # safety: max seconds for API call

        # Dynamic threshold adapts to ambient noise in real time
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.dynamic_energy_ratio = 1.5
        self.recognizer.energy_threshold = config.ENERGY_THRESHOLD

        self.mic = sr.Microphone()
        self._mic_index = None  # default mic
        self.command_queue = queue.Queue()

        self._running = False
        self._muted = False
        self._thread = None
        self._settings = settings
        self._whisper_model = None
        self.last_error = None  # last error message for UI to show

        # Initial calibration against room noise
        try:
            with self.mic as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
        except Exception:
            pass

    def quick_calibrate(self):
        """Quick re-calibrate before listening for a command.
        Call this AFTER playing sounds to reset the mic baseline."""
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
        except Exception:
            pass

    @property
    def stt_engine(self):
        if self._settings:
            return self._settings.get("stt_engine") or "google"
        return "google"

    @property
    def is_muted(self):
        return self._muted

    def toggle_mute(self):
        """Toggle mute on/off. Returns new mute state."""
        self._muted = not self._muted
        return self._muted

    def set_mute(self, muted):
        self._muted = muted

    def start(self):
        """Start continuous background listening for the wake word."""
        if self._running and self._thread and self._thread.is_alive():
            return
        self._running = True
        self._startup_time = __import__("time").time()
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _recognize(self, audio):
        """Recognize audio using the selected engine."""
        engine = self.stt_engine

        if engine == "sphinx":
            try:
                return self.recognizer.recognize_sphinx(audio)
            except sr.UnknownValueError:
                return None
            except Exception:
                return self.recognizer.recognize_google(audio)

        elif engine == "whisper":
            try:
                if self._whisper_model is None:
                    import whisper
                    self._whisper_model = whisper.load_model("base")

                import tempfile
                import os
                wav_data = audio.get_wav_data()
                tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                tmp.write(wav_data)
                tmp.close()
                try:
                    result = self._whisper_model.transcribe(tmp.name, fp16=False)
                    return result["text"].strip()
                finally:
                    os.unlink(tmp.name)
            except ImportError:
                return self.recognizer.recognize_google(audio)
            except Exception:
                return self.recognizer.recognize_google(audio)

        else:  # google (default)
            return self.recognizer.recognize_google(audio)

    def listen_once(self):
        """Listen for a single command (after wake word / hotkey activation).
        Returns recognized text or None.

        Uses a FRESH Microphone instance so it never conflicts with the
        background wake-word listener thread, and a hard timeout thread
        so listen() can NEVER hang forever."""
        result = [None]
        self.last_error = None

        def _do_listen():
            try:
                # Fresh mic instance — avoids conflict with background thread
                mic = sr.Microphone()
                with mic as source:
                    audio = self.recognizer.listen(
                        source,
                        timeout=config.LISTEN_TIMEOUT,
                        phrase_time_limit=config.PHRASE_TIME_LIMIT,
                    )
                text = self._recognize(audio)
                result[0] = text.strip() if text else None
            except sr.WaitTimeoutError:
                self.last_error = "no_speech"
            except sr.UnknownValueError:
                self.last_error = "not_understood"
            except sr.RequestError as e:
                self.last_error = f"Speech service error: {e}"
                log.error("STT RequestError: %s", e)
            except Exception as e:
                self.last_error = f"Microphone error: {e}"
                log.error("Listen error: %s", e)

        # Hard timeout: LISTEN_TIMEOUT (wait for speech to start) +
        # PHRASE_TIME_LIMIT (max recording) + 5s buffer for recognition
        hard_timeout = config.LISTEN_TIMEOUT + config.PHRASE_TIME_LIMIT + 5

        t = threading.Thread(target=_do_listen, daemon=True)
        t.start()
        t.join(timeout=hard_timeout)

        if t.is_alive():
            self.last_error = "Listening timed out"
            return None

        return result[0]

    def _listen_loop(self):
        """Background loop: listen for wake word, then put command on queue.

        Uses a dedicated recognizer + fresh mic each cycle so it never
        conflicts with listen_once().  Accepts common misheard variants
        of 'hey nova' so detection is more forgiving.
        """
        import time

        # Separate recognizer tuned for short wake word phrases
        wake_rec = sr.Recognizer()
        wake_rec.dynamic_energy_threshold = True
        wake_rec.dynamic_energy_adjustment_damping = 0.15
        wake_rec.dynamic_energy_ratio = 1.5
        wake_rec.energy_threshold = config.ENERGY_THRESHOLD
        wake_rec.pause_threshold = 0.6       # shorter pause for wake word
        wake_rec.non_speaking_duration = 0.4

        # Common ways Google STT transcribes "hey nova"
        wake_variants = {
            "hey nova", "hey nora", "hey novo", "a nova",
            "hay nova", "he nova", "hey novah", "hey nava",
            "hey novar", "hey noba", "hey nova.",
        }
        # Also match just "nova" if said clearly on its own
        wake_single = {"nova", "nora", "novo"}

        # Grace period to avoid startup noise
        while self._running and (time.time() - self._startup_time) < 3:
            time.sleep(0.3)

        while self._running:
            if self._muted:
                time.sleep(0.3)
                continue

            try:
                mic = sr.Microphone()
                with mic as source:
                    # Short timeout + phrase limit — wake word is ~1 second
                    audio = wake_rec.listen(source, timeout=2, phrase_time_limit=4)
                text = self._recognize_wake(wake_rec, audio)
                if not text:
                    continue
                text = text.lower().strip()
            except (sr.WaitTimeoutError, sr.UnknownValueError):
                continue
            except sr.RequestError:
                time.sleep(2)
                continue
            except Exception:
                time.sleep(0.5)
                continue

            # Check for wake word (exact or fuzzy match)
            wake = config.WAKE_WORD.lower()
            matched = False
            match_pos = -1

            # Exact match first
            if wake in text:
                matched = True
                match_pos = text.find(wake) + len(wake)
            else:
                # Check phrase variants like "hey nora", "a nova"
                for variant in wake_variants:
                    if variant in text:
                        matched = True
                        match_pos = text.find(variant) + len(variant)
                        break

            # Also match just "nova" said on its own (short utterance)
            if not matched:
                words = text.split()
                if len(words) <= 3:
                    for w in wake_single:
                        if w in words:
                            matched = True
                            idx = words.index(w)
                            remainder_words = words[idx+1:]
                            match_pos = len(text) - len(" ".join(remainder_words)) if remainder_words else len(text)
                            break

            if matched:
                remainder = text[match_pos:].strip() if match_pos >= 0 else ""

                if remainder and len(remainder) > 3:
                    self.command_queue.put(remainder)
                else:
                    self.command_queue.put("__ACTIVATE__")

    def _recognize_wake(self, rec, audio):
        """Recognize audio for wake word detection. Uses Google STT."""
        try:
            return rec.recognize_google(audio)
        except (sr.UnknownValueError, sr.RequestError):
            return None
        except Exception:
            return None
