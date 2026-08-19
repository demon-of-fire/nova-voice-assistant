"""Internet actions: weather, news, stocks, translation, URLs."""

import json
import urllib.request
import urllib.parse
import subprocess
import re


def _fetch_json(url, timeout=8):
    req = urllib.request.Request(url, headers={"User-Agent": "Nova/2.0"})
    resp = urllib.request.urlopen(req, timeout=timeout)
    return json.loads(resp.read())


def _fetch_text(url, timeout=8):
    req = urllib.request.Request(url, headers={"User-Agent": "Nova/2.0"})
    resp = urllib.request.urlopen(req, timeout=timeout)
    return resp.read().decode("utf-8", errors="replace")


def get_weather(location=""):
    """Get current weather for a location using wttr.in."""
    try:
        loc = urllib.parse.quote(location.strip() or "")
        url = f"https://wttr.in/{loc}?format=j1"
        data = _fetch_json(url, timeout=6)

        current = data.get("current_condition", [{}])[0]
        temp = current.get("temp_C", "?")
        feels = current.get("FeelsLikeC", "?")
        desc = current.get("weatherDesc", [{}])[0].get("value", "?")
        humidity = current.get("humidity", "?")
        wind = current.get("windspeedKmph", "?")
        uv = current.get("uvIndex", "?")

        # Location name from request
        request = data.get("request", [{}])[0]
        city = request.get("query", location or "your area")

        return (f"Weather in {city}: {desc}, "
                f"{temp}°C (feels {feels}°C), "
                f"humidity {humidity}%, wind {wind} km/h, UV {uv}.")
    except Exception as e:
        return f"Couldn't get weather: {e}"


def get_news(category="top"):
    """Get latest news headlines using public RSS feeds."""
    try:
        # Use a free news API or RSS-to-JSON
        sources = {
            "top": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
            "world": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en",
            "tech": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en",
            "science": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp0Y1RjU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en",
            "business": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en",
        }
        url = sources.get(category.lower(), sources["top"])

        xml = _fetch_text(url, timeout=6)
        titles = re.findall(r"<title>(.*?)</title>", xml, re.DOTALL)

        # Skip first title (feed title), take next 8
        headlines = []
        for t in titles[1:9]:
            clean = t.strip().replace("&amp;", "&").replace("&quot;", '"')
            clean = re.sub(r"<[^>]+>", "", clean)
            if clean:
                headlines.append(clean)

        if headlines:
            return f"Latest {category} news: " + ". ".join(headlines)
        return "Couldn't fetch news right now."
    except Exception as e:
        return f"Couldn't fetch news: {e}"


def get_stock_price(symbol):
    """Get current stock price for a ticker symbol using a free API."""
    try:
        s = symbol.strip().upper()
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{s}"
        data = _fetch_json(url, timeout=6)

        result = data.get("chart", {}).get("result", [{}])[0]
        meta = result.get("meta", {})
        price = meta.get("regularMarketPrice", "?")
        prev_close = meta.get("previousClose", "?")
        currency = meta.get("currency", "USD")

        # Get change
        if price != "?" and prev_close != "?" and prev_close != 0:
            change = float(price) - float(prev_close)
            pct = (change / float(prev_close)) * 100
            direction = "up" if change > 0 else "down"
            return (f"{s} is at ${price} {currency}, "
                    f"{direction} ${abs(change):.2f} ({abs(pct):.2f}%) today.")
        return f"{s} is at ${price} {currency}."
    except Exception as e:
        return f"Couldn't get price for {symbol}: {e}"


def get_currency_rate(from_currency, to_currency):
    """Get exchange rate between two currencies."""
    try:
        f = from_currency.strip().upper()
        t = to_currency.strip().upper()
        url = f"https://api.frankfurter.app/latest?from={f}&to={t}"
        data = _fetch_json(url, timeout=6)
        rate = data.get("rates", {}).get(t)
        if rate:
            return f"1 {f} = {rate:.4f} {t}."
        return f"Currency pair {f}/{t} not found."
    except Exception as e:
        return f"Couldn't get exchange rate: {e}"


def translate_text(text, target_language):
    """Translate text to a target language using LibreTranslate."""
    try:
        lang_map = {
            "spanish": "es", "french": "fr", "german": "de",
            "italian": "it", "portuguese": "pt", "russian": "ru",
            "japanese": "ja", "chinese": "zh", "korean": "ko",
            "arabic": "ar", "hindi": "hi", "dutch": "nl",
            "polish": "pl", "turkish": "tr", "vietnamese": "vi",
            "thai": "th", "swedish": "sv", "danish": "da",
            "finnish": "fi", "norwegian": "no", "czech": "cs",
            "romanian": "ro", "hungarian": "hu", "greek": "el",
            "hebrew": "he", "indonesian": "id", "malay": "ms",
        }
        target = lang_map.get(target_language.lower().strip(), target_language.lower().strip()[:2])

        data = json.dumps({"q": text, "source": "auto", "target": target}).encode()
        req = urllib.request.Request(
            "https://libretranslate.de/translate",
            data=data,
            headers={"Content-Type": "application/json", "User-Agent": "Nova/2.0"},
        )
        resp = urllib.request.urlopen(req, timeout=8)
        result = json.loads(resp.read())
        translated = result.get("translatedText", "")
        if translated:
            return f"In {target_language}: {translated}"
        return "Translation failed."
    except Exception:
        return "Translation service unavailable right now."


def check_website(url):
    """Check if a website is reachable."""
    try:
        if not url.startswith("http"):
            url = "https://" + url
        req = urllib.request.Request(url, method="HEAD",
                                     headers={"User-Agent": "Nova/2.0"})
        resp = urllib.request.urlopen(req, timeout=5)
        return f"{url} is up (status {resp.status})."
    except urllib.error.HTTPError as e:
        return f"{url} responded with status {e.code}."
    except urllib.error.URLError as e:
        return f"{url} is unreachable: {e.reason}"
    except Exception as e:
        return f"Couldn't check {url}: {e}"


def get_public_ip_info():
    """Get public IP address and location info."""
    try:
        data = _fetch_json("https://ipapi.co/json/", timeout=6)
        ip = data.get("ip", "?")
        city = data.get("city", "?")
        region = data.get("region", "?")
        country = data.get("country_name", "?")
        org = data.get("org", "?")
        return f"Public IP: {ip}. Location: {city}, {region}, {country}. ISP: {org}."
    except Exception:
        try:
            ip = _fetch_text("https://api.ipify.org", timeout=5).strip()
            return f"Public IP: {ip}."
        except Exception as e:
            return f"Couldn't get IP info: {e}"


def shorten_url(url):
    """Shorten a URL using is.gd."""
    try:
        encoded = urllib.parse.quote(url, safe="")
        resp = _fetch_text(f"https://is.gd/create.php?format=simple&url={encoded}", timeout=5)
        short = resp.strip()
        if short and short.startswith("http"):
            return f"Shortened URL: {short}"
        return "Couldn't shorten URL."
    except Exception as e:
        return f"URL shortening failed: {e}"
