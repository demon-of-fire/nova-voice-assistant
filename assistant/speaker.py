"""Text-to-speech using Microsoft Edge neural voices (natural sounding).

Falls back to pyttsx3 SAPI5 if edge-tts fails (no internet).
"""

import asyncio
import tempfile
import threading
import os


# Edge TTS neural voices — these sound human, not robotic
EDGE_VOICES = [
    ("en-US-GuyNeural", "Guy, American male, natural"),
    ("en-US-JennyNeural", "Jenny, American female, natural"),
    ("en-US-AriaNeural", "Aria, American female, expressive"),
    ("en-US-BrianNeural", "Brian, American male, conversational"),
    ("en-US-AndrewNeural", "Andrew, American male, warm"),
    ("en-US-AvaNeural", "Ava, American female, friendly"),
    ("en-US-EmmaNeural", "Emma, American female, clear"),
    ("en-US-ChristopherNeural", "Christopher, American male, professional"),
    ("en-US-EricNeural", "Eric, American male, deep"),
    ("en-US-RogerNeural", "Roger, American male, mature"),
    ("en-US-SteffanNeural", "Steffan, American male, calm"),
    ("en-US-MichelleNeural", "Michelle, American female, warm"),
    ("en-GB-RyanNeural", "Ryan, British male, natural"),
    ("en-GB-SoniaNeural", "Sonia, British female, natural"),
    ("en-AU-WilliamMultilingualNeural", "William, Australian male, natural"),
]

DEFAULT_VOICE = "en-US-GuyNeural"


def list_voices():
    """Return list of (id, name) for available neural voices."""
    return [(vid, vname) for vid, vname in EDGE_VOICES]


class Speaker:
    def __init__(self, settings=None):
        self._settings = settings
        self._lock = threading.Lock()
        self.is_speaking = False
        self._pyttsx3_engine = None  # lazy init fallback only

        # Preload pygame mixer for audio playback
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except Exception:
            pass

    def _get_voice(self):
        """Get the configured voice or default."""
        if self._settings:
            v = self._settings.get("tts_voice")
            if v:
                return v
        return DEFAULT_VOICE

    def _get_rate(self):
        """Get speech rate as edge-tts rate string (e.g., '+0%', '-20%')."""
        if self._settings:
            rate = self._settings.get("tts_rate") or 160
        else:
            rate = 160
        # Convert WPM-ish value to percentage offset from default (~150 wpm)
        offset = int((rate - 150) / 150 * 100)
        sign = "+" if offset >= 0 else ""
        return f"{sign}{offset}%"

    def _speak_edge(self, text):
        """Generate speech with edge-tts and play it."""
        import edge_tts
        import pygame

        voice = self._get_voice()
        rate = self._get_rate()

        # Create temp file for the audio
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp_path = tmp.name
        tmp.close()

        try:
            # Run edge-tts in an event loop
            loop = asyncio.new_event_loop()
            try:
                communicate = edge_tts.Communicate(text, voice, rate=rate)
                loop.run_until_complete(communicate.save(tmp_path))
            finally:
                loop.close()

            # Play the audio
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(tmp_path)

            vol = 1.0
            if self._settings:
                vol = self._settings.get("tts_volume") or 1.0
            pygame.mixer.music.set_volume(vol)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                pygame.time.wait(50)

            pygame.mixer.music.stop()
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    def _speak_fallback(self, text):
        """Fallback: use pyttsx3 SAPI5 (robotic but works offline)."""
        import pyttsx3

        if self._pyttsx3_engine is None:
            self._pyttsx3_engine = pyttsx3.init()

        engine = self._pyttsx3_engine
        rate = 160
        vol = 1.0
        if self._settings:
            rate = self._settings.get("tts_rate") or 160
            vol = self._settings.get("tts_volume") or 1.0
        engine.setProperty("rate", rate)
        engine.setProperty("volume", vol)
        engine.say(text)
        engine.runAndWait()

    def say(self, text, on_done=None):
        """Speak text in a background thread."""
        if not text:
            return

        def _speak():
            self.is_speaking = True
            with self._lock:
                try:
                    self._speak_edge(text)
                except Exception:
                    try:
                        self._speak_fallback(text)
                    except Exception:
                        pass
            self.is_speaking = False
            if on_done:
                on_done()

        t = threading.Thread(target=_speak, daemon=True)
        t.start()
        return t

    def say_sync(self, text):
        """Speak text and block until done."""
        if not text:
            return
        self.is_speaking = True
        with self._lock:
            try:
                self._speak_edge(text)
            except Exception:
                try:
                    self._speak_fallback(text)
                except Exception:
                    pass
        self.is_speaking = False
