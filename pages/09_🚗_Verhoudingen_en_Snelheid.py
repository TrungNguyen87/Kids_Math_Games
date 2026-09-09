import math
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
from utils.visuals import ratio_bar_svg, speed_diagram_svg

GAME_KEY = "verhoudingen"

init_state()
init_language()

with st.sidebar:
    sidebar_common()

page_header("verhoudingen.title", emoji="🚗")
st.caption(t("verhoudingen.tagline"))
st.markdown(t("verhoudingen.intro"))

level_control(GAME_KEY, "verhoudingen_problem")
level = get_level(GAME_KEY)
points = 5 * (level + 1)


def format_euro(value):
    text = f"{value:.2f}"
    if st.session_state.get("language", "nl") == "nl":
        text = text.replace(".", ",")
    return text


def generate_problem():
    answer_kind = "int"
    visual = None

    if level == 0:
        p, q = random.randint(1, 3), random.randint(1, 3)
        while math.gcd(p, q) != 1:
            p, q = random.randint(1, 3), random.randint(1, 3)
        factor = random.randint(2, 3)
        a, b = p * factor, q * factor
        text = t("verhoudingen.q_simplify", a=a, b=b, q=q)
        answer = p
        answer_label = t("verhoudingen.answer_label_number")
        visual = ratio_bar_svg([a, b], labels=[str(a), str(b)])

    elif level == 1:
        p, q = random.randint(2, 6), random.randint(2, 6)
        while math.gcd(p, q) != 1:
            p, q = random.randint(2, 6), random.randint(2, 6)
        factor = random.randint(2, 6)
        a, b = p * factor, q * factor
        text = t("verhoudingen.q_simplify", a=a, b=b, q=q)
        answer = p
        answer_label = t("verhoudingen.answer_label_number")
        visual = ratio_bar_svg([a, b], labels=[str(a), str(b)])

    elif level == 2:
        scale = random.choice([100, 200, 500, 1000, 2000])
        map_cm = random.randint(2, 20)
        text = t("verhoudingen.q_scale", scale=scale, map_cm=map_cm)
        answer = map_cm * scale // 100
        answer_label = t("verhoudingen.answer_label_meter")

    elif level == 3:
        speed = random.choice(range(20, 121, 10))
        time = random.randint(1, 6)
        distance = speed * time
        subtype = random.choice(["find_speed", "find_distance", "find_time"])
        if subtype == "find_speed":
            text = t("verhoudingen.q_speed_find_speed", distance=distance, time=time)
            answer = speed
            answer_label = t("verhoudingen.answer_label_kmh")
            visual = speed_diagram_svg(distance, "km", time, t("units.hour"))
        elif subtype == "find_distance":
            text = t("verhoudingen.q_speed_find_distance", time=time, speed=speed)
            answer = distance
            answer_label = t("verhoudingen.answer_label_km")
            visual = speed_diagram_svg(speed, t("units.kmh"), time, t("units.hour"))
        else:
            text = t("verhoudingen.q_speed_find_time", distance=distance, speed=speed)
            answer = time
            answer_label = t("verhoudingen.answer_label_hour")
            visual = speed_diagram_svg(distance, "km", speed, t("units.kmh"))

    elif level == 4:
        answer_kind = "euro"
        price_per_unit = random.choice([0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0])
        qty = random.randint(3, 12)
        total_price = round(price_per_unit * qty, 2)
        text = t("verhoudingen.q_unit_price", qty=qty, total_price=format_euro(total_price))
        answer = price_per_unit
        answer_label = t("verhoudingen.answer_label_euro")
        visual = ratio_bar_svg([1] * qty, labels=["?"] * qty)

    else:
        speed = random.choice(range(20, 121, 4))
        time = random.randint(1, 4)
        # 15/30/45 only: an "extra" of 0 produced questions that read
        # "... in 3 hours and 0 minutes", which is both clumsy and not the
        # multi-step problem this level is meant to be asking.
        extra_min = random.choice([15, 30, 45])
        distance = speed * (time * 60 + extra_min) // 60
        text = t("verhoudingen.q_multi_step", speed=speed, time=time, extra_min=extra_min)
        answer = distance
        answer_label = t("verhoudingen.answer_label_km")
        visual = speed_diagram_svg(f"{speed} {t('units.kmh')}", "", f"{time}{t('units.hour_abbr')} {extra_min}{t('units.min_abbr')}", "")

    st.session_state.verhoudingen_problem = {
        "text": text,
        "answer": answer,
        "answer_kind": answer_kind,
        "answer_label": answer_label,
        "visual": visual,
    }
    st.session_state.verhoudingen_feedback = None


if "verhoudingen_problem" not in st.session_state or st.session_state.verhoudingen_problem is None:
    generate_problem()

problem = st.session_state.verhoudingen_problem

question_card(problem["text"], emoji="🚗")

if problem["visual"]:
    st.markdown(problem["visual"], unsafe_allow_html=True)

if problem["answer_kind"] == "euro":
    user_val = st.number_input(problem["answer_label"], step=0.01, value=None, format="%.2f", key="verhoudingen_input_euro")
else:
    user_val = st.number_input(problem["answer_label"], step=1, value=None, key="verhoudingen_input_int")

col1, col2 = st.columns([1, 4])
with col1:
    check_clicked = st.button(t("verhoudingen.check_button"), key="check_btn")
with col2:
    next_clicked = st.button(t("verhoudingen.next_button"), key="next_btn")

if check_clicked:
    if user_val is not None:
        if problem["answer_kind"] == "euro":
            is_correct = abs(user_val - problem["answer"]) < 0.005
            correct_answer_display = f"€{format_euro(problem['answer'])}"
        else:
            is_correct = user_val == problem["answer"]
            correct_answer_display = problem["answer"]
        gamelog.log_attempt(
            GAME_KEY, t("game.verhoudingen.name"), level, problem["text"], user_val, correct_answer_display, is_correct, points
        )
        leveled_up, leveled_down = register_attempt(GAME_KEY, is_correct)
        if is_correct:
            add_score(points)
            st.session_state.verhoudingen_feedback = ("success", t("verhoudingen.correct", points=points))
            queue_celebration()
            queue_correct()
        else:
            reset_streak()
            queue_incorrect()
            st.session_state.verhoudingen_feedback = (
                "error",
                f"{t('verhoudingen.incorrect')} {t('common.correct_answer_was', answer=correct_answer_display)}",
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

feedback = st.session_state.get("verhoudingen_feedback")
if feedback:
    kind, message = feedback
    if kind == "success":
        feedback_banner("success", message, icon="🏁")
    else:
        feedback_banner("error", message, tip=t("verhoudingen.why_tip"), icon="🚧")
play_pending()
play_pending_celebration()

if st.session_state.get("streaks", 0) >= 3:
    st.info(t("common.streak_fire", streak=st.session_state.streaks))

st.caption(t("common.session_recorded"))
