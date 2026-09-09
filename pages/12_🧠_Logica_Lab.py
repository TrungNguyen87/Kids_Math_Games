"""
Logica Lab / Logic Lab - reasoning rather than calculating.

Everything else in the app asks "can you work this out?". This one asks
"can you work out *what the rule is*?" - number and shape sequences,
odd-one-out, if/then statements, a small who-has-what deduction grid, and
balance puzzles where symbols stand in for values.

The arithmetic stays deliberately easy (groep 6/7 can all do it); the
difficulty is entirely in spotting the pattern, which is the point.
"""
import random

import streamlit as st

from utils.anim import play_pending_celebration, question_card
from utils.gameflow import settle_answer, show_feedback
from utils.i18n import init_language, t
from utils.sound import play_pending
from utils.state import get_level, init_state
from utils.ui import level_control, page_header, sidebar_common
from utils.visuals import number_line_svg, ratio_bar_svg

GAME_KEY = "logica"

init_state()
init_language()

with st.sidebar:
    sidebar_common()

page_header("logica.title", emoji="🧠")
st.caption(t("logica.tagline"))
st.markdown(t("logica.intro"))

level_control(GAME_KEY, "logica_problem")
level = get_level(GAME_KEY)
points = 5 * (level + 1)

SHAPES = ["🔺", "🟦", "🟢", "⭐", "🟣", "🟠"]
NAME_KEYS = ["logica.name_a", "logica.name_b", "logica.name_c", "logica.name_d"]
THING_KEYS = ["logica.thing_a", "logica.thing_b", "logica.thing_c", "logica.thing_d"]


def _sequence_problem(kinds):
    """A number sequence with a hidden rule; the child gives the next term.
    `kinds` limits which rules can appear, which is how the levels differ."""
    kind = random.choice(kinds)
    if kind == "add":
        start, step = random.randint(1, 12), random.randint(2, 9)
        seq = [start + i * step for i in range(5)]
        rule = t("logica.rule_add", step=step)
    elif kind == "sub":
        step = random.randint(2, 9)
        start = step * random.randint(6, 12)
        seq = [start - i * step for i in range(5)]
        rule = t("logica.rule_sub", step=step)
    elif kind == "mul":
        start, factor = random.randint(1, 4), random.choice([2, 3])
        seq = [start * factor**i for i in range(5)]
        rule = t("logica.rule_mul", factor=factor)
    elif kind == "alternate":
        # Two interleaved rules: +a on the odd positions, +b on the even
        # ones. The classic "why doesn't one difference work?" sequence.
        a, b = random.randint(2, 7), random.randint(2, 7)
        while a == b:
            b = random.randint(2, 7)
        seq = [random.randint(1, 9)]
        for i in range(4):
            seq.append(seq[-1] + (a if i % 2 == 0 else b))
        rule = t("logica.rule_alternate", a=a, b=b)
    elif kind == "square":
        start = random.randint(1, 5)
        seq = [(start + i) ** 2 for i in range(5)]
        rule = t("logica.rule_square")
    else:  # "fib"
        x, y = random.randint(1, 5), random.randint(2, 7)
        seq = [x, y]
        for _ in range(3):
            seq.append(seq[-1] + seq[-2])
        rule = t("logica.rule_fib")

    shown, answer = seq[:4], seq[4]
    return {
        "kind": "number",
        "text": t("logica.q_sequence", seq=", ".join(str(s) for s in shown)),
        "answer": answer,
        "explain": rule,
        "visual": ("numberline", shown),
    }


def _odd_one_out_problem(hard):
    """Four items, three share a property. Pick the one that doesn't."""
    if not hard:
        family = random.choice(["even", "odd", "table"])
        if family == "even":
            group = random.sample([n for n in range(2, 40, 2)], 3)
            odd = random.choice([n for n in range(1, 40, 2)])
            why = t("logica.why_even")
        elif family == "odd":
            group = random.sample([n for n in range(1, 40, 2)], 3)
            odd = random.choice([n for n in range(2, 40, 2)])
            why = t("logica.why_odd")
        else:
            table = random.choice([3, 4, 5])
            group = random.sample([table * k for k in range(2, 13)], 3)
            odd = random.choice([n for n in range(5, 60) if n % table != 0])
            why = t("logica.why_table", table=table)
    else:
        family = random.choice(["square", "prime", "tenfold"])
        if family == "square":
            group = random.sample([n * n for n in range(2, 11)], 3)
            squares = {n * n for n in range(1, 12)}
            odd = random.choice([n for n in range(4, 100) if n not in squares])
            why = t("logica.why_square")
        elif family == "prime":
            primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]
            group = random.sample(primes, 3)
            odd = random.choice([n for n in range(4, 40) if n not in primes])
            why = t("logica.why_prime")
        else:
            group = random.sample([10 * k for k in range(2, 12)], 3)
            odd = random.choice([n for n in range(11, 99) if n % 10 != 0])
            why = t("logica.why_tenfold")

    options = group + [odd]
    random.shuffle(options)
    return {
        "kind": "choice",
        "text": t("logica.q_odd_one_out"),
        "answer": str(odd),
        "options": [str(o) for o in options],
        "explain": why,
        "visual": None,
    }


