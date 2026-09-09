"""
Tiny self-contained sound effects (no external files, no network calls):
short tones are synthesized on import with the stdlib `wave` module and
played back via a hidden autoplay <audio> tag. Browsers may block autoplay
audio that isn't tied closely enough to a user gesture - if that happens
the tag just silently doesn't play, so this is a best-effort enhancement,
never a required one.
"""
import base64
import io
import math
import struct
import wave

import streamlit as st

SAMPLE_RATE = 22050


def _tone(freq, duration, volume=0.35):
    """Raw PCM samples for a single sine tone with a short fade-out (avoids
    an audible click at the end of the clip)."""
    n_samples = int(duration * SAMPLE_RATE)
    samples = bytearray()
    for i in range(n_samples):
        t = i / SAMPLE_RATE
        envelope = 1.0 - (i / n_samples)
        value = volume * envelope * math.sin(2 * math.pi * freq * t)
        samples += struct.pack("<h", int(value * 32767))
    return bytes(samples)


def _wav_bytes(*tones):
    """Concatenate one or more (freq, duration) tone segments into a single
    mono 16-bit WAV file, returned as bytes."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        for freq, duration in tones:
            wf.writeframes(_tone(freq, duration))
    return buf.getvalue()


# A bright little ascending "ta-da" for correct answers, and a low
# descending "womp" for incorrect ones - generated once at import time.
_CORRECT_WAV = _wav_bytes((523.25, 0.09), (659.25, 0.09), (783.99, 0.16))  # C5-E5-G5
_INCORRECT_WAV = _wav_bytes((311.13, 0.14), (233.08, 0.22))  # Eb4-Bb3


def _play(wav_bytes):
    if not st.session_state.get("sound_enabled", True):
        return
    b64 = base64.b64encode(wav_bytes).decode()
    st.markdown(
        f'<audio autoplay style="display:none"><source src="data:audio/wav;base64,{b64}" type="audio/wav"></audio>',
        unsafe_allow_html=True,
    )


def play_correct():
    _play(_CORRECT_WAV)


def play_incorrect():
    _play(_INCORRECT_WAV)


# Games call queue_correct()/queue_incorrect() right after checking an
# answer, immediately before st.rerun(). Rendering the <audio> tag directly
# there would be pointless: st.rerun() discards the current render before
# the browser ever sees it (this bit us once already with a st.success()
# that got wiped the same way). Instead the choice is stashed in session
# state and played on the *next* run, from the feedback-display code that
# actually survives to reach the browser - play_pending() pops it so it
# fires exactly once, not on every later rerun of the same page.
def queue_correct():
    st.session_state["_pending_sound"] = "correct"


def queue_incorrect():
    st.session_state["_pending_sound"] = "incorrect"


def play_pending():
    pending = st.session_state.pop("_pending_sound", None)
    if pending == "correct":
        play_correct()
    elif pending == "incorrect":
        play_incorrect()
