"""NVDA and screen reader accessibility support.

Uses nvdaControllerClient64.dll for direct NVDA communication.
Falls back to Tolk.dll (universal screen reader library) if available.
"""

import ctypes
import ctypes.wintypes as wt
import os
import sys

user32 = ctypes.windll.user32

# Win32 style constants
GWL_STYLE = -16
GWL_EXSTYLE = -20
WS_CAPTION = 0x00C00000
WS_THICKFRAME = 0x00040000
WS_MINIMIZEBOX = 0x00020000
WS_MAXIMIZEBOX = 0x00010000
WS_SYSMENU = 0x00080000
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW = 0x00040000
SWP_FRAMECHANGED = 0x0020
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOZORDER = 0x0004


def _get_base_dir():
    """Get the base directory — works both in dev and PyInstaller bundle."""
    if getattr(sys, '_MEIPASS', None):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ── NVDA Controller Client (LAZY — loaded on first use) ──────────────────
_nvda = None
_nvda_tried = False

def _load_nvda():
    """Load NVDA controller DLL lazily so COM initialization stays predictable."""
    global _nvda, _nvda_tried
    if _nvda_tried:
        return
    _nvda_tried = True

    search_paths = [
        os.path.join(_get_base_dir(), "nvdaControllerClient64.dll"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "nvdaControllerClient64.dll"),
        os.path.join(os.path.expanduser("~"), "Downloads", "x64",
                     "nvdaControllerClient64.dll"),
        os.path.join(os.environ.get("PROGRAMFILES", "C:\\Program Files"),
                     "NVDA", "nvdaControllerClient64.dll"),
        os.path.join(os.environ.get("PROGRAMFILES(X86)", ""),
                     "NVDA", "nvdaControllerClient32.dll"),
    ]

    for path in search_paths:
        if path and os.path.exists(path):
            try:
                _nvda = ctypes.windll.LoadLibrary(path)
                # SET PROPER ARGUMENT TYPES — critical for NVDA to actually speak!
                _nvda.nvdaController_speakText.argtypes = [ctypes.c_wchar_p]
                _nvda.nvdaController_speakText.restype = ctypes.c_int
                _nvda.nvdaController_cancelSpeech.argtypes = []
                _nvda.nvdaController_cancelSpeech.restype = ctypes.c_int
                _nvda.nvdaController_testIfRunning.argtypes = []
                _nvda.nvdaController_testIfRunning.restype = ctypes.c_int

                _nvda.nvdaController_testIfRunning()
                return
            except Exception:
                _nvda = None


# ── Tolk (LAZY — loaded on first use) ────────────────────────────────────
_tolk = None
_tolk_tried = False

def _load_tolk():
    """Load Tolk DLL lazily."""
    global _tolk, _tolk_tried
    if _tolk_tried:
        return
    _tolk_tried = True

    search_paths = [
        os.path.join(_get_base_dir(), "Tolk.dll"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "Tolk.dll"),
        os.path.join(os.path.expanduser("~"), "Downloads", "x64", "Tolk.dll"),
    ]

    for path in search_paths:
        if path and os.path.exists(path):
            try:
                _tolk = ctypes.cdll.LoadLibrary(path)
                _tolk.Tolk_Load()
                _tolk.Tolk_Output.argtypes = [ctypes.c_wchar_p, ctypes.c_bool]
                _tolk.Tolk_Output.restype = ctypes.c_bool
                return
            except Exception:
                _tolk = None


def make_borderless_accessible(tk_root):
    """Remove title bar decorations but keep the window in the accessibility tree."""
    tk_root.update_idletasks()
    hwnd = user32.GetParent(tk_root.winfo_id())

    style = user32.GetWindowLongW(hwnd, GWL_STYLE)
    style &= ~(WS_CAPTION | WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_SYSMENU)
    user32.SetWindowLongW(hwnd, GWL_STYLE, style)

    ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    ex_style |= WS_EX_TOOLWINDOW
    ex_style &= ~WS_EX_APPWINDOW
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)

    user32.SetWindowPos(
        hwnd, None, 0, 0, 0, 0,
        SWP_FRAMECHANGED | SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER
    )


def announce(text):
    """Announce text to the screen reader.

    Tries NVDA controller → Tolk → Win32 fallback.
    DLLs are loaded lazily on first call to avoid COM threading conflicts.

    IMPORTANT: nvdaController_speakText takes a c_wchar_p (LPCWSTR).
    We must pass the text as a proper wide string, not raw Python str.
    """
    if not text:
        return

    # Lazy load on first use after COM-based helpers have had a chance to initialize.
    _load_nvda()
    _load_tolk()

    # Try NVDA direct — pass as c_wchar_p (wide string pointer)
    if _nvda:
        try:
            result = _nvda.nvdaController_speakText(ctypes.c_wchar_p(str(text)))
            if result == 0:
                return
            # Non-zero means NVDA not running, fall through
        except Exception:
            pass

    # Try Tolk (universal)
    if _tolk:
        try:
            _tolk.Tolk_Output(ctypes.c_wchar_p(str(text)), False)
            return
        except Exception:
            pass

    # Fallback: NotifyWinEvent
    try:
        EVENT_SYSTEM_ALERT = 0x0002
        OBJID_CLIENT = -4
        user32.NotifyWinEvent(EVENT_SYSTEM_ALERT, 0, OBJID_CLIENT, 0)
    except Exception:
        pass


def cancel_speech():
    """Cancel any ongoing NVDA speech."""
    _load_nvda()
    if _nvda:
        try:
            _nvda.nvdaController_cancelSpeech()
        except Exception:
            pass


def announce_state(state, detail=""):
    """Announce a state change with a human-readable message."""
    messages = {
        "idle": "Nova ready",
        "listening": "Listening for your command",
        "listening_followup": "Listening for follow up",
        "thinking": "Processing your request",
        "speaking": "Nova speaking",
        "muted": "Microphone muted",
        "unmuted": "Microphone on",
        "error": "Error occurred",
        "apikey_needed": "Gemini API key needed. Open Settings to set it up.",
        "screen_on": "Screen sharing on. Nova can see your screen.",
        "screen_off": "Screen sharing off.",
    }
    msg = messages.get(state, state)
    if detail:
        msg = f"{msg}: {detail}"
    announce(msg)


def announce_error(error_text):
    """Announce an error to the screen reader."""
    announce(f"Error: {error_text}")


def announce_warning(warning_text):
    """Announce a warning to the screen reader."""
    announce(f"Warning: {warning_text}")


def announce_success(success_text):
    """Announce a success message to the screen reader."""
    announce(success_text)
