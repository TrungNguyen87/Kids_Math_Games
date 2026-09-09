"""
Regression tests for the whole app.

Run them with either:

    python tests/test_app.py          # no pytest needed
    pytest tests/test_app.py

They exist because this app has no type checker and no CI, and the bugs it
has actually shipped were not crashes - they were *wrong answers* (a
conversion rounded to the wrong whole number, a correctly simplified
fraction marked wrong, a triangle with a negative angle). A test that only
checks "the page renders" would have caught none of them, so most of what
is here checks the maths instead.

Every test drives the real Streamlit pages through streamlit.testing.v1,
so it also catches the ordinary breakage: an undefined translation key, a
widget argument a newer Streamlit rejects, a page that raises on level 5.
"""
import collections
import itertools
import logging
import math
import os
import random
import re
import sys

logging.disable(logging.WARNING)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from streamlit.testing.v1 import AppTest  # noqa: E402

from utils.i18n import TRANSLATIONS  # noqa: E402
from utils.state import GAME_KEYS  # noqa: E402

PAGES_DIR = os.path.join(REPO_ROOT, "pages")

# page file -> the GAME_KEYS entry it drives (None for non-game pages)
PAGE_GAME = {
    "01_✖️_Tafel_Monster.py": "tafel",
    "02_🍕_Breuken_Baas.py": "breuken",
    "03_📏_Meten_is_Weten.py": "meten",
    "04_💯_Procenten_Puzzel.py": "procenten",
    "07_🕵️_Het_X-Mysterie.py": "algebra",
    "08_📐_Meetkunde_Meesters.py": "meetkunde",
    "09_🚗_Verhoudingen_en_Snelheid.py": "verhoudingen",
    "10_🔢_Getallen_Universum.py": "getallen",
    "11_⚡_Bliksemronde.py": "bliksem",
    "12_🧠_Logica_Lab.py": "logica",
    "13_🔐_Code_Kraker.py": "code",
    "14_🎯_Getallenjacht.py": "jacht",
}


def run_page(filename, game=None, level=0, lang="nl", seed=0):
    """Render one page at a given level/language and return the AppTest."""
    random.seed(seed)
    at = AppTest.from_file(os.path.join(PAGES_DIR, filename), default_timeout=120)
    at.session_state["language"] = lang
    at.session_state["player_name"] = "TestKid"
    if game:
        at.session_state["levels"] = {k: 0 for k in GAME_KEYS}
        at.session_state["levels"][game] = level
    at.run()
    assert not at.exception, f"{filename} L{level} {lang}: {at.exception[0].value}"
    return at


# ---------------------------------------------------------------------------
# Translations
# ---------------------------------------------------------------------------
def test_translation_keys_match():
    """Every Dutch key must have an English one and vice versa - a missing
    key silently falls back to Dutch mid-sentence for an English user."""
    nl, en = set(TRANSLATIONS["nl"]), set(TRANSLATIONS["en"])
    assert nl == en, f"NL-only: {sorted(nl - en)}  EN-only: {sorted(en - nl)}"


def test_no_undefined_translation_keys_used():
    """Every t("literal") in the codebase must resolve to a real key."""
    import glob

    defined = set(TRANSLATIONS["nl"])
    missing = []
    sources = (
        glob.glob(os.path.join(REPO_ROOT, "pages", "*.py"))
        + glob.glob(os.path.join(REPO_ROOT, "utils", "*.py"))
        + [os.path.join(REPO_ROOT, "app.py")]
    )
    for path in sources:
        if os.path.basename(path) == "i18n.py":
            continue  # holds the definitions and the docstring's example key
        src = open(path, encoding="utf-8").read()
        for m in re.finditer(r'(?<![\w.])t\(\s*["\']([a-zA-Z0-9_.]+)["\']', src):
            if m.group(1) not in defined:
                missing.append(f"{os.path.basename(path)}: {m.group(1)}")
    assert not missing, f"undefined translation keys: {missing}"


