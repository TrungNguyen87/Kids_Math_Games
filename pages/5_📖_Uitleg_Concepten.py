import streamlit as st
from utils.ui import set_custom_css, show_score, bilingual_header

st.set_page_config(page_title="Uitleg Concepten", page_icon="📖", layout="wide")
set_custom_css()

with st.sidebar:
    show_score()

bilingual_header("📖 Spiekbriefje (Cheat Sheet)", "Need a quick reminder? Look here!")
st.markdown("Klik op een onderwerp om de uitleg te zien. Handig als je even vastzit! <br><span class='eng-sub'>(Click on a topic to see the explanation. Handy if you get stuck!)</span>", unsafe_allow_html=True)

with st.expander("✖️ Tafels & Vermenigvuldigen (Multiplication)"):
    st.markdown("""
    **Tip:** Splits grote sommen op!
    * 15 x 4 = ?
    * Doe eerst 10 x 4 = 40
    * Dan 5 x 4 = 20
    * Samen is dat 40 + 20 = 60!
    
    <span class='eng-sub'>(Tip: Split up large problems! First 10x4, then 5x4, and add them up!)</span>
    """, unsafe_allow_html=True)

with st.expander("🍕 Breuken (Fractions)"):
    st.markdown("""
    **Boven = Teller (Top = Numerator)**: Hoeveel stukjes je hebt.
    **Onder = Noemer (Bottom = Denominator)**: In hoeveel stukjes de pizza is gesneden.
    
    *Als je breuken optelt met dezelfde noemer, tel je alleen de bovenste getallen (tellers) op!*
    Voorbeeld: 1/4 + 2/4 = 3/4
    
    <span class='eng-sub'>(If you add fractions with the same denominator, you only add the top numbers!)</span>
    """, unsafe_allow_html=True)

with st.expander("📏 Meten is Weten (Measurement)"):
    st.markdown("""
    Onthoud het trapje! (Remember the stairs!)
    * **1 km** = 1000 meter
    * **1 meter** = 100 centimeter
    * **1 centimeter** = 10 millimeter
    
    * **1 kg (kilogram)** = 1000 gram
    * **1 Liter** = 1000 milliliter
    """, unsafe_allow_html=True)

with st.expander("💯 Procenten & Kommagetallen (Percentages & Decimals)"):
    st.markdown("""
    Procent betekent "van de 100" (Per cent = out of 100).
    * 50% is de helft = 1/2 = 0.50
    * 25% is een kwart = 1/4 = 0.25
    * 100% is alles = 1 = 1.00
    """, unsafe_allow_html=True)

st.info("Klaar met lezen? Ga snel terug naar een spel en scoor punten! (Done reading? Go back to a game and score points!)")