def _pattern_problem():
    """A repeating shape pattern - the same "find the rule" skill as the
    number sequences, but readable before you can read."""
    period = random.choice([2, 3, 3, 4])
    palette = random.sample(SHAPES, period)
    seq = [palette[i % period] for i in range(7)]
    shown, answer = seq[:6], seq[6]
    options = list(dict.fromkeys(palette + random.sample(SHAPES, 2)))[:4]
    if answer not in options:
        options[0] = answer
    random.shuffle(options)
    return {
        "kind": "choice",
        "text": t("logica.q_pattern", pattern=" ".join(shown)),
        "answer": answer,
        "options": options,
        "explain": t("logica.why_pattern", period=period),
        "visual": None,
    }


def _statement_problem():
    """If/then reasoning: a rule, a fact, and a conclusion to judge. Half of
    the generated conclusions are deliberately invalid, so "yes" is not a
    winning strategy."""
    group = t(random.choice(["logica.group_a", "logica.group_b", "logica.group_c"]))
    prop = t(random.choice(["logica.prop_a", "logica.prop_b", "logica.prop_c"]))
    name = t(random.choice(NAME_KEYS))
    valid = random.choice([True, False])
    if valid:
        # All A are B; X is an A -> X is a B. Valid.
        text = t("logica.q_syllogism_valid", group=group, prop=prop, name=name)
        answer = t("logica.answer_yes")
        explain = t("logica.why_syllogism_valid")
    else:
        # All A are B; X is a B -> X is an A. The converse, which does not
        # follow - the single most common reasoning slip at this age.
        text = t("logica.q_syllogism_invalid", group=group, prop=prop, name=name)
        answer = t("logica.answer_no")
        explain = t("logica.why_syllogism_invalid")
    return {
        "kind": "choice",
        "text": text,
        "answer": answer,
        "options": [t("logica.answer_yes"), t("logica.answer_no")],
        "explain": explain,
        "visual": None,
    }


def _deduction_problem():
    """A small who-has-what grid. Three children, three objects, two clues
    that between them pin the assignment down exactly."""
    names = [t(k) for k in random.sample(NAME_KEYS, 3)]
    things = [t(k) for k in random.sample(THING_KEYS, 3)]
    assignment = things[:]
    random.shuffle(assignment)
    mapping = dict(zip(names, assignment))

    asked = random.choice(names)
    others = [n for n in names if n != asked]
    # Two clues that between them pin the answer down exactly:
    #   1. the asked child does NOT have `not_thing`
    #   2. one of the other two children DOES have their thing
    # `not_thing` isn't the asked child's and isn't the named child's, so it
    # must be the third child's - which leaves the asked child exactly one
    # option. (Because the mapping is a bijection, at least one of the two
    # others always differs from not_thing, so `next` never runs dry.)
    not_thing = random.choice([th for th in things if th != mapping[asked]])
    fixed_child = next(n for n in others if mapping[n] != not_thing)

    clues = [
        t("logica.clue_not", name=asked, thing=not_thing),
        t("logica.clue_has", name=fixed_child, thing=mapping[fixed_child]),
    ]
    random.shuffle(clues)
    return {
        "kind": "choice",
        "text": t("logica.q_deduction", clues="  \n".join(f"- {c}" for c in clues), name=asked),
        "answer": mapping[asked],
        "options": random.sample(things, len(things)),
        "explain": t("logica.why_deduction"),
        "visual": None,
    }


def _balance_problem():
    """Symbol algebra without the letters: ▲ = 3 ●, ● = 2 ■, so ▲ = ? ■.
    Same substitution reasoning as solving an equation, one step earlier."""
    sym_a, sym_b, sym_c = random.sample(["🔺", "🟦", "🟢", "⭐", "🟣"], 3)
    k1 = random.randint(2, 4)
    k2 = random.randint(2, 4)
    return {
        "kind": "number",
        "text": t("logica.q_balance", a=sym_a, k1=k1, b=sym_b, k2=k2, c=sym_c),
        "answer": k1 * k2,
        "explain": t("logica.why_balance", k1=k1, k2=k2, total=k1 * k2),
        "visual": ("ratio", [1] * k1, [sym_b] * k1),
    }


