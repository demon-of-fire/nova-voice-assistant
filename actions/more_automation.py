"""More automation: delayed screenshot, window transparency, clipboard mgmt, batch rename, organize downloads."""

import os
import subprocess
import threading
import time
import datetime
import shutil
import re
import json
from actions.confirmation import ask_confirmation


DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
AUTOMATION_DIR = os.path.join(os.path.expanduser("~"), ".nova_automation")
_clipboard_history = []


def _ensure_dir():
    os.makedirs(AUTOMATION_DIR, exist_ok=True)


def delayed_screenshot(delay_seconds=5):
    """Take a screenshot after a specified delay in seconds."""
    from actions.screen import take_screenshot
    delay_seconds = max(0, min(300, int(delay_seconds)))

    def _delayed():
        time.sleep(delay_seconds)
        try:
            img_data = take_screenshot()
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            filename = f"screenshot_{datetime.datetime.now():%Y%m%d_%H%M%S}.png"
            path = os.path.join(desktop, filename)
            with open(path, "wb") as f:
                f.write(img_data)
        except Exception:
            pass

    threading.Thread(target=_delayed, daemon=True).start()
    if delay_seconds == 0:
        return "Taking screenshot now."
    return f"Screenshot will be taken in {delay_seconds} seconds."


def set_window_transparency(window_title, opacity=128):
    """Set the transparency of a window by title (0=invisible, 255=opaque)."""
    try:
        import ctypes
        from ctypes import wintypes

        opacity = max(0, min(255, int(opacity)))
        user32 = ctypes.windll.user32

        hwnd = user32.FindWindowW(None, window_title)
        if not hwnd:
            return f"Couldn't find window '{window_title}'."

        GWL_EXSTYLE = -20
        WS_EX_LAYERED = 0x80000
        current = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, current | WS_EX_LAYERED)

        LWA_ALPHA = 0x2
        user32.SetLayeredWindowAttributes(hwnd, 0, opacity, LWA_ALPHA)

        pct = (opacity / 255) * 100
        return f"Set '{window_title}' transparency to {pct:.0f}%."
    except Exception as e:
        return f"Couldn't set window transparency: {e}"


def get_clipboard_history():
    """Show recent clipboard history (up to 10 entries)."""
    if not _clipboard_history:
        return "Clipboard history is empty."
    entries = [f"{i+1}: {t[:80]}" for i, t in enumerate(_clipboard_history[-10:])]
    return "Clipboard history: " + " | ".join(entries)


def clear_clipboard_history():
    """Clear the clipboard history."""
    global _clipboard_history
    _clipboard_history = []
    return "Clipboard history cleared."


def batch_rename(pattern, replacement, directory="", dry_run=True):
    """Batch rename files in a directory using a find/replace pattern."""
    target_dir = directory.strip() if directory.strip() else os.path.expanduser("~")
    if not os.path.isdir(target_dir):
        return f"Directory '{target_dir}' not found."

    try:
        files = [f for f in os.listdir(target_dir)
                 if os.path.isfile(os.path.join(target_dir, f))]
        matched = []
        for f in files:
            if re.search(pattern, f):
                new_name = re.sub(pattern, replacement, f)
                if new_name != f:
                    matched.append((f, new_name))

        if not matched:
            return f"No files matched pattern '{pattern}' in {target_dir}."

        if dry_run:
            preview = "; ".join([f"'{old}' -> '{new}'" for old, new in matched[:10]])
            extra = f" (+{len(matched)-10} more)" if len(matched) > 10 else ""
            return f"[Dry run] Would rename {len(matched)} files: {preview}{extra}"

        if not ask_confirmation(f"Rename {len(matched)} files in {target_dir}?"):
            return "Cancelled."

        renamed = 0
        for old_name, new_name in matched:
            old_path = os.path.join(target_dir, old_name)
            new_path = os.path.join(target_dir, new_name)
            try:
                os.rename(old_path, new_path)
                renamed += 1
            except Exception:
                pass
        return f"Renamed {renamed}/{len(matched)} files in {target_dir}."
    except Exception as e:
        return f"Batch rename error: {e}"


FILE_TYPE_MAP = {
    "Images": (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico", ".tiff"),
    "Documents": (".pdf", ".doc", ".docx", ".txt", ".rtf", ".md", ".csv", ".xls", ".xlsx", ".ppt", ".pptx", ".odt"),
    "Archives": (".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"),
    "Audio": (".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"),
    "Video": (".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"),
    "Programs": (".exe", ".msi", ".bat", ".ps1", ".cmd", ".vbs"),
    "Code": (".py", ".js", ".ts", ".html", ".css", ".json", ".xml", ".yaml", ".yml", ".sh", ".cpp", ".c", ".h", ".java"),
    "Torrents": (".torrent",),
}


def organize_downloads(dry_run=True):
    """Organize the Downloads folder into subfolders by file type."""
    if not os.path.isdir(DOWNLOADS_DIR):
        return f"Downloads folder not found at {DOWNLOADS_DIR}."

    try:
        files = [f for f in os.listdir(DOWNLOADS_DIR)
                 if os.path.isfile(os.path.join(DOWNLOADS_DIR, f)) and not f.startswith(".")]
        if not files:
            return "Downloads folder is empty."

        organized = {}
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            moved = False
            for category, extensions in FILE_TYPE_MAP.items():
                if ext in extensions:
                    organized.setdefault(category, []).append(f)
                    moved = True
                    break
            if not moved:
                organized.setdefault("Other", []).append(f)

        if dry_run:
            parts = []
            for category, items in sorted(organized.items()):
                parts.append(f"{category}: {len(items)}")
            return f"[Dry run] Would organize {len(files)} files into folders: {', '.join(parts)}."

        if not ask_confirmation(f"Organize {len(files)} files in Downloads into folders?"):
            return "Cancelled."

        moved_count = 0
        for category, items in sorted(organized.items()):
            cat_dir = os.path.join(DOWNLOADS_DIR, category)
            os.makedirs(cat_dir, exist_ok=True)
            for f in items:
                try:
                    src = os.path.join(DOWNLOADS_DIR, f)
                    dst = os.path.join(cat_dir, f)
                    # Handle name conflicts
                    if os.path.exists(dst):
                        base, ext = os.path.splitext(f)
                        dst = os.path.join(cat_dir, f"{base}_{datetime.datetime.now():%Y%m%d%H%M%S}{ext}")
                    shutil.move(src, dst)
                    moved_count += 1
                except Exception:
                    pass
        return f"Moved {moved_count}/{len(files)} files into organized folders in Downloads."
    except Exception as e:
        return f"Couldn't organize downloads: {e}"
