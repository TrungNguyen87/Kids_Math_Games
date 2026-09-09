import streamlit as st

from utils.i18n import init_language, t
from utils.state import init_state
from utils.ui import set_custom_css

init_state()
init_language()

st.set_page_config(
    page_title=t("app.title"),
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

set_custom_css()

# Pages are declared here (instead of relying on Streamlit's filename-based
# pages/ auto-discovery) so the navigation menu is rebuilt from t() on every
# rerun - this is what makes the sidebar menu follow the NL/EN language
# toggle instead of always showing the Dutch filenames. It also lets us pin
# an explicit order, keeping the Parent Dashboard as the last entry.
home = st.Page("pages/00_🎮_Home.py", title=t("nav.home"), icon="🎮", url_path="home", default=True)
tafel = st.Page("pages/01_✖️_Tafel_Monster.py", title=t("nav.tafel"), icon="✖️", url_path="tafel")
breuken = st.Page("pages/02_🍕_Breuken_Baas.py", title=t("nav.breuken"), icon="🍕", url_path="breuken")
meten = st.Page("pages/03_📏_Meten_is_Weten.py", title=t("nav.meten"), icon="📏", url_path="meten")
procenten = st.Page("pages/04_💯_Procenten_Puzzel.py", title=t("nav.procenten"), icon="💯", url_path="procenten")
algebra = st.Page("pages/07_🕵️_Het_X-Mysterie.py", title=t("nav.algebra"), icon="🕵️", url_path="algebra")
meetkunde = st.Page("pages/08_📐_Meetkunde_Meesters.py", title=t("nav.meetkunde"), icon="📐", url_path="meetkunde")
verhoudingen = st.Page("pages/09_🚗_Verhoudingen_en_Snelheid.py", title=t("nav.verhoudingen"), icon="🚗", url_path="verhoudingen")
getallen = st.Page("pages/10_🔢_Getallen_Universum.py", title=t("nav.getallen"), icon="🔢", url_path="getallen")
bliksem = st.Page("pages/11_⚡_Bliksemronde.py", title=t("nav.bliksem"), icon="⚡", url_path="bliksemronde")
logica = st.Page("pages/12_🧠_Logica_Lab.py", title=t("nav.logica"), icon="🧠", url_path="logica")
code = st.Page("pages/13_🔐_Code_Kraker.py", title=t("nav.code"), icon="🔐", url_path="code")
jacht = st.Page("pages/14_🎯_Getallenjacht.py", title=t("nav.jacht"), icon="🎯", url_path="getallenjacht")
uitleg = st.Page("pages/05_📖_Uitleg_Concepten.py", title=t("nav.uitleg"), icon="📖", url_path="uitleg")
dashboard = st.Page("pages/06_📊_Ouder_Dashboard.py", title=t("nav.dashboard"), icon="📊", url_path="dashboard")

pg = st.navigation(
    [
        home,
        tafel,
        breuken,
        meten,
        procenten,
        algebra,
        meetkunde,
        verhoudingen,
        getallen,
        # Speed and logic games are grouped after the arithmetic ones, so
        # the menu reads as "practise, then play with what you practised".
        bliksem,
        jacht,
        logica,
        code,
        uitleg,
        dashboard,  # kept last on purpose - the parent-facing page
    ]
)
pg.run()
