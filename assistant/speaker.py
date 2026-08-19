"""Text-to-speech with neural voices via edge-tts, falling back to SAPI5.

Primary: edge-tts (Microsoft Edge neural voices — natural, human-like).
Fallback: Windows SAPI5 (robot voice, works offline).

Both use SSML markup for pitch variation, pauses, and emphasis.
"""

import threading
import queue
import re
import os
import tempfile
import time
import logging
import ctypes

log = logging.getLogger("nova")

DEFAULT_VOICE = ""
_has_edge_tts = False

try:
    import edge_tts
    import asyncio
    _has_edge_tts = True
except ImportError:
    _has_edge_tts = False


def _build_ssml(text, rate="+0%", pitch="+0Hz"):
    """Wrap plain text in basic SSML for more natural delivery."""
    # Split into sentences for prosody at sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    wrapped = []
    for i, s in enumerate(sentences):
        if not s:
            continue
        # Add a slight pitch rise on questions, fall on statements
        s_pitch = pitch
        if s.endswith("?"):
            s_pitch = "+20Hz"
        elif s.endswith("!"):
            s_pitch = "+15Hz"
        wrapped.append(
            f'<prosody rate="{rate}" pitch="{s_pitch}">'
            f'{s.strip()}'
            f'</prosody>'
        )
    body = "\n".join(wrapped)
    return f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"><voice name="{DEFAULT_VOICE}">{body}</voice></speak>'


def list_voices():
    """Return installed voices as (id, name) pairs.

    Attempts edge-tts first, then falls back to SAPI5.
    """
    if _has_edge_tts:
        try:
            voices = asyncio.run(edge_tts.list_voices())
            result = []
            for v in voices:
                if v["Locale"].startswith("en"):
                    result.append((v["Name"], f'{v["Name"]} — {v["Locale"]}'))
            # Sort so premium US voices appear first
            priority = ["Jenny", "Aria", "Emma", "Neural"]
            result.sort(key=lambda x: next((i for i, p in enumerate(priority) if p in x[0]), len(priority)))
            return result
        except Exception:
            pass
    return _list_sapi_voices()


def _list_sapi_voices():
    try:
        import comtypes.client
        import comtypes
        comtypes.CoInitialize()
        voice = comtypes.client.CreateObject("SAPI.SpVoice")
        voices = voice.GetVoices()
        result = []
        for i in range(voices.Count):
            token = voices.Item(i)
            result.append((token.Id, token.GetDescription()))
        return result
    except Exception:
        return []


