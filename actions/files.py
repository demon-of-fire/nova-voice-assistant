"""File Explorer operations: open/reveal paths, find files, clipboard."""

import os
import subprocess
import ctypes


def _expand(path):
    return os.path.abspath(os.path.expandvars(os.path.expanduser(path)))


def _quote_for_explorer(path):
    return os.path.normpath(path)


def _select_arg(path):
    return f"/select,{_quote_for_explorer(path)}"


def list_drives():
    """List available Windows drives."""
    drives = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for i in range(26):
        if bitmask & (1 << i):
            drive = f"{chr(65 + i)}:\\"
            dtype = ctypes.windll.kernel32.GetDriveTypeW(drive)
            label = {
                2: "removable",
                3: "fixed",
                4: "network",
                5: "disc",
                6: "ram",
            }.get(dtype, "unknown")
            drives.append(f"{drive} ({label})")
    return "Available drives: " + ", ".join(drives) if drives else "No drives found."


def open_file_explorer(path=None):
    """Open File Explorer at a folder, file location, or This PC."""
    if not path:
        subprocess.Popen(["explorer.exe", "shell:MyComputerFolder"])
        return "Opened File Explorer."

    full = _expand(path)
    if os.path.isdir(full):
        subprocess.Popen(["explorer.exe", _quote_for_explorer(full)])
        return f"Opened folder {full}."
    if os.path.isfile(full):
        subprocess.Popen(["explorer.exe", _select_arg(full)])
        return f"Opened the location of {os.path.basename(full)}."
    return f"Path not found: {path}"


def open_folder(path):
    """Open a folder in File Explorer."""
    expanded = _expand(path)
    if os.path.isdir(expanded):
        subprocess.Popen(["explorer.exe", _quote_for_explorer(expanded)])
        return f"Opened {expanded}."
    return f"Folder not found: {path}"


def open_path(path):
    """Open a file, folder, URL shortcut, or app-associated document."""
    full = _expand(path)
    if not os.path.exists(full):
        return f"Path not found: {path}"
    try:
        os.startfile(full)
        return f"Opened {os.path.basename(full) or full}."
    except Exception as e:
        return f"Couldn't open {path}: {e}"


def reveal_path(path):
    """Reveal a file or folder in File Explorer and select it."""
    full = _expand(path)
    if not os.path.exists(full):
        return f"Path not found: {path}"
    try:
        subprocess.Popen(["explorer.exe", _select_arg(full)])
        return f"Showing {os.path.basename(full) or full} in File Explorer."
    except Exception as e:
        return f"Couldn't show {path}: {e}"


def find_files(query, directory=None):
    """Search for files matching a name pattern."""
    search_dir = _expand(directory) if directory else os.path.expanduser("~")
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
        subprocess.Popen(["explorer.exe", _select_arg(first)])
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
