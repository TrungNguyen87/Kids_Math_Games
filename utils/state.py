import uuid
from datetime import datetime

import streamlit as st

MIN_LEVEL = 0   # level 0 is an extra-gentle "warm-up" tier below the graded 1-5 scale
MAX_LEVEL = 5
LEVEL_UP_STREAK = 3     # correct answers in a row needed to level up
LEVEL_DOWN_STREAK = 2   # wrong answers in a row that trigger a level down
SESSION_GOAL_MINUTES = 45

GAME_KEYS = [
    "tafel",
    "breuken",
    "meten",
    "procenten",
    "algebra",
    "meetkunde",
    "verhoudingen",
    "getallen",
    # Round 5: logic and speed games. They share the same level/streak/badge
    # machinery as the arithmetic games, so they count towards "tried every
    # game" and show up on the home page's level overview like the rest.
    "bliksem",
    "logica",
    "code",
    "jacht",
]


def init_state():
    """Initialize the session state variables."""
    if "total_score" not in st.session_state:
        st.session_state.total_score = 0
    if "games_played" not in st.session_state:
        st.session_state.games_played = 0
    if "streaks" not in st.session_state:
        st.session_state.streaks = 0
    if "session_id" not in st.session_state:
        st.session_state.session_id = uuid.uuid4().hex[:8]
    if "session_start" not in st.session_state:
        st.session_state.session_start = datetime.now()
    if "player_name" not in st.session_state:
        st.session_state.player_name = ""
    if "questions_answered" not in st.session_state:
        st.session_state.questions_answered = 0
    if "correct_answered" not in st.session_state:
        st.session_state.correct_answered = 0
    if "levels" not in st.session_state:
        st.session_state.levels = {key: MIN_LEVEL for key in GAME_KEYS}
    if "game_streaks" not in st.session_state:
        st.session_state.game_streaks = {key: {"correct": 0, "wrong": 0} for key in GAME_KEYS}
    if "log" not in st.session_state:
        st.session_state.log = []
    if "sound_enabled" not in st.session_state:
        st.session_state.sound_enabled = True
    if "badges" not in st.session_state:
        st.session_state.badges = []
    if "games_tried" not in st.session_state:
        st.session_state.games_tried = set()


def add_score(points=10):
    """Add points to the total score."""
    st.session_state.total_score += points
    st.session_state.streaks += 1


def reset_streak():
    """Reset the current global (fun) streak, shown in the sidebar."""
    st.session_state.streaks = 0


def get_level(game_key):
    """Current difficulty level (1=easy .. 5=master) for a given game."""
    return st.session_state.get("levels", {}).get(game_key, MIN_LEVEL)


def set_level(game_key, level):
    """Set a game's level directly (manual override) and reset its
    adaptive-difficulty streak counters so they start fresh at the new
    level."""
    level = max(MIN_LEVEL, min(MAX_LEVEL, level))
    st.session_state.levels[game_key] = level
    st.session_state.game_streaks[game_key] = {"correct": 0, "wrong": 0}
    return level


def register_attempt(game_key, is_correct):
    """
    Update session counters after an answer is checked and adapt the
    difficulty level for that game: level up after LEVEL_UP_STREAK correct
    answers in a row, level down after LEVEL_DOWN_STREAK wrong answers in a
    row. This is what keeps a session gradually getting harder (or easing
    off when a child is struggling) instead of staying flat.

    Returns (leveled_up, leveled_down).
    """
    st.session_state.questions_answered += 1
    st.session_state.setdefault("games_tried", set()).add(game_key)
    streak = st.session_state.game_streaks.setdefault(game_key, {"correct": 0, "wrong": 0})
    leveled_up = False
    leveled_down = False
    current_level = get_level(game_key)

    if is_correct:
        st.session_state.correct_answered += 1
        streak["correct"] += 1
        streak["wrong"] = 0
        if streak["correct"] >= LEVEL_UP_STREAK and current_level < MAX_LEVEL:
            set_level(game_key, current_level + 1)
            leveled_up = True
    else:
        streak["wrong"] += 1
        streak["correct"] = 0
        if streak["wrong"] >= LEVEL_DOWN_STREAK and current_level > MIN_LEVEL:
            set_level(game_key, current_level - 1)
            leveled_down = True

    return leveled_up, leveled_down


def session_elapsed_minutes():
    """Minutes elapsed since this browser session started playing."""
    delta = datetime.now() - st.session_state.session_start
    return delta.total_seconds() / 60


def session_accuracy():
    """Percentage of correctly answered questions this session (0-100)."""
    total = st.session_state.get("questions_answered", 0)
    if total == 0:
        return 0.0
    return 100 * st.session_state.get("correct_answered", 0) / total
