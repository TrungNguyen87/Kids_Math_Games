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
from utils.ui import (
    level_control,
    page_header,
    sidebar_common,
)
from utils.sound import play_pending, queue_correct, queue_incorrect
from utils.visuals import fraction_visual_svg, percent_bar_svg

GAME_KEY = "procenten"

init_state()
init_language()

with st.sidebar:
    sidebar_common()

page_header("procenten.title", emoji="🏴‍☠️")
st.caption(t("procenten.tagline"))
st.markdown(t("procenten.intro"))

level_control(GAME_KEY, "perc_problem")
level = get_level(GAME_KEY)
points = 5 * (level + 1)

with st.expander(t("common.try_it_heading"), expanded=False):
    st.markdown(t("procenten.explore_intro"))
    explore_pct = st.slider(t("procenten.explore_pct_label"), min_value=0, max_value=100, value=50, step=1, key="explore_pct")
    divisor = math.gcd(explore_pct, 100) or 100
    simplified = f"{explore_pct // divisor}/{100 // divisor}"
    decimal = f"{explore_pct / 100:.2f}"
    st.markdown(percent_bar_svg(explore_pct, label=f"{explore_pct}% = {simplified} = {decimal}"), unsafe_allow_html=True)

VERY_EASY_EQUIVALENTS = [
    ("1/2", "50%", "0.50"),
    ("1/4", "25%", "0.25"),
]
EASY_EQUIVALENTS = [
    ("1/2", "50%", "0.50"),
    ("1/4", "25%", "0.25"),
    ("3/4", "75%", "0.75"),
    ("1/10", "10%", "0.10"),
    ("1/5", "20%", "0.20"),
]
HARD_EQUIVALENTS = EASY_EQUIVALENTS + [
    ("1/8", "12.5%", "0.125"),
    ("3/8", "37.5%", "0.375"),
    ("2/5", "40%", "0.40"),
    ("3/5", "60%", "0.60"),
    ("4/5", "80%", "0.80"),
]
PCT_CHOICES = [5, 10, 15, 20, 25, 50, 75]


def nice_base_for(pct):
    """Pick a base number so pct% of it is a whole number."""
    multiple = 100 // math.gcd(pct, 100)
    return multiple * random.randint(1, 10)


def generate_problem():
    if level in (0, 1, 4):
        if level == 0:
            equivalents = VERY_EASY_EQUIVALENTS
        elif level == 1:
            equivalents = EASY_EQUIVALENTS
        else:
            equivalents = HARD_EQUIVALENTS
        fraction, percentage, decimal = random.choice(equivalents)
        # Level 0 sticks to the simplest direction (recognizing a fraction
        # as a percentage) instead of also asking for decimal conversions.
        q_type = "frac_to_perc" if level == 0 else random.choice(["frac_to_perc", "perc_to_dec", "dec_to_frac"])
        all_fracs = [e[0] for e in equivalents]
        all_percs = [e[1] for e in equivalents]
        all_decs = [e[2] for e in equivalents]

        if q_type == "frac_to_perc":
            text = t("procenten.q_equivalent_frac_to_perc", fraction=fraction)
            answer = percentage
            options = all_percs
            fn, fd = (int(x) for x in fraction.split("/"))
            visual = ("frac", fn, fd)
        elif q_type == "perc_to_dec":
            text = t("procenten.q_equivalent_perc_to_dec", percentage=percentage)
            answer = decimal
            options = all_decs
            visual = ("pct", float(percentage.rstrip("%")), percentage)
        else:
            text = t("procenten.q_equivalent_dec_to_frac", decimal=decimal)
            answer = fraction
            options = all_fracs
            visual = ("pct", float(decimal) * 100, decimal)

        options = list(dict.fromkeys(options))
        random.shuffle(options)
        st.session_state.perc_problem = {
            "mode": "choice", "text": text, "answer": answer, "options": options, "visual": visual,
        }

    elif level == 2:
        pct = random.choice(PCT_CHOICES)
        base = nice_base_for(pct)
        text = t("procenten.q_percent_of", pct=pct, base=base)
        answer = base * pct // 100
        st.session_state.perc_problem = {
            "mode": "numeric",
            "text": text,
            "answer": answer,
            "answer_label": t("procenten.answer_label_number"),
            "visual": ("pct", pct, t("procenten.visual_pct_of", pct=pct, base=base)),
        }

    elif level == 3:
        pct = random.choice(PCT_CHOICES)
        price = nice_base_for(pct)
        discount = price * pct // 100
        if random.choice([True, False]):
            text = t("procenten.q_discount_new_price", price=price, pct=pct)
            answer = price - discount
        else:
            text = t("procenten.q_discount_amount", price=price, pct=pct)
            answer = discount
        st.session_state.perc_problem = {
            "mode": "numeric",
            "text": text,
            "answer": answer,
            "answer_label": t("procenten.answer_label_euro"),
            "visual": ("pct", pct, t("procenten.visual_discount", pct=pct)),
        }

    else:  # level 5: reverse percentage
        pct = random.choice(PCT_CHOICES)
        complement = 100 - pct
        multiple = 100 // math.gcd(complement, 100)
        original = multiple * random.randint(1, 10)
        new_price = original * complement // 100
        saved = original - new_price
        if random.choice([True, False]):
            text = t("procenten.q_reverse_price", pct=pct, new_price=new_price)
        else:
            text = t("procenten.q_reverse_saved", pct=pct, amount=saved)
        st.session_state.perc_problem = {
            "mode": "numeric",
            "text": text,
            "answer": original,
            "answer_label": t("procenten.answer_label_euro"),
            "visual": ("pct", complement, t("procenten.visual_pay_percent", complement=complement)),
        }

    st.session_state.perc_feedback = None


