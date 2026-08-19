"""More internet actions: facts, jokes, quotes, timezone, QR codes, slang."""

import json
import urllib.request
import urllib.parse
import webbrowser
import tempfile
from actions.confirmation import ask_confirmation


def _fetch_json(url, timeout=8):
    req = urllib.request.Request(url, headers={"User-Agent": "Nova/2.0"})
    resp = urllib.request.urlopen(req, timeout=timeout)
    return json.loads(resp.read())


def _fetch_text(url, timeout=8):
    req = urllib.request.Request(url, headers={"User-Agent": "Nova/2.0"})
    resp = urllib.request.urlopen(req, timeout=timeout)
    return resp.read().decode("utf-8", errors="replace")


def get_random_fact():
    """Get a random interesting fact."""
    try:
        data = _fetch_json("https://uselessfacts.jsph.pl/api/v2/facts/random?language=en", timeout=6)
        fact = data.get("text", "")
        if fact:
            return f"Did you know? {fact}"
        return "Couldn't fetch a fact right now."
    except Exception as e:
        return f"Couldn't fetch fact: {e}"


def get_joke():
    """Get a random joke."""
    try:
        data = _fetch_json("https://v2.jokeapi.dev/joke/Any?type=twopart&safe-mode", timeout=6)
        setup = data.get("setup", "")
        delivery = data.get("delivery", "")
        if setup and delivery:
            return f"{setup} ... {delivery}"
        return "Couldn't fetch a joke right now."
    except Exception:
        try:
            data = _fetch_json("https://official-joke-api.appspot.com/random_joke", timeout=6)
            setup = data.get("setup", "")
            punchline = data.get("punchline", "")
            if setup and punchline:
                return f"{setup} ... {punchline}"
            return "Couldn't fetch a joke right now."
        except Exception as e:
            return f"Couldn't fetch joke: {e}"


def get_random_quote():
    """Get a random inspirational quote."""
    try:
        data = _fetch_json("https://zenquotes.io/api/random", timeout=6)
        if data and len(data) > 0:
            q = data[0].get("q", "")
            a = data[0].get("a", "")
            if q and a:
                return f'"{q}" - {a}'
        return "Couldn't fetch a quote right now."
    except Exception:
        try:
            data = _fetch_json("https://api.quotable.io/random", timeout=6)
            content = data.get("content", "")
            author = data.get("author", "")
            if content:
                return f'"{content}" - {author}'
            return "Couldn't fetch a quote right now."
        except Exception as e:
            return f"Couldn't fetch quote: {e}"


def get_timezone_info(location):
    """Get current time and timezone info for a location using WorldTime API."""
    try:
        loc = urllib.parse.quote(location.strip())
        data = _fetch_json(f"https://worldtimeapi.org/api/timezone/{loc}", timeout=8)
        datetime_str = data.get("datetime", "")
        timezone = data.get("timezone", "")
        abbrev = data.get("abbreviation", "")
        if datetime_str:
            date_part = datetime_str[:10]
            time_part = datetime_str[11:19]
            return f"Time in {location}: {date_part} {time_part}, timezone: {timezone} ({abbrev})."
        return f"Couldn't find timezone info for '{location}'. Try a timezone like 'America/New_York' or 'Europe/London'."
    except Exception:
        pass

    try:
        data = _fetch_json("http://worldtimeapi.org/api/ip", timeout=6)
        datetime_str = data.get("datetime", "")
        timezone = data.get("timezone", "")
        abbrev = data.get("abbreviation", "")
        if datetime_str:
            date_part = datetime_str[:10]
            time_part = datetime_str[11:19]
            return f"Current time: {date_part} {time_part}, timezone: {timezone} ({abbrev})."
        return f"Couldn't get timezone info for '{location}'."
    except Exception as e:
        return f"Couldn't fetch timezone info: {e}"


def define_slang(term):
    """Look up a slang term using an online dictionary."""
    try:
        encoded = urllib.parse.quote(term.strip())
        data = _fetch_json(f"https://api.urbandictionary.com/v0/define?term={encoded}", timeout=6)
        entries = data.get("list", [])
        if entries:
            entry = entries[0]
            definition = entry.get("definition", "").replace("[", "").replace("]", "")
            example = entry.get("example", "").replace("[", "").replace("]", "")
            result = f"{term}: {definition[:500]}"
            if example:
                result += f" e.g. {example[:200]}"
            return result
        return f"Couldn't find slang definition for '{term}'."
    except Exception as e:
        return f"Couldn't look up slang: {e}"


def generate_qr_code(text):
    """Generate a QR code using an API and open it in the browser."""
    try:
        encoded = urllib.parse.quote(text.strip())
        url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded}"
        webbrowser.open(url)
        return f"Opened QR code for: {text[:50]}"
    except Exception as e:
        return f"Couldn't generate QR code: {e}"
