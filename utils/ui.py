import streamlit as st

from utils.i18n import language_switcher, t
from utils.state import (
    MAX_LEVEL,
    SESSION_GOAL_MINUTES,
    get_level,
    session_accuracy,
    session_elapsed_minutes,
)

DIFFICULTY_KEYS = [
    "common.difficulty_easy",
    "common.difficulty_medium",
    "common.difficulty_hard",
    "common.difficulty_expert",
    "common.difficulty_master",
]


def set_custom_css():
    """Injects custom CSS to make the app more kid-friendly."""
    css = """
    <style>
    /* General styles */
    .stApp {
        font-family: 'Comic Sans MS', 'Chalkboard SE', 'Marker Felt', sans-serif;
        font-size: 1.2rem;
    }

    /* Make standard text and markdown bigger */
    .stMarkdown p, .stMarkdown li {
        font-size: 1.3rem !important;
    }

    h1 { font-size: 2.5rem !important; color: #ff4b4b; }
    h2 { font-size: 2.0rem !important; color: #ff4b4b; }
    h3 { font-size: 1.7rem !important; color: #ff4b4b; }

    /* Bigger buttons */
    .stButton>button {
        font-size: 1.5rem !important;
        height: 3.5rem !important;
        border-radius: 12px !important;
        font-weight: bold;
        transition: transform 0.2s;
    }
    .stButton>button:hover {
        transform: scale(1.05);
    }

    /* Score container */
    .score-container {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-size: 1.8rem;
        margin-bottom: 20px;
        border: 3px solid #ff4b4b;
    }

    /* Session progress container */
    .session-container {
        background-color: #eef8f0;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 15px;
        border: 2px solid #4caf50;
        font-size: 1.0rem;
    }
    .session-container .label {
        font-weight: bold;
    }

    /* Level badge */
    .level-badge {
        display: inline-block;
        background-color: #fff3cd;
        border: 2px solid #ffb300;
        color: #7a5b00;
        padding: 6px 16px;
        border-radius: 999px;
        font-weight: bold;
        font-size: 1.1rem;
        margin-bottom: 10px;
    }

    /* English/secondary subtitles */
    .eng-sub {
        font-size: 0.9rem;
        color: #666;
        font-style: italic;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def show_score():
    """Displays the global score in the sidebar or main area."""
    score = st.session_state.get("total_score", 0)
    streak = st.session_state.get("streaks", 0)

    st.markdown(
        f"""
        <div class="score-container">
            🌟 <strong>{t('sidebar.score')}: {score}</strong><br>
            🔥 <strong>{t('sidebar.streak')}: {streak}</strong>
        </div>
    """,
        unsafe_allow_html=True,
    )


def show_session_progress():
    """Displays elapsed play time, questions answered and accuracy."""
    elapsed = session_elapsed_minutes()
    questions = st.session_state.get("questions_answered", 0)
    accuracy = session_accuracy()
    goal = SESSION_GOAL_MINUTES
    progress = min(1.0, elapsed / goal) if goal else 0.0

    st.markdown(f"**{t('sidebar.session_heading')}**")
    st.progress(progress, text=f"⏱️ {t('sidebar.session_time')}: {elapsed:.0f} / {goal} min")
    st.markdown(
        f"""
        <div class="session-container">
            📝 <span class="label">{t('sidebar.questions')}:</span> {questions}<br>
            🎯 <span class="label">{t('sidebar.accuracy')}:</span> {accuracy:.0f}%
        </div>
    """,
        unsafe_allow_html=True,
    )


def sidebar_common(show_progress=True):
    """Standard sidebar block used on every page: language toggle, score,
    session progress and a link to the parent dashboard."""
    language_switcher()
    show_score()
    if show_progress:
        show_session_progress()
    st.markdown("---")
    st.markdown(t("sidebar.parent_link"))


def level_label(level):
    idx = max(0, min(len(DIFFICULTY_KEYS) - 1, level - 1))
    return t(DIFFICULTY_KEYS[idx])


def show_level_badge(level):
    st.markdown(
        f"<div class='level-badge'>⭐ {t('common.level')} {level}/{MAX_LEVEL} — {level_label(level)}</div>",
        unsafe_allow_html=True,
    )


def page_header(title_key, subtitle_key=None, emoji=""):
    """Displays a large header, translated, with an optional subtitle."""
    st.markdown(f"<h1>{emoji} {t(title_key)}</h1>", unsafe_allow_html=True)
    if subtitle_key:
        st.markdown(f"<p class='eng-sub'>{t(subtitle_key)}</p>", unsafe_allow_html=True)
