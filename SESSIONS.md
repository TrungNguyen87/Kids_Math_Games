# Session log

A record of each working session on this project: what was asked, what was
actually done, what was found along the way, and what is still open.

The CHANGELOG says *what changed*. This file says *why, and what we learned* —
including the things that turned out to be wrong, so the next session doesn't
rediscover them.

---

## Session 5 — 9 September 2026

**Branch:** `claude/edu-gaming-platform-plan-2e69e7`

### Asked

1. A development plan and roadmap for a bigger, teacher-facing classroom
   platform: multiple pupil accounts, logged and analysed play, per-child
   development roadmaps, and teacher-built exams — for a teacher with no
   software skills. With milestones and pauses for feedback and brainstorm.
2. Whether animation is possible with Streamlit and the current stack.
3. Find and fix small bugs so deployment runs cleanly.
4. More games — logic games suited to groep 6/7, and fast-response games.
5. Always add a changelog and a session log.

### Done

**1. Classroom platform plan** — `docs/PLATFORM_ROADMAP.md`, and published as
a shareable page for the conversation with the teacher.

Seven phases, six checkpoints, roughly 20 weeks to a pilot review. The
checkpoints are the substance: each one ends in a decision the *teacher*
makes, not a status update. Checkpoint 2 is a login dry run with five
children where the developer is not allowed to help; Checkpoint 4 compares
the mastery model against the teacher's own judgement of six pupils they know
well; Checkpoint 5 is the teacher building an exam alone while the developer
watches in silence.

Three things in the plan are worth carrying forward even if the rest is cut:

- **The learning-objective map is the keystone.** Today a log line records
  which *game* was played. Until it records which *objective* was practised,
  none of the analysis, recommendation or exam features are possible. It is
  the first real piece of work and it needs the teacher in the room.
- **The speed games make a second axis possible.** Accuracy says whether a
  child *can*; response time says whether they can *without thinking*. Both
  are recorded now. A child who is accurate but slow needs different work
  from one who is fast but sloppy, and few classroom tools show a teacher
  both.
- **Privacy is a blocking dependency, not a later chore.** This is data about
  identifiable children in a Dutch school. The plan refuses to start Phase 1
  before the AVG questions have written answers — controller vs. processor,
  verwerkersovereenkomst, DPIA, EU hosting, retention, parental access.

The plan also states plainly that Streamlit is unlikely to hold thirty
concurrent pupils, and schedules that decision — with a load test — at
Checkpoint 5, rather than letting it be discovered when a lesson falls over.

**2. Animation** — yes, and quite a lot of it, with no new dependency.

Two mechanisms, both pure CSS:

- Global keyframes and helper classes in a new `utils/anim.py`, injected once
  per run alongside the existing custom CSS.
- A `<style>` block embedded inside each generated SVG in `utils/visuals.py`,
  with class names scoped to that one render.

Every visual now builds itself rather than appearing complete: pizza slices
fill one at a time, dot arrays pop in row by row, bars grow from zero, clock
hands sweep round, shapes draw their own outline, the balance scale rocks and
settles. Question cards slide up; correct answers pop, wrong ones shake;
level-ups and badges fire confetti.

Four things learned that the next session should not have to rediscover:

- **Streamlit rebuilds the DOM for a markdown block on every rerun**, so a CSS
  animation attached to it restarts from 0% each time. That is what makes all
  of this work without JavaScript — and JavaScript was not an option anyway,
  because Streamlit strips `<script>` out of markdown HTML.
- **Inline SVG shares the page's global CSS scope.** Two pizzas on one page
  with a shared `.slice` class animate each other. Every class and element id
  is therefore prefixed with a per-render unique id, and there is a test for
  it.
- **A CSS `transform` silently replaces an SVG `transform` attribute.** The
  rectangle's height label carries `transform="rotate(90 ...)"`; animating it
  with `translateY` tipped it flat. Labels animate opacity only.
- **Confetti has to be queued, exactly like the sound effects.** A game
  triggers it right before `st.rerun()`, and `st.rerun()` throws away the
  current render before the browser sees it. It is stashed in session state
  and fired on the next run.

Everything is disabled under `prefers-reduced-motion`, showing the finished
picture instead of the movement.

**3. Bugs** — seven fixed. None of them were crashes; the app rendered
cleanly at every level in both languages before this session started. They
were *wrong answers*, which is worse, because a child cannot tell the
difference between a bug and being wrong.

- **Meten is Weten level 2 asked questions with wrong answers.** Decimal
  conversions used `round(value * factor)`, so "0,25 cm = ... mm" expected 2
  (Python rounds 2.5 to even) and "0,75 cm" expected 8. About 6% of level-2
  questions. The true answers were not even typeable in the whole-number
  input.
