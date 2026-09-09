import random

import streamlit as st

from utils import badges, gamelog, profiles
from utils.i18n import init_language, t
from utils.state import (
    add_score,
    get_level,
    init_state,
    register_attempt,
    reset_streak,
)
from utils.ui import level_control, page_header, sidebar_common
from utils.anim import (
    feedback_banner,
    play_pending_celebration,
    question_card,
    queue_celebration,
)
from utils.sound import play_pending, queue_correct, queue_incorrect
from utils.visuals import cuboid_svg, rectangle_svg, triangle_svg

GAME_KEY = "meetkunde"
UNIT = "cm"

init_state()
init_language()

with st.sidebar:
    sidebar_common()

page_header("meetkunde.title", emoji="📐")
st.caption(t("meetkunde.tagline"))
st.markdown(t("meetkunde.intro"))

level_control(GAME_KEY, "meetkunde_problem")
level = get_level(GAME_KEY)
points = 5 * (level + 1)

with st.expander(t("common.try_it_heading"), expanded=False):
    st.markdown(t("meetkunde.explore_intro"))
    exp_col1, exp_col2 = st.columns(2)
    with exp_col1:
        explore_w = st.slider(t("meetkunde.width_label"), min_value=1, max_value=15, value=6, step=1, key="explore_w")
    with exp_col2:
        explore_h = st.slider(t("meetkunde.height_label"), min_value=1, max_value=15, value=4, step=1, key="explore_h")
    st.markdown(rectangle_svg(explore_w, explore_h, unit=UNIT), unsafe_allow_html=True)
    st.markdown(t("meetkunde.explore_result", perimeter=2 * (explore_w + explore_h), area=explore_w * explore_h, unit=UNIT))


def generate_problem():
    if level == 0:
        w, h = random.randint(2, 6), random.randint(2, 6)
        if random.choice([True, False]):
            text = t("meetkunde.q_perimeter", w=w, h=h, unit=UNIT)
            answer, unit_suffix = 2 * (w + h), UNIT
        else:
            text = t("meetkunde.q_area_rect", w=w, h=h, unit=UNIT)
            answer, unit_suffix = w * h, f"{UNIT}²"
        visual = ("rect", w, h)

    elif level == 1:
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
        # Pick the missing angle FIRST, then split what's left over the given
        # angles. The old version rejection-sampled and, if all 30 tries
        # failed, fell through with whatever the last (rejected) draw was -
        # for a triangle that can be a negative angle, e.g. "95 + 95 = 180,
        # what is the third angle?" with -10 as the expected answer.
        missing = random.randint(20, 100)
        remaining = total - missing
        given = []
        for i in range(n - 1):
            slots_left = n - 1 - i
            if slots_left == 1:
                given.append(remaining)
            else:
                # Leave at least 20 degrees for each angle still to come.
                lo = max(20, remaining - 140 * (slots_left - 1))
                hi = min(140, remaining - 20 * (slots_left - 1))
                pick = random.randint(lo, max(lo, hi))
                given.append(pick)
                remaining -= pick
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

question_card(problem["text"], emoji="📐")

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
            queue_celebration()
            queue_correct()
        else:
            reset_streak()
            queue_incorrect()
            st.session_state.meetkunde_feedback = (
                "error",
                f"{t('meetkunde.incorrect')} {t('common.correct_answer_was', answer=correct_answer_display)}",
            )
        if leveled_up:
            st.toast(t("common.level_up", level=get_level(GAME_KEY)), icon="🚀")
            queue_celebration()
        elif leveled_down:
            st.toast(t("common.level_down", level=get_level(GAME_KEY)), icon="💪")
        for badge_id, emoji in badges.check_new_badges():
            st.toast(t(f"badges.{badge_id}.name"), icon=emoji)
            queue_celebration()
        profiles.save_current_profile()
        st.rerun()

if next_clicked:
    generate_problem()
    st.rerun()

feedback = st.session_state.get("meetkunde_feedback")
if feedback:
    kind, message = feedback
    if kind == "success":
        feedback_banner("success", message, icon="🏛️")
    else:
        feedback_banner("error", message, tip=t("meetkunde.why_tip"), icon="🧱")
play_pending()
play_pending_celebration()

if st.session_state.get("streaks", 0) >= 3:
    st.info(t("common.streak_fire", streak=st.session_state.streaks))

st.caption(t("common.session_recorded"))