def test_every_game_has_a_name_and_nav_label():
    for key in GAME_KEYS:
        for template in ("game.{}.name", "nav.{}"):
            assert template.format(key) in TRANSLATIONS["nl"], template.format(key)
            assert template.format(key) in TRANSLATIONS["en"], template.format(key)


# ---------------------------------------------------------------------------
# Every page renders, at every level, in both languages
# ---------------------------------------------------------------------------
def test_all_pages_render():
    for filename, game in PAGE_GAME.items():
        for level in range(6):
            for lang in ("nl", "en"):
                run_page(filename, game, level, lang, seed=level * 7)


def test_non_game_pages_render():
    for filename in ("00_🎮_Home.py", "05_📖_Uitleg_Concepten.py", "06_📊_Ouder_Dashboard.py"):
        for lang in ("nl", "en"):
            run_page(filename, lang=lang)


# ---------------------------------------------------------------------------
# Maths correctness - the bugs that actually shipped
# ---------------------------------------------------------------------------
UNIT_IN_METRES = {"mm": 0.001, "cm": 0.01, "m": 1, "km": 1000,
                  "g": 0.001, "kg": 1, "ml": 0.001, "l": 1}


def test_meten_conversions_are_exact():
    """Regression: level 2 used round(value * factor), so "0,25 cm = ... mm"
    expected 2 instead of 2.5 - a wrong answer the child could not have
    typed into the whole-number input anyway."""
    for seed in range(60):
        at = run_page("03_📏_Meten_is_Weten.py", "meten", 2, seed=seed)
        problem = at.session_state["meten_problem"]
        answer = problem["answer"]
        assert float(answer).is_integer(), problem["text"]
        value, unit_from, unit_to = (
            problem["text"].replace("?", "").replace("=", "").replace("...", "").split()
        )
        exact = float(value.replace(",", ".")) * UNIT_IN_METRES[unit_from] / UNIT_IN_METRES[unit_to]
        assert abs(exact - answer) < 1e-6, f"{problem['text']} -> {answer}, exact {exact}"


def test_meten_uses_the_language_decimal_separator():
    nl = run_page("03_📏_Meten_is_Weten.py", "meten", 2, lang="nl", seed=3)
    en = run_page("03_📏_Meten_is_Weten.py", "meten", 2, lang="en", seed=3)
    assert "," in nl.session_state["meten_problem"]["text"]
    assert "." in en.session_state["meten_problem"]["text"]


