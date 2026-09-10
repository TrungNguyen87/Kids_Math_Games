# Changelog

All notable changes to this project are documented in this file.
The format is loosely based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added (round 6 - static web app, GitHub Pages, PWA)

**The whole app now runs in the browser.** A new `web/` folder holds a static
front-end with all twelve games, ported from the Streamlit pages, deployed to
GitHub Pages. No build step, no framework, no bundler: plain HTML, one CSS
file and ES modules, so what is in the repository is exactly what the browser
runs.

*Why:* Streamlit re-runs the whole Python script on every tap and streams the
result back, which put the network inside the loop of an animated, timed game.
The countdowns had to be faked with `st.fragment(run_every=1)` (one round-trip
per second, stepping a whole second at a time) and the answer buttons had to
sit outside that fragment or a rerun would swallow the tap. Streamlit Community
Cloud also sleeps an idle app, so a child opening a bookmark after school gets
a cold start instead of a game. The reasoning and the alternatives considered
are written up in `docs/DEPLOYMENT.md`.

- **Deployment** - `.github/workflows/deploy-pages.yml` publishes `web/` on every
  push to `main`. Free, no second account, no server, no cold start. Full
  click-by-click setup, update, custom-domain and troubleshooting guide in
  **`docs/DEPLOYMENT.md`**.
- **Works offline** - a service worker precaches the whole app, so after one
  visit every game works with no network at all. Installable to a tablet's home
  screen as a PWA (`manifest.webmanifest`, app icons including a maskable one).
  The cache is named after the commit SHA, stamped in at deploy time, so a new
  deploy invalidates it exactly once instead of stranding a child on an old
  copy.

### Improved interaction (the point of the move)

- **Answers are instant.** No round-trip between a tap and the response.
- **On-screen number pad**, in the calculator layout children already know
  (7-8-9 / 4-5-6 / 1-2-3 / 0). `st.number_input` rendered a small desktop
  spinner that, on a tablet, summoned the OS keyboard over the visual and the
  question.
- **Real-time clocks.** The timed games run a `requestAnimationFrame` loop
  against a deadline, so the countdown ring sweeps at the screen's refresh rate
  instead of stepping once a second - and the "answered in 1.2s" speed bonus
  now measures the child rather than the wifi.
- **A correct answer auto-advances** after a beat, so a child in flow never
  hunts for "next". A wrong answer does not: that is the one moment they need
  time to read what the answer should have been.
- **Multiple choice is tappable cards**, and the right answer is revealed in
  place after a wrong pick rather than only named in a sentence underneath.
- **The fraction explorer is the pizza itself** - tap a slice to fill or empty
  it and watch the fraction, decimal and percentage move together. It used to
  be two sliders and a server round-trip per drag.
- **Code Kraker takes digit taps** into slots instead of a column of dropdowns:
  four taps rather than four select-and-scroll gestures, which matters when a
  child gets nine guesses.
- **Number Hunt restyles one tile per tap** instead of rebuilding all twenty
  buttons, so the grid keeps up with a child who is going fast.
- **Home page is game tiles**, each showing that game's level and progress bar,
  instead of a markdown bullet list.

### Improved animation and sound

- **Canvas confetti with real physics** - gravity, drag and tumble, bursting
  from the button the child actually tapped. The CSS version could only drop
  divs in straight lines.
- **A full-screen level-up card**, because a small toast was being missed.
- **Floating "+15" points** out of the button that earned them.
- **Web Audio sound effects**, synthesized in the browser at the instant of the
  tap: a rising arpeggio for a correct answer that climbs a step for every
  answer in the current streak, a fanfare for a level-up, a sparkle for a
  badge, a tick over the last five seconds of a timed round. The Streamlit
  version had to build a WAV file byte by byte in Python and base64 it into a
  hidden autoplay tag.
- **Dark mode**, because homework happens after dinner in winter.
- The whole SVG visual library was ported with its animations intact, including
  the per-render class scoping and the `prefers-reduced-motion` escape hatch on
  every single visual.

### Improved visualisation

- **The parent dashboard's charts are hand-drawn SVG** - no pandas, no Altair.
  A horizontal bar chart for accuracy per game, sorted so the hardest game is
  at the top; a column chart for questions per day with only the peak labelled.
  Both have hover tooltips, keyboard-focusable marks and a "show the numbers"
  table. The two chart colours were validated against the light and dark
  surfaces (contrast and lightness band) rather than picked by eye.
- **Every badge is shown**, the unearned ones dimmed, so a child can see what
  there is left to win.

### Changed

