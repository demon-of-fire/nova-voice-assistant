"""Web actions: search, open URLs, YouTube."""

import webbrowser
import urllib.request
import urllib.parse
import json
import re


def search_web(query):
    encoded = urllib.parse.quote_plus(query)
    webbrowser.open(f"https://www.google.com/search?q={encoded}")
    return f"Searching for {query}."


def quick_search(query):
    """Search the web in the background and return a text summary.
    Uses DuckDuckGo instant answer API (no API key needed)."""
    try:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"
        req = urllib.request.Request(url, headers={"User-Agent": "Nova/1.0"})
        resp = urllib.request.urlopen(req, timeout=5)
        data = json.loads(resp.read())

        # Try abstract (Wikipedia-style summary)
        if data.get("AbstractText"):
            return data["AbstractText"][:500]

        # Try answer (calculations, conversions, etc.)
        if data.get("Answer"):
            return str(data["Answer"])[:500]

        # Try related topics
        topics = data.get("RelatedTopics", [])
        if topics:
            results = []
            for t in topics[:3]:
                if isinstance(t, dict) and t.get("Text"):
                    results.append(t["Text"][:150])
            if results:
                return " ".join(results)

        # Fallback: scrape Google snippet
        return _google_snippet(query)
    except Exception:
        return _google_snippet(query)


def _google_snippet(query):
    """Fallback: fetch Google search and extract a snippet."""
    try:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={encoded}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        resp = urllib.request.urlopen(req, timeout=5)
        html = resp.read().decode("utf-8", errors="ignore")

        # Try to find featured snippet or answer box
        patterns = [
            r'<div[^>]*class="[^"]*BNeawe[^"]*"[^>]*>(.*?)</div>',
            r'<span[^>]*class="[^"]*hgKElc[^"]*"[^>]*>(.*?)</span>',
        ]
        for pat in patterns:
            m = re.search(pat, html)
            if m:
                text = re.sub(r'<[^>]+>', '', m.group(1)).strip()
                if len(text) > 20:
                    return text[:500]

        return f"I searched for {query} but couldn't extract a quick answer. Want me to open it in your browser?"
    except Exception:
        return f"Couldn't search right now. Want me to open Google for {query}?"


def open_url(url):
    webbrowser.open(url)
    return f"Opened {url}."


def search_youtube(query):
    encoded = urllib.parse.quote_plus(query)
    webbrowser.open(f"https://www.youtube.com/results?search_query={encoded}")
    return f"Searching YouTube for {query}."
