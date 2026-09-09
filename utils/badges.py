"""
Milestone badges: a light "why keep playing" layer on top of the raw score,
independent of any one game. Definitions are simple threshold checks against
st.session_state; check_new_badges() is called once per answered question,
after that question's score/level/streak updates have landed, and returns
any badges newly earned so a toast can celebrate them.
"""
import streamlit as st

from utils.state import GAME_KEYS, MAX_LEVEL, get_level


def _played_all_games():
    return set(GAME_KEYS) <= st.session_state.get("games_tried", set())


def _any_level_maxed():
    return any(get_level(k) >= MAX_LEVEL for k in GAME_KEYS)


def _all_levels_maxed():
    return all(get_level(k) >= MAX_LEVEL for k in GAME_KEYS)


# (badge_id, emoji, check) - order doubles as the display order.
BADGE_DEFS = [
    ("q10", "🥉", lambda: st.session_state.get("questions_answered", 0) >= 10),
    ("q50", "🥈", lambda: st.session_state.get("questions_answered", 0) >= 50),
    ("q100", "🥇", lambda: st.session_state.get("questions_answered", 0) >= 100),
    ("streak5", "🔥", lambda: st.session_state.get("streaks", 0) >= 5),
    ("streak10", "🔥🔥", lambda: st.session_state.get("streaks", 0) >= 10),
    ("explorer", "🗺️", _played_all_games),
    ("level5", "⭐", _any_level_maxed),
    ("mastermind", "👑", _all_levels_maxed),
]
BADGE_IDS = [b[0] for b in BADGE_DEFS]
BADGE_EMOJI = {b[0]: b[1] for b in BADGE_DEFS}


def check_new_badges():
    """Evaluate every badge definition, update st.session_state.badges, and
    return the list of (badge_id, emoji) pairs newly earned this call."""
    earned = set(st.session_state.get("badges", []))
    newly = []
    for badge_id, emoji, check in BADGE_DEFS:
        if badge_id not in earned and check():
            earned.add(badge_id)
            newly.append((badge_id, emoji))
    st.session_state.badges = [b for b in BADGE_IDS if b in earned]
    return newly
