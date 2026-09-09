"""
The "what happens after an answer" sequence, in one place.

Every game page used to repeat the same ~40 lines: log the attempt, update
the adaptive level, add score or reset the streak, stash a feedback message,
toast a level change, check badges, save the profile, rerun. The four games
added in round 5 call settle_answer() instead, which keeps them focused on
the part that is actually different - generating and grading their own kind
of puzzle.

The original eight games still carry their inline version; they are left
alone on purpose, so this round's changes stay reviewable.
"""
import streamlit as st

from utils import badges, gamelog, profiles
from utils.anim import queue_celebration
from utils.i18n import t
from utils.sound import queue_correct, queue_incorrect
from utils.state import add_score, get_level, register_attempt, reset_streak


def settle_answer(
    game_key,
    feedback_state_key,
    level,
    question_text,
    student_answer,
    correct_answer,
    is_correct,
    points,
    correct_message=None,
    incorrect_message=None,
    adapt_level=True,
    score=True,
):
    """Record and react to one answered question.

    ``adapt_level=False`` is for the timed games: inside a 60-second round a
    child answers a dozen questions, and letting the difficulty climb three
    times mid-round would change the game under their feet. Those games call
    settle_answer per question for logging and scoring, and adapt the level
    once, at the end of the round.

    ``score=False`` is for games that award their own points (a speed bonus,
    or a deduction game paying out only when the code is finally cracked).

    Returns (leveled_up, leveled_down).
    """
    gamelog.log_attempt(
        game_key,
        t(f"game.{game_key}.name"),
        level,
        question_text,
        student_answer,
        correct_answer,
        is_correct,
        points,
    )

    leveled_up = leveled_down = False
    if adapt_level:
        leveled_up, leveled_down = register_attempt(game_key, is_correct)
    else:
        # Still count the question and mark the game as tried, so the
        # session stats and the "explorer" badge stay honest - just without
        # moving the difficulty.
        st.session_state.questions_answered += 1
        st.session_state.setdefault("games_tried", set()).add(game_key)
        if is_correct:
            st.session_state.correct_answered += 1

    if is_correct:
        if score:
            add_score(points)
        st.session_state[feedback_state_key] = (
            "success",
            correct_message if correct_message is not None else t("common.correct_generic"),
        )
        queue_correct()
    else:
        reset_streak()
        queue_incorrect()
        st.session_state[feedback_state_key] = (
            "error",
            incorrect_message
            if incorrect_message is not None
            else f"{t('common.incorrect_generic')} {t('common.correct_answer_was', answer=correct_answer)}",
        )

    if leveled_up:
        st.toast(t("common.level_up", level=get_level(game_key)), icon="🚀")
        queue_celebration()
    elif leveled_down:
        st.toast(t("common.level_down", level=get_level(game_key)), icon="💪")

    for badge_id, emoji in badges.check_new_badges():
        st.toast(t(f"badges.{badge_id}.name"), icon=emoji)
        queue_celebration()

    profiles.save_current_profile()
    return leveled_up, leveled_down


def adapt_after_round(game_key, correct, total, up_ratio=0.8, down_ratio=0.4):
    """Level a timed game up or down once, based on how the whole round went
    rather than on a streak of individual answers.

    A round is the natural unit here: 9 of 10 right means "that was too easy"
    far more reliably than three quick correct answers in a row does, since
    in a speed game those three can just be three easy draws.

    Returns (leveled_up, leveled_down).
    """
    from utils.state import MAX_LEVEL, MIN_LEVEL, set_level

    if total <= 0:
        return False, False
    ratio = correct / total
    current = get_level(game_key)
    if ratio >= up_ratio and current < MAX_LEVEL:
        set_level(game_key, current + 1)
        st.toast(t("common.level_up", level=get_level(game_key)), icon="🚀")
        queue_celebration()
        return True, False
    if ratio <= down_ratio and current > MIN_LEVEL:
        set_level(game_key, current - 1)
        st.toast(t("common.level_down", level=get_level(game_key)), icon="💪")
        return False, True
    return False, False


def show_feedback(feedback_state_key, tip_key=None, ok_icon="🎉", bad_icon="💪"):
    """Render whatever settle_answer() stashed, as an animated banner."""
    from utils.anim import feedback_banner

    feedback = st.session_state.get(feedback_state_key)
    if not feedback:
        return
    kind, message = feedback
    if kind == "success":
        feedback_banner("success", message, icon=ok_icon)
    else:
        feedback_banner(
            "error", message, tip=t(tip_key) if tip_key else None, icon=bad_icon
        )
