import pandas as pd
import streamlit as st

from utils import gamelog
from utils.i18n import init_language, t
from utils.state import init_state
from utils.ui import page_header, sidebar_common

init_state()
init_language()

with st.sidebar:
    sidebar_common()

page_header("dash.title", "dash.subtitle", emoji="📊")
st.markdown(t("dash.intro"))

history_df = gamelog.get_full_history_dataframe()
session_df = gamelog.get_session_dataframe()

if history_df.empty:
    combined_df = session_df
else:
    combined_df = pd.concat([history_df, session_df], ignore_index=True)
    combined_df = combined_df.drop_duplicates(
        subset=["timestamp", "session_id", "question", "student_answer"], keep="first"
    )

if combined_df.empty:
    st.info(t("dash.no_data"))
    st.stop()

combined_df["timestamp"] = pd.to_datetime(combined_df["timestamp"])
combined_df = combined_df.sort_values("timestamp", ascending=False)

players = sorted(combined_df["player"].dropna().unique().tolist())
selected_player = st.selectbox(t("dash.filter_child"), [t("dash.filter_all")] + players)
if selected_player != t("dash.filter_all"):
    view_df = combined_df[combined_df["player"] == selected_player]
else:
    view_df = combined_df

# --- Summary metrics -------------------------------------------------------
sessions = view_df["session_id"].nunique()
questions = len(view_df)
accuracy = 100 * (view_df["result"] == "correct").mean() if questions else 0.0

duration_per_session = view_df.groupby("session_id")["timestamp"].agg(lambda s: (s.max() - s.min()).total_seconds() / 60)
total_minutes = duration_per_session.sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric(t("dash.metric_sessions"), sessions)
col2.metric(t("dash.metric_questions"), questions)
col3.metric(t("dash.metric_accuracy"), f"{accuracy:.0f}%")
col4.metric(t("dash.metric_time"), f"{total_minutes:.0f}")

st.markdown("---")

# --- Per-game charts ---------------------------------------------------------
game_names = sorted(view_df["game"].dropna().unique().tolist())
if game_names:
    left, right = st.columns(2)
    with left:
        st.markdown(f"#### {t('dash.accuracy_chart_heading')}")
        acc_by_game = view_df.groupby("game")["result"].apply(lambda s: (s == "correct").mean() * 100)
        st.bar_chart(acc_by_game)
    with right:
        st.markdown(f"#### {t('dash.progress_chart_heading')}")
        by_day = view_df.copy()
        by_day["date"] = by_day["timestamp"].dt.date
        questions_per_day = by_day.groupby("date").size()
        st.bar_chart(questions_per_day)

st.markdown("---")

# --- Full log table ----------------------------------------------------------
st.markdown(f"#### {t('dash.table_heading')}")
display_df = view_df[
    ["timestamp", "player", "game", "level", "question", "student_answer", "correct_answer", "result", "points"]
].rename(
    columns={
        "timestamp": t("dash.col_time"),
        "player": t("dash.col_player"),
        "game": t("dash.col_game"),
        "level": t("dash.col_level"),
        "question": t("dash.col_question"),
        "student_answer": t("dash.col_answer"),
        "correct_answer": t("dash.col_correct_answer"),
        "result": t("dash.col_result"),
        "points": t("dash.col_points"),
    }
)
st.dataframe(display_df, width="stretch", hide_index=True)

# --- Downloads -----------------------------------------------------------------
dl1, dl2 = st.columns(2)
with dl1:
    st.download_button(
        t("dash.download_full"),
        data=gamelog.to_csv_bytes(combined_df),
        file_name="reken_spelletjes_geschiedenis.csv",
        mime="text/csv",
    )
with dl2:
    st.download_button(
        t("dash.download_session"),
        data=gamelog.to_csv_bytes(session_df),
        file_name=f"reken_spelletjes_sessie_{st.session_state.get('session_id', 'huidig')}.csv",
        mime="text/csv",
        disabled=session_df.empty,
    )

st.markdown("---")

# --- Danger zone: clear history --------------------------------------------
if st.button(t("dash.clear_history_button")):
    st.session_state.confirm_clear_history = True

if st.session_state.get("confirm_clear_history"):
    st.warning(t("dash.clear_history_confirm"))
    if st.button(t("dash.clear_history_confirm_button")):
        gamelog.clear_history()
        st.session_state.log = []
        st.session_state.confirm_clear_history = False
        # st.toast (unlike st.success) survives the rerun below, so the
        # confirmation is actually visible instead of being wiped instantly.
        st.toast(t("dash.clear_history_done"), icon="🗑️")
        st.rerun()
