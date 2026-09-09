"""
Code Kraker / Code Breaker - Mastermind with digits.

A secret code is generated; after each guess the child is told how many
digits are *exactly right* (right digit, right place) and how many are the
*right digit in the wrong place*. Nothing else. Cracking it needs pure
elimination reasoning - no arithmetic at all - which makes it the game in
this app that most directly trains "what must be true given what I know".

Scoring rewards efficiency: the fewer guesses used, the more points.
A code that is never cracked scores nothing but still gets logged, so the
teacher dashboard shows the attempt.
"""
import random

import streamlit as st

from utils.anim import play_pending_celebration, question_card, queue_celebration
from utils.gameflow import settle_answer
from utils.i18n import init_language, t
from utils.sound import play_pending, queue_correct, queue_incorrect
from utils.state import add_score, get_level, init_state
from utils.ui import level_control, page_header, sidebar_common

GAME_KEY = "code"

# (code length, digits allowed 1..N, guesses allowed, repeats permitted)
LEVEL_RULES = {
    0: (2, 4, 8, False),
    1: (3, 4, 8, False),
    2: (3, 6, 8, False),
    3: (3, 6, 8, True),
    4: (4, 6, 9, True),
    5: (4, 8, 9, True),
}

init_state()
init_language()

with st.sidebar:
    sidebar_common()

page_header("code.title", emoji="🔐")
st.caption(t("code.tagline"))
st.markdown(t("code.intro"))

level_control(GAME_KEY, "code_secret")
level = get_level(GAME_KEY)
length, max_digit, max_guesses, allow_repeats = LEVEL_RULES[level]
base_points = 5 * (level + 1)


def new_code():
    digits = list(range(1, max_digit + 1))
    if allow_repeats:
        secret = [random.choice(digits) for _ in range(length)]
    else:
        secret = random.sample(digits, length)
    st.session_state.code_secret = secret
    st.session_state.code_guesses = []
    st.session_state.code_solved = False
    st.session_state.code_gave_up = False


def score_guess(secret, guess):
    """Mastermind scoring. ``exact`` = right digit in the right place;
    ``misplaced`` = right digit somewhere else. Digits already counted as
    exact are removed first, so a repeated digit is never counted twice -
    the classic bug in a naive implementation, and one a child *will* catch
    because it makes the clues contradict each other."""
    exact = sum(1 for s, g in zip(secret, guess) if s == g)
    left_secret = [s for s, g in zip(secret, guess) if s != g]
    left_guess = [g for s, g in zip(secret, guess) if s != g]
    misplaced = 0
    for g in left_guess:
        if g in left_secret:
            left_secret.remove(g)
            misplaced += 1
    return exact, misplaced


# A change of level changes the code's shape, so start a fresh code whenever
# the stored one no longer matches the current rules.
secret = st.session_state.get("code_secret")
if not secret or len(secret) != length or max(secret) > max_digit:
    new_code()
    secret = st.session_state.code_secret

guesses = st.session_state.code_guesses
solved = st.session_state.code_solved
gave_up = st.session_state.code_gave_up
guesses_left = max_guesses - len(guesses)

question_card(
    t("code.prompt", length=length, max_digit=max_digit, guesses=guesses_left),
    emoji="🔐",
)
st.caption(
    t("code.repeats_allowed") if allow_repeats else t("code.repeats_not_allowed")
)

# --- Guess history --------------------------------------------------------
if guesses:
    st.markdown(f"#### {t('code.history_heading')}")
    header = f"| # | {t('code.col_guess')} | 🎯 {t('code.col_exact')} | 🔄 {t('code.col_misplaced')} |"
    lines = [header, "|:---:|:---:|:---:|:---:|"]
    for i, (guess, exact, misplaced) in enumerate(guesses, start=1):
        lines.append(
            f"| {i} | **{' '.join(str(d) for d in guess)}** | {exact} | {misplaced} |"
        )
    st.markdown("\n".join(lines))

# --- Playing --------------------------------------------------------------
if not solved and not gave_up and guesses_left > 0:
    st.markdown(f"**{t('code.your_guess')}**")
    cols = st.columns(length)
    guess = []
    for i, col in enumerate(cols):
        with col:
            guess.append(
                st.selectbox(
                    f"{t('code.position')} {i + 1}",
                    list(range(1, max_digit + 1)),
                    key=f"code_pos_{level}_{i}",
                )
            )

    b1, b2 = st.columns([1, 3])
    with b1:
        submit = st.button(t("code.check_button"), key="check_btn", type="primary")
    with b2:
        give_up = st.button(t("code.give_up_button"), key="code_give_up")

    if submit:
        duplicate_problem = not allow_repeats and len(set(guess)) != len(guess)
        if duplicate_problem:
            # Not a wrong answer, just an impossible one under this level's
            # rules - so it is neither logged nor counted against the budget.
            st.warning(t("code.no_repeats_warning"), icon="⚠️")
        else:
            exact, misplaced = score_guess(secret, guess)
            st.session_state.code_guesses.append((guess, exact, misplaced))
            used = len(st.session_state.code_guesses)

            if exact == length:
                st.session_state.code_solved = True
                # Efficiency bonus: cracking it on guess 1 of 8 pays roughly
                # double what cracking it on the last guess does.
                bonus = max(0, max_guesses - used)
                earned = base_points * 2 + base_points * bonus // 2
                add_score(earned)
                queue_correct()
                queue_celebration()
                settle_answer(
                    GAME_KEY,
                    "code_feedback",
                    level,
                    t("code.log_question", length=length, max_digit=max_digit),
                    " ".join(str(d) for d in guess),
                    " ".join(str(d) for d in secret),
                    True,
                    earned,
                    correct_message=t("code.cracked", guesses=used, points=earned),
                    score=False,  # already added above, with the efficiency bonus
                )
            elif used >= max_guesses:
                queue_incorrect()
                settle_answer(
                    GAME_KEY,
                    "code_feedback",
                    level,
                    t("code.log_question", length=length, max_digit=max_digit),
                    " ".join(str(d) for d in guess),
                    " ".join(str(d) for d in secret),
                    False,
                    0,
                    incorrect_message=t(
                        "code.out_of_guesses", code=" ".join(str(d) for d in secret)
                    ),
                )
            st.rerun()

    if give_up:
        st.session_state.code_gave_up = True
        st.rerun()

# --- Round over -----------------------------------------------------------
else:
    if solved:
        used = len(guesses)
        st.balloons()
        st.success(t("code.cracked_banner", code=" ".join(str(d) for d in secret), guesses=used), icon="🔓")
    elif gave_up:
        st.info(t("code.revealed", code=" ".join(str(d) for d in secret)), icon="🙈")
    else:
        st.error(t("code.out_of_guesses", code=" ".join(str(d) for d in secret)), icon="⏳")

    if st.button(t("code.new_code_button"), key="code_new", type="primary"):
        new_code()
        st.rerun()

with st.expander(t("code.how_to_heading")):
    st.markdown(t("code.how_to_body"))

play_pending()
play_pending_celebration()

st.caption(t("common.session_recorded"))
