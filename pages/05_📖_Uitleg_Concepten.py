import streamlit as st

from utils.i18n import init_language, t
from utils.state import init_state
from utils.ui import page_header, sidebar_common

init_state()
init_language()

with st.sidebar:
    sidebar_common(show_progress=False)

page_header("uitleg.title", "uitleg.subtitle", emoji="📖")
st.markdown(t("uitleg.intro"))

with st.expander(t("uitleg.topic_tafel")):
    st.markdown(t("uitleg.body_tafel"))

with st.expander(t("uitleg.topic_breuken")):
    st.markdown(t("uitleg.body_breuken"))

with st.expander(t("uitleg.topic_meten")):
    st.markdown(t("uitleg.body_meten"))

with st.expander(t("uitleg.topic_procenten")):
    st.markdown(t("uitleg.body_procenten"))

with st.expander(t("uitleg.topic_algebra")):
    st.markdown(t("uitleg.body_algebra"))

with st.expander(t("uitleg.topic_meetkunde")):
    st.markdown(t("uitleg.body_meetkunde"))

with st.expander(t("uitleg.topic_verhoudingen")):
    st.markdown(t("uitleg.body_verhoudingen"))

with st.expander(t("uitleg.topic_getallen")):
    st.markdown(t("uitleg.body_getallen"))

st.info(t("uitleg.footer"))
