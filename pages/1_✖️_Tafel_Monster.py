import streamlit as st
import random
import time
from utils.state import add_score, get_bilingual_text
from utils.ui import set_custom_css, show_score, bilingual_header

st.set_page_config(page_title="Tafel Monster", page_icon="✖️", layout="wide")
set_custom_css()

with st.sidebar:
    show_score()

bilingual_header("Ruimte Avontuur: Tafel Monster!", "Space Adventure: Multiplication Monster!", emoji="🚀")
st.markdown("Versla de ruimtemonsters door de keersommen goed op te lossen! <br><span class='eng-sub'>(Defeat the space monsters by solving the multiplication problems correctly!)</span>", unsafe_allow_html=True)

# State for the current problem
if 'tafel_problem' not in st.session_state:
    st.session_state.tafel_problem = None
if 'tafel_feedback' not in st.session_state:
    st.session_state.tafel_feedback = ""

def generate_problem():
    a = random.randint(2, 15)
    b = random.randint(2, 10)
    st.session_state.tafel_problem = (a, b, a * b)
    st.session_state.tafel_feedback = ""
    st.session_state.tafel_user_answer = ""

if st.session_state.tafel_problem is None:
    generate_problem()

a, b, answer = st.session_state.tafel_problem

st.markdown(f"### Wat is {a} x {b}? <span class='eng-sub'>(What is {a} x {b}?)</span>", unsafe_allow_html=True)

user_ans = st.number_input("Jouw antwoord (Your answer):", step=1, value=None, key="tafel_input")

col1, col2 = st.columns([1, 4])
with col1:
    if st.button("Controleer! (Check!)"):
        if user_ans == answer:
            st.session_state.tafel_feedback = "✅ Goed gedaan! (+10 punten) <br><span class='eng-sub'>(Well done! +10 points)</span>"
            add_score(10)
            st.balloons()
            # Generate new problem after delay could be nice, but for now we just show a 'Volgende' button
        elif user_ans is not None:
            st.session_state.tafel_feedback = "❌ Oeps, probeer het nog eens! <br><span class='eng-sub'>(Oops, try again!)</span>"
            st.session_state.streaks = 0

with col2:
    if st.button("Volgende (Next) ➡️"):
        generate_problem()
        st.rerun()

if st.session_state.tafel_feedback:
    if "Goed gedaan" in st.session_state.tafel_feedback:
        st.success(st.session_state.tafel_feedback, icon="👽")
    else:
        st.error(st.session_state.tafel_feedback, icon="🛸")