- **Results now live on the child's device**, in browser storage, instead of a
  CSV on the server. Better in three ways - it survives redeploys (the old one
  did not), it survives being offline, and no child's data leaves the machine -
  and worse in one: a tablet and a laptop keep separate histories. The
  dashboard's CSV export is therefore prominent, and its columns are identical
  to the ones `utils/gamelog.py` wrote, so old and new exports open side by
  side. This also settles most of the privacy questions in
  `docs/PLATFORM_ROADMAP.md` section 6 for free: no server, no third party, no
  analytics, no external fonts or CDNs on a page a child sees.
- `utils/i18n.py` remains the single source of truth for copy in both
  languages. `web/js/i18n-data.js` is generated from it by `tools/gen_i18n.py`,
  which refuses to run if a key exists in one language and not the other.
  14 new keys were added for the web-only UI (473 total).

### Fixed

- **The nav scrim covered the whole app at phone width.** Its `display: block`
  inside a `@media (max-width: 900px)` block silently overrode the built-in
  `[hidden] { display: none }`, so on every phone and tablet a semi-transparent
  overlay sat on top of the game and swallowed every tap. Found by looking at a
  screenshot, not by a test - so the browser smoke test now hit-tests the first
  control at phone width and clicks it.
- **`Node.append(null)` printed the word "null" on the page.** `append()`
  stringifies its arguments, so a conditional child written as
  `condition ? el(...) : null` rendered as text. It was visible under the
  streak counter in the sidebar. Added a filtering `append()` helper in
  `web/js/dom.js` and used it at the three sites with conditional children.

### Tests

- `tests/web/test_logic.mjs` - 62 tests run under `node --test`. Every question
  generator is exercised several hundred times per level and checked against
  the rule it has to keep: divisions divide exactly, "simplify" answers really
  are in lowest terms, angles sum to 180 or 360 with no angle below 20 degrees,
  long division's remainder is smaller than its divisor, one-decimal answers
  have one decimal, every multiple-choice question contains its own answer,
  Mastermind never counts a repeated digit twice, and every Number Hunt round
  is winnable without tapping the whole grid. Plus NL/EN key parity, matching
  placeholders per key, and SVG well-formedness.
- `tests/web/smoke.mjs` - a real Chromium pass over all 15 routes, checking for
  console errors, playing a question through the number pad, confirming it
  reaches the dashboard, switching language, watching a countdown actually
  tick, checking the phone layout is tappable and does not scroll sideways, and
  reloading with the network off.
- `tools/check_precache.py` - compares the service worker's precache list
  against the files on disk in both directions. CI runs it before every deploy,
  because a file missing from that list works perfectly in testing and then
  404s offline, in front of a child.

### Added (round 5 - animation, logic & speed games, classroom plan)
- **Animation layer** (`utils/anim.py` + animated SVGs in `utils/visuals.py`).
  Pure CSS keyframes and inline-SVG animation - no new dependency and no
  JavaScript (Streamlit strips `<script>` from markdown anyway):
  - Every visual now *builds itself*: pizza slices fill one at a time, dot
    arrays pop in row by row, percent/tape/ratio bars grow from zero, clock
    hands sweep round to the time, the number line's markers drop in, hop
    arcs draw in counting order, rectangles and triangles draw their own
    outline before the fill washes in, the cuboid assembles face by face,
    and the balance scale rocks and settles level.
  - Each question arrives in an animated card that slides up with a single
    light sweep, so it is obvious the question changed even when the new one
    looks like the old one.
  - Correct answers pop a green banner; wrong ones shake a red one. Level-ups
    and new badges fire a CSS confetti burst, queued the same way sounds are
    (rendering it before `st.rerun()` would throw it away).
  - The sidebar score box pops and shows `+N` only on the runs where the
    score actually went up, and the level badge pops only when the level
    actually changed.
  - Class names and element ids are scoped per render, so two visuals on one
    page cannot animate each other, and **everything is switched off under
    `prefers-reduced-motion`** - the finished picture shows immediately
    instead.
- **Four new games**, taking the app from 8 to 12:
  - ⚡ **Bliksemronde / Lightning Round** - a 60-second speed round with four
    answer buttons, a combo multiplier and a speed bonus for answering inside
    3 seconds. The clock is an `st.fragment(run_every=1)` so it ticks without
    rebuilding the answer buttons under the child's finger.
  - 🎯 **Getallenjacht / Number Hunt** - a timed grid hunt: tap every multiple,
    prime, square or digit-sum match before the clock runs out, with three
    lives and a bonus for clearing the grid. Trains number *properties* from
    the recognition side.
  - 🧠 **Logica Lab / Logic Lab** - reasoning rather than calculating: number
    and shape sequences, odd-one-out, if/then statements (including the
    invalid converse, the classic slip at this age), a who-has-what deduction
    grid, symbol balance puzzles and magic squares.
  - 🔐 **Code Kraker / Code Breaker** - Mastermind with digits. Pure
    elimination reasoning, scored on how few guesses it took.
  All four have 6 levels, full NL/EN translation, session logging, badges and
  the level picker, and are wired into the navigation, the home page and the
  cheat sheet.
