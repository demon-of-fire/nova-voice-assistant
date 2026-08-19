"""Utility actions: calculator, timer, notes, units, dictionary."""

import os
import subprocess
import datetime
import json
import urllib.request
import urllib.parse
import re
import math
from actions.confirmation import ask_confirmation


NOTES_DIR = os.path.join(os.path.expanduser("~"), "nova_notes")


def _ensure_notes_dir():
    os.makedirs(NOTES_DIR, exist_ok=True)


def calculate(expression):
    """Evaluate a math expression safely."""
    allowed = {
        "abs": abs, "round": round, "min": min, "max": max,
        "sum": sum, "pow": pow, "int": int, "float": float,
        "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
        "tan": math.tan, "log": math.log, "log10": math.log10,
        "ceil": math.ceil, "floor": math.floor, "pi": math.pi,
        "e": math.e, "degrees": math.degrees, "radians": math.radians,
    }
    try:
        result = eval(expression, {"__builtins__": {}}, allowed)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Couldn't calculate: {e}"


def create_timer(minutes, label=""):
    """Create a Windows timer notification that fires after N minutes."""
    seconds = int(minutes) * 60
    label = label or f"Timer ({minutes} min)"
    ps_cmd = (
        f"Start-Sleep -Seconds {seconds}; "
        f"[System.Windows.MessageBox]::Show('{label} is done!', 'Nova Timer')"
    )
    subprocess.Popen(
        ["powershell", "-NoProfile", "-Command", ps_cmd],
        close_fds=True,
    )
    return f"Timer set for {minutes} minutes."


def take_note(title, content):
    """Save a quick note."""
    _ensure_notes_dir()
    safe_title = re.sub(r'[<>:"/\\|?*]', "_", title.strip())
    if not safe_title:
        safe_title = f"note_{datetime.datetime.now():%Y%m%d_%H%M%S}"
    path = os.path.join(NOTES_DIR, f"{safe_title}.txt")
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        return f"Saved note '{safe_title}'."
    except Exception as e:
        return f"Couldn't save note: {e}"


def list_notes():
    """List all saved notes."""
    _ensure_notes_dir()
    try:
        files = sorted(os.listdir(NOTES_DIR))
        if not files:
            return "No notes saved yet."
        notes = []
        for f in files:
            if f.endswith(".txt"):
                path = os.path.join(NOTES_DIR, f)
                size = os.path.getsize(path)
                modified = datetime.datetime.fromtimestamp(
                    os.path.getmtime(path)
                ).strftime("%b %d %I:%M %p")
                notes.append(f"{f[:-4]} ({size}B, {modified})")
        return f"Notes ({len(notes)}): " + ", ".join(notes[:20])
    except Exception as e:
        return f"Error listing notes: {e}"


def read_note(title):
    """Read the contents of a note by title."""
    _ensure_notes_dir()
    safe_title = re.sub(r'[<>:"/\\|?*]', "_", title.strip())
    path = os.path.join(NOTES_DIR, f"{safe_title}.txt")
    if not os.path.isfile(path):
        return f"Note '{safe_title}' not found."
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read(2000)
        if len(content) == 2000:
            content += "... (truncated)"
        return f"Note '{safe_title}': {content}"
    except Exception as e:
        return f"Error reading note: {e}"


def delete_note(title):
    """Delete a saved note. Requires confirmation."""
    _ensure_notes_dir()
    safe_title = re.sub(r'[<>:"/\\|?*]', "_", title.strip())
    path = os.path.join(NOTES_DIR, f"{safe_title}.txt")
    if not os.path.isfile(path):
        return f"Note '{safe_title}' not found."
    if not ask_confirmation(f"Delete note '{safe_title}'?"):
        return "Cancelled."
    try:
        os.remove(path)
        return f"Deleted note '{safe_title}'."
    except Exception as e:
        return f"Error deleting note: {e}"


def convert_units(value, from_unit, to_unit):
    """Convert between common units of measurement."""
    value = float(value)
    from_l = from_unit.lower().strip()
    to_l = to_unit.lower().strip()

    conversions = {
        # Length
        ("inches", "cm"): lambda v: v * 2.54,
        ("cm", "inches"): lambda v: v / 2.54,
        ("feet", "meters"): lambda v: v * 0.3048,
        ("meters", "feet"): lambda v: v / 0.3048,
        ("miles", "km"): lambda v: v * 1.60934,
        ("km", "miles"): lambda v: v / 1.60934,
        # Weight
        ("pounds", "kg"): lambda v: v * 0.453592,
        ("kg", "pounds"): lambda v: v / 0.453592,
        ("ounces", "grams"): lambda v: v * 28.3495,
        ("grams", "ounces"): lambda v: v / 28.3495,
        # Temperature
        ("f", "c"): lambda v: (v - 32) * 5 / 9,
        ("c", "f"): lambda v: v * 9 / 5 + 32,
        ("fahrenheit", "celsius"): lambda v: (v - 32) * 5 / 9,
        ("celsius", "fahrenheit"): lambda v: v * 9 / 5 + 32,
        # Volume
        ("gallons", "liters"): lambda v: v * 3.78541,
        ("liters", "gallons"): lambda v: v / 3.78541,
        ("quarts", "liters"): lambda v: v * 0.946353,
        ("liters", "quarts"): lambda v: v / 0.946353,
    }

    key = (from_l, to_l)
    if key in conversions:
        result = conversions[key](value)
        return f"{value} {from_unit} = {result:.4f} {to_unit}"
    return f"Conversion from {from_unit} to {to_unit} not supported."


def lookup_word(word):
    """Look up a word definition using the FreeDictionary API."""
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{urllib.parse.quote(word)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Nova/2.0"})
        resp = urllib.request.urlopen(req, timeout=5)
        data = json.loads(resp.read())
        if not data:
            return f"Couldn't find '{word}'."

        entry = data[0]
        word_text = entry.get("word", word)
        phonetics = entry.get("phonetic", "")
        meanings = entry.get("meanings", [])

        parts = [f"{word_text}{' (' + phonetics + ')' if phonetics else ''}"]
        for m in meanings[:3]:
            pos = m.get("partOfSpeech", "")
            defs = m.get("definitions", [])
            if defs:
                d = defs[0]
                definition = d.get("definition", "")
                example = d.get("example", "")
                parts.append(f"({pos}) {definition}")
                if example:
                    parts.append(f"  e.g. '{example}'")

        return " ".join(parts[:5])
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return f"Couldn't find '{word}'."
        return f"Dictionary lookup failed: {e}"
    except Exception as e:
        return f"Dictionary lookup error: {e}"


def get_word_of_the_day():
    """Get the word of the day."""
    try:
        url = "https://api.dictionaryapi.dev/api/v2/entries/en/word"
        req = urllib.request.Request(url, headers={"User-Agent": "Nova/2.0"})
        resp = urllib.request.urlopen(req, timeout=5)
        data = json.loads(resp.read())
        if data and len(data) > 0:
            entry = data[0]
            word = entry.get("word", "")
            meanings = entry.get("meanings", [])
            if meanings and meanings[0].get("definitions"):
                defn = meanings[0]["definitions"][0].get("definition", "")
                return f"Word of the day: {word}. {defn}"
        return lookup_word("serendipity")
    except Exception:
        return lookup_word("serendipity")
