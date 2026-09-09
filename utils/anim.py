"""
The app's animation layer - pure CSS keyframes and inline-SVG animation,
no new dependency and no JavaScript (Streamlit strips <script> out of
markdown anyway).

Two things live here:

1. ``animation_css()`` - the global keyframes/utility classes, injected once
   per run from ``utils.ui.set_custom_css``.
2. Small render helpers (``feedback_banner``, ``score_flash``, ``confetti``,
   ``countdown_ring_svg``, ...) that games call instead of hand-writing HTML.

Every animation is wrapped so that a visitor with the OS-level "reduce
motion" accessibility setting on sees the finished state immediately
instead of the movement - some kids (and adults) get motion sick or
distracted, and a maths game should never be the thing that triggers it.

Why re-rendering replays the animations: Streamlit throws away and rebuilds
the DOM for a markdown block on every rerun, so a CSS animation attached to
it starts again from 0% each time a new question is drawn. That is exactly
the behaviour we want here, and it is why none of this needs JS.
"""
import random

import streamlit as st

# Class/keyframe names are all prefixed "kmg" (Kids Math Games) because
# inline SVG and st.markdown HTML share the page's global CSS scope - an
# unprefixed ".pop" would fight with Streamlit's own stylesheet.
_CSS = """
<style>
@keyframes kmgPop {
    0%   { transform: scale(0.55); opacity: 0; }
    55%  { transform: scale(1.12); opacity: 1; }
    75%  { transform: scale(0.96); }
    100% { transform: scale(1); opacity: 1; }
}
@keyframes kmgShake {
    0%, 100% { transform: translateX(0); }
    12%      { transform: translateX(-11px) rotate(-1.5deg); }
    28%      { transform: translateX(10px) rotate(1.5deg); }
    44%      { transform: translateX(-7px) rotate(-1deg); }
    60%      { transform: translateX(6px) rotate(1deg); }
    78%      { transform: translateX(-3px); }
}
@keyframes kmgSlideUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes kmgFadeIn {
    from { opacity: 0; }
    to   { opacity: 1; }
}
@keyframes kmgPulse {
    0%, 100% { transform: scale(1); }
    50%      { transform: scale(1.06); }
}
@keyframes kmgGlow {
    0%, 100% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.55); }
    50%      { box-shadow: 0 0 0 14px rgba(76, 175, 80, 0); }
}
@keyframes kmgFloat {
    0%, 100% { transform: translateY(0); }
    50%      { transform: translateY(-7px); }
}
@keyframes kmgConfettiFall {
    0%   { transform: translateY(-10vh) rotate(0deg); opacity: 1; }
    100% { transform: translateY(105vh) rotate(720deg); opacity: 0; }
}
@keyframes kmgSweep {
    from { transform: translateX(-120%); }
    to   { transform: translateX(220%); }
}

/* --- Feedback banners (replace the plain st.success/st.error boxes) --- */
.kmg-banner {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 16px 20px;
    border-radius: 14px;
    font-size: 1.25rem;
    font-weight: bold;
    margin: 14px 0 6px 0;
    border: 3px solid;
}
.kmg-banner .kmg-banner-icon { font-size: 2.1rem; line-height: 1; }
.kmg-banner-ok {
    background: #e8f5e9;
    border-color: #4caf50;
    color: #1b5e20;
    animation: kmgPop 0.5s cubic-bezier(0.22, 1.2, 0.36, 1) both,
               kmgGlow 1.1s ease-out 0.3s 1;
}
.kmg-banner-ok .kmg-banner-icon { animation: kmgFloat 1.4s ease-in-out 0.5s 2; }
.kmg-banner-bad {
    background: #ffebee;
    border-color: #ef5350;
    color: #b71c1c;
    animation: kmgShake 0.55s cubic-bezier(0.36, 0.07, 0.19, 0.97) both;
}
.kmg-banner-tip {
    display: block;
    font-size: 0.95rem;
    font-weight: normal;
    opacity: 0.85;
    margin-top: 4px;
}

/* --- Score / streak chips --- */
.kmg-score-up {
    animation: kmgPop 0.55s cubic-bezier(0.22, 1.2, 0.36, 1) both;
}
.kmg-streak-flame {
    display: inline-block;
    animation: kmgPulse 0.9s ease-in-out infinite;
}
.kmg-badge-new {
    display: inline-block;
    animation: kmgPop 0.6s cubic-bezier(0.22, 1.2, 0.36, 1) both,
               kmgFloat 1.6s ease-in-out 0.6s infinite;
}

/* --- Question card: each new question slides up into place --- */
.kmg-question {
    animation: kmgSlideUp 0.4s ease-out both;
    position: relative;
    overflow: hidden;
    background: linear-gradient(135deg, #fff8e1 0%, #ffffff 65%);
    border: 3px solid #ffb300;
    border-radius: 16px;
    padding: 18px 22px;
    margin-bottom: 8px;
    font-size: 1.55rem;
    font-weight: bold;
    color: #5d4037;
}
/* A slow light "sheen" travelling across the card - just enough motion to
   make the question feel alive without competing with the numbers on it. */
.kmg-question::after {
    content: "";
    position: absolute;
    top: 0; left: 0;
    width: 45%;
    height: 100%;
    background: linear-gradient(100deg, transparent, rgba(255,255,255,0.75), transparent);
    animation: kmgSweep 2.4s ease-in-out 0.35s 1;
    pointer-events: none;
}

/* --- Level badge gets a gentle pulse right after a level change --- */
.kmg-levelup { animation: kmgPop 0.6s cubic-bezier(0.22, 1.2, 0.36, 1) both, kmgPulse 0.9s ease-in-out 0.6s 2; }

/* --- Confetti overlay --- */
.kmg-confetti-wrap {
    position: fixed;
    inset: 0;
    pointer-events: none;   /* never swallows a click meant for the app */
    overflow: hidden;
    z-index: 999;
}
.kmg-confetti-piece {
    position: absolute;
    top: 0;
    width: 10px;
    height: 14px;
    border-radius: 2px;
    animation-name: kmgConfettiFall;
    animation-timing-function: cubic-bezier(0.3, 0.1, 0.6, 1);
    animation-fill-mode: forwards;
    animation-iteration-count: 1;
}

/* --- Timed games: the clock bar turns from green to red as time runs out --- */
.kmg-timer-wrap {
    background: #eceff1;
    border: 3px solid #5d4037;
    border-radius: 999px;
    height: 26px;
    overflow: hidden;
    margin-bottom: 6px;
}
.kmg-timer-fill {
    height: 100%;
    border-radius: 999px;
    transition: width 0.95s linear, background-color 0.95s linear;
}
.kmg-timer-low { animation: kmgPulse 0.6s ease-in-out infinite; }

/* --- Tap targets in the grid games --- */
.kmg-hit  { animation: kmgPop 0.4s cubic-bezier(0.22, 1.2, 0.36, 1) both; }
.kmg-miss { animation: kmgShake 0.45s both; }

/* Honour the OS "reduce motion" setting: show the end state, skip the
   movement. The decorative sheen and confetti are hidden outright. */
@media (prefers-reduced-motion: reduce) {
    .kmg-banner-ok, .kmg-banner-bad, .kmg-banner-ok .kmg-banner-icon,
    .kmg-score-up, .kmg-streak-flame, .kmg-badge-new, .kmg-question,
    .kmg-levelup, .kmg-hit, .kmg-miss, .kmg-timer-low {
        animation: none !important;
    }
    .kmg-question::after, .kmg-confetti-wrap { display: none !important; }
    .kmg-timer-fill { transition: none !important; }
}
</style>
"""

