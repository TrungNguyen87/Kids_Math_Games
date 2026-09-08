import streamlit as st
from utils.state import init_state
from utils.ui import set_custom_css, show_score, bilingual_header, bilingual_text

# Page config
st.set_page_config(
    page_title="Math Games for Groep 6 & 7",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize state
init_state()

# Inject CSS
set_custom_css()

# Sidebar
with st.sidebar:
    st.image("https://api.dicebear.com/7.x/bottts/svg?seed=Math&backgroundColor=ffdfbf", width=150)
    st.markdown("### 🏆 Jouw Score <span class='eng-sub'>(Your Score)</span>", unsafe_allow_html=True)
    show_score()
    st.markdown("---")
    st.markdown("Kies een spel uit het menu hierboven! <br><span class='eng-sub'>(Choose a game from the menu above!)</span>", unsafe_allow_html=True)

# Main Dashboard
bilingual_header("Welkom bij de Reken Spelletjes!", "Welcome to the Math Games!", emoji="🎮")

st.markdown(f"""
### Klaar om te spelen? <span class='eng-sub'>(Ready to play?)</span>

Hier kun je rekenen oefenen en punten verdienen! Kies links in het menu een spel uit.
<br><span class='eng-sub'>(Here you can practice math and earn points! Choose a game from the menu on the left.)</span>

---

**Spelletjes:**
* ✖️ **Tafel Monster** *(Space Theme)* - Keersommen (Multiplication)
* 🍕 **Breuken Baas** *(Pizza Theme)* - Breuken (Fractions)
* 📏 **Meten is Weten** *(Builder Theme)* - Meten & Wegen (Measurement)
* 📖 **Uitleg Concepten** - Hulp nodig? Kijk hier! (Need help? Look here!)
""", unsafe_allow_html=True)

# Balloons for fun if they just started
if st.session_state.get('total_score', 0) == 0 and st.session_state.get('games_played', 0) == 0:
    if st.button("Start je avontuur! (Start your adventure!)"):
        st.balloons()
        st.session_state.games_played += 1
        st.rerun()
