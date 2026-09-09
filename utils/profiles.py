"""
Persistent player profiles: lets a returning kid pick up where they left
off instead of starting from zero every browser session. Keyed by the
player name typed on the home page and stored as a small JSON file next to
the CSV session log (same "persists across sessions, resets on redeploy"
tradeoff already documented for logs/all_sessions_log.csv).
"""
import json
import os

import streamlit as st

from utils.state import GAME_KEYS, MIN_LEVEL

PROFILE_DIR = "logs"
PROFILE_FILE = os.path.join(PROFILE_DIR, "player_profiles.json")


def _load_all():
    if not os.path.exists(PROFILE_FILE):
        return {}
    try:
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _save_all(data):
    try:
        os.makedirs(PROFILE_DIR, exist_ok=True)
        with open(PROFILE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except OSError:
        # Read-only filesystem or other disk issue: the session still works
        # in-memory, it just won't be there next time.
        pass


def load_profile(name):
    """Return the saved profile dict for `name`, or None if there isn't one."""
    return _load_all().get(name)


def apply_profile(name):
    """Restore a saved profile's score/levels/badges/games-tried into the
    current session. Returns True if a profile was found and applied."""
    profile = load_profile(name)
    if profile is None:
        return False
    st.session_state.total_score = profile.get("total_score", 0)
    st.session_state.levels = {
        key: profile.get("levels", {}).get(key, MIN_LEVEL) for key in GAME_KEYS
    }
    st.session_state.badges = profile.get("badges", [])
    st.session_state.games_tried = set(profile.get("games_tried", []))
    return True


def save_current_profile():
    """Persist the current session's score/levels/badges under the current
    player name. No-op if no name has been entered yet."""
    name = st.session_state.get("player_name", "")
    if not name:
        return
    all_profiles = _load_all()
    all_profiles[name] = {
        "total_score": st.session_state.get("total_score", 0),
        "levels": st.session_state.get("levels", {}),
        "badges": st.session_state.get("badges", []),
        "games_tried": sorted(st.session_state.get("games_tried", set())),
    }
    _save_all(all_profiles)
