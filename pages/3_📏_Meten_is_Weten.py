import random

import streamlit as st

from utils import gamelog
from utils.i18n import init_language, t
from utils.state import (
    add_score,
    get_level,
    init_state,
    register_attempt,
    reset_streak,
)
from utils.ui import (
    page_header,
    set_custom_css,
    show_level_badge,
    sidebar_common,
)

GAME_KEY = "meten"

init_state()
init_language()

st.set_page_config(page_title="Meten is Weten", page_icon="📏", layout="wide")
set_custom_css()

with st.sidebar:
    sidebar_common()

page_header("meten.title", emoji="🏗️")
st.caption(t("meten.tagline"))
st.markdown(t("meten.intro"))

level = get_level(GAME_KEY)
show_level_badge(level)
points = 5 * (level + 1)

CONVERSIONS = [
    ("cm", "mm", 10),
    ("m", "cm", 100),
    ("km", "m", 1000),
    ("kg", "g", 1000),
    ("l", "ml", 1000),
]
DECIMAL_STEPS = [0.25, 0.5, 0.75, 1.5, 2.5, 3.5, 4.5]


def format_euro(value):
    text = f"{value:.2f}"
    if st.session_state.get("language", "nl") == "nl":
        text = text.replace(".", ",")
    return text


def generate_problem():
    answer_kind = "int"  # "int" or "euro"

    if level == 1:
        unit1, unit2, factor = random.choice(CONVERSIONS)
        if random.choice([True, False]):
            val1 = random.randint(1, 20)
            val2 = val1 * factor
            text = t("meten.q_convert", v1=val1, u1=unit1, v2=val2, u2=unit2)
        else:
            val2 = random.randint(1, 20)
            val1 = val2 * factor
            text = t("meten.q_convert", v1=val1, u1=unit2, v2=val2, u2=unit1)
        answer = val2
        answer_label = t("meten.answer_label_generic")

    elif level == 2:
        unit1, unit2, factor = random.choice(CONVERSIONS)
        val1 = random.choice(DECIMAL_STEPS)
        val2 = round(val1 * factor)
        text = f"{val1} {unit1} = ... {unit2}?"
        answer = val2
        answer_label = t("meten.answer_label_generic")

    elif level == 3:
        unit_big, unit_small, factor = random.choice(CONVERSIONS)
        a = random.randint(1, 9)
        b = random.randint(1, factor - 1)
        text = t("meten.q_combo", a=a, u_big=unit_big, b=b, u_small=unit_small)
        answer = a * factor + b
        answer_label = t("meten.answer_label_generic")

    elif level == 4:
        start_minutes = random.randint(0, 23 * 60 + 55 - 180)
        gap = random.choice([15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 75, 90, 105, 120])
        end_minutes = start_minutes + gap
        t1 = f"{start_minutes // 60:02d}:{start_minutes % 60:02d}"
        t2 = f"{end_minutes // 60:02d}:{end_minutes % 60:02d}"
        key = random.choice(["meten.q_time_between", "meten.q_time_countdown"])
        text = t(key, t1=t1, t2=t2)
        answer = gap
        answer_label = t("meten.answer_label_minutes")

    else:
        answer_kind = "euro"
        if random.choice([True, False]):
            price = round(random.choice([x / 20 for x in range(4, 200)]), 2)
            notes = [n for n in (5, 10, 20) if n > price]
            paid = min(notes) if notes else 20
            text = t("meten.q_money_change", price=format_euro(price), paid=format_euro(paid))
            answer = round(paid - price, 2)
        else:
            price = random.choice([0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5])
            qty = random.randint(2, 6)
            text = t("meten.q_money_total", qty=qty, price=format_euro(price))
            answer = round(price * qty, 2)
        answer_label = t("meten.answer_label_euro")

    st.session_state.meten_problem = {
        "text": text,
        "answer": answer,
        "answer_kind": answer_kind,
        "answer_label": answer_label,
    }
    st.session_state.meten_feedback = None


if "meten_problem" not in st.session_state or st.session_state.meten_problem is None:
    generate_problem()

problem = st.session_state.meten_problem

st.markdown(f"### 🧱 {problem['text']}")

if problem["answer_kind"] == "euro":
    user_val = st.number_input(problem["answer_label"], step=0.01, value=None, format="%.2f", key="meten_input_euro")
else:
    user_val = st.number_input(problem["answer_label"], step=1, value=None, key="meten_input_int")

col1, col2 = st.columns([1, 4])
with col1:
    check_clicked = st.button(t("meten.check_button"))
with col2:
    next_clicked = st.button(t("meten.next_button"))

if check_clicked:
    if user_val is not None:
        if problem["answer_kind"] == "euro":
            is_correct = abs(user_val - problem["answer"]) < 0.005
            correct_answer_display = format_euro(problem["answer"])
        else:
            is_correct = user_val == problem["answer"]
            correct_answer_display = problem["answer"]
        gamelog.log_attempt(
            GAME_KEY, t("game.meten.name"), level, problem["text"], user_val, correct_answer_display, is_correct, points
        )
        leveled_up, leveled_down = register_attempt(GAME_KEY, is_correct)
        if is_correct:
            add_score(points)
            st.session_state.meten_feedback = ("success", t("meten.correct", points=points))
            st.balloons()
        else:
            reset_streak()
            st.session_state.meten_feedback = (
                "error",
                f"{t('meten.incorrect')} {t('common.correct_answer_was', answer=correct_answer_display)}",
            )
        if leveled_up:
            st.toast(t("common.level_up", level=get_level(GAME_KEY)), icon="🚀")
        elif leveled_down:
            st.toast(t("common.level_down", level=get_level(GAME_KEY)), icon="💪")
        st.rerun()

if next_clicked:
    generate_problem()
    st.rerun()

feedback = st.session_state.get("meten_feedback")
if feedback:
    kind, message = feedback
    if kind == "success":
        st.success(message, icon="👷")
    else:
        st.error(message, icon="🚧")

if st.session_state.get("streaks", 0) >= 3:
    st.info(t("common.streak_fire", streak=st.session_state.streaks))

st.caption(t("common.session_recorded"))
