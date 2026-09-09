# Changelog

All notable changes to this project are documented in this file.
The format is loosely based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Fixed (round 3)
- **Menu now actually follows the language toggle.** Switched from
  Streamlit's filename-based `pages/` auto-discovery to an explicit
  `st.navigation`/`st.Page` router in `app.py`, rebuilt from `t()` on every
  rerun - previously the sidebar menu always showed the Dutch filenames
  regardless of the NL/EN toggle. This also makes page order explicit, so
  the Parent Dashboard is now always the last item instead of sitting in
  the middle of the list.
- **Player name now actually saves.** Streamlit clears a widget's
  session-state entry whenever that widget isn't rendered on the current
  page, so binding `player_name` directly to the home page's `text_input`
  key meant it was wiped the instant you navigated to a game. The durable
  value now lives in its own session-state key, re-seeded into the widget
  every time the home page runs; the sidebar also shows "Playing as: ..."
  on every page so it's clear the name was saved.
- **Tafel Monster's hint no longer gives away the answer.** For
  missing-factor/division questions, the old hint drew an accurate a×b
  dot grid, so counting one side of it read off the missing factor
  directly. It now shows a skip-counting number line for the known
  factor with the product flagged as a target - the child still has to
  count the hops themselves (`utils/visuals.py: skip_count_svg`).
- **More interactive visuals.** Breuken Baas's fraction explorer now uses
  draggable sliders instead of number inputs; Procenten Puzzel and
  Meetkunde Meesters gained their own slider-driven live explorers
  (percent bar; rectangle width/height with live perimeter & area).
- **Cheat sheet (Uitleg Concepten) now covers all 8 games**, not just the
  original 4 - added NL/EN explanations for equations (X-Mysterie),
  geometry, ratios/speed, and negative numbers/long arithmetic.
- Hardcoded Dutch text that ignored the language toggle: percentage
  visual captions ("van"/"korting"), speed-diagram units ("uur"/"km/u"),
  and shape-label words baked into `utils/visuals.py` (basis/hoogte/totaal,
  and the cuboid width label using the Dutch "b" abbreviation even in
  English).
- Breuken Baas's "simplify as far as possible" question could generate a
  fraction that wasn't actually fully reduced (e.g. asking to simplify to
  2/4 instead of 1/2); the numerator is now always coprime with the target
  denominator.
- Clicking the already-active level button reset that game's
  adaptive-difficulty streak counters for no reason.
- "Clear all history" on the Parent Dashboard didn't clear the current
  session's in-memory log (so answered questions kept reappearing in the
  table) and its confirmation message was immediately wiped by the rerun
  that followed it; both are fixed.

### Added (round 2)
- **Manual level picker.** Every game now shows a row of clickable 1-5
  level buttons at the top (`utils/ui.py: level_control`), so leveling up
  is an explicit, visible action a child (or parent) can take directly -
  on top of the automatic adaptive leveling from round 1, which still runs
  in the background.
- **Visualizations everywhere** (`utils/visuals.py`, pure inline SVG, no
  new dependency): a pizza chart / fraction bar that updates live, a
  percent fill bar, a dot array for multiplication, an analog clock face,
  tape diagrams (bar models) for money and part-whole problems, a ratio
  bar, a balance scale for equations, a number line for negative numbers,
  and labeled rectangle/triangle/cuboid shapes for geometry. Visuals only
  ever show the *given* numbers in a question, never the answer.
- **Interactive fraction explorer** on Breuken Baas: a free-play slider
  section ("🔍 Probeer het zelf uit!") where changing the numerator or
  denominator instantly redraws the pizza and its percentage - exactly the
  "pick a fraction, watch the pizza/percentage change" interaction asked
  for. Tafel Monster also gained an optional "show me a picture" hint
  revealing a dot array for the current problem.
