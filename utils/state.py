import streamlit as st

def init_state():
    """Initialize the session state variables."""
    if 'total_score' not in st.session_state:
        st.session_state.total_score = 0
    if 'games_played' not in st.session_state:
        st.session_state.games_played = 0
    if 'streaks' not in st.session_state:
        st.session_state.streaks = 0

def add_score(points=10):
    """Add points to the total score."""
    st.session_state.total_score += points
    st.session_state.streaks += 1
    
def reset_streak():
    """Reset the current streak."""
    st.session_state.streaks = 0

def get_bilingual_text(dutch_text, english_text):
    """
    Format text to show Dutch primarily, with English in smaller/italic font.
    """
    return f"{dutch_text} <br><span style='font-size: 0.8em; color: #888; font-style: italic;'>({english_text})</span>"
