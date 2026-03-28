"""Screen capture and mouse control actions for Nova's screen sharing mode."""

import io
import pyautogui


def take_screenshot():
    """Capture the entire screen. Returns PNG bytes."""
    img = pyautogui.screenshot()
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def click_at(x, y, button="left"):
    """Click at screen coordinates."""
    x, y = int(x), int(y)
    button = str(button).lower()
    if button not in ("left", "right", "middle"):
        button = "left"
    pyautogui.click(x, y, button=button)
    return f"Clicked {button} at ({x}, {y})"


def double_click_at(x, y):
    """Double-click at screen coordinates."""
    x, y = int(x), int(y)
    pyautogui.doubleClick(x, y)
    return f"Double-clicked at ({x}, {y})"


def right_click_at(x, y):
    """Right-click at screen coordinates."""
    x, y = int(x), int(y)
    pyautogui.rightClick(x, y)
    return f"Right-clicked at ({x}, {y})"


def move_mouse(x, y):
    """Move the mouse cursor to screen coordinates."""
    x, y = int(x), int(y)
    pyautogui.moveTo(x, y)
    return f"Moved mouse to ({x}, {y})"


def scroll_screen(clicks, x=None, y=None):
    """Scroll the mouse wheel. Positive = up, negative = down."""
    clicks = int(clicks)
    if x is not None and y is not None:
        pyautogui.scroll(clicks, int(x), int(y))
    else:
        pyautogui.scroll(clicks)
    direction = "up" if clicks > 0 else "down"
    return f"Scrolled {direction} by {abs(clicks)}"


def drag_to(start_x, start_y, end_x, end_y):
    """Click and drag from one point to another."""
    pyautogui.moveTo(int(start_x), int(start_y))
    pyautogui.drag(int(end_x) - int(start_x), int(end_y) - int(start_y), duration=0.5)
    return f"Dragged from ({start_x}, {start_y}) to ({end_x}, {end_y})"


def get_screen_size():
    """Get the screen resolution."""
    w, h = pyautogui.size()
    return f"Screen size: {w}x{h}"


def get_mouse_position():
    """Get the current mouse cursor position."""
    x, y = pyautogui.position()
    return f"Mouse at ({x}, {y})"