CONFETTI_COLORS = ["#ff4b4b", "#ffb300", "#4caf50", "#42a5f5", "#ab47bc", "#ff7043"]


def animation_css():
    """The global keyframes + helper classes. Injected once per run by
    utils.ui.set_custom_css()."""
    return _CSS


def question_card(text, emoji=""):
    """Render the current question in an animated card. Each new question
    slides up and gets a one-off light sweep, so it's obvious at a glance
    that the question actually changed - with plain st.markdown, a new
    question of the same shape ("6 x 7?" -> "6 x 8?") is easy to miss."""
    prefix = f"{emoji} " if emoji else ""
    st.markdown(
        f'<div class="kmg-question">{prefix}{text}</div>',
        unsafe_allow_html=True,
    )


def feedback_banner(kind, message, tip=None, icon=None):
    """Animated replacement for st.success()/st.error(): a green banner that
    pops in for a correct answer, a red one that shakes for a wrong one."""
    ok = kind == "success"
    css_class = "kmg-banner-ok" if ok else "kmg-banner-bad"
    icon = icon if icon is not None else ("🎉" if ok else "💪")
    tip_html = f'<span class="kmg-banner-tip">{tip}</span>' if tip else ""
    st.markdown(
        f'<div class="kmg-banner {css_class}">'
        f'<span class="kmg-banner-icon">{icon}</span>'
        f"<span>{message}{tip_html}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


def confetti(pieces=34):
    """A short burst of falling confetti. Pure CSS: the overlay is
    pointer-events:none and every piece ends at opacity 0, so once the
    animation is done the element is inert and invisible."""
    bits = []
    for _ in range(pieces):
        left = random.uniform(0, 100)
        delay = random.uniform(0, 0.5)
        duration = random.uniform(1.6, 2.9)
        color = random.choice(CONFETTI_COLORS)
        size = random.randint(7, 13)
        bits.append(
            f'<div class="kmg-confetti-piece" style="left:{left:.1f}%;'
            f"width:{size}px;height:{size + 4}px;background:{color};"
            f'animation-duration:{duration:.2f}s;animation-delay:{delay:.2f}s"></div>'
        )
    st.markdown(f'<div class="kmg-confetti-wrap">{"".join(bits)}</div>', unsafe_allow_html=True)


def timer_bar(remaining, total, label=""):
    """A countdown bar that shrinks and shifts green -> amber -> red. Used by
    the timed games; the width/colour transition is CSS, so the bar keeps
    gliding smoothly between the once-per-second reruns instead of jumping."""
    total = max(1e-9, total)
    frac = max(0.0, min(1.0, remaining / total))
    if frac > 0.5:
        color = "#4caf50"
    elif frac > 0.25:
        color = "#ffb300"
    else:
        color = "#ef5350"
    low = " kmg-timer-low" if frac <= 0.25 else ""
    st.markdown(
        f'<div class="kmg-timer-wrap{low}">'
        f'<div class="kmg-timer-fill" style="width:{frac * 100:.1f}%;background:{color}"></div>'
        f"</div>"
        f'<div style="text-align:center;font-weight:bold;font-size:1.1rem">{label}</div>',
        unsafe_allow_html=True,
    )


def countdown_ring_svg(remaining, total, size=110):
    """A circular countdown dial - the same information as timer_bar() but
    compact enough to sit next to a question. The sweep is done with
    stroke-dasharray so it needs no JS tick."""
    total = max(1e-9, total)
    frac = max(0.0, min(1.0, remaining / total))
    r = size / 2 - 9
    circumference = 2 * 3.141592653589793 * r
    offset = circumference * (1 - frac)
    color = "#4caf50" if frac > 0.5 else ("#ffb300" if frac > 0.25 else "#ef5350")
    return f"""<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
        <circle cx="{size/2}" cy="{size/2}" r="{r}" fill="#fff" stroke="#eceff1" stroke-width="9"/>
        <circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="{color}" stroke-width="9"
                stroke-linecap="round" stroke-dasharray="{circumference:.1f}"
                stroke-dashoffset="{offset:.1f}"
                transform="rotate(-90 {size/2} {size/2})"
                style="transition: stroke-dashoffset 0.95s linear, stroke 0.95s linear"/>
        <text x="{size/2}" y="{size/2 + 9}" text-anchor="middle" font-size="26" font-weight="bold"
              fill="#5d4037">{int(remaining)}</text>
    </svg>"""


def score_flash(score, streak, score_label, streak_label):
    """The sidebar score box, popping once whenever the score actually goes
    up. The previous score is remembered in session state so the animation
    fires on a scoring answer only, not on every single rerun (a box that
    bounces when you merely switch language is just noise)."""
    previous = st.session_state.get("_anim_prev_score")
    gained = previous is not None and score > previous
    st.session_state["_anim_prev_score"] = score
    pop = " kmg-score-up" if gained else ""
    flame = '<span class="kmg-streak-flame">🔥</span>' if streak >= 3 else "🔥"
    delta = (
        f'<div style="font-size:1.05rem;color:#2e7d32">+{score - previous}</div>'
        if gained
        else ""
    )
    st.markdown(
        f'<div class="score-container{pop}">'
        f"🌟 <strong>{score_label}: {score}</strong><br>"
        f"{flame} <strong>{streak_label}: {streak}</strong>"
        f"{delta}"
        f"</div>",
        unsafe_allow_html=True,
    )


# Confetti has to be queued rather than rendered on the spot, for the same
# reason the sound effects are (see utils/sound.py): a game calls this right
# before st.rerun(), and st.rerun() throws away the current render before the
# browser ever sees it. play_pending_celebration() pops the flag on the next
# run, so the burst fires exactly once.
def queue_celebration():
    st.session_state["_pending_celebration"] = True


def play_pending_celebration(pieces=34):
    if st.session_state.pop("_pending_celebration", False):
        confetti(pieces)
