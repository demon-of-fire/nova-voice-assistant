"""Action registry — maps Gemini function calls to actual handlers."""

from google import genai

from actions.apps import launch_app, close_app
from actions.windows import minimize_window, maximize_window, close_window, switch_window, snap_window
from actions.input_control import type_text, press_keys
from actions.system import (
    set_volume, get_volume, set_brightness, get_system_info,
    shutdown_pc, restart_pc, lock_pc, cancel_shutdown,
    get_time, get_date,
    media_play_pause, media_next, media_previous, media_stop,
    quit_assistant,
)
from actions.web import search_web, quick_search, open_url, search_youtube
from actions.files import open_folder, find_files, copy_to_clipboard, read_clipboard
from actions.shell import run_command, run_powershell, install_app, uninstall_app, list_installed_apps
from actions.filesystem import (
    read_file, write_file, edit_file, append_to_file,
    delete_file, create_folder, delete_folder, list_directory,
    get_file_info, move_file, copy_file,
)
from actions.process import list_processes, kill_process, get_process_info
from actions.network import get_network_info, get_wifi_networks, ping, get_public_ip
from actions.code import run_python, create_script


# Maps function name -> callable
ACTIONS = {
    "launch_app": launch_app,
    "close_app": close_app,
    "minimize_window": minimize_window,
    "maximize_window": maximize_window,
    "close_window": close_window,
    "switch_window": switch_window,
    "snap_window": snap_window,
    "type_text": type_text,
    "press_keys": press_keys,
    "set_volume": set_volume,
    "get_volume": get_volume,
    "set_brightness": set_brightness,
    "get_system_info": get_system_info,
    "shutdown_pc": shutdown_pc,
    "restart_pc": restart_pc,
    "lock_pc": lock_pc,
    "cancel_shutdown": cancel_shutdown,
    "get_time": get_time,
    "get_date": get_date,
    "media_play_pause": media_play_pause,
    "media_next": media_next,
    "media_previous": media_previous,
    "media_stop": media_stop,
    "quit_assistant": quit_assistant,
    "search_web": search_web,
    "quick_search": quick_search,
    "open_url": open_url,
    "search_youtube": search_youtube,
    "open_folder": open_folder,
    "find_files": find_files,
    "copy_to_clipboard": copy_to_clipboard,
    "read_clipboard": read_clipboard,
    # Shell
    "run_command": run_command,
    "run_powershell": run_powershell,
    "install_app": install_app,
    "uninstall_app": uninstall_app,
    "list_installed_apps": list_installed_apps,
    # Filesystem
    "read_file": read_file,
    "write_file": write_file,
    "edit_file": edit_file,
    "append_to_file": append_to_file,
    "delete_file": delete_file,
    "create_folder": create_folder,
    "delete_folder": delete_folder,
    "list_directory": list_directory,
    "get_file_info": get_file_info,
    "move_file": move_file,
    "copy_file": copy_file,
    # Process
    "list_processes": list_processes,
    "kill_process": kill_process,
    "get_process_info": get_process_info,
    # Network
    "get_network_info": get_network_info,
    "get_wifi_networks": get_wifi_networks,
    "ping": ping,
    "get_public_ip": get_public_ip,
    # Code
    "run_python": run_python,
    "create_script": create_script,
}


def _s(name, desc, props, required=None):
    """Shorthand to build a FunctionDeclaration dict."""
    d = {"name": name, "description": desc, "parameters": {"type": "object", "properties": props}}
    if required:
        d["parameters"]["required"] = required
    return d


