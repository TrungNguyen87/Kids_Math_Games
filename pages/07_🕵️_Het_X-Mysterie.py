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
from utils.visuals import balance_scale_svg

GAME_KEY = "algebra"

init_state()
init_language()

with st.sidebar:
    sidebar_common()

page_header("algebra.title", emoji="🕵️")
st.caption(t("algebra.tagline"))
st.markdown(t("algebra.intro"))

level_control(GAME_KEY, "algebra_problem")
level = get_level(GAME_KEY)
points = 5 * (level + 1)


def generate_problem():
    two_var = False

    if level == 0:
        # Warm-up: addition only, small numbers - no subtraction yet.
        a = random.randint(1, 5)
        x = random.randint(1, 10)
        b = a + x
        text = t("algebra.q_add", a=a, b=b)
        left = f"x + {a}"
        answer = {"x": x}
        visual = [(left, str(b))]

    elif level == 1:
        a = random.randint(1, 15)
        if random.choice([True, False]):
            x = random.randint(1, 20)
            b = a + x
            text = t("algebra.q_add", a=a, b=b)
            left = f"x + {a}"
        else:
            x = random.randint(a + 1, a + 20)
            b = x - a
            text = t("algebra.q_sub", a=a, b=b)
            left = f"x - {a}"
        answer = {"x": x}
        visual = [(left, str(b))]

    elif level == 2:
        a = random.randint(2, 9)
        if random.choice([True, False]):
            x = random.randint(2, 12)
            b = a * x
            text = t("algebra.q_mul", a=a, b=b)
            left = f"{a} × x"
        else:
            q = random.randint(2, 12)
            x = a * q
            b = q
            text = t("algebra.q_div", a=a, q=q)
            left = f"x : {a}"
        answer = {"x": x}
        visual = [(left, str(b))]

    elif level == 3:
        a = random.randint(2, 6)
        x = random.randint(1, 10)
        ax = a * x
        if random.choice([True, False]):
            b = random.randint(1, 15)
            c = ax + b
            text = t("algebra.q_two_step_add", a=a, b=b, c=c)
            left = f"{a}x + {b}"
        else:
            b = random.randint(1, max(1, ax))
            c = ax - b
            text = t("algebra.q_two_step_sub", a=a, b=b, c=c)
            left = f"{a}x - {b}"
        answer = {"x": x}
        visual = [(left, str(c))]

    elif level == 4:
        a = random.randint(2, 8)
        x = random.choice([v for v in range(-10, 11) if v != 0])
        b = random.randint(1, 25)
        ax = a * x
        if random.choice([True, False]):
            c = ax + b
            text = t("algebra.q_two_step_add", a=a, b=b, c=c)
            left = f"{a}x + {b}"
        else:
            c = ax - b
            text = t("algebra.q_two_step_sub", a=a, b=b, c=c)
            left = f"{a}x - {b}"
        answer = {"x": x}
        visual = [(left, str(c))]

    else:
        two_var = True
        x = random.randint(2, 20)
        y = random.randint(1, x - 1)
        s = x + y
        d = x - y
        text = t("algebra.q_system", s=s, d=d)
        answer = {"x": x, "y": y}
        visual = [("x + y", str(s)), ("x - y", str(d))]

    st.session_state.algebra_problem = {
        "text": text,
        "answer": answer,
        "visual": visual,
        "two_var": two_var,
    }
    st.session_state.algebra_feedback = None


if "algebra_problem" not in st.session_state or st.session_state.algebra_problem is None:
    generate_problem()

problem = st.session_state.algebra_problem

question_card(problem["text"], emoji="🕵️")

visual_cols = st.columns(len(problem["visual"]))
for vcol, (left_text, right_text) in zip(visual_cols, problem["visual"]):
    with vcol:
        st.markdown(balance_scale_svg(left_text, right_text), unsafe_allow_html=True)

if problem["two_var"]:
    col_x, col_y = st.columns(2)
    with col_x:
        user_x = st.number_input(t("algebra.x_label"), step=1, value=None, key="algebra_x")
    with col_y:
        user_y = st.number_input(t("algebra.y_label"), step=1, value=None, key="algebra_y")
else:
    user_x = st.number_input(t("algebra.x_label"), step=1, value=None, key="algebra_x")
    user_y = None

col1, col2 = st.columns([1, 4])
with col1:
    check_clicked = st.button(t("algebra.check_button"), key="check_btn")
with col2:
    next_clicked = st.button(t("algebra.next_button"), key="next_btn")

if check_clicked:
    answered = user_x is not None and (not problem["two_var"] or user_y is not None)
    if answered:
        if problem["two_var"]:
            is_correct = user_x == problem["answer"]["x"] and user_y == problem["answer"]["y"]
            student_answer = f"x={user_x}, y={user_y}"
            correct_answer = f"x={problem['answer']['x']}, y={problem['answer']['y']}"
        else:
            is_correct = user_x == problem["answer"]["x"]
            student_answer = f"x={user_x}"
            correct_answer = f"x={problem['answer']['x']}"

        gamelog.log_attempt(
            GAME_KEY, t("game.algebra.name"), level, problem["text"], student_answer, correct_answer, is_correct, points
        )
        leveled_up, leveled_down = register_attempt(GAME_KEY, is_correct)
        if is_correct:
            add_score(points)
            st.session_state.algebra_feedback = ("success", t("algebra.correct", points=points))
            st.balloons()
            queue_correct()
        else:
            reset_streak()
            queue_incorrect()
            st.session_state.algebra_feedback = (
                "error",
                f"{t('algebra.incorrect')} {t('common.correct_answer_was', answer=correct_answer)}",
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

feedback = st.session_state.get("algebra_feedback")
if feedback:
    kind, message = feedback
    if kind == "success":
        feedback_banner("success", message, icon="🕵️")
    else:
        feedback_banner("error", message, tip=t("algebra.why_tip"), icon="🧩")
play_pending()
play_pending_celebration()

if st.session_state.get("streaks", 0) >= 3:
    st.info(t("common.streak_fire", streak=st.session_state.streaks))

st.caption(t("common.session_recorded"))
