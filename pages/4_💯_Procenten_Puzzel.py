import streamlit as st
import random
from utils.state import add_score
from utils.ui import set_custom_css, show_score, bilingual_header

st.set_page_config(page_title="Procenten Puzzel", page_icon="💯", layout="wide")
set_custom_css()

with st.sidebar:
    show_score()

bilingual_header("Piraten Schat: Procenten Puzzel!", "Pirate Treasure: Percentage Puzzle!", emoji="🏴‍☠️")
st.markdown("Zoek de juiste schatkaart door de percentages, kommagetallen en breuken te matchen! <br><span class='eng-sub'>(Find the right treasure map by matching percentages, decimals, and fractions!)</span>", unsafe_allow_html=True)

if 'perc_problem' not in st.session_state:
    st.session_state.perc_problem = None
if 'perc_feedback' not in st.session_state:
    st.session_state.perc_feedback = ""

def generate_perc_problem():
    equivalents = [
        ("1/2", "50%", "0.50"),
        ("1/4", "25%", "0.25"),
        ("3/4", "75%", "0.75"),
        ("1/10", "10%", "0.10"),
        ("1/5", "20%", "0.20")
    ]
    fraction, percentage, decimal = random.choice(equivalents)
    
    # Pick a random question type
    q_type = random.choice(['frac_to_perc', 'perc_to_dec', 'dec_to_frac'])
    
    if q_type == 'frac_to_perc':
        q_text = f"Wat is {fraction} in procenten? (What is {fraction} in percentages?)"
        ans = percentage
        options = ["50%", "25%", "75%", "10%", "20%", "100%"]
    elif q_type == 'perc_to_dec':
        q_text = f"Wat is {percentage} als kommagetal? (What is {percentage} as a decimal?)"
        ans = decimal
        options = ["0.50", "0.25", "0.75", "0.10", "0.20", "1.00"]
    else:
        q_text = f"Wat is {decimal} als breuk? (What is {decimal} as a fraction?)"
        ans = fraction
        options = ["1/2", "1/4", "3/4", "1/10", "1/5", "1/1"]
        
    random.shuffle(options)
    st.session_state.perc_problem = (q_text, ans, options)
    st.session_state.perc_feedback = ""

if st.session_state.perc_problem is None:
    generate_perc_problem()

q, correct_ans, opts = st.session_state.perc_problem

st.markdown(f"### 💎 {q}", unsafe_allow_html=True)

user_choice = st.radio("Kies je antwoord (Choose your answer):", opts, index=None, key="perc_radio")

col1, col2 = st.columns([1, 4])
with col1:
    if st.button("Graaf schat op! (Dig treasure!)"):
        if user_choice == correct_ans:
            st.session_state.perc_feedback = "✅ Schat gevonden! (+10 punten) <br><span class='eng-sub'>(Treasure found! +10 points)</span>"
            add_score(10)
            st.balloons()
        elif user_choice is not None:
            st.session_state.perc_feedback = "❌ Verkeerde plek gegraven. Probeer opnieuw! <br><span class='eng-sub'>(Dug in the wrong spot. Try again!)</span>"
            st.session_state.streaks = 0

with col2:
    if st.button("Nieuwe kaart (New map) ➡️"):
        generate_perc_problem()
        st.rerun()

if st.session_state.perc_feedback:
    if "Schat" in st.session_state.perc_feedback:
        st.success(st.session_state.perc_feedback, icon="💰")
    else:
        st.error(st.session_state.perc_feedback, icon="☠️")
