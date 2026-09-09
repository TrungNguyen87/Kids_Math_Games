"""
Bliksemronde / Lightning Round - the app's first *speed* game.

Everything else in the app rewards being right. This one rewards being right
*quickly*: a 60-second round, four answer buttons, one tap per question, and
a running combo that multiplies the points for consecutive fast answers. It
is aimed at automating number facts a groep 6/7 child already understands but
still has to work out step by step.

Two Streamlit details make it work:

* The countdown lives in an ``st.fragment(run_every=1)``. Only that fragment
  reruns each second, so the clock ticks without rebuilding (and re-shuffling)
  the answer buttons underneath the child's finger.
* The answer buttons sit *outside* the fragment. A button inside an
  auto-rerunning fragment is a race: the rerun can land between the render
  and the click, and the tap is lost.
"""
import random
import time

import streamlit as st

from utils.anim import (
    play_pending_celebration,
    question_card,
    timer_bar,
)
from utils.gameflow import adapt_after_round, settle_answer
from utils.i18n import init_language, t
from utils.sound import play_pending
from utils.state import add_score, get_level, init_state
from utils.ui import level_control, page_header, sidebar_common

GAME_KEY = "bliksem"
ROUND_SECONDS = 60
# A run of fast correct answers multiplies the points, capped so a long
# lucky streak can't dwarf everything else the child does in the app.
COMBO_STEPS = [1, 1, 2, 2, 3, 3, 4]
FAST_ANSWER_SECONDS = 3.0

init_state()
init_language()

with st.sidebar:
    sidebar_common()

page_header("bliksem.title", emoji="⚡")
st.caption(t("bliksem.tagline"))
st.markdown(t("bliksem.intro"))

level_control(GAME_KEY, "bliksem_problem")
level = get_level(GAME_KEY)
base_points = 2 * (level + 1)


def _operands(level):
    """Number ranges per level. Kept deliberately smaller than the equivalent
    level in Tafel Monster: this is about instant recall, not about doing the
    hardest sum in the app against a clock."""
    if level == 0:
        return random.randint(1, 5), random.randint(1, 5), ["+"]
    if level == 1:
        return random.randint(2, 10), random.randint(2, 10), ["+", "-"]
    if level == 2:
        return random.randint(2, 10), random.randint(2, 10), ["+", "-", "x"]
    if level == 3:
        return random.randint(3, 12), random.randint(3, 12), ["+", "-", "x"]
    if level == 4:
        return random.randint(4, 15), random.randint(3, 12), ["x", ":", "+"]
    return random.randint(6, 20), random.randint(3, 15), ["x", ":", "-"]


def generate_problem():
    a, b, ops = _operands(level)
    op = random.choice(ops)
    if op == "+":
        answer = a + b
        text = f"{a} + {b}"
    elif op == "-":
        # Keep it non-negative: a speed round is the wrong place to also be
        # thinking about the minus side of zero (that is Getallen Universum).
        a, b = max(a, b), min(a, b)
        answer = a - b
        text = f"{a} − {b}"
    elif op == "x":
        answer = a * b
        text = f"{a} × {b}"
    else:
        product = a * b
        answer = a
        text = f"{product} : {b}"

    # Three distractors that are *plausibly* wrong - near misses and the
    # classic off-by-one-times errors - so the buttons test the fact rather
    # than being answerable by "pick the only sensible-looking number".
    candidates = {answer}
    pool = [answer + 1, answer - 1, answer + 2, answer - 2, answer + 10, answer - 10]
    if op == "x":
        pool += [a * (b + 1), a * (b - 1), (a + 1) * b, a + b]
    elif op == ":":
        pool += [answer + b, max(1, answer - b), a * b]
    random.shuffle(pool)
    for c in pool:
        if len(candidates) == 4:
            break
        if c >= 0 and c != answer:
            candidates.add(c)
    filler = 1
    while len(candidates) < 4:
        candidates.add(answer + filler * 3)
        filler += 1

    options = list(candidates)
    random.shuffle(options)

    st.session_state.bliksem_problem = {
        "text": text,
        "answer": answer,
        "options": options,
        "shown_at": time.time(),
    }


def start_round():
    st.session_state.bliksem_state = "running"
    st.session_state.bliksem_deadline = time.time() + ROUND_SECONDS
    st.session_state.bliksem_correct = 0
    st.session_state.bliksem_total = 0
    st.session_state.bliksem_combo = 0
    st.session_state.bliksem_round_points = 0
    st.session_state.bliksem_times = []
    st.session_state.bliksem_last = None
    generate_problem()


def finish_round():
    st.session_state.bliksem_state = "finished"
    correct = st.session_state.get("bliksem_correct", 0)
    total = st.session_state.get("bliksem_total", 0)
    # One level decision for the whole round - see gameflow.adapt_after_round
    # for why a round is a better signal here than a per-answer streak.
    adapt_after_round(GAME_KEY, correct, total)
    best = st.session_state.get("bliksem_best", 0)
    if correct > best:
        st.session_state.bliksem_best = correct
        st.session_state.bliksem_new_record = True


state = st.session_state.setdefault("bliksem_state", "idle")

# --------------------------------------------------------------------------
# Idle: explain the round and wait for the child to start it
# --------------------------------------------------------------------------
if state == "idle":
    st.markdown(t("bliksem.how_to", seconds=ROUND_SECONDS))
    best = st.session_state.get("bliksem_best", 0)
    if best:
        st.info(t("bliksem.your_record", best=best), icon="🏆")
    if st.button(t("bliksem.start_button"), key="bliksem_start", type="primary"):
        start_round()
        st.rerun()