class Speaker:
    """Speaker with neural voice support, queue, and SSML markup."""

    def __init__(self, settings=None):
        self._settings = settings
        self._lock = threading.Lock()
        self._queue = queue.Queue()
        self._speaking = False
        self._stop_requested = False
        self._thread = None
        self._current_edge_task = None
        self.is_speaking = False

        # Pre-cache edge voice list
        self._edge_voices = []
        if _has_edge_tts:
            try:
                self._edge_voices = asyncio.run(edge_tts.list_voices())
            except Exception:
                pass

        # Start background processing thread
        self._start_worker()

    def _start_worker(self):
        def _worker():
            while True:
                try:
                    item = self._queue.get(timeout=30)
                    if item is None:
                        break
                    text, on_done = item
                    self._speaking = True
                    self.is_speaking = True
                    try:
                        self._speak_internal(text)
                    except Exception as e:
                        log.error("Speech error: %s", e)
                    self._speaking = False
                    self.is_speaking = False
                    if on_done:
                        try:
                            on_done()
                        except Exception:
                            pass
                except queue.Empty:
                    continue
                except Exception:
                    continue

        self._thread = threading.Thread(target=_worker, daemon=True)
        self._thread.start()

    def _get_edge_voice(self, preferred):
        """Get an edge-tts voice name matching the user's preference."""
        if not self._edge_voices:
            return "en-US-JennyNeural"
        if preferred:
            for v in self._edge_voices:
                if preferred in v.get("Name", ""):
                    return v["Name"]
        # Default to best available English voice
        for priority in ["Jenny", "Aria", "Emma", "Neural"]:
            for v in self._edge_voices:
                if priority in v.get("Name", "") and v.get("Locale", "").startswith("en"):
                    return v["Name"]
        return "en-US-JennyNeural"

    def _speak_internal(self, text):
        """Speak using edge-tts (preferred) or SAPI5 fallback."""
        # Try edge-tts first if available
        if _has_edge_tts:
            try:
                self._speak_edge(text)
                return
            except Exception as e:
                log.warning("edge-tts failed, falling back to SAPI5: %s", e)

        self._speak_sapi(text)

    def _speak_edge(self, text):
        """Speak using Edge neural TTS with SSML.

        Uses Windows MCI to play the MP3 since winsound.PlaySound only supports WAV.
        """
        voice_name = self._get_edge_voice(self._settings.get("tts_voice") if self._settings else None)
        rate = self._settings.get("tts_rate") if self._settings else None
        rate_str = "+0%"
        if rate:
            # Map 100-300 WPM to -50% to +50%
            rate_str = f"{max(-50, min(50, int((rate - 175) / 2.5)))}%"

        ssml = _build_ssml(text, rate=rate_str)
        communicate = edge_tts.Communicate(ssml=ssml, voice=voice_name)

        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp_path = tmp.name
        tmp.close()

        async def _save_audio():
            await communicate.save(tmp_path)

        asyncio.run(_save_audio())

        # Play the MP3 via Windows MCI (winsound only handles WAV)
        try:
            mci = ctypes.windll.winmm.mciSendStringW
            escaped_path = tmp_path.replace("\\", "\\\\")
            mci(f'open "{escaped_path}" type mpegvideo alias nova_tts', None, 0, 0)
            mci("play nova_tts wait", None, 0, 0)
            mci("close nova_tts", None, 0, 0)
        except Exception:
            import winsound
            winsound.PlaySound(tmp_path, winsound.SND_FILENAME | winsound.SND_NOSTOP)

        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    def _speak_sapi(self, text):
        """Speak using SAPI5 fallback with SSML markup."""
        import comtypes.client
        import comtypes
        comtypes.CoInitialize()
        voice = comtypes.client.CreateObject("SAPI.SpVoice")

        # Apply voice selection
        voice_id = self._settings.get("tts_voice") if self._settings else None
        if voice_id:
            try:
                voices = voice.GetVoices()
                for i in range(voices.Count):
                    token = voices.Item(i)
                    if token.Id == voice_id:
                        voice.Voice = token
                        break
            except Exception:
                pass

        # Apply rate
        try:
            rate = self._settings.get("tts_rate") or 175
            voice.Rate = max(-10, min(10, int((rate - 160) / 20)))
        except Exception:
            pass

        # Apply volume
        try:
            volume = self._settings.get("tts_volume")
            if volume is not None:
                voice.Volume = max(0, min(100, int(float(volume) * 100)))
        except Exception:
            pass

        # Build SSML with prosody — MUST use SVSFIsXML so SSML tags are parsed, not spoken
        ssml = _build_ssml(text)
        SVSFlagsAsync = 1
        SVSFIsXML = 8
        voice.Speak(ssml, SVSFlagsAsync | SVSFIsXML)

    def say(self, text, on_done=None):
        """Speak text in background. Non-blocking."""
        if not text:
            if on_done:
                on_done()
            return
        self._queue.put((text, on_done))

    def say_sync(self, text):
        """Speak text and block until done."""
        if not text:
            return
        self.is_speaking = True
        self._speaking = True
        try:
            self._speak_internal(text)
        except Exception as e:
            log.error("say_sync error: %s", e)
        self._speaking = False
        self.is_speaking = False

    def stop(self):
        """Stop current speech and clear the queue."""
        self._stop_requested = True
        # Clear the queue
        while True:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
        self._speaking = False
        self.is_speaking = False

    @property
    def busy(self):
        return self._speaking or not self._queue.empty()
