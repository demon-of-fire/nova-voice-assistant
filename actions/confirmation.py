"""Confirmation dialog for dangerous actions — uses the webview UI modal."""

DANGEROUS_ACTIONS = {
    "delete_file", "delete_folder",
    "write_file", "edit_file", "append_to_file", "move_file",
    "install_app", "uninstall_app",
    "run_command", "run_powershell",
    "kill_process", "close_app",
    "shutdown_pc", "restart_pc",
    "run_python", "create_script",
    "quit_assistant",
}

_settings_ref = None
_ui_ref = None
_suppress = False


def set_settings(settings):
    """Store a reference to Settings so we can check confirm_actions."""
    global _settings_ref
    _settings_ref = settings


def set_ui(ui):
    """Store a reference to the UI so we can show the confirmation modal."""
    global _ui_ref
    _ui_ref = ui


def needs_confirmation(action_name):
    """Return True if the action requires user confirmation before executing."""
    if _settings_ref and not _settings_ref.get("confirm_actions"):
        return False
    return action_name in DANGEROUS_ACTIONS


def suppress_next():
    """Suppress the next ask_confirmation call (used after brain.py already prompted).

    Prevents double confirmation dialogs: brain.py prompts once, then the
    action handler's own ask_confirmation is skipped.
    """
    global _suppress
    _suppress = True


def ask_confirmation(action_description):
    """Show a confirmation dialog via the webview modal. Returns True if user confirms.

    Falls back to auto-deny if no UI is available.
    """
    global _suppress
    if _suppress:
        _suppress = False
        return True
    if _ui_ref:
        return _ui_ref.ask_confirmation(action_description)
    return False