- **4 new games** for the end of groep 7 / middle of groep 8:
  - 🕵️ **Het X-Mysterie** - solving equations for x (one-step through
    two-step, including negative solutions), up to a **2-variable linear
    system** (`x + y = S`, `x - y = D`) at the top level, visualized as a
    balance scale.
  - 📐 **Meetkunde Meesters** - perimeter & area of rectangles, triangle
    area, compound-shape area, cuboid volume, and missing-angle problems
    (triangle/quadrilateral angle sums), each with a labeled shape drawing.
  - 🚗 **Verhoudingen & Snelheid** - simplifying ratios, map scale, speed =
    distance/time (solving for any of the three), unit price, and
    multi-step speed/time word problems.
  - 🔢 **Getallen Universum** - negative number arithmetic on a number
    line, two-digit long multiplication, long division with remainder, and
    decimal multiplication/division.
  All four follow the same pattern as the original games: 5 adaptive +
  manually-selectable levels, full NL/EN translation, and session logging.

### Fixed
- Page filenames are now zero-padded (`01_`...`10_`) so Streamlit's
  filename-based nav sorts correctly now that there are 10 pages (`10_`
  used to sort before `1_`-`9_` alphabetically).
- Check/Next buttons on every game now have explicit widget keys.

### Added (round 1)
- **Adaptive difficulty levels (1-5) for every game.** Each game (Tafel Monster,
  Breuken Baas, Meten is Weten, Procenten Puzzel) now starts at an easy level
  and automatically levels up after 3 correct answers in a row, and eases
  back down after 2 wrong answers in a row, so a session gradually ramps up
  in challenge instead of staying flat. A level badge (Makkelijk → Meester /
  Easy → Master) is shown on every game page.
- **New, harder question types**, aimed at Dutch "groep 6 & 7" (ages ~9-11):
  - *Tafel Monster*: missing-factor problems, division facts, two-digit
    multiplication, and word problems, on top of the original tables.
  - *Breuken Baas*: fraction subtraction, simplifying fractions, adding
    fractions with different denominators, and multiplying a fraction by a
    whole number.
  - *Meten is Weten*: decimal unit conversions, mixed-unit addition,
    clock/time calculations (elapsed minutes), and money problems
    (change, total cost).
  - *Procenten Puzzel*: percentage-of-a-number, discount/new-price word
    problems, harder fraction/decimal/percent equivalents (eighths, fifths),
    and reverse-percentage ("what was the original price?") problems.
- **More randomization and variety** in every question generator so repeat
  plays rarely look identical, and a session can comfortably run 45+ minutes
  before questions feel repetitive.
- **Session log**: every answered question (game, level, question text,
  child's answer, correct answer, right/wrong, points, timestamp) is
  recorded for the current browser session and appended to
  `logs/all_sessions_log.csv` on disk, so history accumulates across
  multiple play sessions.
- **Parent Dashboard** (new page, "📊 Ouder Dashboard"): summary metrics
  (sessions, questions answered, accuracy, total play time), an accuracy
  chart per game, a questions-per-day chart, a filterable full log table,
  a player-name filter, and CSV download buttons for the full history and
  for just the current session. Includes an (confirmation-gated) option to
  clear stored history.
- **Player name field** on the home page so multiple children's results can
  be told apart in the log/dashboard.
- **Language switcher** (🇳🇱 Nederlands / 🇬🇧 English) in the sidebar on every
  page. All UI text - including every question template, button, and
  feedback message - is pre-translated and switches instantly; no manual
  per-session translation needed.
- **Session progress widget** in the sidebar: elapsed play time vs. a
  45-minute goal, questions answered this session, and running accuracy.
- `requirements.txt` (streamlit, pandas) for reproducible installs/deploys.
- This changelog.

### Changed
- Replaced the old "always show Dutch + small English subtitle" text style
  with a proper single-language UI driven by the language switcher.
- Score-per-correct-answer now scales with difficulty level (10 to 30
  points) instead of a flat 10 points.
- Uitleg Concepten (cheat sheet) gained explanations for the new time,
  money, and percentage-of-a-number topics, and is now fully translated.

### Notes
- On hosting platforms with an ephemeral filesystem, `logs/all_sessions_log.csv`
  persists across sessions during uptime but resets on redeploy/restart —
  use the dashboard's download buttons to keep a permanent copy.
