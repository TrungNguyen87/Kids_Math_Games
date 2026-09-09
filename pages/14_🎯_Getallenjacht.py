"""
Getallenjacht / Number Hunt - the second speed game, and the one that
trains number *properties* rather than number facts.

A rule appears ("tap every multiple of 6") and a grid of numbers fills the
screen. Tap the ones that match before the clock runs out. A hit turns
green, a miss turns red and costs a life. Clearing the whole grid before
time is up wins a bonus.

Where Bliksemronde asks "what is 7 x 8?", this asks "which of these twenty
numbers are in the 7-times table?" - the same knowledge, approached from the
recognition side, which is what makes divisibility and factors click.

Same fragment/button split as Bliksemronde: the clock auto-reruns on its
own, the tappable grid does not.
"""
import random
import time

import streamlit as st

from utils.anim import feedback_banner, play_pending_celebration, queue_celebration, timer_bar
from utils.gameflow import adapt_after_round, settle_answer
from utils.i18n import init_language, t
from utils.sound import play_pending, queue_correct, queue_incorrect
from utils.state import add_score, get_level, init_state
from utils.ui import level_control, page_header, sidebar_common

GAME_KEY = "jacht"
GRID_COLS = 5
GRID_ROWS = 4
LIVES = 3

# Seconds on the clock per level - it gets *shorter* as the rules get harder.
LEVEL_SECONDS = {0: 75, 1: 70, 2: 60, 3: 55, 4: 50, 5: 45}

init_state()
init_language()

with st.sidebar:
    sidebar_common()

page_header("jacht.title", emoji="🎯")
st.caption(t("jacht.tagline"))
st.markdown(t("jacht.intro"))

level_control(GAME_KEY, "jacht_state")
level = get_level(GAME_KEY)
round_seconds = LEVEL_SECONDS[level]
base_points = 3 * (level + 1)

PRIMES = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97}


def _rules_for_level(level):
    """Which hunt rules this level can draw from. Each entry is
    (rule_id, label_kwargs, predicate, number_range)."""
    if level == 0:
        return [
            ("even", {}, lambda n: n % 2 == 0, (1, 40)),
            ("odd", {}, lambda n: n % 2 == 1, (1, 40)),
        ]
    if level == 1:
        table = random.choice([2, 5, 10])
        return [
            ("multiple", {"n": table}, lambda n, k=table: n % k == 0, (1, 60)),
            ("greater", {"n": 25}, lambda n: n > 25, (5, 50)),
        ]
    if level == 2:
        table = random.choice([3, 4, 6])
        return [
            ("multiple", {"n": table}, lambda n, k=table: n % k == 0, (1, 70)),
            ("between", {"lo": 20, "hi": 40}, lambda n: 20 <= n <= 40, (5, 60)),
        ]
    if level == 3:
        table = random.choice([6, 7, 8, 9])
        return [
            ("multiple", {"n": table}, lambda n, k=table: n % k == 0, (1, 99)),
            ("digitsum", {"n": 9}, lambda n: sum(int(d) for d in str(n)) == 9, (10, 99)),
        ]
    if level == 4:
        return [
            ("prime", {}, lambda n: n in PRIMES, (2, 60)),
            ("square", {}, lambda n: int(n**0.5) ** 2 == n, (1, 100)),
            ("multiple", {"n": 12}, lambda n: n % 12 == 0, (1, 120)),
        ]
    return [
        ("prime", {}, lambda n: n in PRIMES, (2, 99)),
        ("factor_of", {"n": 72}, lambda n: 72 % n == 0, (1, 80)),
        ("multiple_both", {"a": 3, "b": 4}, lambda n: n % 12 == 0, (1, 120)),
    ]


