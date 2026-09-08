import streamlit as st
import random
from utils.state import add_score
from utils.ui import set_custom_css, show_score, bilingual_header

st.set_page_config(page_title="Breuken Baas", page_icon="🍕", layout="wide")
set_custom_css()

with st.sidebar:
    show_score()

bilingual_header("Pizzeria: Breuken Baas!", "Pizzeria: Fraction Boss!", emoji="👨‍🍳")
st.markdown("Help de kok de pizza's te verdelen! Tel de breuken bij elkaar op. <br><span class='eng-sub'>(Help the chef divide the pizzas! Add the fractions together.)</span>", unsafe_allow_html=True)

if 'breuk_problem' not in st.session_state:
    st.session_state.breuk_problem = None
if 'breuk_feedback' not in st.session_state:
    st.session_state.breuk_feedback = ""

def generate_breuk_problem():
    # Simple addition of fractions with the same denominator for now
    den = random.choice([4, 6, 8, 10])
    num1 = random.randint(1, den - 1)
    num2 = random.randint(1, den - num1) # Ensure sum <= 1
    st.session_state.breuk_problem = (num1, num2, den, num1 + num2)
    st.session_state.breuk_feedback = ""

if st.session_state.breuk_problem is None:
    generate_breuk_problem()

n1, n2, d, ans_n = st.session_state.breuk_problem

st.markdown(f"### 🍕 Hoeveel is {n1}/{d} + {n2}/{d}? <span class='eng-sub'>(What is {n1}/{d} + {n2}/{d}?)</span>", unsafe_allow_html=True)

col_ans1, col_ans2 = st.columns([1, 4])
with col_ans1:
    user_num = st.number_input("Teller (Top number):", step=1, value=None, key="teller")
    st.markdown("<hr style='margin: 0px;'>", unsafe_allow_html=True)
    user_den = st.number_input("Noemer (Bottom number):", step=1, value=d, disabled=True, key="noemer")

col_btn1, col_btn2 = st.columns([1, 4])
with col_btn1:
    if st.button("Serveer Pizza! (Serve!)"):
        if user_num == ans_n:
            st.session_state.breuk_feedback = "✅ Heerlijk! Goed gerekend! (+10 punten) <br><span class='eng-sub'>(Delicious! Well calculated! +10 points)</span>"
            add_score(10)
            st.balloons()
        elif user_num is not None:
            st.session_state.breuk_feedback = "❌ Oeps, de klant wacht! Probeer het opnieuw. <br><span class='eng-sub'>(Oops, the customer is waiting! Try again.)</span>"
            st.session_state.streaks = 0

with col_btn2:
    if st.button("Volgende Bestelling (Next Order) ➡️"):
        generate_breuk_problem()
        st.rerun()

if st.session_state.breuk_feedback:
    if "Heerlijk" in st.session_state.breuk_feedback:
        st.success(st.session_state.breuk_feedback, icon="🎉")
    else:
        st.error(st.session_state.breuk_feedback, icon="🔥")
