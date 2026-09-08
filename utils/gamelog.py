"""
Session logging for the parent dashboard.

Every answered question is recorded both in-memory (st.session_state.log,
so it can be downloaded immediately after a session) and appended to a CSV
file on disk (logs/all_sessions_log.csv) so a parent can see history across
multiple play sessions/days, not just the current browser tab.

Note: on hosting platforms with an ephemeral filesystem the on-disk history
resets when the app is redeployed/restarted, but persists across sessions
in between - the in-app download button is the reliable way to keep a
permanent copy.
"""
import csv
import io
import os
from datetime import datetime

import pandas as pd
import streamlit as st

from utils.i18n import t

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "all_sessions_log.csv")

FIELDNAMES = [
    "timestamp",
    "session_id",
    "player",
    "game",
    "level",
    "question",
    "student_answer",
    "correct_answer",
    "result",
    "points",
]


def log_attempt(game_key, game_name, level, question, student_answer, correct_answer, is_correct, points):
    """Record one answered question, in-session and on disk."""
    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "session_id": st.session_state.get("session_id", ""),
        "player": st.session_state.get("player_name", "") or t("dash.player_unknown"),
        "game": game_name,
        "level": level,
        "question": question,
        "student_answer": "" if student_answer is None else student_answer,
        "correct_answer": correct_answer,
        "result": "correct" if is_correct else "fout",
        "points": points if is_correct else 0,
    }
    st.session_state.setdefault("log", []).append(entry)
    _persist(entry)
    return entry


def _persist(entry):
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        write_header = not os.path.exists(LOG_FILE)
        with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            if write_header:
                writer.writeheader()
            writer.writerow(entry)
    except OSError:
        # Read-only filesystem or other disk issue: keep going, the
        # in-session log + download button still work.
        pass


def get_session_dataframe():
    return pd.DataFrame(st.session_state.get("log", []), columns=FIELDNAMES)


def get_full_history_dataframe():
    if os.path.exists(LOG_FILE):
        try:
            return pd.read_csv(LOG_FILE)
        except pd.errors.EmptyDataError:
            return pd.DataFrame(columns=FIELDNAMES)
    return pd.DataFrame(columns=FIELDNAMES)


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")


def clear_history():
    try:
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
    except OSError:
        pass