- **Breuken Baas punished a child for simplifying.** "1/2 + 2/4" expects 4/4;
  a child who worked it out and then reduced to 1/1 — the thing we teach them
  to do — was marked wrong. Grading now cross-multiplies.
- **Meetkunde Meesters could ask for a negative angle.** A rejection-sampling
  loop fell through after 30 tries using the last *rejected* draw.
- `requirements.txt` allowed Streamlit `>=1.37`, but the dashboard needs
  `>=1.49` for `st.dataframe(width="stretch")` — a fresh deploy resolving an
  older version would have crashed on the parent dashboard.
- `use_container_width` is deprecated and slated for removal.
- Verhoudingen could ask about a journey of "3 hours and 0 minutes".
- `speed_diagram_svg` had a hardcoded English "in" and a fixed element id
  that collides if two diagrams share a page.

**How they were found** matters more than the list. Rendering every page at
every level in both languages found *nothing*. Fuzzing the generators and
checking invariants against independently computed answers found all of them.
That approach is now committed as `tests/test_app.py` — 23 tests, runnable
with plain `python tests/test_app.py`.

**4. Four new games**, taking the app from 8 to 12:

| Game | Kind | What it actually trains |
|---|---|---|
| ⚡ Bliksemronde | Speed | Automaticity — recall without calculation |
| 🎯 Getallenjacht | Speed | Number properties from the recognition side |
| 🧠 Logica Lab | Logic | Pattern-finding, deduction, invalid inference |
| 🔐 Code Kraker | Logic | Elimination reasoning, no arithmetic at all |

Design notes worth keeping:

- **The timed games use `st.fragment(run_every=1)` for the clock, with the
  answer buttons outside the fragment.** A button inside an auto-rerunning
  fragment is a race: the rerun can land between the render and the tap, and
  the tap is lost.
- **Timed games adapt their level once per round, not per answer.** Inside a
  60-second round, three quick correct answers are often just three easy
  draws; 9-of-10 across a whole round is a much more honest signal.
- **Logica Lab's if/then questions generate the invalid converse half the
  time** ("All cats are fast; Sofie is fast; is Sofie a cat?"). Answering
  "yes" every time scores 50%, which is the point — that inference is the
  classic slip at this age.
- **Code Kraker's bulls-and-cows scoring is tested against a reference
  implementation over all 4096 secret/guess pairs.** The naive version counts
  a repeated digit twice, and the clues then contradict each other — which a
  child *will* notice, and will reasonably conclude the game is broken.

A shared `utils/gameflow.py` now holds the post-answer sequence the new games
use. The original eight keep their inline version on purpose, so this round's
diff stays reviewable.

### Findings the next session should know

- The app has no crash-level bugs left that this session could find; every
  page renders at every level in both languages, and the 23 tests pass.
- The bugs that ship here are *arithmetic* bugs. Any new question generator
  should get an invariant test that computes the answer a second, independent
  way — not just a "does it render" check.
- `logs/` is still an ephemeral filesystem. Profiles and history survive
  restarts only while the host keeps the disk; the download buttons remain
  the only reliable copy. The roadmap's Phase 1 replaces this with a real
  database and should be done before any classroom pilot.
- `utils/i18n.py` is now 459 keys and about 900 lines. It is still fine as a
  single dict, but if it doubles again it should move to per-language files.

### Still open

- The platform roadmap is a proposal. Nothing in it is built, and Checkpoint 1
  is meant to make it shorter.
- No load test has been run. The claim that Streamlit will struggle with 30
  concurrent pupils is reasoning, not measurement, and the roadmap treats it
  as a question to answer rather than a fact.
- The learning-objective map does not exist yet. It needs the teacher.
- No CI. The tests are committed and runnable but nothing runs them
  automatically on push.

---

## Sessions 1–4 (summarised)

Reconstructed from the CHANGELOG; these predate this file.

- **Session 1** — Adaptive difficulty levels 1–5 for the original four games,
  harder question types aimed at groep 6/7, session logging to CSV, the parent
  dashboard, the player-name field, the NL/EN language switcher, and the
  sidebar session-progress widget.
- **Session 2** — The manual level picker, the inline-SVG visualisation
  library, the interactive fraction explorer, and four new games for the end
  of groep 7 / middle of groep 8: Het X-Mysterie, Meetkunde Meesters,
  Verhoudingen & Snelheid, Getallen Universum.
- **Session 3** — Fixes: the navigation menu now follows the language toggle
  (moved from filename-based pages to an explicit `st.navigation` router); the
  player name actually persists; Tafel Monster's hint no longer gives away the
  answer; more interactive explorers; the cheat sheet extended to all eight
  games.
- **Session 4** — Persistent player profiles, milestone badges, synthesized
  sound effects, a gentler warm-up level 0, and "why" tips on wrong answers.