def start_round():
    rule_id, label_kwargs, predicate, (lo, hi) = random.choice(_rules_for_level(level))

    # Build the grid so it always has a workable number of targets: too few
    # and there is nothing to hunt, too many and tapping everything wins.
    cells = GRID_COLS * GRID_ROWS
    target_count = random.randint(max(3, cells // 5), max(4, cells // 3))
    pool_hits = [n for n in range(lo, hi + 1) if predicate(n)]
    pool_misses = [n for n in range(lo, hi + 1) if not predicate(n)]
    target_count = min(target_count, len(pool_hits))

    hits = random.sample(pool_hits, target_count)
    misses = random.sample(pool_misses, min(cells - target_count, len(pool_misses)))
    numbers = hits + misses
    # Top up with anything left if the pools were thin (a very tight rule at
    # a small range), keeping the grid rectangular either way.
    spare = [n for n in range(lo, hi + 1) if n not in numbers]
    while len(numbers) < cells and spare:
        numbers.append(spare.pop(random.randrange(len(spare))))
    random.shuffle(numbers)

    st.session_state.jacht_state = "running"
    st.session_state.jacht_rule_id = rule_id
    st.session_state.jacht_rule_label = t(f"jacht.rule_{rule_id}", **label_kwargs)
    st.session_state.jacht_numbers = numbers
    st.session_state.jacht_targets = {n for n in numbers if predicate(n)}
    st.session_state.jacht_found = set()
    st.session_state.jacht_wrong = set()
    st.session_state.jacht_lives = LIVES
    st.session_state.jacht_deadline = time.time() + round_seconds
    st.session_state.jacht_round_points = 0
    st.session_state.jacht_cleared = False


def finish_round(cleared=False):
    st.session_state.jacht_state = "finished"
    st.session_state.jacht_cleared = cleared
    found = len(st.session_state.get("jacht_found", set()))
    targets = len(st.session_state.get("jacht_targets", set()))
    wrong = len(st.session_state.get("jacht_wrong", set()))
    if cleared:
        bonus = base_points * 3
        add_score(bonus)
        st.session_state.jacht_round_points += bonus
        queue_celebration()
    # One question in the log per round, holding the whole result - a
    # per-tap log entry would bury the arithmetic games in the dashboard.
    settle_answer(
        GAME_KEY,
        "jacht_feedback",
        level,
        t("jacht.log_question", rule=st.session_state.get("jacht_rule_label", "")),
        t("jacht.log_answer", found=found, wrong=wrong),
        t("jacht.log_correct", targets=targets),
        cleared,
        st.session_state.jacht_round_points,
        correct_message=t("jacht.round_cleared", points=st.session_state.jacht_round_points),
        incorrect_message=t("jacht.round_ended", found=found, targets=targets),
        adapt_level=False,
        score=False,
    )
    adapt_after_round(GAME_KEY, found, max(1, targets))


state = st.session_state.setdefault("jacht_state", "idle")

# --------------------------------------------------------------------------
if state == "idle":
    st.markdown(t("jacht.how_to", seconds=round_seconds, lives=LIVES))
    if st.button(t("jacht.start_button"), key="jacht_start", type="primary"):
        start_round()
        st.rerun()

# --------------------------------------------------------------------------
elif state == "running":
    if time.time() >= st.session_state.jacht_deadline:
        finish_round(cleared=False)
        st.rerun()

    @st.fragment(run_every=1)
    def countdown():
        left = st.session_state.get("jacht_deadline", 0) - time.time()
        if left <= 0:
            finish_round(cleared=False)
            st.rerun(scope="app")
        timer_bar(left, round_seconds, t("jacht.seconds_left", seconds=int(left) + 1))

    countdown()

    found = st.session_state.jacht_found
    targets = st.session_state.jacht_targets
    lives = st.session_state.jacht_lives

    st.markdown(f"### 🎯 {st.session_state.jacht_rule_label}")
    info1, info2, info3 = st.columns(3)
    info1.metric(t("jacht.stat_found"), f"{len(found)}/{len(targets)}")
    info2.metric(t("jacht.stat_lives"), "❤️" * lives if lives else "💔")
    info3.metric(t("jacht.stat_points"), st.session_state.jacht_round_points)

    numbers = st.session_state.jacht_numbers
    for row in range(GRID_ROWS):
        row_numbers = numbers[row * GRID_COLS : (row + 1) * GRID_COLS]
        if not row_numbers:
            break
        cols = st.columns(GRID_COLS)
        for col, number in zip(cols, row_numbers):
            with col:
                if number in found:
                    st.markdown(
                        f'<div class="kmg-hit" style="text-align:center;padding:14px;border-radius:12px;'
                        f'background:#c8e6c9;border:3px solid #4caf50;font-size:1.4rem;font-weight:bold">'
                        f"✅ {number}</div>",
                        unsafe_allow_html=True,
                    )
                elif number in st.session_state.jacht_wrong:
                    st.markdown(
                        f'<div class="kmg-miss" style="text-align:center;padding:14px;border-radius:12px;'
                        f'background:#ffcdd2;border:3px solid #ef5350;font-size:1.4rem;font-weight:bold">'
                        f"❌ {number}</div>",
                        unsafe_allow_html=True,
                    )
                elif st.button(str(number), key=f"jacht_{number}", width="stretch"):
                    if number in targets:
                        st.session_state.jacht_found.add(number)
                        gained = base_points
                        add_score(gained)
                        st.session_state.jacht_round_points += gained
                        queue_correct()
                        if st.session_state.jacht_found == targets:
                            finish_round(cleared=True)
                    else:
                        st.session_state.jacht_wrong.add(number)
                        st.session_state.jacht_lives -= 1
                        queue_incorrect()
                        if st.session_state.jacht_lives <= 0:
                            finish_round(cleared=False)
                    st.rerun()

    if st.button(t("jacht.stop_button"), key="jacht_stop"):
        finish_round(cleared=False)
        st.rerun()

# --------------------------------------------------------------------------
else:
    found = st.session_state.get("jacht_found", set())
    targets = st.session_state.get("jacht_targets", set())
    wrong = st.session_state.get("jacht_wrong", set())
    missed = sorted(targets - found)

    st.markdown(f"### {t('jacht.round_over')}")
    if st.session_state.get("jacht_cleared"):
        queue_celebration()
        feedback_banner("success", t("jacht.cleared_banner", points=st.session_state.get("jacht_round_points", 0)), icon="🏆")
    elif st.session_state.get("jacht_lives", 1) <= 0:
        feedback_banner("error", t("jacht.out_of_lives"), icon="💔")
    else:
        st.info(t("jacht.time_up"), icon="⏰")

    res1, res2, res3 = st.columns(3)
    res1.metric(t("jacht.stat_found"), f"{len(found)}/{len(targets)}")
    res2.metric(t("jacht.stat_wrong"), len(wrong))
    res3.metric(t("jacht.stat_points"), st.session_state.get("jacht_round_points", 0))

    st.markdown(f"**{t('jacht.rule_was')}** {st.session_state.get('jacht_rule_label', '')}")
    if missed:
        st.markdown(t("jacht.you_missed", numbers=", ".join(str(n) for n in missed)))
    if wrong:
        st.markdown(t("jacht.you_mistapped", numbers=", ".join(str(n) for n in sorted(wrong))))

    again, back = st.columns(2)
    with again:
        if st.button(t("jacht.again_button"), key="jacht_again", type="primary"):
            start_round()
            st.rerun()
    with back:
        if st.button(t("jacht.menu_button"), key="jacht_menu"):
            st.session_state.jacht_state = "idle"
            st.rerun()

play_pending()
play_pending_celebration()

st.caption(t("common.session_recorded"))
