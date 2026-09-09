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
from utils.visuals import array_grid_svg, skip_count_svg

GAME_KEY = "tafel"

init_state()
init_language()

with st.sidebar:
    sidebar_common()

page_header("tafel.title", emoji="🚀")
st.caption(t("tafel.tagline"))
st.markdown(t("tafel.intro"))

level_control(GAME_KEY, "tafel_problem")
level = get_level(GAME_KEY)
points = 5 * (level + 1)

WORD_TEMPLATES = ["tafel.word_boxes", "tafel.word_rows", "tafel.word_moons"]


def generate_problem():
    if level == 1:
        a, b = random.randint(1, 5), random.randint(2, 10)
    elif level == 2:
        a, b = random.randint(2, 10), random.randint(2, 10)
    elif level == 3:
        a, b = random.randint(2, 12), random.randint(2, 12)
    elif level == 4:
        a, b = random.randint(11, 20), random.randint(2, 9)
    else:
        a, b = random.randint(11, 20), random.randint(11, 20)

    product = a * b

    type_choices = ["mult"]
    if level >= 2:
        type_choices.append("missing_factor")
    if level >= 3:
        type_choices.append("division")
    if level >= 4:
        type_choices.append("word")
    q_type = random.choice(type_choices)

    known_factor = None  # set for missing_factor/division: the one factor still given in the question
    if q_type == "mult":
        text = t("tafel.q_mult", a=a, b=b)
        answer = product
    elif q_type == "missing_factor":
        if random.choice([True, False]):
            text = t("tafel.q_missing_b", a=a, product=product)
            answer = b
            known_factor = a
        else:
            text = t("tafel.q_missing_a", b=b, product=product)
            answer = a
            known_factor = b
    elif q_type == "division":
        text = t("tafel.q_division", product=product, a=a)
        answer = b
        known_factor = a
    else:
        text = t(random.choice(WORD_TEMPLATES), a=a, b=b)
        answer = product

    st.session_state.tafel_problem = {
        "text": text,
        "answer": answer,
        "a": a,
        "b": b,
        "product": product,
        "q_type": q_type,
        "known_factor": known_factor,
    }
    st.session_state.tafel_feedback = None


if "tafel_problem" not in st.session_state or st.session_state.tafel_problem is None:
    generate_problem()

problem = st.session_state.tafel_problem

st.markdown(f"### 👾 {problem['text']}")

with st.expander(t("common.show_visual_hint")):
    if problem["q_type"] in ("missing_factor", "division"):
        # The unknown here is one of the two factors, so an accurate a x b
        # grid would let a child read the answer straight off by counting a
        # side - that's the direct answer, not a hint. Instead, show a
        # skip-counting number line for the *known* factor: the child still
        # has to count hops to the target themselves.
        st.markdown(t("common.skip_count_hint", step=problem["known_factor"]))
        st.markdown(skip_count_svg(problem["known_factor"], problem["product"]), unsafe_allow_html=True)
    else:
        st.markdown(array_grid_svg(problem["a"], problem["b"]), unsafe_allow_html=True)

user_ans = st.number_input(t("common.your_answer"), step=1, value=None, key="tafel_input")

col1, col2 = st.columns([1, 4])
with col1:
    check_clicked = st.button(t("tafel.check_button"), key="check_btn")
with col2:
    next_clicked = st.button(t("tafel.next_button"), key="next_btn")

if check_clicked:
    is_correct = user_ans is not None and user_ans == problem["answer"]
    if user_ans is not None:
        gamelog.log_attempt(
            GAME_KEY, t("game.tafel.name"), level, problem["text"], user_ans, problem["answer"], is_correct, points
        )
        leveled_up, leveled_down = register_attempt(GAME_KEY, is_correct)
        if is_correct:
            add_score(points)
            st.session_state.tafel_feedback = ("success", t("tafel.correct", points=points))
            st.balloons()
        else:
            reset_streak()
            st.session_state.tafel_feedback = (
                "error",
                f"{t('tafel.incorrect')} {t('common.correct_answer_was', answer=problem['answer'])}",
            )
        if leveled_up:
            st.toast(t("common.level_up", level=get_level(GAME_KEY)), icon="🚀")
        elif leveled_down:
            st.toast(t("common.level_down", level=get_level(GAME_KEY)), icon="💪")
        st.rerun()

if next_clicked:
    generate_problem()
    st.rerun()

feedback = st.session_state.get("tafel_feedback")
if feedback:
    kind, message = feedback
    if kind == "success":
        st.success(message, icon="👽")
    else:
        st.error(message, icon="🛸")

if st.session_state.get("streaks", 0) >= 3:
    st.info(t("common.streak_fire", streak=st.session_state.streaks))

st.caption(t("common.session_recorded"))
