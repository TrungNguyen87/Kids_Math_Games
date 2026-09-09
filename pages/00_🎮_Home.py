import streamlit as st

from utils import badges, profiles
from utils.i18n import init_language, t
from utils.state import GAME_KEYS, get_level, init_state
from utils.ui import level_label, page_header, sidebar_common

init_state()
init_language()

# Resolve the player name and load any saved profile for it BEFORE
# rendering the sidebar (which shows the score) - otherwise the sidebar
# would render with the pre-load score for one frame, contradicting the
# "loaded your saved progress" message shown further down the same run.
# The widget's own key ("player_name_input") isn't created until later in
# this script, but its session-state value from the previous run is still
# there (Streamlit clears a widget's key only when it *isn't* rendered on
# the current page - this page renders it every time), so it's safe to
# read here ahead of the actual st.text_input(...) call below.
current_name = st.session_state.get("player_name_input", st.session_state.get("player_name", ""))
just_loaded = False
if current_name and st.session_state.get("loaded_profile_for") != current_name:
    just_loaded = profiles.apply_profile(current_name)
    st.session_state.loaded_profile_for = current_name
    st.session_state.player_name = current_name

with st.sidebar:
    st.image("https://api.dicebear.com/7.x/bottts/svg?seed=Math&backgroundColor=ffdfbf", width=150)
    sidebar_common()

page_header("home.title", "home.subtitle", emoji="🎮")

# The widget's own key ("player_name_input") is scoped to this page: Streamlit
# clears a widget's session-state entry whenever the widget isn't rendered on
# the currently running page, so navigating away and back would wipe it. We
# therefore keep the durable value in a separate key ("player_name", used
# everywhere else in the app - gamelog, sidebar, dashboard) and re-seed the
# widget from it every time this page runs.
entered_name = st.text_input(
    t("dash.player_name_label"),
    value=st.session_state.get("player_name", ""),
    key="player_name_input",
    placeholder=t("dash.player_name_placeholder"),
)
st.session_state.player_name = entered_name

if entered_name:
    if just_loaded:
        st.success(t("home.profile_loaded", name=entered_name, score=st.session_state.total_score), icon="🔄")
    else:
        st.success(t("home.player_saved", name=entered_name), icon="✅")

st.markdown(t("home.intro"))

st.markdown("---")
st.markdown(f"### {t('home.games_heading')}")
st.markdown(
    f"""
* {t('home.game_tafel')}
* {t('home.game_breuken')}
* {t('home.game_meten')}
* {t('home.game_procenten')}
* {t('home.game_algebra')}
* {t('home.game_meetkunde')}
* {t('home.game_verhoudingen')}
* {t('home.game_getallen')}
* {t('home.game_bliksem')}
* {t('home.game_jacht')}
* {t('home.game_logica')}
* {t('home.game_code')}
* {t('home.game_uitleg')}
* {t('home.game_dashboard')}
"""
)

st.markdown("---")
st.markdown(f"### {t('home.level_overview')}")
# Four per row: with 12 games, splitting into two rows of six left the
# metric labels too narrow to read on a laptop.
PER_ROW = 4
rows = [GAME_KEYS[i : i + PER_ROW] for i in range(0, len(GAME_KEYS), PER_ROW)]
for row in rows:
    cols = st.columns(PER_ROW)
    for col, key in zip(cols, row):
        with col:
            lvl = get_level(key)
            st.metric(t(f"game.{key}.name"), f"{lvl}/5", level_label(lvl), delta_color="off")

st.markdown("---")
st.markdown(f"### {t('home.badges_heading')}")
earned_badges = st.session_state.get("badges", [])
if earned_badges:
    st.markdown(
        " &nbsp; ".join(
            f"{badges.BADGE_EMOJI[b]} {t(f'badges.{b}.name')}" for b in earned_badges
        )
    )
else:
    st.caption(t("home.badges_none"))

st.markdown("---")
st.markdown(f"### {t('home.about_heading')}")
st.markdown(t("home.about_text"))

if st.session_state.get("total_score", 0) == 0 and st.session_state.get("games_played", 0) == 0:
    if st.button(t("home.start_button")):
        st.balloons()
        st.session_state.games_played += 1
        st.rerun()
