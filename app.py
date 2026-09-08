import streamlit as st

from utils.i18n import init_language, t
from utils.state import GAME_KEYS, get_level, init_state
from utils.ui import (
    level_label,
    page_header,
    set_custom_css,
    sidebar_common,
)

init_state()
init_language()

st.set_page_config(
    page_title=t("app.title"),
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

set_custom_css()

with st.sidebar:
    st.image("https://api.dicebear.com/7.x/bottts/svg?seed=Math&backgroundColor=ffdfbf", width=150)
    sidebar_common()

page_header("home.title", "home.subtitle", emoji="🎮")

st.text_input(
    t("dash.player_name_label"),
    key="player_name",
    placeholder=t("dash.player_name_placeholder"),
)

st.markdown(t("home.intro"))

st.markdown("---")
st.markdown(f"### {t('home.games_heading')}")
st.markdown(
    f"""
* {t('home.game_tafel')}
* {t('home.game_breuken')}
* {t('home.game_meten')}
* {t('home.game_procenten')}
* {t('home.game_uitleg')}
* {t('home.game_dashboard')}
"""
)

st.markdown("---")
st.markdown(f"### {t('home.level_overview')}")
cols = st.columns(len(GAME_KEYS))
for col, key in zip(cols, GAME_KEYS):
    with col:
        lvl = get_level(key)
        st.metric(t(f"game.{key}.name"), f"{lvl}/5", level_label(lvl), delta_color="off")

st.markdown("---")
st.markdown(f"### {t('home.about_heading')}")
st.markdown(t("home.about_text"))

if st.session_state.get("total_score", 0) == 0 and st.session_state.get("games_played", 0) == 0:
    if st.button(t("home.start_button")):
        st.balloons()
        st.session_state.games_played += 1
        st.rerun()