# --------------------------------------------------------------------------
# Running: clock ticking, one question at a time
# --------------------------------------------------------------------------
elif state == "running":
    remaining = st.session_state.bliksem_deadline - time.time()
    if remaining <= 0:
        finish_round()
        st.rerun()

    @st.fragment(run_every=1)
    def countdown():
        """Ticks once a second on its own. When the clock runs out it asks
        for a *whole-app* rerun (scope="app"), because ending the round has
        to replace the question and buttons that live outside this fragment."""
        left = st.session_state.get("bliksem_deadline", 0) - time.time()
        if left <= 0:
            finish_round()
            st.rerun(scope="app")
        timer_bar(left, ROUND_SECONDS, t("bliksem.seconds_left", seconds=int(left) + 1))

    countdown()

    stat1, stat2, stat3 = st.columns(3)
    stat1.metric(t("bliksem.stat_correct"), st.session_state.bliksem_correct)
    stat2.metric(t("bliksem.stat_asked"), st.session_state.bliksem_total)
    combo = st.session_state.bliksem_combo
    stat3.metric(
        t("bliksem.stat_combo"),
        f"x{COMBO_STEPS[min(combo, len(COMBO_STEPS) - 1)]}",
        t("bliksem.combo_hint", n=combo) if combo else None,
        delta_color="off",
    )

    problem = st.session_state.bliksem_problem
    question_card(f"{problem['text']} = ?", emoji="⚡")

    last = st.session_state.get("bliksem_last")
    if last:
        ok, shown_answer, elapsed = last
        if ok:
            st.success(t("bliksem.quick_correct", seconds=f"{elapsed:.1f}"), icon="⚡")
        else:
            st.error(t("bliksem.quick_wrong", answer=shown_answer), icon="💨")

    cols = st.columns(4)
    for i, (col, option) in enumerate(zip(cols, problem["options"])):
        with col:
            if st.button(str(option), key=f"bliksem_opt_{i}", width="stretch"):
                elapsed = time.time() - problem["shown_at"]
                is_correct = option == problem["answer"]
                st.session_state.bliksem_total += 1
                st.session_state.bliksem_times.append(elapsed)

                if is_correct:
                    st.session_state.bliksem_correct += 1
                    st.session_state.bliksem_combo += 1
                    multiplier = COMBO_STEPS[
                        min(st.session_state.bliksem_combo, len(COMBO_STEPS) - 1)
                    ]
                    gained = base_points * multiplier
                    if elapsed <= FAST_ANSWER_SECONDS:
                        gained += base_points  # speed bonus
                    st.session_state.bliksem_round_points += gained
                    add_score(gained)
                else:
                    st.session_state.bliksem_combo = 0
                    gained = 0

                st.session_state.bliksem_last = (is_correct, problem["answer"], elapsed)
                settle_answer(
                    GAME_KEY,
                    "bliksem_feedback",
                    level,
                    f"{problem['text']} = ?",
                    option,
                    problem["answer"],
                    is_correct,
                    gained,
                    # The level is adapted once at the end of the round, and
                    # the points were already awarded above (they include the
                    # combo multiplier and the speed bonus).
                    adapt_level=False,
                    score=False,
                )
                generate_problem()
                st.rerun()

    if st.button(t("bliksem.stop_button"), key="bliksem_stop"):
        finish_round()
        st.rerun()

# --------------------------------------------------------------------------
# Finished: the scoreboard
# --------------------------------------------------------------------------
else:
    correct = st.session_state.get("bliksem_correct", 0)
    total = st.session_state.get("bliksem_total", 0)
    times = st.session_state.get("bliksem_times", [])
    avg = sum(times) / len(times) if times else 0.0
    accuracy = 100 * correct / total if total else 0.0

    st.markdown(f"### {t('bliksem.round_over')}")
    if st.session_state.pop("bliksem_new_record", False):
        st.balloons()
        st.success(t("bliksem.new_record", best=correct), icon="🏆")

    res1, res2, res3, res4 = st.columns(4)
    res1.metric(t("bliksem.stat_correct"), correct)
    res2.metric(t("bliksem.stat_asked"), total)
    res3.metric(t("bliksem.stat_accuracy"), f"{accuracy:.0f}%")
    res4.metric(t("bliksem.stat_avg_time"), f"{avg:.1f}s")

    st.markdown(t("bliksem.round_points", points=st.session_state.get("bliksem_round_points", 0)))

    if total == 0:
        st.info(t("bliksem.no_answers"), icon="🤔")
    elif accuracy >= 80:
        st.success(t("bliksem.praise_high"), icon="🌟")
    elif accuracy >= 50:
        st.info(t("bliksem.praise_mid"), icon="👍")
    else:
        st.info(t("bliksem.praise_low"), icon="💪")

    again, back = st.columns(2)
    with again:
        if st.button(t("bliksem.again_button"), key="bliksem_again", type="primary"):
            start_round()
            st.rerun()
    with back:
        if st.button(t("bliksem.menu_button"), key="bliksem_menu"):
            st.session_state.bliksem_state = "idle"
            st.rerun()

play_pending()
play_pending_celebration()

st.caption(t("common.session_recorded"))
