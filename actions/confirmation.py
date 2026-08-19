"""Confirmation dialog for dangerous actions — uses the webview UI modal."""

# Actions that have their OWN confirmation inside the handler are NOT listed here
# to avoid double-confirmation. Only actions WITHOUT handler-level confirmation
# are listed (plus quit_assistant which is always allowed).
DANGEROUS_ACTIONS = {
    "shutdown_pc", "restart_pc",
    "empty_recycle_bin",
    "manage_startup_app",
    "restart_service", "stop_service",
    "quit_assistant",
}

_settings_ref = None
_ui_ref = None


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


def ask_confirmation(action_description):
    """Show a confirmation dialog via the webview modal. Returns True if user confirms.

    Falls back to auto-deny if no UI is available.
    If confirm_actions is disabled in settings, auto-allows (returns True).
    """
    if _settings_ref is not None and not _settings_ref.get("confirm_actions"):
        return True
    if _ui_ref:
        return _ui_ref.ask_confirmation(action_description)
    return False
