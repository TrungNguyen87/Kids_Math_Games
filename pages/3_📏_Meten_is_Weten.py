import streamlit as st
import random
from utils.state import add_score
from utils.ui import set_custom_css, show_score, bilingual_header

st.set_page_config(page_title="Meten is Weten", page_icon="📏", layout="wide")
set_custom_css()

with st.sidebar:
    show_score()

bilingual_header("Bouwplaats: Meten is Weten!", "Construction Site: Measurement!", emoji="🏗️")
st.markdown("Help de bouwvakker met de juiste afmetingen! <br><span class='eng-sub'>(Help the builder with the correct measurements!)</span>", unsafe_allow_html=True)

if 'meten_problem' not in st.session_state:
    st.session_state.meten_problem = None
if 'meten_feedback' not in st.session_state:
    st.session_state.meten_feedback = ""

def generate_meten_problem():
    conversions = [
        ("cm", "mm", 10),
        ("m", "cm", 100),
        ("km", "m", 1000),
        ("kg", "g", 1000),
        ("l", "ml", 1000)
    ]
    unit1, unit2, factor = random.choice(conversions)
    
    # Sometimes from large to small, sometimes small to large
    if random.choice([True, False]):
        # Large to small
        val1 = random.randint(1, 20)
        val2 = val1 * factor
        st.session_state.meten_problem = (val1, unit1, val2, unit2)
    else:
        # Small to large
        val2 = random.randint(1, 20)
        val1 = val2 * factor
        st.session_state.meten_problem = (val1, unit2, val2, unit1)
        
    st.session_state.meten_feedback = ""

if st.session_state.meten_problem is None:
    generate_meten_problem()

v1, u1, v2, u2 = st.session_state.meten_problem

st.markdown(f"### 🧱 {v1} {u1} = ... {u2}? <span class='eng-sub'>(Convert to {u2})</span>", unsafe_allow_html=True)

user_val = st.number_input(f"Vul in (Fill in):", step=1, value=None, key="meten_input")

col1, col2 = st.columns([1, 4])
with col1:
    if st.button("Bouw! (Build!)"):
        if user_val == v2:
            st.session_state.meten_feedback = "✅ Super stevig gebouwd! (+10 punten) <br><span class='eng-sub'>(Super solidly built! +10 points)</span>"
            add_score(10)
            st.balloons()
        elif user_val is not None:
            st.session_state.meten_feedback = "❌ Pas op, het gebouw wiebelt! Probeer opnieuw. <br><span class='eng-sub'>(Watch out, the building is wobbling! Try again.)</span>"
            st.session_state.streaks = 0

with col2:
    if st.button("Nieuwe klus (New Job) ➡️"):
        generate_meten_problem()
        st.rerun()

if st.session_state.meten_feedback:
    if "Super" in st.session_state.meten_feedback:
        st.success(st.session_state.meten_feedback, icon="👷")
    else:
        st.error(st.session_state.meten_feedback, icon="🚧")
