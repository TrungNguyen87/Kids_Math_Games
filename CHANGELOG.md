# Changelog

All notable changes to this project are documented in this file.
The format is loosely based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
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
