"""File operations: open folders, find files, clipboard."""

import os
import subprocess
import ctypes


def open_folder(path):
    """Open a folder in File Explorer."""
    expanded = os.path.expandvars(os.path.expanduser(path))
    if os.path.isdir(expanded):
        os.startfile(expanded)
        return f"Opened {expanded}."
    return f"Folder not found: {path}"


def find_files(query, directory=None):
    """Search for files matching a name pattern."""
    search_dir = directory or os.path.expanduser("~")
    search_dir = os.path.expandvars(search_dir)
    results = []

    try:
        for root, dirs, files in os.walk(search_dir):
            # Skip hidden/system dirs
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in (
                "node_modules", "__pycache__", ".git", "AppData"
            )]
            for f in files:
                if query.lower() in f.lower():
                    results.append(os.path.join(root, f))
                    if len(results) >= 10:
                        break
            if len(results) >= 10:
                break
    except PermissionError:
        pass

    if results:
        # Open the folder containing the first result
        first = results[0]
        subprocess.Popen(f'explorer /select,"{first}"', shell=True)
        if len(results) == 1:
            return f"Found {os.path.basename(first)} and opened its location."
        return f"Found {len(results)} files. Showing the first one: {os.path.basename(first)}."
    return f"No files matching '{query}' found in {search_dir}."


def copy_to_clipboard(text):
    """Copy text to the Windows clipboard."""
    import subprocess
    process = subprocess.Popen(["clip"], stdin=subprocess.PIPE)
    process.communicate(text.encode("utf-16-le"))
    return "Copied to clipboard."


def read_clipboard():
    """Read text from the Windows clipboard."""
    CF_UNICODETEXT = 13
    u32 = ctypes.windll.user32
    k32 = ctypes.windll.kernel32

    u32.OpenClipboard(0)
    try:
        handle = u32.GetClipboardData(CF_UNICODETEXT)
        if handle:
            k32.GlobalLock.restype = ctypes.c_wchar_p
            text = k32.GlobalLock(handle)
            k32.GlobalUnlock(handle)
            if text:
                preview = text[:200] + "..." if len(text) > 200 else text
                return f"Clipboard contains: {preview}"
        return "Clipboard is empty."
    finally:
        u32.CloseClipboard()
