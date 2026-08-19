"""Native Windows global hotkeys using RegisterHotKey."""

import ctypes
import ctypes.wintypes as wt
import logging
import threading


log = logging.getLogger("nova")

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012

_MODIFIERS = {
    "alt": MOD_ALT,
    "ctrl": MOD_CONTROL,
    "control": MOD_CONTROL,
    "shift": MOD_SHIFT,
    "win": MOD_WIN,
    "windows": MOD_WIN,
}

_KEYS = {
    **{f"f{i}": 0x6F + i for i in range(1, 25)},
    **{chr(i): i for i in range(ord("A"), ord("Z") + 1)},
    **{chr(i).lower(): i for i in range(ord("A"), ord("Z") + 1)},
    **{str(i): ord(str(i)) for i in range(10)},
    "esc": 0x1B,
    "escape": 0x1B,
    "space": 0x20,
    "enter": 0x0D,
    "comma": 0xBC,
    ",": 0xBC,
}


class NativeHotkeyManager:
    def __init__(self):
        self._hotkeys = []
        self._callbacks = {}
        self._thread = None
        self._thread_id = 0
        self._ready = threading.Event()
        self._running = False

    def add(self, hotkey, callback):
        modifiers, vk = _parse_hotkey(hotkey)
        hotkey_id = len(self._hotkeys) + 1
        self._hotkeys.append((hotkey_id, modifiers, vk, hotkey))
        self._callbacks[hotkey_id] = callback

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, name="NovaHotkeys", daemon=True)
        self._thread.start()
        self._ready.wait(timeout=3)

    def stop(self):
        self._running = False
        if self._thread_id:
            ctypes.windll.user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)

    def _run(self):
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        self._thread_id = kernel32.GetCurrentThreadId()

        registered = []
        for hotkey_id, modifiers, vk, label in self._hotkeys:
            if user32.RegisterHotKey(None, hotkey_id, modifiers, vk):
                registered.append(hotkey_id)
                log.info("Registered native hotkey: %s", label)
            else:
                err = ctypes.get_last_error()
                log.error("Failed to register native hotkey %s: Windows error %s", label, err)

        self._ready.set()

        msg = wt.MSG()
        try:
            while self._running and user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == WM_HOTKEY:
                    callback = self._callbacks.get(int(msg.wParam))
                    if callback:
                        try:
                            callback()
                        except Exception:
                            log.exception("Native hotkey callback failed")
                else:
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            for hotkey_id in registered:
                user32.UnregisterHotKey(None, hotkey_id)


def _parse_hotkey(hotkey):
    modifiers = 0
    key = None
    for part in hotkey.lower().replace(" ", "").split("+"):
        if part in _MODIFIERS:
            modifiers |= _MODIFIERS[part]
        else:
            key = part

    if not key or key not in _KEYS:
        raise ValueError(f"Unsupported hotkey: {hotkey}")
    return modifiers, _KEYS[key]
