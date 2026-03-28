"""Window management using Win32 API via ctypes."""

import ctypes
import ctypes.wintypes as wt
from difflib import SequenceMatcher

user32 = ctypes.windll.user32

# Constants
SW_MINIMIZE = 6
SW_MAXIMIZE = 3
SW_RESTORE = 9
SW_SHOW = 5
WM_CLOSE = 0x0010
SWP_NOZORDER = 0x0004
SWP_SHOWWINDOW = 0x0040
MONITOR_DEFAULTTONEAREST = 2


def _get_visible_windows():
    """Return list of (hwnd, title) for all visible windows with titles."""
    results = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def callback(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value
                if title:
                    results.append((hwnd, title))
        return True

    user32.EnumWindows(callback, 0)
    return results


def _find_window(title_query):
    """Find a window by partial title match. Returns hwnd or None."""
    if not title_query:
        return user32.GetForegroundWindow()

    windows = _get_visible_windows()
    query = title_query.lower()

    # Substring match first
    for hwnd, title in windows:
        if query in title.lower():
            return hwnd

    # Fuzzy match
    best_hwnd, best_score = None, 0
    for hwnd, title in windows:
        score = SequenceMatcher(None, query, title.lower()).ratio()
        if score > best_score:
            best_hwnd, best_score = hwnd, score
    if best_score > 0.4:
        return best_hwnd

    return None


def _get_window_title(hwnd):
    length = user32.GetWindowTextLengthW(hwnd)
    if length > 0:
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value
    return "window"


def minimize_window(window_title=None):
    hwnd = _find_window(window_title)
    if not hwnd:
        return f"Couldn't find a window matching '{window_title}'."
    user32.ShowWindow(hwnd, SW_MINIMIZE)
    return f"Minimized {_get_window_title(hwnd)}."


def maximize_window(window_title=None):
    hwnd = _find_window(window_title)
    if not hwnd:
        return f"Couldn't find a window matching '{window_title}'."
    user32.ShowWindow(hwnd, SW_MAXIMIZE)
    return f"Maximized {_get_window_title(hwnd)}."


def close_window(window_title=None):
    hwnd = _find_window(window_title)
    if not hwnd:
        return f"Couldn't find a window matching '{window_title}'."
    title = _get_window_title(hwnd)
    user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
    return f"Closed {title}."


def switch_window(window_title):
    hwnd = _find_window(window_title)
    if not hwnd:
        return f"Couldn't find a window matching '{window_title}'."
    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.SetForegroundWindow(hwnd)
    return f"Switched to {_get_window_title(hwnd)}."


def snap_window(direction, window_title=None):
    hwnd = _find_window(window_title)
    if not hwnd:
        return f"Couldn't find a window matching '{window_title}'."

    # Get screen dimensions
    screen_w = user32.GetSystemMetrics(0)
    screen_h = user32.GetSystemMetrics(1)

    half_w = screen_w // 2
    if direction == "left":
        x, y, w, h = 0, 0, half_w, screen_h
    else:
        x, y, w, h = half_w, 0, half_w, screen_h

    # Restore first if maximized
    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.SetWindowPos(hwnd, None, x, y, w, h, SWP_NOZORDER | SWP_SHOWWINDOW)
    return f"Snapped {_get_window_title(hwnd)} to the {direction}."
