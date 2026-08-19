"""More text tools: markdown stripping, Caesar cipher, lorem ipsum, palindrome, anagram, stats."""

import re
import random
import string
import math


def strip_markdown(text):
    """Strip markdown formatting from text, returning plain text."""
    text = re.sub(r"#{1,6}\s+", "", text)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"`{1,3}(.*?)`{1,3}", r"\1", text)
    text = re.sub(r"~~(.*?)~~", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\d+\.\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\|", " ", text)
    text = re.sub(r"[-*_]{3,}", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def caesar_cipher(text, shift, decode=False):
    """Apply a Caesar cipher shift to text."""
    try:
        shift = int(shift)
        if decode:
            shift = -shift
        result = []
        for char in text:
            if char.isupper():
                result.append(chr((ord(char) - 65 + shift) % 26 + 65))
            elif char.islower():
                result.append(chr((ord(char) - 97 + shift) % 26 + 97))
            else:
                result.append(char)
        mode = "decoded" if decode else "encoded"
        return f"{mode.capitalize()}: {''.join(result)}"
    except Exception as e:
        return f"Caesar cipher error: {e}"


def generate_lorem_ipsum(paragraphs=1, sentences_per=5):
    """Generate lorem ipsum placeholder text."""
    paragraphs = max(1, min(20, int(paragraphs)))
    sentences_per = max(1, min(50, int(sentences_per)))

    words = [
        "lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing",
        "elit", "sed", "do", "eiusmod", "tempor", "incididunt", "ut", "labore",
        "et", "dolore", "magna", "aliqua", "ut", "enim", "ad", "minim", "veniam",
        "quis", "nostrud", "exercitation", "ullamco", "laboris", "nisi", "ut",
        "aliquip", "ex", "ea", "commodo", "consequat", "duis", "aute", "irure",
        "dolor", "in", "reprehenderit", "in", "voluptate", "velit", "esse",
        "cillum", "dolore", "eu", "fugiat", "nulla", "pariatur", "excepteur",
        "sint", "occaecat", "cupidatat", "non", "proident", "sunt", "in", "culpa",
        "qui", "officia", "deserunt", "mollit", "anim", "id", "est", "laborum",
    ]

    result = []
    for _ in range(paragraphs):
        sentences = []
        for _ in range(sentences_per):
            k = random.randint(5, 15)
            sentence_words = [random.choice(words) for _ in range(k)]
            sentence = " ".join(sentence_words)
            sentence = sentence[0].upper() + sentence[1:] + "."
            sentences.append(sentence)
        result.append(" ".join(sentences))

    return "\n\n".join(result)[:2000]


def check_palindrome(text):
    """Check if text is a palindrome (reads same forward and backward)."""
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', text).lower()
    if not cleaned:
        return "No text to check."
    if cleaned == cleaned[::-1]:
        return f"'{text[:60]}' is a palindrome."
    return f"'{text[:60]}' is not a palindrome."


def check_anagram(text1, text2):
    """Check if two texts are anagrams of each other."""
    clean1 = re.sub(r'[^a-zA-Z]', '', text1).lower()
    clean2 = re.sub(r'[^a-zA-Z]', '', text2).lower()
    if not clean1 or not clean2:
        return "Both texts need letters to compare."
    if sorted(clean1) == sorted(clean2):
        return f"'{text1[:40]}' and '{text2[:40]}' are anagrams."
    return f"'{text1[:40]}' and '{text2[:40]}' are NOT anagrams."


def text_statistics(text):
    """Get detailed text statistics including readability metrics."""
    if not text.strip():
        return "No text to analyze."

    words = [w for w in text.split() if w.strip()]
    word_count = len(words)
    char_count = len(text)
    char_no_space = len(text.replace(" ", ""))
    sentences = len(re.split(r'[.!?]+', text)) - 1
    paragraphs = len([p for p in text.split("\n") if p.strip()])
    syllables = 0
    for word in words:
        w = word.lower().strip(string.punctuation)
        if w:
            s = max(1, len(re.findall(r'[aeiouy]+', w)))
            syllables += s

    avg_word_len = (char_no_space / word_count) if word_count else 0
    avg_syllables = (syllables / word_count) if word_count else 0

    # Flesch-Kincaid grade level
    if sentences > 0 and word_count > 0:
        fk_grade = 0.39 * (word_count / sentences) + 11.8 * (syllables / word_count) - 15.59
        fk_grade = max(0, min(20, round(fk_grade, 1)))
    else:
        fk_grade = "N/A"

    return (f"{word_count} words, {char_count} chars ({char_no_space} no spaces), "
            f"{sentences} sentences, {paragraphs} paragraphs, "
            f"avg word length {avg_word_len:.1f}, avg syllables {avg_syllables:.1f}, "
            f"Flesch-Kincaid grade {fk_grade}.")
