"""Generate high-quality Siri/Alexa-like sound effects.

Creates professional-sounding UI audio using additive synthesis,
reverb simulation, and proper ADSR envelopes. These aren't simple
beeps — they have warmth, shimmer, and presence.

Run this once to populate the sounds/ directory.
"""

import math
import struct
import wave
import os
import random

SAMPLE_RATE = 44100
SOUNDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")
os.makedirs(SOUNDS_DIR, exist_ok=True)


def write_wav(path, samples, sr=SAMPLE_RATE):
    """Write float samples to a 16-bit WAV file."""
    # Normalize
    peak = max(abs(s) for s in samples) if samples else 1.0
    if peak > 0:
        samples = [s / peak * 0.85 for s in samples]  # leave headroom

    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        for s in samples:
            w.writeframes(struct.pack("<h", int(max(-1, min(1, s)) * 32767)))


def sine(freq, t):
    return math.sin(2 * math.pi * freq * t)


def triangle(freq, t):
    p = (t * freq) % 1.0
    return 4 * abs(p - 0.5) - 1


def adsr(t, attack, decay, sustain_level, release, duration):
    """ADSR envelope."""
    if t < attack:
        return t / attack
    elif t < attack + decay:
        return 1.0 - (1.0 - sustain_level) * (t - attack) / decay
    elif t < duration - release:
        return sustain_level
    elif t < duration:
        return sustain_level * (1.0 - (t - (duration - release)) / release)
    return 0.0


def reverb(samples, decay=0.3, delays=None):
    """Simple comb filter reverb."""
    if delays is None:
        delays = [int(SAMPLE_RATE * d) for d in [0.023, 0.031, 0.041, 0.053]]

    out = list(samples)
    for delay in delays:
        for i in range(delay, len(out)):
            out[i] += out[i - delay] * decay
    return out


def lowpass(samples, cutoff_freq, sr=SAMPLE_RATE):
    """Simple one-pole lowpass filter."""
    rc = 1.0 / (2.0 * math.pi * cutoff_freq)
    dt = 1.0 / sr
    alpha = dt / (rc + dt)
    out = [samples[0]]
    for i in range(1, len(samples)):
        out.append(out[-1] + alpha * (samples[i] - out[-1]))
    return out


def note(freq, duration, volume=0.5, attack=0.01, decay=0.05, sustain=0.7, release=0.1,
         harmonics=None, vibrato_rate=0, vibrato_depth=0):
    """Generate a rich note with harmonics and optional vibrato."""
    n = int(SAMPLE_RATE * duration)
    if harmonics is None:
        harmonics = [(1, 1.0), (2, 0.3), (3, 0.1)]  # fundamental + overtones

    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = adsr(t, attack, decay, sustain, release, duration)

        # Vibrato
        freq_mod = freq
        if vibrato_rate > 0:
            freq_mod = freq * (1 + vibrato_depth * sine(vibrato_rate, t))

        # Additive synthesis with harmonics
        s = 0
        for h_mult, h_vol in harmonics:
            s += h_vol * sine(freq_mod * h_mult, t)

        samples.append(s * env * volume)
    return samples


def silence(duration):
    return [0.0] * int(SAMPLE_RATE * duration)


# ============================================================
# SOUND GENERATORS
# ============================================================

def gen_activate():
    """Siri-like activation — a bright, warm, two-note ascending chime.

    Think of the Apple Siri sound: two quick crystalline notes rising,
    with a shimmer of harmonics and gentle reverb tail.
    """
    # Note 1: E6 — quick, sets up anticipation
    n1 = note(1318.5, 0.12, volume=0.6, attack=0.003, decay=0.03, sustain=0.5, release=0.06,
              harmonics=[(1, 1.0), (2, 0.4), (3, 0.15), (4, 0.05), (5, 0.02)])

    gap = silence(0.02)

    # Note 2: B6 — longer, brighter, with shimmer
    n2_main = note(1975.5, 0.22, volume=0.7, attack=0.003, decay=0.04, sustain=0.4, release=0.12,
                   harmonics=[(1, 1.0), (2, 0.45), (3, 0.2), (4, 0.08), (5, 0.03)])
    # Add a detuned layer for shimmer
    n2_shimmer = note(1980, 0.22, volume=0.15, attack=0.003, decay=0.04, sustain=0.4, release=0.12,
                      harmonics=[(1, 1.0), (2, 0.3)])

    n2 = [a + b for a, b in zip(n2_main, n2_shimmer)]

    samples = n1 + gap + n2

    # Light reverb for spaciousness
    samples = reverb(samples, decay=0.15, delays=[int(SAMPLE_RATE * d) for d in [0.018, 0.029, 0.037]])
    # Gentle lowpass to soften
    samples = lowpass(samples, 8000)

    return samples


def gen_deactivate():
    """Descending two-note chime — the conversation is done."""
    n1 = note(1975.5, 0.1, volume=0.5, attack=0.003, decay=0.03, sustain=0.4, release=0.05,
              harmonics=[(1, 1.0), (2, 0.35), (3, 0.12)])
    gap = silence(0.025)
    n2 = note(1318.5, 0.18, volume=0.45, attack=0.003, decay=0.04, sustain=0.3, release=0.1,
              harmonics=[(1, 1.0), (2, 0.3), (3, 0.1)])

    samples = n1 + gap + n2
    samples = reverb(samples, decay=0.12)
    samples = lowpass(samples, 6000)
    return samples