TOOL_DECLARATIONS = [
    _s("launch_app", "Open/launch an application by name on the user's PC.",
       {"app_name": {"type": "string", "description": "Name of the app to open (e.g. 'Spotify', 'Chrome', 'File Explorer')"}},
       ["app_name"]),

    _s("close_app", "Close/kill a running application by name.",
       {"app_name": {"type": "string", "description": "Name of the app to close"}},
       ["app_name"]),

    _s("minimize_window", "Minimize a window. If no title given, minimizes the current foreground window.",
       {"window_title": {"type": "string", "description": "Part of the window title to match (optional)"}}),

    _s("maximize_window", "Maximize a window. If no title given, maximizes the current foreground window.",
       {"window_title": {"type": "string", "description": "Part of the window title to match (optional)"}}),

    _s("close_window", "Close a window gracefully. If no title given, closes the foreground window.",
       {"window_title": {"type": "string", "description": "Part of the window title to match (optional)"}}),

    _s("switch_window", "Bring a window to the foreground / switch to it.",
       {"window_title": {"type": "string", "description": "Part of the window title to switch to"}},
       ["window_title"]),

    _s("snap_window", "Snap a window to the left or right half of the screen.",
       {"direction": {"type": "string", "enum": ["left", "right"], "description": "Which half of the screen"},
        "window_title": {"type": "string", "description": "Part of the window title (optional)"}},
       ["direction"]),

    _s("type_text", "Type out text using the keyboard, as if the user typed it.",
       {"text": {"type": "string", "description": "The text to type"}},
       ["text"]),

    _s("press_keys", "Press a keyboard shortcut or key combination (e.g. 'ctrl+c', 'alt+tab', 'enter').",
       {"keys": {"type": "string", "description": "Key combo like 'ctrl+c', 'alt+f4', 'win+d'"}},
       ["keys"]),

    _s("set_volume", "Set system volume level.",
       {"level": {"type": "integer", "description": "Volume level 0-100"}},
       ["level"]),

    _s("get_volume", "Get the current system volume level.", {}),

    _s("set_brightness", "Set screen brightness level.",
       {"level": {"type": "integer", "description": "Brightness level 0-100"}},
       ["level"]),

    _s("get_system_info", "Get system info: CPU, RAM, battery, OS.", {}),

    _s("shutdown_pc", "Schedule a PC shutdown.",
       {"delay_seconds": {"type": "integer", "description": "Delay in seconds before shutdown (default 60)"}}),

    _s("restart_pc", "Schedule a PC restart.",
       {"delay_seconds": {"type": "integer", "description": "Delay in seconds before restart (default 60)"}}),

    _s("lock_pc", "Lock the workstation immediately.", {}),

    _s("cancel_shutdown", "Cancel a pending shutdown or restart.", {}),

    _s("get_time", "Get the current time.", {}),

    _s("get_date", "Get today's date.", {}),

    _s("media_play_pause", "Play or pause the current media (music, video, podcast). Works with Spotify, YouTube, VLC, and any media player.", {}),

    _s("media_next", "Skip to the next track or video in any media player.", {}),

    _s("media_previous", "Go back to the previous track or video in any media player.", {}),

    _s("media_stop", "Stop media playback entirely.", {}),

    _s("quit_assistant", "Quit and close the Nova assistant completely. Use when the user says goodbye, close, quit, exit, or shut down Nova.", {}),

    _s("search_web", "Search Google for a query and OPEN it in the browser. Only use this when the user explicitly wants to see results in their browser.",
       {"query": {"type": "string", "description": "What to search for"}},
       ["query"]),

    _s("quick_search", "Search the web in the background and return a text answer WITHOUT opening a browser. Use this for questions, facts, live scores, weather, definitions, calculations — anything where the user just wants a spoken answer.",
       {"query": {"type": "string", "description": "What to search for"}},
       ["query"]),

    _s("open_url", "Open a URL in the default browser.",
       {"url": {"type": "string", "description": "The URL to open"}},
       ["url"]),

    _s("search_youtube", "Search YouTube for a query.",
       {"query": {"type": "string", "description": "What to search for on YouTube"}},
       ["query"]),

    _s("open_folder", "Open a folder in File Explorer.",
       {"path": {"type": "string", "description": "Folder path to open"}},
       ["path"]),

    _s("find_files", "Search for files by name on the PC.",
       {"query": {"type": "string", "description": "Filename or pattern to search for"},
        "directory": {"type": "string", "description": "Directory to search in (default: user home)"}},
       ["query"]),

    _s("copy_to_clipboard", "Copy text to the clipboard.",
       {"text": {"type": "string", "description": "Text to copy"}},
       ["text"]),

    _s("read_clipboard", "Read the current clipboard contents.", {}),

    # ── Shell ───────────────────────────────────────────────────────────────

    _s("run_command", "Run a shell command (cmd or powershell) and return its output. Requires user confirmation.",
       {"command": {"type": "string", "description": "The command to execute"},
        "shell": {"type": "string", "enum": ["cmd", "powershell"], "description": "Shell to use (default: cmd)"}},
       ["command"]),

    _s("run_powershell", "Run a PowerShell command and return its output. Requires user confirmation.",
       {"command": {"type": "string", "description": "The PowerShell command to execute"}},
       ["command"]),

    _s("install_app", "Install an application using winget. Requires user confirmation.",
       {"app_name": {"type": "string", "description": "Name of the app to install"}},
       ["app_name"]),

    _s("uninstall_app", "Uninstall an application using winget. Requires user confirmation.",
       {"app_name": {"type": "string", "description": "Name of the app to uninstall"}},
       ["app_name"]),

    _s("list_installed_apps", "List all installed applications using winget.", {}),

    # ── Filesystem ──────────────────────────────────────────────────────────

    _s("read_file", "Read the contents of a text file (first 3000 characters).",
       {"path": {"type": "string", "description": "Path to the file to read"}},
       ["path"]),

    _s("write_file", "Write content to a file (creates or overwrites). Requires user confirmation.",
       {"path": {"type": "string", "description": "Path of the file to write"},
        "content": {"type": "string", "description": "Content to write to the file"}},
       ["path", "content"]),

    _s("edit_file", "Find and replace text in a file. Requires user confirmation.",
       {"path": {"type": "string", "description": "Path to the file to edit"},
        "find": {"type": "string", "description": "Text to find"},
        "replace": {"type": "string", "description": "Text to replace it with"}},
       ["path", "find", "replace"]),

    _s("append_to_file", "Append content to the end of a file. Requires user confirmation.",
       {"path": {"type": "string", "description": "Path to the file"},
        "content": {"type": "string", "description": "Content to append"}},
       ["path", "content"]),

    _s("delete_file", "Delete a file. Requires user confirmation.",
       {"path": {"type": "string", "description": "Path to the file to delete"}},
       ["path"]),

    _s("create_folder", "Create a directory (including parent directories).",
       {"path": {"type": "string", "description": "Path of the folder to create"}},
       ["path"]),

    _s("delete_folder", "Delete a folder and all its contents. Requires user confirmation.",
       {"path": {"type": "string", "description": "Path of the folder to delete"}},
       ["path"]),

    _s("list_directory", "List files and folders in a directory.",
       {"path": {"type": "string", "description": "Directory path to list (default: user home)"}}),

    _s("get_file_info", "Get file metadata: size, modified date, type.",
       {"path": {"type": "string", "description": "Path to the file or folder"}},
       ["path"]),

    _s("move_file", "Move or rename a file or folder. Requires user confirmation.",
       {"source": {"type": "string", "description": "Current path"},
        "destination": {"type": "string", "description": "New path"}},
       ["source", "destination"]),

    _s("copy_file", "Copy a file or folder to a new location.",
       {"source": {"type": "string", "description": "Source path"},
        "destination": {"type": "string", "description": "Destination path"}},
       ["source", "destination"]),

    # ── Process ─────────────────────────────────────────────────────────────

    _s("list_processes", "List the top 20 processes by CPU and memory usage.", {}),

    _s("kill_process", "Kill a running process by name or PID. Requires user confirmation.",
       {"name_or_pid": {"type": "string", "description": "Process name or PID to kill"}},
       ["name_or_pid"]),

    _s("get_process_info", "Get detailed info about a running process.",
       {"name": {"type": "string", "description": "Process name to look up"}},
       ["name"]),

    # ── Network ─────────────────────────────────────────────────────────────

    _s("get_network_info", "Get network info: local IP, WiFi name, connection status.", {}),

    _s("get_wifi_networks", "List available WiFi networks nearby.", {}),

    _s("ping", "Ping a host and return latency info.",
       {"host": {"type": "string", "description": "Hostname or IP to ping"}},
       ["host"]),

    _s("get_public_ip", "Get the public IP address of this computer.", {}),

    # ── Code ────────────────────────────────────────────────────────────────

    _s("run_python", "Execute Python code and return its output. Requires user confirmation.",
       {"code": {"type": "string", "description": "Python code to execute"}},
       ["code"]),

    _s("create_script", "Create a script file with code. Requires user confirmation.",
       {"path": {"type": "string", "description": "File path for the script"},
        "code": {"type": "string", "description": "The script code"},
        "language": {"type": "string", "description": "Programming language (default: python)"}},
       ["path", "code"]),
]


def execute(fn_name, args):
    """Execute a registered action. Returns a result string."""
    handler = ACTIONS.get(fn_name)
    if not handler:
        return f"Unknown action: {fn_name}"
    try:
        # Filter out None args (Gemini sometimes sends explicit nulls)
        clean_args = {k: v for k, v in args.items() if v is not None}
        return handler(**clean_args)
    except Exception as e:
        return f"Error running {fn_name}: {e}"
