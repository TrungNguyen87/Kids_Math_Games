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
from utils.ui import level_control, page_header, set_custom_css, sidebar_common
from utils.visuals import cuboid_svg, rectangle_svg, triangle_svg

GAME_KEY = "meetkunde"
UNIT = "cm"

init_state()
init_language()

st.set_page_config(page_title="Meetkunde Meesters", page_icon="📐", layout="wide")
set_custom_css()

with st.sidebar:
    sidebar_common()

page_header("meetkunde.title", emoji="📐")
st.caption(t("meetkunde.tagline"))
st.markdown(t("meetkunde.intro"))

level_control(GAME_KEY, "meetkunde_problem")
level = get_level(GAME_KEY)
points = 5 * (level + 1)


def generate_problem():
    if level == 1:
        w, h = random.randint(2, 12), random.randint(2, 12)
        if random.choice([True, False]):
            text = t("meetkunde.q_perimeter", w=w, h=h, unit=UNIT)
            answer, unit_suffix = 2 * (w + h), UNIT
        else:
            text = t("meetkunde.q_area_rect", w=w, h=h, unit=UNIT)
            answer, unit_suffix = w * h, f"{UNIT}²"
        visual = ("rect", w, h)

    elif level == 2:
        height_val = random.choice(range(2, 13, 2))
        base = random.randint(2, 15)
        text = t("meetkunde.q_area_triangle", base=base, height=height_val, unit=UNIT)
        answer, unit_suffix = base * height_val // 2, f"{UNIT}²"
        visual = ("triangle", base, height_val)

    elif level == 3:
        h = random.randint(2, 10)
        w1 = random.randint(2, 10)
        w2 = random.randint(2, 10)
        text = t("meetkunde.q_area_compound", w1=w1, w2=w2, h=h, unit=UNIT)
        answer, unit_suffix = (w1 + w2) * h, f"{UNIT}²"
        visual = ("compound", w1, w2, h)

    elif level == 4:
        l, w, h = random.randint(2, 10), random.randint(2, 10), random.randint(2, 10)
        text = t("meetkunde.q_volume", l=l, w=w, h=h, unit=UNIT)
        answer, unit_suffix = l * w * h, f"{UNIT}³"
        visual = ("cuboid", l, w, h)

    else:
        shape = random.choice(["triangle", "quadrilateral"])
        total = 180 if shape == "triangle" else 360
        n = 3 if shape == "triangle" else 4
        for _ in range(30):
            given = [random.randint(35, 95) for _ in range(n - 1)]
            missing = total - sum(given)
            if 10 <= missing <= 150:
                break
        given_text = " + ".join(str(g) for g in given)
        shape_text = t(f"meetkunde.shape_{shape}")
        text = t("meetkunde.q_angle", shape=shape_text, total=total, given=given_text)
        answer, unit_suffix = missing, "°"
        visual = ("triangle", 12, 8) if shape == "triangle" else ("rect", 10, 8)

    st.session_state.meetkunde_problem = {
        "text": text,
        "answer": answer,
        "unit_suffix": unit_suffix,
        "visual": visual,
    }
    st.session_state.meetkunde_feedback = None


if "meetkunde_problem" not in st.session_state or st.session_state.meetkunde_problem is None:
    generate_problem()

problem = st.session_state.meetkunde_problem

st.markdown(f"### 📐 {problem['text']}")

visual = problem["visual"]
if visual[0] == "rect":
    st.markdown(rectangle_svg(visual[1], visual[2], unit=UNIT), unsafe_allow_html=True)
elif visual[0] == "triangle":
    st.markdown(triangle_svg(visual[1], visual[2], unit=UNIT), unsafe_allow_html=True)
elif visual[0] == "cuboid":
    st.markdown(cuboid_svg(visual[1], visual[2], visual[3], unit=UNIT), unsafe_allow_html=True)
elif visual[0] == "compound":
    _, w1, w2, h = visual
    vcol1, vcol2 = st.columns(2)
    with vcol1:
        st.markdown(rectangle_svg(w1, h, unit=UNIT), unsafe_allow_html=True)
    with vcol2:
        st.markdown(rectangle_svg(w2, h, unit=UNIT), unsafe_allow_html=True)

label = t("meetkunde.answer_label_deg") if problem["unit_suffix"] == "°" else t("meetkunde.answer_label")
user_val = st.number_input(label, step=1, value=None, key="meetkunde_input")

col1, col2 = st.columns([1, 4])
with col1:
    check_clicked = st.button(t("meetkunde.check_button"), key="check_btn")
with col2:
    next_clicked = st.button(t("meetkunde.next_button"), key="next_btn")

if check_clicked:
    if user_val is not None:
        is_correct = user_val == problem["answer"]
        correct_answer_display = f"{problem['answer']} {problem['unit_suffix']}"
        gamelog.log_attempt(
            GAME_KEY, t("game.meetkunde.name"), level, problem["text"], user_val, correct_answer_display, is_correct, points
        )
        leveled_up, leveled_down = register_attempt(GAME_KEY, is_correct)
        if is_correct:
            add_score(points)
            st.session_state.meetkunde_feedback = ("success", t("meetkunde.correct", points=points))
            st.balloons()
        else:
            reset_streak()
            st.session_state.meetkunde_feedback = (
                "error",
                f"{t('meetkunde.incorrect')} {t('common.correct_answer_was', answer=correct_answer_display)}",
            )
        if leveled_up:
            st.toast(t("common.level_up", level=get_level(GAME_KEY)), icon="🚀")
        elif leveled_down:
            st.toast(t("common.level_down", level=get_level(GAME_KEY)), icon="💪")
        st.rerun()

if next_clicked:
    generate_problem()
    st.rerun()

feedback = st.session_state.get("meetkunde_feedback")
if feedback:
    kind, message = feedback
    if kind == "success":
        st.success(message, icon="🏛️")
    else:
        st.error(message, icon="🧱")

if st.session_state.get("streaks", 0) >= 3:
    st.info(t("common.streak_fire", streak=st.session_state.streaks))

st.caption(t("common.session_recorded"))
