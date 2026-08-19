"""More utility actions: password gen, UUID, dice, coin, random, shopping, reminders, stopwatch."""

import os
import json
import random
import string
import uuid
import threading
import time
import datetime
import re
from actions.confirmation import ask_confirmation


SHOPPING_FILE = os.path.join(os.path.expanduser("~"), ".nova_shopping_list.json")
REMINDERS_FILE = os.path.join(os.path.expanduser("~"), ".nova_reminders.json")
_stopwatch_start = None
_stopwatch_laps = []
_stopwatch_running = False


def generate_password(length=16, include_symbols=True):
    """Generate a secure random password."""
    length = max(4, min(128, int(length)))
    chars = string.ascii_letters + string.digits
    if include_symbols:
        chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
    password = "".join(random.SystemRandom().choice(chars) for _ in range(length))
    return f"Generated password ({length} chars): {password}"


def generate_uuid():
    """Generate a UUID (Universally Unique Identifier)."""
    return f"UUID: {uuid.uuid4()}"


def roll_dice(count=1, sides=6):
    """Roll virtual dice."""
    count = max(1, min(20, int(count)))
    sides = max(2, min(100, int(sides)))
    rolls = [random.randint(1, sides) for _ in range(count)]
    total = sum(rolls)
    if count == 1:
        return f"Rolled a d{sides}: {rolls[0]}"
    return f"Rolled {count}d{sides}: {rolls} (total: {total})"


def flip_coin(count=1):
    """Flip a coin or multiple coins."""
    count = max(1, min(20, int(count)))
    results = [random.choice(["heads", "tails"]) for _ in range(count)]
    if count == 1:
        return f"Coin flip: {results[0]}"
    heads = results.count("heads")
    tails = results.count("tails")
    return f"Flipped {count} coins: {heads} heads, {tails} tails"


def pick_random(items_text, count=1):
    """Pick random item(s) from a comma-separated list."""
    items = [i.strip() for i in items_text.split(",") if i.strip()]
    if not items:
        return "No items to pick from."
    count = max(1, min(len(items), int(count)))
    picked = random.sample(items, count)
    if count == 1:
        return f"Random pick: {picked[0]}"
    return f"Random picks ({count}): {', '.join(picked)}"


def _load_shopping():
    if os.path.exists(SHOPPING_FILE):
        try:
            with open(SHOPPING_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return []


def _save_shopping(items):
    with open(SHOPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)


def create_shopping_list(items_text):
    """Create a new shopping list from comma-separated items."""
    items = [i.strip() for i in items_text.split(",") if i.strip()]
    if not items:
        return "No items provided."
    _save_shopping(items)
    return f"Shopping list created with {len(items)} items: {', '.join(items)}"


def add_to_shopping_list(item):
    """Add an item to the shopping list."""
    items = _load_shopping()
    items.append(item.strip())
    _save_shopping(items)
    return f"Added '{item}' to shopping list."


def remove_from_shopping_list(item):
    """Remove an item from the shopping list."""
    items = _load_shopping()
    filtered = [i for i in items if i.lower() != item.strip().lower()]
    if len(filtered) == len(items):
        return f"'{item}' not found in shopping list."
    _save_shopping(filtered)
    return f"Removed '{item}' from shopping list."


def show_shopping_list():
    """Show the current shopping list."""
    items = _load_shopping()
    if not items:
        return "Shopping list is empty."
    return f"Shopping list ({len(items)} items): " + ", ".join(items)


def _load_reminders():
    if os.path.exists(REMINDERS_FILE):
        try:
            with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return []


def _save_reminders(reminders):
    with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(reminders, f, indent=2)


def set_reminder(text, minutes):
    """Set a one-time reminder that fires after N minutes."""
    minutes = max(1, min(1440, int(minutes)))
    reminder = {
        "text": text.strip(),
        "minutes": minutes,
        "created": datetime.datetime.now().isoformat(),
    }
    reminders = _load_reminders()
    reminders.append(reminder)
    _save_reminders(reminders)

    def _fire():
        time.sleep(minutes * 60)
        import subprocess
        subprocess.Popen(
            ["powershell", "-NoProfile", "-Command",
             f"[System.Windows.MessageBox]::Show('{text.strip()}', 'Nova Reminder')"],
        )
        current = _load_reminders()
        current = [r for r in current if r["created"] != reminder["created"]]
        _save_reminders(current)

    threading.Thread(target=_fire, daemon=True).start()
    return f"Reminder set for {minutes} minutes: '{text.strip()}'."


def start_stopwatch():
    """Start the stopwatch."""
    global _stopwatch_start, _stopwatch_running, _stopwatch_laps
    if _stopwatch_running:
        return "Stopwatch is already running."
    _stopwatch_start = time.time()
    _stopwatch_laps = []
    _stopwatch_running = True
    return "Stopwatch started."


def stop_stopwatch():
    """Stop the stopwatch and return elapsed time."""
    global _stopwatch_running
    if not _stopwatch_running:
        return "No stopwatch running."
    elapsed = time.time() - _stopwatch_start
    _stopwatch_running = False
    mins = int(elapsed // 60)
    secs = elapsed % 60
    return f"Stopwatch stopped at {mins}m {secs:.1f}s."


def lap_stopwatch():
    """Record a lap on the stopwatch."""
    if not _stopwatch_running:
        return "No stopwatch running."
    now = time.time()
    elapsed = now - _stopwatch_start
    _stopwatch_laps.append(elapsed)
    mins = int(elapsed // 60)
    secs = elapsed % 60
    return f"Lap {len(_stopwatch_laps)}: {mins}m {secs:.1f}s."
