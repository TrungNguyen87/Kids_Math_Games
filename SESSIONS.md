# Session log

A record of each working session on this project: what was asked, what was
actually done, what was found along the way, and what is still open.

The CHANGELOG says *what changed*. This file says *why, and what we learned* —
including the things that turned out to be wrong, so the next session doesn't
rediscover them.

---

## Session 6 — 10 September 2026

**Branch:** `claude/game-deployment-platform-4sln0n`

### Asked

1. Streamlit may not be a good deployment target for interactive, visual,
   animated games. Find a better **free** hosting option that is easy for kids
   to reach and easy to deploy.
2. Migrate all the games to it, improving interaction, animation and
   visualisation along the way.
3. Write a detailed step-by-step deployment guide.

### Decided: GitHub Pages, and a static client-side app

The platform question and the architecture question turned out to be the same
question. The reason Streamlit hurts here is not that its hosting is bad — it
is that **every tap is a server round-trip**, and these games are now animated
and timed. The countdowns had to be faked with `st.fragment(run_every=1)`: one
round-trip per second, stepping a whole second at a time, with the answer
buttons deliberately placed outside the fragment because a rerun landing
between render and click would swallow the tap. That is a lot of care spent
working around the platform rather than on the game.

So the fix is not "host Streamlit somewhere better". It is to make the app
client-side, at which point the hosting question answers itself: any static
host will do, and the cheapest, simplest one is the GitHub the code is already
on.

Cloudflare Pages and Netlify were the real alternatives and would both work.
GitHub Pages won on one specific ground: **it needs nothing new.** No second
account, no second dashboard, no second set of credentials to lose. For a
project maintained in evenings that beats CDN benchmarks. It is also free
without qualification here, because the repository is public.

Three consequences worth stating plainly, since they were the actual decision:

- **No cold start.** Streamlit Community Cloud sleeps an idle app; a child
  opening a bookmark after school would get "this app has gone to sleep".
- **It works offline.** A service worker precaches everything, so the games work
  in the car and at a grandparent's house. This was not possible before at all.
- **Results stop being a server file.** That is a real trade, not a pure win —
  see below.

### Done

**All twelve games, plus home, the explainer and the parent dashboard**, ported
to `web/` as plain ES modules. No build step, no framework, no bundler: what is
in the repository is what the browser runs. Question generators, level curves,
scoring, badges, adaptive difficulty and both languages were ported unchanged —
the Node test suite exists mostly to prove that.

**`utils/i18n.py` stayed the source of truth for copy.** `tools/gen_i18n.py`
parses it with `ast` (no Streamlit import needed) and emits
`web/js/i18n-data.js`, refusing to run if a key exists in one language and not
the other. That is what stopped 473 strings drifting between two front-ends
during the port.

**The interaction work is where the platform move actually pays.** The number
pad is the clearest example: `st.number_input` renders a small desktop spinner
that, on a tablet, summons the OS keyboard over the visual and the question. A
purpose-built pad in the calculator layout children already know is not a
nicer version of that — it is the thing that makes a tablet usable at all.
Similarly: correct answers auto-advance so a child in flow never hunts for
"next" (wrong ones deliberately do not — that is the one moment they need to
read); the fraction explorer is now the pizza itself, tapped slice by slice;
Number Hunt restyles one tile per tap instead of rebuilding twenty buttons.

**Animation and sound got the upgrade the CSS-only version could not have.**
Canvas confetti with gravity and tumble, bursting from the button the child
tapped. A full-screen level-up card, because the old toast was being missed.
Web Audio effects generated at the instant of the tap, including a correct
answer arpeggio that climbs a step for every answer in the streak — a small
thing a child notices within about four answers. All of it still honours
`prefers-reduced-motion`, on every single visual.

**The dashboard charts are hand-written SVG**, which removed pandas and Altair
from the payload. Both are single-measure charts, so both use one hue rather
than a categorical palette — a rainbow of game colours would imply a
distinction that is not in the data. The two hues were checked against the
light and dark surfaces for contrast and lightness rather than picked by eye.

### Found along the way

**Two bugs a test suite would not have caught, both found by looking.**

The first: at phone width, a semi-transparent overlay covered the entire app
and swallowed every tap. The nav scrim's `display: block` inside a
`@media (max-width: 900px)` block silently overrode the built-in
`[hidden] { display: none }`. It was invisible in the desktop screenshots and
the app still *rendered* correctly on a phone — it just could not be used.
Found by noticing that a mobile screenshot looked washed out. The smoke test
now hit-tests the first control at phone width and clicks it, so this class of
bug fails loudly next time.

The second: `Node.append(null)` prints the literal word "null". A conditional
child written as `condition ? el(...) : null` renders as text, because
`append()` stringifies its arguments. It was sitting under the streak counter
in the sidebar on every screenshot. Fixed with a filtering `append()` helper.

Both are worth remembering as a pattern: **the browser will happily render
something wrong rather than throw.** The Node tests caught none of it; a
screenshot caught both.

**A third, smaller one:** headless Chromium will not screenshot at an exact
small size — `--window-size` below ~500px and `--force-device-scale-factor`
below 0.5 are both clamped. Rather than add Pillow for three icons,
`tools/png_tool.py` crops and box-downscales PNGs with nothing but `zlib` and
`struct`.

### The trade being made, stated plainly

**Results are now per device.** The Streamlit version wrote
`logs/all_sessions_log.csv` on the server: one shared history, wiped on every
redeploy. Browser storage is better in three ways — it survives redeploys, it
survives being offline, and no child's data ever leaves their device — and
worse in one: a tablet and a laptop keep separate histories.

The CSV export is therefore prominent on the dashboard rather than at the
bottom, and its columns are byte-identical to the ones `utils/gamelog.py`
wrote, so an old export and a new one open side by side.

This also settles most of `docs/PLATFORM_ROADMAP.md` section 6 for free: no
server, no third party, no analytics, no external fonts or CDNs on any page a
child sees. Worth noting for the roadmap: the classroom platform will still
need a real backend, and nothing here blocks that — the generators, level curve
and objective map are still portable logic, and a static front-end can talk to
an API whenever one exists.

### Still open

- **The Streamlit app was deliberately not deleted.** `app.py`, `pages/` and
  `utils/` still run, and `utils/i18n.py` is still the source of truth for
  copy. Delete the Streamlit half once the web version has been used for a few
  weeks and nothing turns out to be missing — that is a decision to make on
  evidence, not on migration day.
- **Pages has to be switched on once by hand:** Settings → Pages → Source =
  *GitHub Actions*. It cannot be done from a workflow. `docs/DEPLOYMENT.md` §4
  walks through it.
- The parent dashboard shows the last 200 attempts in its table; everything
  older is in the CSV. If a parent ever wants to scroll further, that becomes a
  paging question.
- No per-device sync, by design. If the roadmap's classroom platform happens,
  that is where it belongs — not bolted onto the static app.

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
