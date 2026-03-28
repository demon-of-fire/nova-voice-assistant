"""Extended filesystem operations: read, write, edit, delete, move, copy."""

import os
import shutil
import datetime
from actions.confirmation import ask_confirmation


def _expand(path):
    """Expand environment variables and user home in a path."""
    return os.path.expandvars(os.path.expanduser(path))


def read_file(path):
    """Read the contents of a file (first 3000 characters)."""
    full = _expand(path)
    if not os.path.isfile(full):
        return f"File not found: {path}"
    try:
        with open(full, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(3000)
        if len(content) == 3000:
            content += "\n... (truncated at 3000 characters)"
        return content
    except Exception as e:
        return f"Error reading file: {e}"


def write_file(path, content):
    """Write content to a file (creates or overwrites)."""
    full = _expand(path)
    if not ask_confirmation(f"Write file:\n{full}"):
        return "Action cancelled by user."
    try:
        os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Wrote {len(content)} characters to {os.path.basename(full)}."
    except Exception as e:
        return f"Error writing file: {e}"


def edit_file(path, find, replace):
    """Find and replace text in a file."""
    full = _expand(path)
    if not os.path.isfile(full):
        return f"File not found: {path}"
    if not ask_confirmation(f"Edit file {full}:\nReplace '{find}' with '{replace}'"):
        return "Action cancelled by user."
    try:
        with open(full, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        count = text.count(find)
        if count == 0:
            return f"Text '{find}' not found in {os.path.basename(full)}."
        text = text.replace(find, replace)
        with open(full, "w", encoding="utf-8") as f:
            f.write(text)
        return f"Replaced {count} occurrence(s) in {os.path.basename(full)}."
    except Exception as e:
        return f"Error editing file: {e}"


def append_to_file(path, content):
    """Append content to a file."""
    full = _expand(path)
    if not ask_confirmation(f"Append to file:\n{full}"):
        return "Action cancelled by user."
    try:
        os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
        with open(full, "a", encoding="utf-8") as f:
            f.write(content)
        return f"Appended {len(content)} characters to {os.path.basename(full)}."
    except Exception as e:
        return f"Error appending to file: {e}"


def delete_file(path):
    """Delete a file."""
    full = _expand(path)
    if not os.path.isfile(full):
        return f"File not found: {path}"
    if not ask_confirmation(f"Delete file:\n{full}"):
        return "Action cancelled by user."
    try:
        os.remove(full)
        return f"Deleted {os.path.basename(full)}."
    except Exception as e:
        return f"Error deleting file: {e}"


def create_folder(path):
    """Create a directory (including parents)."""
    full = _expand(path)
    try:
        os.makedirs(full, exist_ok=True)
        return f"Created folder {full}."
    except Exception as e:
        return f"Error creating folder: {e}"


def delete_folder(path):
    """Delete a folder and its contents."""
    full = _expand(path)
    if not os.path.isdir(full):
        return f"Folder not found: {path}"
    if not ask_confirmation(f"Delete folder and ALL contents:\n{full}"):
        return "Action cancelled by user."
    try:
        shutil.rmtree(full)
        return f"Deleted folder {os.path.basename(full)} and all its contents."
    except Exception as e:
        return f"Error deleting folder: {e}"


def list_directory(path=None):
    """List contents of a directory."""
    full = _expand(path) if path else os.path.expanduser("~")
    if not os.path.isdir(full):
        return f"Directory not found: {path}"
    try:
        entries = os.listdir(full)
        if not entries:
            return f"{full} is empty."
        dirs = sorted([e for e in entries if os.path.isdir(os.path.join(full, e))])
        files = sorted([e for e in entries if os.path.isfile(os.path.join(full, e))])
        parts = []
        if dirs:
            parts.append(f"Folders ({len(dirs)}): {', '.join(dirs[:30])}")
            if len(dirs) > 30:
                parts.append(f"  ...and {len(dirs) - 30} more folders")
        if files:
            parts.append(f"Files ({len(files)}): {', '.join(files[:30])}")
            if len(files) > 30:
                parts.append(f"  ...and {len(files) - 30} more files")
        return "\n".join(parts)
    except PermissionError:
        return f"Permission denied: {full}"
    except Exception as e:
        return f"Error listing directory: {e}"


def get_file_info(path):
    """Get file metadata: size, modified date, type."""
    full = _expand(path)
    if not os.path.exists(full):
        return f"Path not found: {path}"
    try:
        stat = os.stat(full)
        size = stat.st_size
        modified = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%B %d, %Y at %I:%M %p")
        created = datetime.datetime.fromtimestamp(stat.st_ctime).strftime("%B %d, %Y at %I:%M %p")

        if size < 1024:
            size_str = f"{size} bytes"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            size_str = f"{size / (1024 * 1024):.1f} MB"
        else:
            size_str = f"{size / (1024 * 1024 * 1024):.2f} GB"

        kind = "Folder" if os.path.isdir(full) else f"File ({os.path.splitext(full)[1] or 'no extension'})"
        return (f"{os.path.basename(full)}: {kind}, {size_str}. "
                f"Modified {modified}. Created {created}.")
    except Exception as e:
        return f"Error getting file info: {e}"


def move_file(source, destination):
    """Move or rename a file/folder."""
    src = _expand(source)
    dst = _expand(destination)
    if not os.path.exists(src):
        return f"Source not found: {source}"
    if not ask_confirmation(f"Move:\n{src}\nto:\n{dst}"):
        return "Action cancelled by user."
    try:
        shutil.move(src, dst)
        return f"Moved {os.path.basename(src)} to {dst}."
    except Exception as e:
        return f"Error moving file: {e}"


def copy_file(source, destination):
    """Copy a file."""
    src = _expand(source)
    dst = _expand(destination)
    if not os.path.exists(src):
        return f"Source not found: {source}"
    try:
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
            shutil.copy2(src, dst)
        return f"Copied {os.path.basename(src)} to {dst}."
    except Exception as e:
        return f"Error copying: {e}"
