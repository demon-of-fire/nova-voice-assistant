"""Action registry — maps Gemini function calls to actual handlers."""

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
from actions.screen import (
    click_at, double_click_at, right_click_at, move_mouse,
    scroll_screen, drag_to, get_screen_size, get_mouse_position,
)
from actions.utility import (
    calculate, create_timer, take_note, list_notes, read_note,
    delete_note, convert_units, lookup_word, get_word_of_the_day,
)
from actions.internet import (
    get_weather, get_news, get_stock_price, get_currency_rate,
    translate_text, check_website, get_public_ip_info, shorten_url,
)
from actions.automation import (
    start_pomodoro, keep_awake, stop_keeping_awake,
    save_window_layout, restore_window_layout, list_layouts,
    get_battery_report,
)
from actions.text_tools import (
    transform_text, count_words, format_json, minify_json,
    convert_base, extract_emails, extract_urls, compare_texts,
)
from actions.system_tools import (
    set_power_plan, get_power_plan, get_storage_usage, list_drives,
    empty_recycle_bin, manage_startup_app, create_restore_point,
    disk_cleanup, get_system_uptime,
)
from actions.more_utility import (
    generate_password, generate_uuid, roll_dice, flip_coin, pick_random,
    create_shopping_list, add_to_shopping_list, remove_from_shopping_list,
    show_shopping_list, set_reminder, start_stopwatch, stop_stopwatch,
    lap_stopwatch,
)
from actions.more_system import (
    list_services, restart_service, start_service, stop_service,
    get_audio_devices, get_display_info, get_env_var, list_env_vars,
    list_startup_programs,
)
from actions.more_internet import (
    get_random_fact, get_joke, get_random_quote, get_timezone_info,
    define_slang, generate_qr_code,
)
from actions.more_text import (
    strip_markdown, caesar_cipher, generate_lorem_ipsum,
    check_palindrome, check_anagram, text_statistics,
)
from actions.more_automation import (
    delayed_screenshot, set_window_transparency, get_clipboard_history,
    clear_clipboard_history, batch_rename, organize_downloads,
)
from actions.more_media import (
    get_now_playing, set_app_volume, take_region_screenshot,
    pick_color, toggle_magnifier, set_magnifier_zoom,
)


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
    # Screen control
    "click_at": click_at,
    "double_click_at": double_click_at,
    "right_click_at": right_click_at,
    "move_mouse": move_mouse,
    "scroll_screen": scroll_screen,
    "drag_to": drag_to,
    "get_screen_size": get_screen_size,
    "get_mouse_position": get_mouse_position,
    # Utility
    "calculate": calculate,
    "create_timer": create_timer,
    "take_note": take_note,
    "list_notes": list_notes,
    "read_note": read_note,
    "delete_note": delete_note,
    "convert_units": convert_units,
    "lookup_word": lookup_word,
    "get_word_of_the_day": get_word_of_the_day,
    # Internet
    "get_weather": get_weather,
    "get_news": get_news,
    "get_stock_price": get_stock_price,
    "get_currency_rate": get_currency_rate,
    "translate_text": translate_text,
    "check_website": check_website,
    "get_public_ip_info": get_public_ip_info,
    "shorten_url": shorten_url,
    # Automation
    "start_pomodoro": start_pomodoro,
    "keep_awake": keep_awake,
    "stop_keeping_awake": stop_keeping_awake,
    "save_window_layout": save_window_layout,
    "restore_window_layout": restore_window_layout,
    "list_layouts": list_layouts,
    "get_battery_report": get_battery_report,
    # Text tools
    "transform_text": transform_text,
    "count_words": count_words,
    "format_json": format_json,
    "minify_json": minify_json,
    "convert_base": convert_base,
    "extract_emails": extract_emails,
    "extract_urls": extract_urls,
    "compare_texts": compare_texts,
    # System tools
    "set_power_plan": set_power_plan,
    "get_power_plan": get_power_plan,
    "get_storage_usage": get_storage_usage,
    "list_drives": list_drives,
    "empty_recycle_bin": empty_recycle_bin,
    "manage_startup_app": manage_startup_app,
    "create_restore_point": create_restore_point,
    "disk_cleanup": disk_cleanup,
    "get_system_uptime": get_system_uptime,
    # More utility
    "generate_password": generate_password,
    "generate_uuid": generate_uuid,
    "roll_dice": roll_dice,
    "flip_coin": flip_coin,
    "pick_random": pick_random,
    "create_shopping_list": create_shopping_list,
    "add_to_shopping_list": add_to_shopping_list,
    "remove_from_shopping_list": remove_from_shopping_list,
    "show_shopping_list": show_shopping_list,
    "set_reminder": set_reminder,
    "start_stopwatch": start_stopwatch,
    "stop_stopwatch": stop_stopwatch,
    "lap_stopwatch": lap_stopwatch,
    # More system
    "list_services": list_services,
    "restart_service": restart_service,
    "start_service": start_service,
    "stop_service": stop_service,
    "get_audio_devices": get_audio_devices,
    "get_display_info": get_display_info,
    "get_env_var": get_env_var,
    "list_env_vars": list_env_vars,
    "list_startup_programs": list_startup_programs,
    # More internet
    "get_random_fact": get_random_fact,
    "get_joke": get_joke,
    "get_random_quote": get_random_quote,
    "get_timezone_info": get_timezone_info,
    "define_slang": define_slang,
    "generate_qr_code": generate_qr_code,
    # More text
    "strip_markdown": strip_markdown,
    "caesar_cipher": caesar_cipher,
    "generate_lorem_ipsum": generate_lorem_ipsum,
    "check_palindrome": check_palindrome,
    "check_anagram": check_anagram,
    "text_statistics": text_statistics,
    # More automation
    "delayed_screenshot": delayed_screenshot,
    "set_window_transparency": set_window_transparency,
    "get_clipboard_history": get_clipboard_history,
    "clear_clipboard_history": clear_clipboard_history,
    "batch_rename": batch_rename,
    "organize_downloads": organize_downloads,
    # More media
    "get_now_playing": get_now_playing,
    "set_app_volume": set_app_volume,
    "take_region_screenshot": take_region_screenshot,
    "pick_color": pick_color,
    "toggle_magnifier": toggle_magnifier,
    "set_magnifier_zoom": set_magnifier_zoom,
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

    _s("quit_assistant", "Quit the Nova voice assistant itself. ONLY use when the user explicitly says 'quit Nova', 'close Nova', 'exit Nova', or 'goodbye Nova'. Do NOT use this for closing other apps or windows — use close_app or close_window instead.", {}),

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

    # ── Screen control (requires screen sharing to be active) ────────────

    _s("click_at", "Click at a specific screen coordinate. Use when the user asks you to click something on screen. You MUST have analyzed a screenshot first to know coordinates.",
       {"x": {"type": "number", "description": "X pixel coordinate"},
        "y": {"type": "number", "description": "Y pixel coordinate"},
        "button": {"type": "string", "description": "Mouse button: left, right, or middle (default: left)"}},
       ["x", "y"]),

    _s("double_click_at", "Double-click at a screen coordinate.",
       {"x": {"type": "number", "description": "X coordinate"},
        "y": {"type": "number", "description": "Y coordinate"}},
       ["x", "y"]),

    _s("right_click_at", "Right-click at a screen coordinate.",
       {"x": {"type": "number", "description": "X coordinate"},
        "y": {"type": "number", "description": "Y coordinate"}},
       ["x", "y"]),

    _s("move_mouse", "Move the mouse cursor to a screen coordinate.",
       {"x": {"type": "number", "description": "X coordinate"},
        "y": {"type": "number", "description": "Y coordinate"}},
       ["x", "y"]),

    _s("scroll_screen", "Scroll the mouse wheel. Positive = up, negative = down.",
       {"clicks": {"type": "number", "description": "Number of scroll clicks (positive=up, negative=down)"},
        "x": {"type": "number", "description": "X coordinate to scroll at (optional)"},
        "y": {"type": "number", "description": "Y coordinate to scroll at (optional)"}},
       ["clicks"]),

    _s("drag_to", "Click and drag from one point to another.",
       {"start_x": {"type": "number"}, "start_y": {"type": "number"},
        "end_x": {"type": "number"}, "end_y": {"type": "number"}},
       ["start_x", "start_y", "end_x", "end_y"]),

    _s("get_screen_size", "Get the screen resolution.", {}),

    _s("get_mouse_position", "Get the current mouse cursor position.", {}),

    # ── Utility ─────────────────────────────────────────────────────────────

    _s("calculate", "Evaluate a math expression (e.g. '2 + 2', 'sqrt(144)', 'sin(30)'). Supports + - * /, trig, log, etc.",
       {"expression": {"type": "string", "description": "Math expression to evaluate"}},
       ["expression"]),

    _s("create_timer", "Set a timer that will notify after N minutes.",
       {"minutes": {"type": "integer", "description": "Number of minutes for the timer"},
        "label": {"type": "string", "description": "Optional label for the timer"}},
       ["minutes"]),

    _s("take_note", "Save a quick text note.",
       {"title": {"type": "string", "description": "Title of the note"},
        "content": {"type": "string", "description": "Content of the note"}},
       ["title", "content"]),

    _s("list_notes", "List all saved notes.", {}),

    _s("read_note", "Read the contents of a saved note by title.",
       {"title": {"type": "string", "description": "Title of the note to read"}},
       ["title"]),

    _s("delete_note", "Delete a saved note by title.",
       {"title": {"type": "string", "description": "Title of the note to delete"}},
       ["title"]),

    _s("convert_units", "Convert between units of measurement (length, weight, temperature, volume).",
       {"value": {"type": "number", "description": "The numeric value to convert"},
        "from_unit": {"type": "string", "description": "Source unit (e.g. inches, cm, pounds, kg, f, c)"},
        "to_unit": {"type": "string", "description": "Target unit"}},
       ["value", "from_unit", "to_unit"]),

    _s("lookup_word", "Look up a word in the dictionary — get definition, pronunciation, and examples.",
       {"word": {"type": "string", "description": "Word to look up"}},
       ["word"]),

    _s("get_word_of_the_day", "Get the word of the day.", {}),

    # ── Internet ────────────────────────────────────────────────────────────

    _s("get_weather", "Get current weather conditions for a location.",
       {"location": {"type": "string", "description": "City name or location (optional, defaults to current area)"}}),

    _s("get_news", "Get the latest news headlines by category.",
       {"category": {"type": "string", "description": "News category: top, world, tech, science, business (default: top)"}}),

    _s("get_stock_price", "Get the current stock price and daily change for a ticker symbol.",
       {"symbol": {"type": "string", "description": "Stock ticker symbol (e.g. AAPL, GOOGL, MSFT)"}},
       ["symbol"]),

    _s("get_currency_rate", "Get the exchange rate between two currencies.",
       {"from_currency": {"type": "string", "description": "Source currency code (e.g. USD, EUR, GBP)"},
        "to_currency": {"type": "string", "description": "Target currency code"}},
       ["from_currency", "to_currency"]),

    _s("translate_text", "Translate text to another language.",
       {"text": {"type": "string", "description": "The text to translate"},
        "target_language": {"type": "string", "description": "Target language (e.g. Spanish, French, German, Japanese)"}},
       ["text", "target_language"]),

    _s("check_website", "Check if a website is reachable and responding.",
       {"url": {"type": "string", "description": "URL of the website to check"}},
       ["url"]),

    _s("get_public_ip_info", "Get the public IP address and location info for this computer.", {}),

    _s("shorten_url", "Shorten a URL using is.gd.",
       {"url": {"type": "string", "description": "The URL to shorten"}},
       ["url"]),

    # ── Automation ──────────────────────────────────────────────────────────

    _s("start_pomodoro", "Start a Pomodoro timer for focused work sessions. Notifies you when time is up.",
       {"minutes": {"type": "integer", "description": "Minutes for the Pomodoro (default 25, max 180)"}}),

    _s("keep_awake", "Prevent the PC from going to sleep for a set number of minutes.",
       {"minutes": {"type": "integer", "description": "Minutes to keep awake (default 60, max 480)"}}),

    _s("stop_keeping_awake", "Allow the PC to sleep normally again. Stops the keep-awake mode.", {}),

    _s("save_window_layout", "Save the current window positions and sizes to a named layout profile.",
       {"name": {"type": "string", "description": "Name for this window layout"}},
       ["name"]),

    _s("restore_window_layout", "Restore a previously saved window layout by name.",
       {"name": {"type": "string", "description": "Name of the layout to restore"}},
       ["name"]),

    _s("list_layouts", "List all saved window layout profiles.", {}),

    _s("get_battery_report", "Get battery charge level, status, and estimated runtime.", {}),

    # ── Text Tools ──────────────────────────────────────────────────────────

    _s("transform_text", "Transform text: uppercase, lowercase, title, reverse, slug, swapcase, invert.",
       {"text": {"type": "string", "description": "Text to transform"},
        "transformation": {"type": "string", "description": "Type: uppercase, lowercase, title, reverse, slug, swapcase, invert"}},
       ["text", "transformation"]),

    _s("count_words", "Count words, characters, sentences, and paragraphs in text.",
       {"text": {"type": "string", "description": "Text to analyze"}},
       ["text"]),

    _s("format_json", "Format/validate a JSON string with proper indentation.",
       {"text": {"type": "string", "description": "JSON text to format"}},
       ["text"]),

    _s("minify_json", "Minify a JSON string by removing whitespace.",
       {"text": {"type": "string", "description": "JSON text to minify"}},
       ["text"]),

    _s("convert_base", "Convert a number between binary (2), octal (8), decimal (10), and hexadecimal (16).",
       {"value": {"type": "string", "description": "The number to convert"},
        "from_base": {"type": "integer", "description": "Source base (2, 8, 10, or 16)"},
        "to_base": {"type": "integer", "description": "Target base (2, 8, 10, or 16)"}},
       ["value", "from_base", "to_base"]),

    _s("extract_emails", "Extract all email addresses from a block of text.",
       {"text": {"type": "string", "description": "Text to extract emails from"}},
       ["text"]),

    _s("extract_urls", "Extract all URLs from a block of text.",
       {"text": {"type": "string", "description": "Text to extract URLs from"}},
       ["text"]),

    _s("compare_texts", "Compare two texts and report how they differ.",
       {"text1": {"type": "string", "description": "First text"},
        "text2": {"type": "string", "description": "Second text"}},
       ["text1", "text2"]),

    # ── System Tools ────────────────────────────────────────────────────────

    _s("set_power_plan", "Change the Windows power plan: balanced, power saver, high performance, or ultimate performance.",
       {"plan": {"type": "string", "description": "Power plan name: balanced, power saver, high performance, ultimate performance"}},
       ["plan"]),

    _s("get_power_plan", "Get the current active Windows power plan.", {}),

    _s("get_storage_usage", "Get disk storage usage for a drive (e.g. C:, D:).",
       {"drive": {"type": "string", "description": "Drive letter (e.g. C:, D:). Defaults to system drive."}}),

    _s("list_drives", "List all available drives with type and free space.", {}),

    _s("empty_recycle_bin", "Empty the Windows Recycle Bin.", {}),

    _s("manage_startup_app", "Enable or disable a startup application.",
       {"action": {"type": "string", "enum": ["enable", "disable"], "description": "Whether to enable or disable"},
        "name": {"type": "string", "description": "Name of the startup entry"}},
       ["action", "name"]),

    _s("create_restore_point", "Create a Windows system restore point. Requires admin rights in some configurations.",
       {"description": {"type": "string", "description": "Description for the restore point"}},
       ["description"]),

    _s("disk_cleanup", "Open the Windows Disk Cleanup utility.", {}),

    _s("get_system_uptime", "Get how long the system has been running since last boot.", {}),

    # ── More Utility ─────────────────────────────────────────────────────────

    _s("generate_password", "Generate a secure random password.",
       {"length": {"type": "integer", "description": "Length of password (4-128, default 16)"},
        "include_symbols": {"type": "boolean", "description": "Include special characters (default true)"}}),

    _s("generate_uuid", "Generate a UUID (Universally Unique Identifier).", {}),

    _s("roll_dice", "Roll virtual dice.",
       {"count": {"type": "integer", "description": "Number of dice to roll (1-20, default 1)"},
        "sides": {"type": "integer", "description": "Sides per die (2-100, default 6)"}}),

    _s("flip_coin", "Flip a coin or multiple coins.",
       {"count": {"type": "integer", "description": "Number of coins to flip (1-20, default 1)"}}),

    _s("pick_random", "Pick random item(s) from a comma-separated list.",
       {"items_text": {"type": "string", "description": "Comma-separated list of items to choose from"},
        "count": {"type": "integer", "description": "Number of items to pick (default 1)"}},
       ["items_text"]),

    _s("create_shopping_list", "Create a new shopping list from comma-separated items.",
       {"items_text": {"type": "string", "description": "Comma-separated items to add"}},
       ["items_text"]),

    _s("add_to_shopping_list", "Add an item to the shopping list.",
       {"item": {"type": "string", "description": "Item to add"}},
       ["item"]),

    _s("remove_from_shopping_list", "Remove an item from the shopping list.",
       {"item": {"type": "string", "description": "Item to remove"}},
       ["item"]),

    _s("show_shopping_list", "Show the current shopping list.", {}),

    _s("set_reminder", "Set a one-time reminder that pops up after N minutes.",
       {"text": {"type": "string", "description": "Reminder text/message"},
        "minutes": {"type": "integer", "description": "Minutes from now (1-1440)"}},
       ["text", "minutes"]),

    _s("start_stopwatch", "Start the stopwatch.", {}),

    _s("stop_stopwatch", "Stop the stopwatch and return elapsed time.", {}),

    _s("lap_stopwatch", "Record a lap on the running stopwatch.", {}),

    # ── More System ──────────────────────────────────────────────────────────

    _s("list_services", "List Windows services by status.",
       {"status": {"type": "string", "enum": ["running", "stopped", "all"], "description": "Filter by status (default: running)"}}),

    _s("restart_service", "Restart a Windows service by name. Requires user confirmation.",
       {"service_name": {"type": "string", "description": "Name of the service to restart"}},
       ["service_name"]),

    _s("start_service", "Start a stopped Windows service.",
       {"service_name": {"type": "string", "description": "Name of the service to start"}},
       ["service_name"]),

    _s("stop_service", "Stop a running Windows service. Requires user confirmation.",
       {"service_name": {"type": "string", "description": "Name of the service to stop"}},
       ["service_name"]),

    _s("get_audio_devices", "List audio input and output devices.", {}),

    _s("get_display_info", "Get display/monitor information: resolution, number of monitors.", {}),

    _s("get_env_var", "Get the value of an environment variable.",
       {"name": {"type": "string", "description": "Environment variable name"}},
       ["name"]),

    _s("list_env_vars", "List environment variables, optionally filtered by a pattern.",
       {"pattern": {"type": "string", "description": "Filter pattern (optional)"}}),

    _s("list_startup_programs", "List programs that run at Windows startup.", {}),

    # ── More Internet ────────────────────────────────────────────────────────

    _s("get_random_fact", "Get a random interesting fact.", {}),

    _s("get_joke", "Get a random joke.", {}),

    _s("get_random_quote", "Get a random inspirational quote.", {}),

    _s("get_timezone_info", "Get current time and timezone info for a location (e.g. America/New_York, Europe/London).",
       {"location": {"type": "string", "description": "Timezone name like America/New_York or Europe/London"}},
       ["location"]),

    _s("define_slang", "Look up a slang term or urban dictionary definition.",
       {"term": {"type": "string", "description": "Slang term to define"}},
       ["term"]),

    _s("generate_qr_code", "Generate a QR code for text or a URL and open it in the browser.",
       {"text": {"type": "string", "description": "Text or URL to encode as QR code"}},
       ["text"]),

    # ── More Text ────────────────────────────────────────────────────────────

    _s("strip_markdown", "Strip markdown formatting from text, returning plain text.",
       {"text": {"type": "string", "description": "Markdown text to strip"}},
       ["text"]),

    _s("caesar_cipher", "Encode or decode text using a Caesar cipher shift.",
       {"text": {"type": "string", "description": "Text to transform"},
        "shift": {"type": "integer", "description": "Shift value (1-25)"},
        "decode": {"type": "boolean", "description": "If true, decode instead of encode"}},
       ["text", "shift"]),

    _s("generate_lorem_ipsum", "Generate lorem ipsum placeholder text.",
       {"paragraphs": {"type": "integer", "description": "Number of paragraphs (1-20, default 1)"},
        "sentences_per": {"type": "integer", "description": "Sentences per paragraph (1-50, default 5)"}}),

    _s("check_palindrome", "Check if text is a palindrome (reads same forward and backward).",
       {"text": {"type": "string", "description": "Text to check"}},
       ["text"]),

    _s("check_anagram", "Check if two texts are anagrams of each other.",
       {"text1": {"type": "string", "description": "First text"},
        "text2": {"type": "string", "description": "Second text"}},
       ["text1", "text2"]),

    _s("text_statistics", "Get detailed text statistics: words, chars, sentences, readability scores.",
       {"text": {"type": "string", "description": "Text to analyze"}},
       ["text"]),

    # ── More Automation ──────────────────────────────────────────────────────

    _s("delayed_screenshot", "Take a screenshot after a specified delay in seconds. Saves to Desktop.",
       {"delay_seconds": {"type": "integer", "description": "Delay in seconds (0-300, default 5)"}}),

    _s("set_window_transparency", "Set the transparency of a window by title (0=invisible, 255=opaque).",
       {"window_title": {"type": "string", "description": "Title of the window"},
        "opacity": {"type": "integer", "description": "Opacity 0-255 (default 128, half transparent)"}},
       ["window_title"]),

    _s("get_clipboard_history", "Show recent clipboard history.", {}),

    _s("clear_clipboard_history", "Clear the clipboard history.", {}),

    _s("batch_rename", "Batch rename files in a directory by find/replace pattern.",
       {"pattern": {"type": "string", "description": "Regex pattern to find in filenames"},
        "replacement": {"type": "string", "description": "Replacement text"},
        "directory": {"type": "string", "description": "Directory to operate in (default: user home)"},
        "dry_run": {"type": "boolean", "description": "Preview changes without applying (default true)"}},
       ["pattern", "replacement"]),

    _s("organize_downloads", "Organize the Downloads folder into subfolders by file type.",
       {"dry_run": {"type": "boolean", "description": "Preview changes without moving files (default true)"}}),

    # ── More Media ───────────────────────────────────────────────────────────

    _s("get_now_playing", "Get info about currently playing media (track title, artist, status).", {}),

    _s("set_app_volume", "Set volume level for a specific application.",
       {"app_name": {"type": "string", "description": "Name of the application process"},
        "level": {"type": "integer", "description": "Volume level 0-100"}},
       ["app_name", "level"]),

    _s("take_region_screenshot", "Take a screenshot of a specific screen region and save to Desktop.",
       {"x1": {"type": "number", "description": "Top-left X coordinate"},
        "y1": {"type": "number", "description": "Top-left Y coordinate"},
        "x2": {"type": "number", "description": "Bottom-right X coordinate"},
        "y2": {"type": "number", "description": "Bottom-right Y coordinate"}},
       ["x1", "y1", "x2", "y2"]),

    _s("pick_color", "Open a color picker dialog and return the selected color.", {}),

    _s("toggle_magnifier", "Toggle Windows Magnifier on or off.",
       {"state": {"type": "string", "description": "on, off, or leave empty to toggle"}}),

    _s("set_magnifier_zoom", "Set Magnifier zoom level (100-1000%). Requires Magnifier to be running.",
       {"level": {"type": "integer", "description": "Zoom level percentage (100-1000, default 200)"}}),
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
