import streamlit as st

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

    /* English subtitles */
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
    score = st.session_state.get('total_score', 0)
    streak = st.session_state.get('streaks', 0)
    
    st.markdown(f"""
        <div class="score-container">
            🌟 <strong>Score: {score}</strong><br>
            🔥 <strong>Streak: {streak}</strong>
        </div>
    """, unsafe_allow_html=True)

def bilingual_header(dutch_text, english_text, emoji=""):
    """Displays a large header with Dutch and English."""
    st.markdown(f"<h1>{emoji} {dutch_text}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p class='eng-sub'>{english_text}</p>", unsafe_allow_html=True)
    
def bilingual_subheader(dutch_text, english_text, emoji=""):
    """Displays a subheader with Dutch and English."""
    st.markdown(f"<h2>{emoji} {dutch_text}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p class='eng-sub'>{english_text}</p>", unsafe_allow_html=True)

def bilingual_text(dutch_text, english_text):
    """Returns a string formatted for standard markdown bilingual text."""
    return f"{dutch_text} <span class='eng-sub'>({english_text})</span>"