- **`utils/gameflow.py`** - the shared "what happens after an answer" sequence
  (log, adapt, score, feedback, toast, badges, save). The timed games adapt
  their level **once per round** instead of per answer: inside a 60-second
  round, three quick correct answers are just three easy draws, whereas
  9-of-10 for a whole round really does mean "too easy".
- **Cheat sheet** gained three new sections: logical thinking & patterns,
  cracking codes, and faster mental maths (the 9-times trick, divisibility
  by 3 and 4, what a prime is).
- **`tests/test_app.py`** - 23 regression tests, runnable with plain
  `python tests/test_app.py` or with pytest. They check translation parity
  and that no `t()` call references an undefined key; that every page renders
  at every level in both languages; the maths behind each bug fixed below;
  Mastermind scoring against a reference implementation over all 4096
  secret/guess pairs; that generated sequences actually follow the rule they
  claim; that Number Hunt's targets match its stated rule; and that generated
  SVG is well-formed and properly scoped.
- **`docs/PLATFORM_ROADMAP.md`** - a phased development plan for turning the
  app into a classroom platform (pupil accounts, live class view, per-child
  development tracking, teacher-built exams), with six checkpoints where the
  teacher decides rather than the developer reports. Includes the honest
  assessment that Streamlit is unlikely to hold thirty concurrent pupils and
  schedules that decision, with a load test, at Checkpoint 5.

### Fixed (round 5)
- **Meten is Weten level 2 gave mathematically wrong answers.** Decimal
  conversions used `round(value * factor)`, so "0,25 cm = ... mm" expected
  **2** (Python rounds 2.5 to even) and "0,75 cm = ... mm" expected **8**.
  Both are wrong, and the true answers - 2.5 and 7.5 - could not have been
  typed into the whole-number input anyway. Level 2 now offers only decimal
  steps that convert to a whole number of the smaller unit. The question also
  went through an f-string that bypassed the translation system, so Dutch
  showed "0.5 cm" instead of "0,5 cm"; it now uses the template and a
  language-aware decimal separator.
- **Breuken Baas marked a correctly simplified answer wrong.** Grading
  compared the literal numerator/denominator pair, so on "1/2 + 2/4" a child
  who worked it out and then simplified 4/4 to 1/1 - exactly what we teach
  them to do - was told they were wrong. Grading now cross-multiplies and
  accepts any equal fraction, and when the expected answer is not in lowest
  terms the feedback shows the simplified form beside it.
- **Meetkunde Meesters could ask for a negative angle.** The missing-angle
  generator rejection-sampled up to 30 times and then fell through using
  whatever the last *rejected* draw was - for a triangle, that can be
  "95 + 95 = 180, what is the third angle?" with -10 as the expected answer.
  It now picks the missing angle first and splits the remainder, which is
  correct by construction (verified over 200,000 trials).
- **`requirements.txt` allowed a Streamlit too old to run the app.** The floor
  was `>=1.37`, but the parent dashboard's `st.dataframe(width="stretch")`
  needs `>=1.49`; older versions reject the string outright. Bumped, with the
  reason written next to it.
- Replaced `use_container_width`, which Streamlit has deprecated and will
  remove, with `width="stretch"`.
- Verhoudingen & Snelheid level 5 could ask how far a train travels "in 3
  hours and 0 minutes".
- `speed_diagram_svg` had a hardcoded English "in" between the distance and
  the time (so Dutch read "120 km in 2 uur" with an English joiner), and used
  a fixed `id="arrow"` for its arrowhead marker, which collides if two speed
  diagrams ever share a page.
- The home page's level overview split the games into two rows, which with 12
  games left the labels too narrow to read; it now lays out four per row.

### Added (round 4 - fun & difficulty-range improvements)
- **Persistent player profiles.** Score, levels, and badges are now saved
  to disk per player name (`logs/player_profiles.json`) and restored the
  next time that name is entered - a kid no longer starts from zero every
  time they open the app (`utils/profiles.py`).
- **Milestone badges**: questions-answered tiers (10/50/100), streak
  badges (5/10 in a row), "tried every game", "reached level 5", and
  "level 5 in every game" - shown on the home page and toasted the moment
  they're earned (`utils/badges.py`).
- **Sound effects** for correct/incorrect answers - short tones synthesized
  on the fly (no external audio files or network calls) via a hidden
  autoplay `<audio>` tag, with a sidebar toggle to turn them off
  (`utils/sound.py`).
- **A gentler "Warm-up" level (0)** below the existing 1-5 scale in every
  game, for kids who find even the current easiest level too hard. The
  adaptive system still levels a confident kid up out of it within 3
  correct answers.
- **"Why" tips on wrong answers**: a short, game-specific strategy
  reminder now shows next to "the answer was X" instead of just the
  correction on its own.

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
