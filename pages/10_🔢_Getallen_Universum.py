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
from utils.ui import level_control, page_header, sidebar_common
from utils.visuals import number_line_svg

GAME_KEY = "getallen"

init_state()
init_language()

with st.sidebar:
    sidebar_common()

page_header("getallen.title", emoji="🔢")
st.caption(t("getallen.tagline"))
st.markdown(t("getallen.intro"))

level_control(GAME_KEY, "getallen_problem")
level = get_level(GAME_KEY)
points = 5 * (level + 1)


def fmt(n):
    return f"({n})" if n < 0 else str(n)


def format_num1(value):
    text = f"{value:.1f}"
    if st.session_state.get("language", "nl") == "nl":
        text = text.replace(".", ",")
    return text


def generate_problem():
    answer_kind = "int"  # "int", "decimal1", or "two_part"
    visual = None

    if level == 1:
        a = random.choice([v for v in range(-15, 16) if v != 0])
        b = random.choice([v for v in range(-15, 16) if v != 0])
        if random.choice([True, False]):
            text = t("getallen.q_negative_add", a=fmt(a), b=fmt(b))
            answer = a + b
        else:
            text = t("getallen.q_negative_sub", a=fmt(a), b=fmt(b))
            answer = a - b
        visual = number_line_svg(min(-20, a - 5), max(20, a + 5), [(a, "start")])

    elif level == 2:
        a = random.randint(-10, 10)
        step = random.randint(2, 5)
        jumps = random.randint(2, 5)
        direction = random.choice(["right", "left"])
        sign = 1 if direction == "right" else -1
        answer = a + sign * step * jumps
        text = t("getallen.q_jump", a=a, jumps=jumps, step=step, direction=t(f"getallen.direction_{direction}"))
        lo = min(-25, a - step * jumps - 5)
        hi = max(25, a + step * jumps + 5)
        visual = number_line_svg(lo, hi, [(a, "start")])

    elif level == 3:
        a = random.randint(11, 99)
        b = random.randint(11, 99)
        text = t("getallen.q_long_mult", a=a, b=b)
        answer = a * b

    elif level == 4:
        divisor = random.randint(3, 12)
        quotient = random.randint(4, 20)
        remainder = random.randint(0, divisor - 1)
        dividend = divisor * quotient + remainder
        text = t("getallen.q_long_div", dividend=dividend, divisor=divisor)
        answer = {"q": quotient, "r": remainder}
        answer_kind = "two_part"

    else:
        if random.choice([True, False]):
            n = random.randint(11, 95)
            b = random.randint(2, 9)
            a_val = n / 10
            text = t("getallen.q_decimal_mult", a=format_num1(a_val), b=b)
            answer = round(n * b / 10, 1)
        else:
            b = random.randint(2, 9)
            quotient_n = random.randint(11, 95)
            dividend_val = round(quotient_n * b / 10, 1)
            text = t("getallen.q_decimal_div", dividend=format_num1(dividend_val), b=b)
            answer = round(quotient_n / 10, 1)
        answer_kind = "decimal1"

    st.session_state.getallen_problem = {
        "text": text,
        "answer": answer,
        "answer_kind": answer_kind,
        "visual": visual,
    }
    st.session_state.getallen_feedback = None


if "getallen_problem" not in st.session_state or st.session_state.getallen_problem is None:
    generate_problem()

problem = st.session_state.getallen_problem

st.markdown(f"### 🔢 {problem['text']}")

if problem["visual"]:
    st.markdown(problem["visual"], unsafe_allow_html=True)

user_q = user_r = None
if problem["answer_kind"] == "two_part":
    col_q, col_r = st.columns(2)
    with col_q:
        user_q = st.number_input(t("getallen.quotient_label"), step=1, value=None, key="getallen_q")
    with col_r:
        user_r = st.number_input(t("getallen.remainder_label"), step=1, value=None, key="getallen_r")
elif problem["answer_kind"] == "decimal1":
    user_val = st.number_input(t("getallen.answer_label"), step=0.1, value=None, format="%.1f", key="getallen_decimal")
else:
    user_val = st.number_input(t("getallen.answer_label"), step=1, value=None, key="getallen_int")

col1, col2 = st.columns([1, 4])
with col1:
    check_clicked = st.button(t("getallen.check_button"), key="check_btn")
with col2:
    next_clicked = st.button(t("getallen.next_button"), key="next_btn")

if check_clicked:
    if problem["answer_kind"] == "two_part":
        answered = user_q is not None and user_r is not None
    else:
        answered = user_val is not None

    if answered:
        if problem["answer_kind"] == "two_part":
            is_correct = user_q == problem["answer"]["q"] and user_r == problem["answer"]["r"]
            student_answer = f"{user_q} {t('getallen.remainder_word')} {user_r}"
            correct_answer_display = f"{problem['answer']['q']} {t('getallen.remainder_word')} {problem['answer']['r']}"
        elif problem["answer_kind"] == "decimal1":
            is_correct = abs(user_val - problem["answer"]) < 0.05
            student_answer = user_val
            correct_answer_display = format_num1(problem["answer"])
        else:
            is_correct = user_val == problem["answer"]
            student_answer = user_val
            correct_answer_display = problem["answer"]

        gamelog.log_attempt(
            GAME_KEY, t("game.getallen.name"), level, problem["text"], student_answer, correct_answer_display, is_correct, points
        )
        leveled_up, leveled_down = register_attempt(GAME_KEY, is_correct)
        if is_correct:
            add_score(points)
            st.session_state.getallen_feedback = ("success", t("getallen.correct", points=points))
            st.balloons()
        else:
            reset_streak()
            st.session_state.getallen_feedback = (
                "error",
                f"{t('getallen.incorrect')} {t('common.correct_answer_was', answer=correct_answer_display)}",
            )
        if leveled_up:
            st.toast(t("common.level_up", level=get_level(GAME_KEY)), icon="🚀")
        elif leveled_down:
            st.toast(t("common.level_down", level=get_level(GAME_KEY)), icon="💪")
        st.rerun()

if next_clicked:
    generate_problem()
    st.rerun()

feedback = st.session_state.get("getallen_feedback")
if feedback:
    kind, message = feedback
    if kind == "success":
        st.success(message, icon="🛰️")
    else:
        st.error(message, icon="☄️")

if st.session_state.get("streaks", 0) >= 3:
    st.info(t("common.streak_fire", streak=st.session_state.streaks))

st.caption(t("common.session_recorded"))