def test_breuken_accepts_an_equivalent_simplified_answer():
    """Regression: "1/2 + 2/4" expects 4/4, and a child who answered the
    equivalent 1/1 was marked wrong."""
    for seed in range(400):
        at = run_page("02_🍕_Breuken_Baas.py", "breuken", 4, seed=seed)
        problem = at.session_state["breuk_problem"]
        divisor = math.gcd(problem["correct_num"], problem["correct_den"])
        if divisor == 1:
            continue
        at.number_input(key="teller").set_value(problem["correct_num"] // divisor)
        at.number_input(key="noemer").set_value(problem["correct_den"] // divisor)
        at.button(key="check_btn").click().run()
        assert at.session_state["breuk_feedback"][0] == "success", problem["text"]
        return
    raise AssertionError("no reducible fraction generated in 400 tries")


def test_breuken_still_rejects_a_wrong_answer():
    at = run_page("02_🍕_Breuken_Baas.py", "breuken", 4, seed=1)
    problem = at.session_state["breuk_problem"]
    at.number_input(key="teller").set_value(problem["correct_num"] + 1)
    at.number_input(key="noemer").set_value(problem["correct_den"])
    at.button(key="check_btn").click().run()
    assert at.session_state["breuk_feedback"][0] == "error"


def test_meetkunde_angles_are_positive_and_sum_correctly():
    """Regression: the old rejection-sampling loop could fall through after
    30 failed tries and ask for a triangle's third angle of -10 degrees."""
    for seed in range(80):
        at = run_page("08_📐_Meetkunde_Meesters.py", "meetkunde", 5, seed=seed)
        problem = at.session_state["meetkunde_problem"]
        assert problem["unit_suffix"] == "°"
        assert 0 < problem["answer"] < 180, problem["text"]
        given = [int(g) for g in re.findall(r"\d+", problem["text"])]
        total = 360 if 360 in given else 180
        angles = [g for g in given if g != total]
        assert sum(angles) + problem["answer"] == total, problem["text"]


def test_verhoudingen_never_says_zero_minutes():
    for seed in range(80):
        at = run_page("09_🚗_Verhoudingen_en_Snelheid.py", "verhoudingen", 5, seed=seed)
        text = at.session_state["verhoudingen_problem"]["text"]
        assert " 0 minuten" not in text and " 0 minutes" not in text, text


def test_all_games_produce_an_answer_at_every_level():
    """A generator that returns None, or a level that silently produces no
    problem, would show an empty question card."""
    problem_keys = {
        "tafel": "tafel_problem", "breuken": "breuk_problem", "meten": "meten_problem",
        "procenten": "perc_problem", "algebra": "algebra_problem",
        "meetkunde": "meetkunde_problem", "verhoudingen": "verhoudingen_problem",
        "getallen": "getallen_problem", "logica": "logica_problem",
    }
    for filename, game in PAGE_GAME.items():
        state_key = problem_keys.get(game)
        if not state_key:
            continue
        for level in range(6):
            at = run_page(filename, game, level, seed=level * 3)
            problem = at.session_state[state_key]
            assert problem, f"{game} L{level} produced no problem"
            assert problem.get("text"), f"{game} L{level} produced no question text"
            has_answer = "answer" in problem or "correct_num" in problem
            assert has_answer, f"{game} L{level} produced no answer"


# ---------------------------------------------------------------------------
# Round-5 games
# ---------------------------------------------------------------------------
def test_mastermind_scoring_matches_a_reference_implementation():
    """The bulls-and-cows count must handle repeated digits: a naive version
    counts a repeat twice and the clues then contradict each other, which is
    exactly the kind of thing a child WILL notice."""
    module = _load_code_kraker_scorer()

    def reference(secret, guess):
        exact = sum(1 for s, g in zip(secret, guess) if s == g)
        common = sum((collections.Counter(secret) & collections.Counter(guess)).values())
        return exact, common - exact

    for secret in itertools.product(range(1, 5), repeat=3):
        for guess in itertools.product(range(1, 5), repeat=3):
            assert module(list(secret), list(guess)) == reference(secret, guess), (secret, guess)


def _load_code_kraker_scorer():
    """Pull score_guess() out of the Code Kraker page without running the
    page (it is a Streamlit script, not an importable module)."""
    path = os.path.join(PAGES_DIR, "13_🔐_Code_Kraker.py")
    source = open(path, encoding="utf-8").read()
    start = source.index("def score_guess(")
    end = source.index("\n# A change of level", start)
    namespace = {}
    exec(compile(source[start:end], path, "exec"), namespace)
    return namespace["score_guess"]


def test_code_kraker_can_be_solved_and_pays_out():
    for level in (0, 3, 5):
        at = run_page("13_🔐_Code_Kraker.py", "code", level, seed=level)
        secret = at.session_state["code_secret"]
        before = at.session_state["total_score"]
        for i, digit in enumerate(secret):
            at.selectbox(key=f"code_pos_{level}_{i}").set_value(digit)
        at.button(key="check_btn").click().run()
        assert not at.exception, at.exception[0].value
        assert at.session_state["code_solved"], f"level {level} not solved"
        assert at.session_state["total_score"] > before, f"level {level} paid nothing"


def test_logica_answers_are_valid():
    for level in range(6):
        for seed in range(20):
            at = run_page("12_🧠_Logica_Lab.py", "logica", level, seed=seed * 17 + level)
            problem = at.session_state["logica_problem"]
            assert problem["answer"] is not None
            assert problem["explain"]
            if problem["kind"] == "choice":
                assert problem["answer"] in problem["options"], problem["text"]
                assert len(set(problem["options"])) == len(problem["options"]), problem["options"]
            else:
                assert isinstance(problem["answer"], int), problem["text"]


def test_logica_sequences_follow_their_stated_rule():
    checked = 0
    for level in range(6):
        for seed in range(30):
            at = run_page("12_🧠_Logica_Lab.py", "logica", level, seed=seed * 7 + level * 101)
            problem = at.session_state["logica_problem"]
            match = re.match(r"Welk getal komt hierna\? ([\d, ]+), \.\.\.", problem["text"])
            if not match:
                continue
            checked += 1
            full = [int(x) for x in match.group(1).split(",")] + [problem["answer"]]
            steps = [b - a for a, b in zip(full, full[1:])]
            ratios = [b / a for a, b in zip(full, full[1:]) if a]
            valid = (
                len(set(steps)) == 1
                or (len(ratios) == len(full) - 1 and len(set(ratios)) == 1)
                or (len(set(steps[0::2])) == 1 and len(set(steps[1::2])) == 1)
                or all(int(v**0.5) ** 2 == v for v in full)
                or all(full[i] == full[i - 1] + full[i - 2] for i in range(2, len(full)))
            )
            assert valid, f"{full}: {problem['explain']}"
    assert checked > 10, "no sequences were generated to check"


def test_number_hunt_targets_match_the_rule():
    primes = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
              53, 59, 61, 67, 71, 73, 79, 83, 89, 97}
    predicates = {
        "even": lambda n: n % 2 == 0,
        "odd": lambda n: n % 2 == 1,
        "prime": lambda n: n in primes,
        "square": lambda n: int(n**0.5) ** 2 == n,
    }
    for level in range(6):
        for seed in range(12):
            at = run_page("14_🎯_Getallenjacht.py", "jacht", level, seed=seed * 13 + level)
            at.button(key="jacht_start").click().run()
            assert not at.exception, at.exception[0].value
            numbers = at.session_state["jacht_numbers"]
            targets = at.session_state["jacht_targets"]
            rule = at.session_state["jacht_rule_id"]
            assert len(numbers) == len(set(numbers)), f"duplicate numbers: {numbers}"
            assert targets, f"rule {rule} produced no targets"
            assert targets <= set(numbers)
            if rule in predicates:
                expected = {n for n in numbers if predicates[rule](n)}
                assert expected == targets, f"{rule}: {sorted(expected)} != {sorted(targets)}"


def test_number_hunt_clearing_the_grid_wins_the_round():
    at = run_page("14_🎯_Getallenjacht.py", "jacht", 1, seed=3)
    at.button(key="jacht_start").click().run()
    for number in sorted(at.session_state["jacht_targets"]):
        at.button(key=f"jacht_{number}").click().run()
        assert not at.exception, at.exception[0].value
    assert at.session_state["jacht_cleared"]
    assert at.session_state["jacht_state"] == "finished"


def test_number_hunt_three_wrong_taps_ends_the_round():
    at = run_page("14_🎯_Getallenjacht.py", "jacht", 1, seed=9)
    at.button(key="jacht_start").click().run()
    wrong = [n for n in at.session_state["jacht_numbers"] if n not in at.session_state["jacht_targets"]]
    for number in wrong[:3]:
        at.button(key=f"jacht_{number}").click().run()
        assert not at.exception, at.exception[0].value
    assert at.session_state["jacht_lives"] <= 0
    assert at.session_state["jacht_state"] == "finished"


def test_lightning_round_combo_resets_on_a_wrong_answer():
    at = run_page("11_⚡_Bliksemronde.py", "bliksem", 2, seed=5)
    at.button(key="bliksem_start").click().run()
    combos = []
    for step in range(6):  # right, right, wrong, right, right, wrong
        problem = at.session_state["bliksem_problem"]
        wanted = (
            problem["answer"]
            if step % 3 != 2
            else next(o for o in problem["options"] if o != problem["answer"])
        )
        at.button(key=f"bliksem_opt_{problem['options'].index(wanted)}").click().run()
        assert not at.exception, at.exception[0].value
        combos.append(at.session_state["bliksem_combo"])
    assert combos == [1, 2, 0, 1, 2, 0], combos
    assert at.session_state["bliksem_correct"] == 4


def test_lightning_round_options_are_distinct_and_contain_the_answer():
    for level in range(6):
        for seed in range(15):
            at = run_page("11_⚡_Bliksemronde.py", "bliksem", level, seed=seed * 11 + level)
            at.button(key="bliksem_start").click().run()
            for _ in range(5):
                problem = at.session_state["bliksem_problem"]
                options = problem["options"]
                assert len(options) == 4, options
                assert len(set(options)) == 4, options
                assert problem["answer"] in options, problem
                assert all(o >= 0 for o in options), options
                index = options.index(problem["answer"])
                at.button(key=f"bliksem_opt_{index}").click().run()
                assert not at.exception, at.exception[0].value


# ---------------------------------------------------------------------------
# Visuals
# ---------------------------------------------------------------------------
def test_generated_svgs_are_well_formed_and_scoped():
    """Inline SVG shares the page's CSS scope, so two visuals on one page
    must not use the same class names or element ids."""
    import xml.etree.ElementTree as ET

    import utils.visuals as visuals

    visuals.t = lambda key, **kwargs: key.split(".")[-1]
    cases = [
        visuals.pizza_svg(3, 8), visuals.pizza_svg(0, 5), visuals.pizza_svg(8, 8),
        visuals.fraction_bar_svg(7, 16), visuals.percent_bar_svg(40),
        visuals.percent_bar_svg(0), visuals.array_grid_svg(4, 6),
        visuals.array_grid_svg(15, 18), visuals.clock_svg(14, 35),
        visuals.clock_svg(0, 0), visuals.tape_diagram_svg(10, 3.5),
        visuals.ratio_bar_svg([3, 5, 2]), visuals.balance_scale_svg("x + 5", "12"),
        visuals.number_line_svg(-10, 10, [(-3, "start")]),
        visuals.skip_count_svg(7, 56), visuals.rectangle_svg(8, 5, unit="cm"),
        visuals.triangle_svg(12, 6, unit="cm"), visuals.cuboid_svg(4, 3, 5, unit="cm"),
        visuals.speed_diagram_svg(120, "km", 2, "uur"),
    ]
    seen_ids = set()
    for svg in cases:
        root = ET.fromstring(svg)  # raises if the markup is malformed
        uid = root.get("id")
        if not uid:
            continue
        assert uid not in seen_ids, f"duplicate svg id {uid}"
        seen_ids.add(uid)
        for attr in re.findall(r'class="([^"]+)"', svg):
            for name in attr.split():
                assert name.startswith(uid), f"unscoped class {name!r} in svg {uid}"


def test_repeat_renders_get_distinct_ids():
    import utils.visuals as visuals

    first = re.search(r'id="(\w+)"', visuals.pizza_svg(1, 4)).group(1)
    second = re.search(r'id="(\w+)"', visuals.pizza_svg(1, 4)).group(1)
    assert first != second


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    tests = [(name, obj) for name, obj in sorted(globals().items())
             if name.startswith("test_") and callable(obj)]
    failed = []
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001 - a test runner reports everything
            failed.append((name, exc))
            print(f"  FAIL  {name}: {exc}")
    print(f"\n{len(tests) - len(failed)}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