def _magic_square_problem():
    """A 3x3 magic square with one cell blanked out. Every row, column and
    diagonal has the same total, so the missing cell is fully determined."""
    base = [[8, 1, 6], [3, 5, 7], [4, 9, 2]]  # the classic 3x3, total 15
    mult = random.choice([1, 2, 3])
    add = random.choice([0, 1, 2, 5, 10])
    grid = [[v * mult + add for v in row] for row in base]
    total = sum(grid[0])
    ri, ci = random.randint(0, 2), random.randint(0, 2)
    answer = grid[ri][ci]

    # An empty header row, so all three data rows show as data - a markdown
    # table has to have a header, and promoting the top row of the square
    # into it would make that row look special when it isn't.
    rows = []
    for r in range(3):
        cells = ["**?**" if (r, c) == (ri, ci) else str(grid[r][c]) for c in range(3)]
        rows.append("| " + " | ".join(cells) + " |")
    grid_md = "\n".join(["|  |  |  |", "|:---:|:---:|:---:|"] + rows)

    return {
        "kind": "number",
        "text": t("logica.q_magic", total=total),
        "answer": answer,
        "explain": t("logica.why_magic", total=total),
        "visual": None,
        "markdown": grid_md,
    }


def generate_problem():
    if level == 0:
        problem = random.choice([lambda: _sequence_problem(["add"]), _pattern_problem])()
    elif level == 1:
        problem = random.choice(
            [lambda: _sequence_problem(["add", "sub"]), _pattern_problem, lambda: _odd_one_out_problem(False)]
        )()
    elif level == 2:
        problem = random.choice(
            [lambda: _sequence_problem(["add", "sub", "mul"]), lambda: _odd_one_out_problem(False), _statement_problem]
        )()
    elif level == 3:
        problem = random.choice(
            [
                lambda: _sequence_problem(["mul", "alternate"]),
                lambda: _odd_one_out_problem(True),
                _statement_problem,
                _balance_problem,
            ]
        )()
    elif level == 4:
        problem = random.choice(
            [
                lambda: _sequence_problem(["alternate", "square"]),
                lambda: _odd_one_out_problem(True),
                _deduction_problem,
                _balance_problem,
            ]
        )()
    else:
        problem = random.choice(
            [
                lambda: _sequence_problem(["square", "fib", "alternate"]),
                _deduction_problem,
                _magic_square_problem,
                _balance_problem,
            ]
        )()

    st.session_state.logica_problem = problem
    st.session_state.logica_feedback = None


if "logica_problem" not in st.session_state or st.session_state.logica_problem is None:
    generate_problem()

problem = st.session_state.logica_problem

question_card(problem["text"], emoji="🧠")

if problem.get("markdown"):
    st.markdown(problem["markdown"])

visual = problem.get("visual")
if visual and visual[0] == "numberline":
    seq = visual[1]
    lo = min(seq) - max(1, (max(seq) - min(seq)) // 4)
    hi = max(seq) + max(1, (max(seq) - min(seq)) // 2)
    st.markdown(
        number_line_svg(lo, hi, [(v, str(v)) for v in seq]),
        unsafe_allow_html=True,
    )
elif visual and visual[0] == "ratio":
    st.markdown(ratio_bar_svg(visual[1], labels=visual[2]), unsafe_allow_html=True)

if problem["kind"] == "number":
    user_answer = st.number_input(t("common.your_answer"), step=1, value=None, key="logica_number")
else:
    user_answer = st.radio(t("common.choose_answer"), problem["options"], index=None, key="logica_choice")

col1, col2 = st.columns([1, 4])
with col1:
    check_clicked = st.button(t("logica.check_button"), key="check_btn")
with col2:
    next_clicked = st.button(t("logica.next_button"), key="next_btn")

if check_clicked and user_answer is not None:
    is_correct = user_answer == problem["answer"]
    settle_answer(
        GAME_KEY,
        "logica_feedback",
        level,
        problem["text"],
        user_answer,
        problem["answer"],
        is_correct,
        points,
        correct_message=t("logica.correct", points=points, explain=problem["explain"]),
        incorrect_message=(
            f"{t('logica.incorrect')} "
            f"{t('common.correct_answer_was', answer=problem['answer'])} "
            f"{problem['explain']}"
        ),
    )
    st.rerun()

if next_clicked:
    generate_problem()
    st.rerun()

show_feedback("logica_feedback", tip_key="logica.why_tip", ok_icon="🧠", bad_icon="🔍")
play_pending()
play_pending_celebration()

if st.session_state.get("streaks", 0) >= 3:
    st.info(t("common.streak_fire", streak=st.session_state.streaks))

st.caption(t("common.session_recorded"))