def gen_listening():
    """Soft ambient pulse that plays while listening — warm, non-intrusive.

    Like the soft hum you feel when Siri is waiting. A gentle pad
    with slow pulsing.
    """
    duration = 1.5
    n = int(SAMPLE_RATE * duration)
    samples = []

    for i in range(n):
        t = i / SAMPLE_RATE
        # Very slow pulse envelope
        pulse = 0.5 + 0.5 * sine(1.5, t)
        # Warm pad — low frequency, rich harmonics
        s = 0.0
        s += 0.4 * sine(440, t)      # A4 fundamental
        s += 0.2 * sine(880, t)      # octave
        s += 0.1 * sine(1320, t)     # fifth
        s += 0.05 * sine(1760, t)    # 2 octaves
        # Soft noise for texture
        s += 0.02 * (random.random() * 2 - 1)

        # Fade in/out
        env = 1.0
        if t < 0.1:
            env = t / 0.1
        elif t > duration - 0.3:
            env = (duration - t) / 0.3

        samples.append(s * pulse * env * 0.15)

    samples = lowpass(samples, 3000)
    return samples


def gen_thinking():
    """Processing indicator — rhythmic soft ticks, like a thinking clock.

    Three subtle, spaced taps with warm tone, then silence. Feels
    like the system is working without being annoying.
    """
    tick_times = [0.0, 0.12, 0.24]
    duration = 0.5
    n = int(SAMPLE_RATE * duration)
    samples = [0.0] * n

    for tick_t in tick_times:
        for i in range(int(SAMPLE_RATE * 0.06)):  # each tick is 60ms
            t = i / SAMPLE_RATE
            idx = int(tick_t * SAMPLE_RATE) + i
            if idx < n:
                env = adsr(t, 0.002, 0.01, 0.3, 0.03, 0.06)
                s = 0.4 * sine(1200, t) + 0.15 * sine(2400, t) + 0.05 * sine(3600, t)
                samples[idx] += s * env

    samples = lowpass(samples, 5000)
    samples = reverb(samples, decay=0.1)
    return samples


def gen_mute():
    """Alexa-like mute — a soft descending blip. Quick, clear, final."""
    # Quick descending glide
    duration = 0.15
    n = int(SAMPLE_RATE * duration)
    samples = []

    for i in range(n):
        t = i / SAMPLE_RATE
        # Frequency glides down
        freq = 900 - 400 * (t / duration)
        env = adsr(t, 0.003, 0.03, 0.5, 0.06, duration)
        s = sine(freq, t) * 0.5 + sine(freq * 2, t) * 0.15
        samples.append(s * env * 0.6)

    samples = lowpass(samples, 4000)
    return samples


def gen_unmute():
    """Alexa-like unmute — ascending blip. Bright, confirming."""
    duration = 0.15
    n = int(SAMPLE_RATE * duration)
    samples = []

    for i in range(n):
        t = i / SAMPLE_RATE
        # Frequency glides up
        freq = 600 + 500 * (t / duration)
        env = adsr(t, 0.003, 0.03, 0.5, 0.06, duration)
        s = sine(freq, t) * 0.5 + sine(freq * 2, t) * 0.2
        samples.append(s * env * 0.6)

    samples = lowpass(samples, 5000)
    return samples


def gen_error():
    """Error tone — two quick low notes, feels wrong but not harsh."""
    n1 = note(350, 0.1, volume=0.5, attack=0.003, decay=0.02, sustain=0.4, release=0.04,
              harmonics=[(1, 1.0), (2, 0.5), (3, 0.25)])
    gap = silence(0.06)
    n2 = note(280, 0.16, volume=0.45, attack=0.003, decay=0.03, sustain=0.3, release=0.08,
              harmonics=[(1, 1.0), (2, 0.5), (3, 0.3)])

    samples = n1 + gap + n2
    samples = lowpass(samples, 3000)
    return samples


def gen_not_understood():
    """Gentle 'hmm?' — a soft rising-then-falling two-note query.

    Sounds like a polite question, conveying 'I heard something
    but didn't understand' without being annoying.
    """
    n1 = note(600, 0.08, volume=0.4, attack=0.003, decay=0.02, sustain=0.3, release=0.04,
              harmonics=[(1, 1.0), (2, 0.3), (3, 0.1)])
    gap = silence(0.04)
    n2 = note(900, 0.14, volume=0.35, attack=0.003, decay=0.03, sustain=0.3, release=0.08,
              harmonics=[(1, 1.0), (2, 0.25), (3, 0.08)])
    n3 = note(700, 0.18, volume=0.3, attack=0.003, decay=0.04, sustain=0.2, release=0.1,
              harmonics=[(1, 1.0), (2, 0.2)])

    samples = n1 + gap + n2 + silence(0.03) + n3
    samples = lowpass(samples, 5000)
    return samples


# ============================================================
# MAIN
# ============================================================

def main():
    generators = {
        "activate": gen_activate,
        "deactivate": gen_deactivate,
        "not_understood": gen_not_understood,
        "listening": gen_listening,
        "thinking": gen_thinking,
        "mute": gen_mute,
        "unmute": gen_unmute,
        "error": gen_error,
    }

    for name, gen_func in generators.items():
        path = os.path.join(SOUNDS_DIR, f"{name}.wav")
        print(f"Generating {name}...", end=" ")
        samples = gen_func()
        write_wav(path, samples)
        size = os.path.getsize(path)
        print(f"OK ({size:,} bytes, {len(samples)/SAMPLE_RATE:.2f}s)")

    print("\nDone! All sounds saved to:", SOUNDS_DIR)


if __name__ == "__main__":
    main()
