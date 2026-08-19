"""Text tools: formatting, counting, JSON, base conversion, definitions."""

import json
import math
import re


def transform_text(text, transformation):
    """Transform text: uppercase, lowercase, title, capitalize, reverse, slug."""
    t = transformation.lower().strip()
    if t in ("upper", "uppercase"):
        return text.upper()
    elif t in ("lower", "lowercase"):
        return text.lower()
    elif t in ("title", "titlecase"):
        return text.title()
    elif t in ("capitalize", "capitalise"):
        return text.capitalize()
    elif t == "reverse":
        return text[::-1]
    elif t == "swapcase":
        return text.swapcase()
    elif t in ("slug", "slugify"):
        slug = re.sub(r'[^a-zA-Z0-9\s-]', "", text.lower()).strip()
        slug = re.sub(r'[\s_]+', "-", slug)
        return slug
    elif t in ("invert", "invertcase"):
        return "".join(c.lower() if c.isupper() else c.upper() for c in text)
    else:
        return f"Unknown transformation '{transformation}'. Try: uppercase, lowercase, title, reverse, slug."


def count_words(text):
    """Count words, characters, sentences, and paragraphs in text."""
    words = len([w for w in text.split() if w.strip()])
    chars = len(text)
    chars_no_space = len(text.replace(" ", ""))
    sentences = len(re.split(r'[.!?]+', text)) - 1
    paragraphs = len([p for p in text.split("\n") if p.strip()])
    return (f"{words} words, {chars} characters ({chars_no_space} without spaces), "
            f"{sentences} sentences, {paragraphs} paragraphs.")


def format_json(text):
    """Format or validate a JSON string."""
    try:
        parsed = json.loads(text)
        pretty = json.dumps(parsed, indent=2)
        if len(pretty) > 2000:
            pretty = pretty[:2000] + "\n... (truncated)"
        return pretty
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}"
    except Exception as e:
        return f"Error formatting JSON: {e}"


def minify_json(text):
    """Minify a JSON string by removing whitespace."""
    try:
        parsed = json.loads(text)
        return json.dumps(parsed, separators=(",", ":"))
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}"


def convert_base(value, from_base, to_base):
    """Convert a number between bases (2, 8, 10, 16)."""
    try:
        value = str(value).strip()
        from_b = int(from_base)
        to_b = int(to_base)

        valid_bases = {2, 8, 10, 16}
        if from_b not in valid_bases or to_b not in valid_bases:
            return "Supported bases: 2 (binary), 8 (octal), 10 (decimal), 16 (hex)."

        # Parse the input number
        decimal = int(value, from_b)
        prefixes = {2: "0b", 8: "0o", 10: "", 16: "0x"}
        result = {
            2: bin(decimal),
            8: oct(decimal),
            10: str(decimal),
            16: hex(decimal),
        }
        return f"{value} (base {from_b}) = {result[to_b]} (base {to_b})"
    except ValueError:
        return f"'{value}' is not valid in base {from_base}."
    except Exception as e:
        return f"Conversion error: {e}"


def extract_emails(text):
    """Extract email addresses from text."""
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    if emails:
        return "Found emails: " + ", ".join(emails[:10])
    return "No email addresses found."


def extract_urls(text):
    """Extract URLs from text."""
    urls = re.findall(r'https?://[^\s<>"\']+|www\.[^\s<>"\']+', text)
    if urls:
        return "Found URLs: " + ", ".join(urls[:10])
    return "No URLs found."


def compare_texts(text1, text2):
    """Compare two texts and report differences."""
    if text1 == text2:
        return "The texts are identical."
    words1 = text1.split()
    words2 = text2.split()
    len_diff = len(words1) - len(words2)
    diff_word = "more" if len_diff > 0 else "fewer"
    return (f"Texts differ. First has {len(words1)} words, "
            f"second has {len(words2)} words "
            f"({abs(len_diff)} {diff_word} words in first).")
