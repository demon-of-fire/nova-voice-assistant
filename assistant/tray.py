"""System tray icon so Nova runs in the background."""

import threading
from PIL import Image, ImageDraw
import pystray


def _create_icon_image():
    """Generate a simple blue circle icon (no .ico file needed)."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, size - 4, size - 4], fill=(74, 158, 255, 255))
    draw.ellipse([18, 18, size - 18, size - 18], fill=(120, 190, 255, 255))
    return img


def create_tray(on_show, on_quit):
    """Create and return a system tray icon."""
    image = _create_icon_image()
    menu = pystray.Menu(
        pystray.MenuItem("Show Nova", on_show, default=True),
        pystray.MenuItem("Quit", on_quit),
    )
    icon = pystray.Icon("Nova", image, "Nova Voice Assistant", menu)
    return icon


def run_tray(on_show, on_quit):
    """Run the system tray icon in a background thread."""
    icon = create_tray(on_show, on_quit)

    def _run():
        icon.run()

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return icon
