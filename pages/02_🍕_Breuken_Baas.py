import math
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
    level_control,
    page_header,
    sidebar_common,
)
from utils.visuals import fraction_visual_svg

GAME_KEY = "breuken"

init_state()
init_language()

with st.sidebar:
    sidebar_common()

page_header("breuken.title", emoji="👨‍🍳")
st.caption(t("breuken.tagline"))
st.markdown(t("breuken.intro"))

level_control(GAME_KEY, "breuk_problem")
level = get_level(GAME_KEY)
points = 5 * (level + 1)

with st.expander(t("common.try_it_heading"), expanded=False):
    st.markdown(t("breuken.explore_intro"))
    exp_col1, exp_col2 = st.columns(2)
    with exp_col2:
        explore_den = st.slider(t("breuken.denominator_label"), min_value=1, max_value=20, value=4, step=1, key="explore_den")
    if st.session_state.get("explore_num", 0) > explore_den:
        st.session_state.explore_num = explore_den
    with exp_col1:
        # Numerator can't exceed the (possibly just-changed) denominator, so
        # dragging the denominator slider down always keeps a valid fraction.
        explore_num = st.slider(t("breuken.numerator_label"), min_value=0, max_value=explore_den, value=min(1, explore_den), step=1, key="explore_num")
    st.markdown(fraction_visual_svg(explore_num, explore_den), unsafe_allow_html=True)


def generate_problem():
    if level == 1:
        den = random.choice([4, 6, 8, 10])
        n1 = random.randint(1, den - 1)
        n2 = random.randint(1, den - n1)
        text = t("breuken.q_add", n1=n1, n2=n2, d=den)
        correct_num, correct_den = n1 + n2, den
        den_editable = False
        visual_fracs = [(n1, den), (n2, den)]
    elif level == 2:
        den = random.choice([4, 6, 8, 10, 12])
        if random.choice([True, False]):
            n1 = random.randint(1, den - 1)
            n2 = random.randint(1, den - 1)
            text = t("breuken.q_add", n1=n1, n2=n2, d=den)
            correct_num, correct_den = n1 + n2, den
        else:
            n1 = random.randint(2, den - 1)
            n2 = random.randint(1, n1)
            text = t("breuken.q_sub", n1=n1, n2=n2, d=den)
            correct_num, correct_den = n1 - n2, den
        den_editable = False
        visual_fracs = [(n1, den), (n2, den)]
    elif level == 3:
        factor = random.randint(2, 4)
        simplified_den = random.choice([2, 3, 4, 5, 6])
        # Must be coprime with simplified_den, otherwise this "fully
        # simplified" fraction (e.g. 2/4) wouldn't actually be in lowest
        # terms, contradicting the question's "simplify as far as possible".
        simplified_num = random.choice([n for n in range(1, simplified_den) if math.gcd(n, simplified_den) == 1])
        den = simplified_den * factor
        num = simplified_num * factor
        text = t("breuken.q_simplify", n=num, d=den, new_d=simplified_den)
        correct_num, correct_den = simplified_num, simplified_den
        den_editable = False
        visual_fracs = [(num, den)]
    elif level == 4:
        d1 = random.choice([2, 3, 4, 5])
        k = random.choice([2, 3])
        d2 = d1 * k
        n1 = random.randint(1, d1 - 1)
        n2 = random.randint(1, d2 - 1)
        text = t("breuken.q_diff_denom", n1=n1, d1=d1, n2=n2, d2=d2)
        correct_num, correct_den = n1 * k + n2, d2
        den_editable = True
        visual_fracs = [(n1, d1), (n2, d2)]
    else:
        den = random.choice([3, 4, 5, 6])
        num = random.randint(1, den - 1)
        k = random.randint(2, 4)
        text = t("breuken.q_multiply", k=k, n=num, d=den)
        correct_num, correct_den = num * k, den
        den_editable = False
        visual_fracs = [(num, den)]

    st.session_state.breuk_problem = {
        "text": text,
        "correct_num": correct_num,
        "correct_den": correct_den,
        "den_editable": den_editable,
        "visual_fracs": visual_fracs,
    }
    st.session_state.breuk_feedback = None


if "breuk_problem" not in st.session_state or st.session_state.breuk_problem is None:
    generate_problem()

problem = st.session_state.breuk_problem

st.markdown(f"### 🍕 {problem['text']}")

visual_cols = st.columns(len(problem["visual_fracs"]))
for vcol, (vn, vd) in zip(visual_cols, problem["visual_fracs"]):
    with vcol:
        st.markdown(fraction_visual_svg(vn, vd), unsafe_allow_html=True)

col_ans1, col_ans2 = st.columns([1, 1])
with col_ans1:
    user_num = st.number_input(t("breuken.numerator_label"), step=1, value=None, key="teller")
with col_ans2:
    if problem["den_editable"]:
        user_den = st.number_input(t("breuken.denominator_label"), step=1, value=None, key="noemer")
    else:
        st.number_input(
            t("breuken.denominator_label"),
            step=1,
            value=problem["correct_den"],
            disabled=True,
            key="noemer_disabled",
        )
        user_den = problem["correct_den"]

col_btn1, col_btn2 = st.columns([1, 4])
with col_btn1:
    check_clicked = st.button(t("breuken.check_button"), key="check_btn")
with col_btn2:
    next_clicked = st.button(t("breuken.next_button"), key="next_btn")

if check_clicked:
    answered = user_num is not None and (not problem["den_editable"] or user_den is not None)
    if answered:
        is_correct = user_num == problem["correct_num"] and user_den == problem["correct_den"]
        student_answer = f"{user_num}/{user_den}"
        correct_answer = f"{problem['correct_num']}/{problem['correct_den']}"
        gamelog.log_attempt(
            GAME_KEY, t("game.breuken.name"), level, problem["text"], student_answer, correct_answer, is_correct, points
        )
        leveled_up, leveled_down = register_attempt(GAME_KEY, is_correct)
        if is_correct:
            add_score(points)
            st.session_state.breuk_feedback = ("success", t("breuken.correct", points=points))
            st.balloons()
        else:
            reset_streak()
            st.session_state.breuk_feedback = (
                "error",
                f"{t('breuken.incorrect')} {t('common.correct_answer_was', answer=correct_answer)}",
            )
        if leveled_up:
            st.toast(t("common.level_up", level=get_level(GAME_KEY)), icon="🚀")
        elif leveled_down:
            st.toast(t("common.level_down", level=get_level(GAME_KEY)), icon="💪")
        st.rerun()

if next_clicked:
    generate_problem()
    st.rerun()

feedback = st.session_state.get("breuk_feedback")
if feedback:
    kind, message = feedback
    if kind == "success":
        st.success(message, icon="🎉")
    else:
        st.error(message, icon="🔥")

if st.session_state.get("streaks", 0) >= 3:
    st.info(t("common.streak_fire", streak=st.session_state.streaks))

st.caption(t("common.session_recorded"))