if "perc_problem" not in st.session_state or st.session_state.perc_problem is None:
    generate_problem()

problem = st.session_state.perc_problem

st.markdown(f"### 💎 {problem['text']}")

visual = problem.get("visual")
if visual and visual[0] == "frac":
    st.markdown(fraction_visual_svg(visual[1], visual[2]), unsafe_allow_html=True)
elif visual and visual[0] == "pct":
    st.markdown(percent_bar_svg(visual[1], label=visual[2]), unsafe_allow_html=True)

if problem["mode"] == "choice":
    user_choice = st.radio(t("common.choose_answer"), problem["options"], index=None, key="perc_radio")
else:
    user_choice = st.number_input(problem["answer_label"], step=1, value=None, key="perc_numeric")

col1, col2 = st.columns([1, 4])
with col1:
    check_clicked = st.button(t("procenten.check_button"), key="check_btn")
with col2:
    next_clicked = st.button(t("procenten.next_button"), key="next_btn")

if check_clicked:
    if user_choice is not None:
        is_correct = user_choice == problem["answer"]
        gamelog.log_attempt(
            GAME_KEY, t("game.procenten.name"), level, problem["text"], user_choice, problem["answer"], is_correct, points
        )
        leveled_up, leveled_down = register_attempt(GAME_KEY, is_correct)
        if is_correct:
            add_score(points)
            st.session_state.perc_feedback = ("success", t("procenten.correct", points=points))
            st.balloons()
            queue_correct()
        else:
            reset_streak()
            queue_incorrect()
            st.session_state.perc_feedback = (
                "error",
                f"{t('procenten.incorrect')} {t('common.correct_answer_was', answer=problem['answer'])}",
            )
        if leveled_up:
            st.toast(t("common.level_up", level=get_level(GAME_KEY)), icon="🚀")
        elif leveled_down:
            st.toast(t("common.level_down", level=get_level(GAME_KEY)), icon="💪")
        for badge_id, emoji in badges.check_new_badges():
            st.toast(t(f"badges.{badge_id}.name"), icon=emoji)
        profiles.save_current_profile()
        st.rerun()

if next_clicked:
    generate_problem()
    st.rerun()

feedback = st.session_state.get("perc_feedback")
if feedback:
    kind, message = feedback
    if kind == "success":
        st.success(message, icon="💰")
    else:
        st.error(message, icon="☠️")
        st.caption(t("procenten.why_tip"))
play_pending()

if st.session_state.get("streaks", 0) >= 3:
    st.info(t("common.streak_fire", streak=st.session_state.streaks))

st.caption(t("common.session_recorded"))
