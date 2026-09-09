"""
Small SVG visualization library used across the games. Every function
returns a plain SVG string (rendered with st.markdown(..., unsafe_allow_html=True))
so kids get an immediate visual for the math they're working with, instead
of just numbers on a screen.

The visuals are *animated*: pizza slices fill one by one, dot arrays pop in
row by row, bars grow from zero, clock hands sweep round, shapes draw their
own outline. That is done with a small <style> block embedded inside each
SVG (see _anim_style) rather than with SMIL or JavaScript, so it needs no
dependency and keeps working inside Streamlit's markdown renderer.

Two rules everything here follows:

* Class names are scoped with a per-render unique id. Inline SVG shares the
  page's global CSS scope, so two pizzas on one page with a shared ".slice"
  class would animate each other.
* Every animation ends on the finished picture and is disabled wholesale
  under prefers-reduced-motion, so the visual is never *only* legible while
  it is moving.
"""
import itertools
import math

from utils.i18n import t

# Monotonic counter used to scope each SVG's CSS classes and element ids to
# that one render (see the module docstring).
_uid_counter = itertools.count()


def _uid():
    return f"k{next(_uid_counter):x}"


def _anim_style(uid, rules, reduced=None):
    """A <style> block for one SVG, with a prefers-reduced-motion escape
    hatch that switches every animated element to its finished state."""
    reduced = reduced or f"#{uid} * {{ animation: none !important; }}"
    return (
        "<style>"
        f"{rules}"
        f"@media (prefers-reduced-motion: reduce) {{ {reduced} }}"
        "</style>"
    )

# A warm, consistent, kid-friendly palette used across every visual.
FILL = "#ffb74d"
EMPTY = "#fff3e0"
STROKE = "#5d4037"
ACCENT = "#4caf50"
ACCENT2 = "#42a5f5"
DANGER = "#ef5350"


def _polar(cx, cy, r, angle_deg):
    a = math.radians(angle_deg)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def pizza_svg(numerator, denominator, size=180):
    """A pizza cut into `denominator` equal slices, `numerator` of them
    filled. Great for fractions <= ~12 pieces; for more pieces use
    fraction_bar_svg instead (a pizza that thin is hard to read)."""
    denominator = max(1, int(denominator))
    numerator = max(0, min(int(numerator), denominator))
    uid = _uid()
    cx = cy = size / 2
    r = size / 2 - 6
    parts = []
    # The filled slices are laid down one after another so a child literally
    # watches "3 of the 8 pieces" being counted out, instead of the whole
    # fraction appearing at once.
    for i in range(denominator):
        a0 = -90 + i * (360 / denominator)
        a1 = -90 + (i + 1) * (360 / denominator)
        x0, y0 = _polar(cx, cy, r, a0)
        x1, y1 = _polar(cx, cy, r, a1)
        large_arc = 1 if (360 / denominator) > 180 else 0
        filled = i < numerator
        color = FILL if filled else EMPTY
        d = f"M {cx},{cy} L {x0:.2f},{y0:.2f} A {r},{r} 0 {large_arc} 1 {x1:.2f},{y1:.2f} Z"
        cls = f"{uid}-fill" if filled else f"{uid}-empty"
        delay = 0.06 * i if filled else 0.0
        parts.append(
            f'<path class="{cls}" style="animation-delay:{delay:.2f}s" d="{d}" '
            f'fill="{color}" stroke="{STROKE}" stroke-width="2"/>'
        )
    pct = round(100 * numerator / denominator)
    label = f"{numerator}/{denominator} = {pct}%"
    style = _anim_style(
        uid,
        f"@keyframes {uid}slice {{ from {{ opacity:0; transform:scale(0.35); }} "
        f"to {{ opacity:1; transform:scale(1); }} }}"
        f"@keyframes {uid}base {{ from {{ opacity:0; }} to {{ opacity:1; }} }}"
        f".{uid}-fill {{ transform-origin:{cx}px {cy}px; "
        f"animation:{uid}slice 0.34s cubic-bezier(0.22,1.2,0.36,1) both; }}"
        f".{uid}-empty {{ animation:{uid}base 0.3s ease-out both; }}",
    )
    return f"""<svg id="{uid}" width="{size}" height="{size + 34}" viewBox="0 0 {size} {size + 34}" xmlns="http://www.w3.org/2000/svg">
        {style}
        {''.join(parts)}
        <text x="{cx}" y="{size + 24}" text-anchor="middle" font-size="18" font-weight="bold" fill="{STROKE}">{label}</text>
    </svg>"""


def fraction_bar_svg(numerator, denominator, width=280, height=50):
    """A row of `denominator` equal blocks, `numerator` filled. Used for
    fractions with too many pieces to show clearly as a pizza."""
    denominator = max(1, int(denominator))
    numerator = max(0, min(int(numerator), denominator))
    uid = _uid()
    gap = 3
    block_w = (width - gap * (denominator - 1)) / denominator
    blocks = []
    for i in range(denominator):
        x = i * (block_w + gap)
        filled = i < numerator
        color = FILL if filled else EMPTY
        cls = f"{uid}-fill" if filled else f"{uid}-empty"
        delay = 0.05 * i if filled else 0.0
        blocks.append(
            f'<rect class="{cls}" style="animation-delay:{delay:.2f}s;transform-origin:{x + block_w / 2:.1f}px {height / 2:.1f}px" '
            f'x="{x:.1f}" y="0" width="{block_w:.1f}" height="{height}" fill="{color}" stroke="{STROKE}" stroke-width="2" rx="4"/>'
        )
    pct = round(100 * numerator / denominator)
    style = _anim_style(
        uid,
        f"@keyframes {uid}blk {{ 0% {{ opacity:0; transform:scaleY(0.15); }} "
        f"70% {{ opacity:1; transform:scaleY(1.12); }} 100% {{ transform:scaleY(1); }} }}"
        f"@keyframes {uid}base {{ from {{ opacity:0; }} to {{ opacity:1; }} }}"
        f".{uid}-fill {{ animation:{uid}blk 0.3s ease-out both; }}"
        f".{uid}-empty {{ animation:{uid}base 0.3s ease-out both; }}",
    )
    return f"""<svg id="{uid}" width="{width}" height="{height + 30}" viewBox="0 0 {width} {height + 30}" xmlns="http://www.w3.org/2000/svg">
        {style}
        {''.join(blocks)}
        <text x="{width / 2}" y="{height + 22}" text-anchor="middle" font-size="16" font-weight="bold" fill="{STROKE}">{numerator}/{denominator} = {pct}%</text>
    </svg>"""


def fraction_visual_svg(numerator, denominator):
    """Picks a pizza for small denominators, a bar for larger ones."""
    if denominator <= 12:
        return pizza_svg(numerator, denominator)
    return fraction_bar_svg(numerator, denominator)


def percent_bar_svg(percent, width=280, height=44, label=None):
    """A horizontal fill bar (0-100%) with 25% gridlines."""
    percent = max(0, min(100, percent))
    uid = _uid()
    fill_w = width * percent / 100
    ticks = "".join(
        f'<line x1="{width * p / 100:.1f}" y1="0" x2="{width * p / 100:.1f}" y2="{height}" stroke="{STROKE}" stroke-width="1" stroke-dasharray="3,3"/>'
        for p in (25, 50, 75)
    )
    text = label if label is not None else f"{percent}%"
    # The bar fills left-to-right so the percentage is seen being "poured
    # in" up to its mark, rather than just appearing at that length.
    style = _anim_style(
        uid,
        f"@keyframes {uid}grow {{ from {{ transform:scaleX(0); }} to {{ transform:scaleX(1); }} }}"
        f".{uid}-bar {{ transform-origin:0 0; animation:{uid}grow 0.75s cubic-bezier(0.25,0.9,0.35,1) both; }}",
        reduced=f".{uid}-bar {{ animation:none !important; transform:scaleX(1); }}",
    )
    return f"""<svg id="{uid}" width="{width}" height="{height + 26}" viewBox="0 0 {width} {height + 26}" xmlns="http://www.w3.org/2000/svg">
        {style}
        <rect x="0" y="0" width="{width}" height="{height}" fill="{EMPTY}" stroke="{STROKE}" stroke-width="2" rx="6"/>
        <rect class="{uid}-bar" x="0" y="0" width="{fill_w:.1f}" height="{height}" fill="{ACCENT}" rx="6"/>
        {ticks}
        <text x="{width / 2}" y="{height + 20}" text-anchor="middle" font-size="16" font-weight="bold" fill="{STROKE}">{text}</text>
    </svg>"""


def array_grid_svg(a, b, max_dots=100, dot_r=7, gap=22):
    """A rows-x-cols dot array for multiplication (a x b). Falls back to a
    labeled grid outline (no individual dots) when a*b is too big to read."""
    a, b = int(a), int(b)
    if a * b <= max_dots:
        uid = _uid()
        width = b * gap
        height = a * gap
        dots = []
        # Dots pop in row by row, which is the whole point of an array
        # picture: "a rows of b" is something you watch being built up.
        for row in range(a):
            for col in range(b):
                cx = col * gap + gap / 2
                cy = row * gap + gap / 2
                delay = 0.09 * row + 0.02 * col
                dots.append(
                    f'<circle class="{uid}-dot" style="animation-delay:{delay:.2f}s;transform-origin:{cx}px {cy}px" '
                    f'cx="{cx}" cy="{cy}" r="{dot_r}" fill="{FILL}" stroke="{STROKE}" stroke-width="1.5"/>'
                )
        style = _anim_style(
            uid,
            f"@keyframes {uid}dot {{ 0% {{ opacity:0; transform:scale(0); }} "
            f"65% {{ opacity:1; transform:scale(1.35); }} 100% {{ transform:scale(1); }} }}"
            f".{uid}-dot {{ animation:{uid}dot 0.32s cubic-bezier(0.22,1.2,0.36,1) both; }}",
        )
        return f"""<svg id="{uid}" width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
            {style}
            {''.join(dots)}
        </svg>"""

    # Too many for individual dots: draw a labeled grid rectangle instead.
    width, height = 220, 140
    cols_shown, rows_shown = min(b, 10), min(a, 10)
    cell_w, cell_h = width / cols_shown, height / rows_shown
    lines = []
    for i in range(1, cols_shown):
        x = i * cell_w
        lines.append(f'<line x1="{x:.1f}" y1="0" x2="{x:.1f}" y2="{height}" stroke="{STROKE}" stroke-width="1" opacity="0.5"/>')
    for i in range(1, rows_shown):
        y = i * cell_h
        lines.append(f'<line x1="0" y1="{y:.1f}" x2="{width}" y2="{y:.1f}" stroke="{STROKE}" stroke-width="1" opacity="0.5"/>')
    return f"""<svg width="{width}" height="{height + 26}" viewBox="0 0 {width} {height + 26}" xmlns="http://www.w3.org/2000/svg">
        <rect x="0" y="0" width="{width}" height="{height}" fill="{EMPTY}" stroke="{STROKE}" stroke-width="2" rx="6"/>
        {''.join(lines)}
        <text x="{width / 2}" y="{height + 20}" text-anchor="middle" font-size="16" font-weight="bold" fill="{STROKE}">{a} &#215; {b}</text>
    </svg>"""


def clock_svg(hour, minute, size=140, highlight=ACCENT2):
    """An analog clock face showing the given time."""
    cx = cy = size / 2
    r = size / 2 - 8
    ticks = []
    for i in range(12):
        angle = i * 30
        x0, y0 = _polar(cx, cy, r, angle)
        x1, y1 = _polar(cx, cy, r - 8, angle)
        ticks.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{STROKE}" stroke-width="2"/>')
    uid = _uid()
    hour_angle = ((hour % 12) + minute / 60) * 30 - 90
    minute_angle = minute * 6 - 90
    hx, hy = _polar(cx, cy, r * 0.5, hour_angle)
    mx, my = _polar(cx, cy, r * 0.8, minute_angle)
    label = f"{hour:02d}:{minute:02d}"
    # Both hands are drawn at their final position and then rotated back to
    # 12 o'clock at the start of the animation, so they sweep round to the
    # time being asked about. Winding the minute hand a full extra turn
    # makes the "time passing" idea read at a glance.
    hour_from = -(hour_angle + 90)
    minute_from = -(minute_angle + 90) - 360
    style = _anim_style(
        uid,
        f"@keyframes {uid}h {{ from {{ transform:rotate({hour_from:.1f}deg); }} to {{ transform:rotate(0deg); }} }}"
        f"@keyframes {uid}m {{ from {{ transform:rotate({minute_from:.1f}deg); }} to {{ transform:rotate(0deg); }} }}"
        f".{uid}-hand {{ transform-origin:{cx}px {cy}px; }}"
        f".{uid}-h {{ animation:{uid}h 0.9s cubic-bezier(0.3,0.9,0.3,1) both; }}"
        f".{uid}-m {{ animation:{uid}m 0.9s cubic-bezier(0.3,0.9,0.3,1) both; }}",
    )
    return f"""<svg id="{uid}" width="{size}" height="{size + 26}" viewBox="0 0 {size} {size + 26}" xmlns="http://www.w3.org/2000/svg">
        {style}
        <circle cx="{cx}" cy="{cy}" r="{r}" fill="{EMPTY}" stroke="{STROKE}" stroke-width="3"/>
        {''.join(ticks)}
        <line class="{uid}-hand {uid}-h" x1="{cx}" y1="{cy}" x2="{hx:.1f}" y2="{hy:.1f}" stroke="{STROKE}" stroke-width="4" stroke-linecap="round"/>
        <line class="{uid}-hand {uid}-m" x1="{cx}" y1="{cy}" x2="{mx:.1f}" y2="{my:.1f}" stroke="{highlight}" stroke-width="3" stroke-linecap="round"/>
        <circle cx="{cx}" cy="{cy}" r="4" fill="{STROKE}"/>
        <text x="{cx}" y="{size + 18}" text-anchor="middle" font-size="16" font-weight="bold" fill="{STROKE}">{label}</text>
    </svg>"""


def tape_diagram_svg(total, part, width=280, height=46, total_label=None, part_label=None, rest_label=None):
    """A bar-model / tape diagram: a full bar of `total`, with `part`
    marked off at the front. Used for money (paid vs. price -> change) and
    part-whole measurement questions."""
    total = max(1e-9, total)
    part = max(0, min(part, total))
    part_w = width * part / total
    uid = _uid()
    total_label = total_label if total_label is not None else f"{total:g}"
    part_label = part_label if part_label is not None else f"{part:g}"
    rest_label = rest_label if rest_label is not None else f"{total - part:g}"
    style = _anim_style(
        uid,
        f"@keyframes {uid}grow {{ from {{ transform:scaleX(0); }} to {{ transform:scaleX(1); }} }}"
        f"@keyframes {uid}slide {{ from {{ opacity:0; }} to {{ opacity:1; }} }}"
        f".{uid}-part {{ transform-origin:0 0; animation:{uid}grow 0.6s cubic-bezier(0.25,0.9,0.35,1) both; }}"
        f".{uid}-cut {{ animation:{uid}slide 0.3s ease-out 0.55s both; }}",
        reduced=f".{uid}-part {{ animation:none !important; transform:scaleX(1); }} "
        f".{uid}-cut {{ animation:none !important; opacity:1; }}",
    )
    return f"""<svg id="{uid}" width="{width}" height="{height + 46}" viewBox="0 0 {width} {height + 46}" xmlns="http://www.w3.org/2000/svg">
        {style}
        <rect x="0" y="20" width="{width}" height="{height}" fill="{EMPTY}" stroke="{STROKE}" stroke-width="2" rx="6"/>
        <rect class="{uid}-part" x="0" y="20" width="{part_w:.1f}" height="{height}" fill="{ACCENT2}" rx="6"/>
        <line class="{uid}-cut" x1="{part_w:.1f}" y1="14" x2="{part_w:.1f}" y2="{height + 26}" stroke="{STROKE}" stroke-width="2" stroke-dasharray="4,3"/>
        <text x="{width / 2}" y="14" text-anchor="middle" font-size="14" fill="{STROKE}">{t('visual.total')}: {total_label}</text>
        <text x="{max(24, part_w / 2):.1f}" y="{20 + height / 2 + 5}" text-anchor="middle" font-size="14" font-weight="bold" fill="#ffffff">{part_label}</text>
        <text x="{part_w + max(24, (width - part_w) / 2):.1f}" y="{20 + height / 2 + 5}" text-anchor="middle" font-size="14" font-weight="bold" fill="{STROKE}">{rest_label}</text>
    </svg>"""


def ratio_bar_svg(parts, colors=None, width=280, height=46, labels=None):
    """A bar split into proportional segments, one per ratio part."""
    total = sum(parts) or 1
    uid = _uid()
    colors = colors or [FILL, ACCENT2, ACCENT, DANGER, "#ab47bc"]
    segments = []
    x = 0.0
    # Segments unroll one after another, so a ratio reads as "this much,
    # then this much" rather than as a single pre-split bar.
    for i, p in enumerate(parts):
        w = width * p / total
        color = colors[i % len(colors)]
        delay = 0.11 * i
        segments.append(
            f'<rect class="{uid}-seg" style="animation-delay:{delay:.2f}s;transform-origin:{x:.1f}px 0" '
            f'x="{x:.1f}" y="0" width="{w:.1f}" height="{height}" fill="{color}" stroke="{STROKE}" stroke-width="2"/>'
        )
        label = labels[i] if labels else str(p)
        segments.append(
            f'<text class="{uid}-lbl" style="animation-delay:{delay + 0.2:.2f}s" '
            f'x="{x + w / 2:.1f}" y="{height / 2 + 5}" text-anchor="middle" font-size="14" font-weight="bold" fill="#ffffff">{label}</text>'
        )
        x += w
    style = _anim_style(
        uid,
        f"@keyframes {uid}seg {{ from {{ transform:scaleX(0); }} to {{ transform:scaleX(1); }} }}"
        f"@keyframes {uid}lbl {{ from {{ opacity:0; }} to {{ opacity:1; }} }}"
        f".{uid}-seg {{ animation:{uid}seg 0.36s cubic-bezier(0.25,0.9,0.35,1) both; }}"
        f".{uid}-lbl {{ animation:{uid}lbl 0.25s ease-out both; }}",
        reduced=f".{uid}-seg {{ animation:none !important; transform:scaleX(1); }} "
        f".{uid}-lbl {{ animation:none !important; opacity:1; }}",
    )
    return f"""<svg id="{uid}" width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
        {style}
        {''.join(segments)}
    </svg>"""


def balance_scale_svg(left_text, right_text, balanced=True, width=280, height=170):
    """A simple see-saw balance scale visualizing an equation: left side
    text vs right side text, level when `balanced` is True."""
    tilt = 0 if balanced else 10
    cx = width / 2
    fulcrum_y = height * 0.55
    beam_half = width * 0.36
    angle = math.radians(tilt)
    lx = cx - beam_half * math.cos(angle)
    ly = fulcrum_y - beam_half * math.sin(angle)
    rx = cx + beam_half * math.cos(angle)
    ry = fulcrum_y + beam_half * math.sin(angle)
    pan_r = 34
    uid = _uid()
    # The whole beam rocks and settles level, the way a real balance does -
    # a small piece of motion that says "these two sides are equal", which
    # is the entire idea behind solving for x.
    style = _anim_style(
        uid,
        f"@keyframes {uid}rock {{ 0% {{ transform:rotate(-7deg); }} 35% {{ transform:rotate(4.5deg); }} "
        f"60% {{ transform:rotate(-2.5deg); }} 82% {{ transform:rotate(1.2deg); }} 100% {{ transform:rotate(0deg); }} }}"
        f".{uid}-beam {{ transform-origin:{cx}px {fulcrum_y}px; "
        f"animation:{uid}rock 1.5s cubic-bezier(0.4,0.05,0.3,1) both; }}",
        reduced=f".{uid}-beam {{ animation:none !important; transform:rotate(0deg); }}",
    )
    return f"""<svg id="{uid}" width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
        {style}
        <polygon points="{cx-14},{height-20} {cx+14},{height-20} {cx},{fulcrum_y}" fill="{STROKE}"/>
        <g class="{uid}-beam">
        <line x1="{lx:.1f}" y1="{ly:.1f}" x2="{rx:.1f}" y2="{ry:.1f}" stroke="{STROKE}" stroke-width="5"/>
        <line x1="{lx:.1f}" y1="{ly:.1f}" x2="{lx:.1f}" y2="{ly+40:.1f}" stroke="{STROKE}" stroke-width="2"/>
        <line x1="{rx:.1f}" y1="{ry:.1f}" x2="{rx:.1f}" y2="{ry+40:.1f}" stroke="{STROKE}" stroke-width="2"/>
        <ellipse cx="{lx:.1f}" cy="{ly+44:.1f}" rx="{pan_r}" ry="12" fill="{FILL}" stroke="{STROKE}" stroke-width="2"/>
        <ellipse cx="{rx:.1f}" cy="{ry+44:.1f}" rx="{pan_r}" ry="12" fill="{ACCENT2}" stroke="{STROKE}" stroke-width="2"/>
        <text x="{lx:.1f}" y="{ly+40:.1f}" text-anchor="middle" font-size="16" font-weight="bold" fill="{STROKE}">{left_text}</text>
        <text x="{rx:.1f}" y="{ry+40:.1f}" text-anchor="middle" font-size="16" font-weight="bold" fill="{STROKE}">{right_text}</text>
        </g>
    </svg>"""


def number_line_svg(lo, hi, points, width=320, height=90):
    """A number line from lo to hi with one or more labeled/colored points,
    e.g. [(value, color, label)], plus an arrow between the first two
    points if given (used to show a +/- jump)."""
    lo, hi = int(lo), int(hi)
    span = max(1, hi - lo)
    margin = 20
    usable = width - 2 * margin

    def x_of(v):
        return margin + usable * (v - lo) / span

    y = height * 0.45
    ticks = []
    step = max(1, span // 10)
    v = lo
    while v <= hi:
        x = x_of(v)
        ticks.append(f'<line x1="{x:.1f}" y1="{y-6}" x2="{x:.1f}" y2="{y+6}" stroke="{STROKE}" stroke-width="1.5"/>')
        if v % (step * 2 if step >= 1 else 1) == 0 or span <= 12:
            ticks.append(f'<text x="{x:.1f}" y="{y+22}" text-anchor="middle" font-size="11" fill="{STROKE}">{v}</text>')
        v += step

    uid = _uid()
    markers = []
    colors = [ACCENT2, ACCENT, DANGER]
    # Markers drop onto the line and bounce, so the eye is pulled to where
    # on the line the starting number actually sits.
    for i, (val, label) in enumerate(points):
        x = x_of(val)
        color = colors[i % len(colors)]
        delay = 0.35 + 0.18 * i
        markers.append(
            f'<circle class="{uid}-mark" style="animation-delay:{delay:.2f}s;transform-origin:{x:.1f}px {y}px" '
            f'cx="{x:.1f}" cy="{y}" r="7" fill="{color}" stroke="{STROKE}" stroke-width="2"/>'
        )
        markers.append(
            f'<text class="{uid}-mark" style="animation-delay:{delay + 0.08:.2f}s;transform-origin:{x:.1f}px {y-14}px" '
            f'x="{x:.1f}" y="{y-14}" text-anchor="middle" font-size="13" font-weight="bold" fill="{color}">{label}</text>'
        )

    style = _anim_style(
        uid,
        f"@keyframes {uid}draw {{ from {{ transform:scaleX(0); }} to {{ transform:scaleX(1); }} }}"
        f"@keyframes {uid}drop {{ 0% {{ opacity:0; transform:translateY(-20px) scale(0.5); }} "
        f"70% {{ opacity:1; transform:translateY(2px) scale(1.2); }} 100% {{ transform:translateY(0) scale(1); }} }}"
        f".{uid}-axis {{ transform-origin:{margin}px {y}px; animation:{uid}draw 0.45s ease-out both; }}"
        f".{uid}-mark {{ animation:{uid}drop 0.4s cubic-bezier(0.22,1.2,0.36,1) both; }}",
        reduced=f".{uid}-axis {{ animation:none !important; transform:scaleX(1); }} "
        f".{uid}-mark {{ animation:none !important; opacity:1; transform:none; }}",
    )
    return f"""<svg id="{uid}" width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
        {style}
        <line class="{uid}-axis" x1="{margin}" y1="{y}" x2="{width-margin}" y2="{y}" stroke="{STROKE}" stroke-width="2"/>
        {''.join(ticks)}
        {''.join(markers)}
    </svg>"""


def skip_count_svg(step, target, width=320, height=100):
    """A skip-counting number line: ticks at 0, step, 2*step, 3*step, ...
    up to just past `target`, with the target highlighted. Used as a
    *guidance* hint for missing-factor/division problems - it requires the
    child to count how many hops it takes to reach the target themselves,
    rather than printing the missing factor (the answer) directly."""
    step = max(1, int(step))
    target = max(step, int(target))
    hops_to_target = target // step
    n_hops = min(hops_to_target + 1, 14)
    margin = 26
    usable = width - 2 * margin
    y = height * 0.45

    def x_of(i):
        return margin + usable * i / n_hops

    uid = _uid()
    ticks = []
    hop_arcs = []
    # Each hop is revealed in turn, and an arc is drawn from the previous
    # tick to it - a child counting the hops sees them appear at counting
    # speed, which is the point of the hint (it still never shows the
    # answer, only the hops they have to count themselves).
    for i in range(n_hops + 1):
        value = i * step
        x = x_of(i)
        is_target = value == target
        color = DANGER if is_target else STROKE
        r = 6 if is_target else 4
        delay = 0.16 * i
        if i > 0:
            xp = x_of(i - 1)
            arc = f"M {xp:.1f},{y} Q {(xp + x) / 2:.1f},{y - 26} {x:.1f},{y}"
            hop_arcs.append(
                f'<path class="{uid}-hop" style="animation-delay:{delay - 0.1:.2f}s" d="{arc}" '
                f'fill="none" stroke="{ACCENT2}" stroke-width="2" stroke-dasharray="3,3"/>'
            )
        grp = [
            f'<line x1="{x:.1f}" y1="{y-8}" x2="{x:.1f}" y2="{y+8}" stroke="{STROKE}" stroke-width="1.5"/>',
            f'<circle cx="{x:.1f}" cy="{y}" r="{r}" fill="{color}"/>',
            f'<text x="{x:.1f}" y="{y+24}" text-anchor="middle" font-size="12" font-weight="{"bold" if is_target else "normal"}" fill="{color}">{value}</text>',
        ]
        if is_target:
            grp.append(f'<text x="{x:.1f}" y="{y-16}" text-anchor="middle" font-size="16">&#128681;</text>')
        ticks.append(
            f'<g class="{uid}-tick" style="animation-delay:{delay:.2f}s;transform-origin:{x:.1f}px {y}px">'
            + "".join(grp)
            + "</g>"
        )

    style = _anim_style(
        uid,
        f"@keyframes {uid}tick {{ 0% {{ opacity:0; transform:scale(0.4); }} "
        f"70% {{ opacity:1; transform:scale(1.2); }} 100% {{ transform:scale(1); }} }}"
        f"@keyframes {uid}hop {{ from {{ opacity:0; }} to {{ opacity:1; }} }}"
        f".{uid}-tick {{ animation:{uid}tick 0.28s cubic-bezier(0.22,1.2,0.36,1) both; }}"
        f".{uid}-hop {{ animation:{uid}hop 0.22s ease-out both; }}",
        reduced=f"#{uid} * {{ animation:none !important; opacity:1; transform:none; }}",
    )
    return f"""<svg id="{uid}" width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
        {style}
        <line x1="{margin}" y1="{y}" x2="{x_of(n_hops):.1f}" y2="{y}" stroke="{STROKE}" stroke-width="2"/>
        {''.join(hop_arcs)}
        {''.join(ticks)}
    </svg>"""


def rectangle_svg(w, h, unit="", width=260, height=180):
    """A labeled rectangle for perimeter/area questions."""
    pad = 40
    max_w, max_h = width - 2 * pad, height - 2 * pad
    scale = min(max_w / w, max_h / h)
    rw, rh = w * scale, h * scale
    x0, y0 = (width - rw) / 2, (height - rh) / 2 - 10
    uid = _uid()
    # The outline draws itself (stroke-dashoffset) and the fill washes in
    # behind it, so the shape is "constructed" rather than stamped down.
    perimeter = 2 * (rw + rh) + 24
    style = _anim_style(
        uid,
        f"@keyframes {uid}draw {{ from {{ stroke-dashoffset:{perimeter:.0f}; }} to {{ stroke-dashoffset:0; }} }}"
        f"@keyframes {uid}wash {{ from {{ opacity:0; }} to {{ opacity:1; }} }}"
        # Opacity only, never transform: the height label carries its own
        # SVG rotate() attribute and a CSS transform would silently replace
        # it, tipping the label back flat.
        f"@keyframes {uid}lbl {{ from {{ opacity:0; }} to {{ opacity:1; }} }}"
        f".{uid}-outline {{ stroke-dasharray:{perimeter:.0f}; animation:{uid}draw 0.7s ease-out both; }}"
        f".{uid}-fill {{ animation:{uid}wash 0.5s ease-out 0.5s both; }}"
        f".{uid}-lbl {{ animation:{uid}lbl 0.3s ease-out 0.8s both; }}",
        reduced=f"#{uid} * {{ animation:none !important; opacity:1; stroke-dashoffset:0; transform:none; }}",
    )
    return f"""<svg id="{uid}" width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
        {style}
        <rect class="{uid}-fill" x="{x0:.1f}" y="{y0:.1f}" width="{rw:.1f}" height="{rh:.1f}" fill="{FILL}" stroke="none" rx="4"/>
        <rect class="{uid}-outline" x="{x0:.1f}" y="{y0:.1f}" width="{rw:.1f}" height="{rh:.1f}" fill="none" stroke="{STROKE}" stroke-width="3" rx="4"/>
        <text class="{uid}-lbl" x="{x0+rw/2:.1f}" y="{y0-10:.1f}" text-anchor="middle" font-size="15" font-weight="bold" fill="{STROKE}">{w} {unit}</text>
        <text class="{uid}-lbl" x="{x0+rw+22:.1f}" y="{y0+rh/2:.1f}" text-anchor="middle" font-size="15" font-weight="bold" fill="{STROKE}" transform="rotate(90 {x0+rw+22:.1f} {y0+rh/2:.1f})">{h} {unit}</text>
    </svg>"""


def triangle_svg(base, height_val, unit="", width=260, height=180):
    """A labeled triangle (base + height, with the height shown as a dashed
    line) for triangle-area questions."""
    pad = 40
    max_w, max_h = width - 2 * pad, height - 2 * pad
    scale = min(max_w / base, max_h / height_val)
    tb, th = base * scale, height_val * scale
    x0, y0 = (width - tb) / 2, height - pad
    apex_x, apex_y = x0 + tb * 0.35, y0 - th
    uid = _uid()
    # Outline draws itself, then the dashed height line grows down from the
    # apex - the height is the part children forget, so it gets its own
    # separate beat instead of arriving with everything else.
    side = math.hypot(apex_x - x0, apex_y - y0) + math.hypot(x0 + tb - apex_x, y0 - apex_y) + tb + 12
    style = _anim_style(
        uid,
        f"@keyframes {uid}draw {{ from {{ stroke-dashoffset:{side:.0f}; }} to {{ stroke-dashoffset:0; }} }}"
        f"@keyframes {uid}hdraw {{ from {{ transform:scaleY(0); }} to {{ transform:scaleY(1); }} }}"
        f"@keyframes {uid}wash {{ from {{ opacity:0; }} to {{ opacity:1; }} }}"
        f".{uid}-outline {{ stroke-dasharray:{side:.0f}; animation:{uid}draw 0.7s ease-out both; }}"
        f".{uid}-fill {{ animation:{uid}wash 0.5s ease-out 0.5s both; }}"
        f".{uid}-h {{ transform-origin:{apex_x:.1f}px {apex_y:.1f}px; animation:{uid}hdraw 0.4s ease-out 0.75s both; }}"
        f".{uid}-lbl {{ animation:{uid}wash 0.3s ease-out 0.95s both; }}",
        reduced=f"#{uid} * {{ animation:none !important; opacity:1; stroke-dashoffset:0; transform:none; }}",
    )
    return f"""<svg id="{uid}" width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
        {style}
        <polygon class="{uid}-fill" points="{x0:.1f},{y0:.1f} {x0+tb:.1f},{y0:.1f} {apex_x:.1f},{apex_y:.1f}" fill="{FILL}" stroke="none"/>
        <polygon class="{uid}-outline" points="{x0:.1f},{y0:.1f} {x0+tb:.1f},{y0:.1f} {apex_x:.1f},{apex_y:.1f}" fill="none" stroke="{STROKE}" stroke-width="3"/>
        <line class="{uid}-h" x1="{apex_x:.1f}" y1="{apex_y:.1f}" x2="{apex_x:.1f}" y2="{y0:.1f}" stroke="{STROKE}" stroke-width="1.5" stroke-dasharray="4,3"/>
        <text class="{uid}-lbl" x="{x0+tb/2:.1f}" y="{y0+18:.1f}" text-anchor="middle" font-size="14" font-weight="bold" fill="{STROKE}">{t('visual.base')}: {base} {unit}</text>
        <text class="{uid}-lbl" x="{apex_x+10:.1f}" y="{(apex_y+y0)/2:.1f}" font-size="14" font-weight="bold" fill="{STROKE}">{t('visual.height')}: {height_val} {unit}</text>
    </svg>"""


def cuboid_svg(l, w, h, unit="", width=260, height=200):
    """A simple isometric box for volume questions."""
    pad = 40
    ox, oy = pad, height - pad
    dx, dy = 0.5, 0.28  # isometric skew for depth (w)
    scale = min((width - 2 * pad) / (l + w * 0.9), (height - 2 * pad) / (h + w * 0.5))
    L, W, H = l * scale, w * scale, h * scale

    front = [(ox, oy), (ox + L, oy), (ox + L, oy - H), (ox, oy - H)]
    top = [(ox, oy - H), (ox + L, oy - H), (ox + L + W * dx, oy - H - W * dy), (ox + W * dx, oy - H - W * dy)]
    side = [(ox + L, oy), (ox + L + W * dx, oy - W * dy), (ox + L + W * dx, oy - H - W * dy), (ox + L, oy - H)]

    def pts(p):
        return " ".join(f"{x:.1f},{y:.1f}" for x, y in p)

    uid = _uid()
    # The three faces assemble one at a time (front, then side, then top),
    # which makes the box read as three dimensions rather than a flat
    # hexagon - exactly the confusion that trips kids up on volume.
    style = _anim_style(
        uid,
        f"@keyframes {uid}face {{ from {{ opacity:0; transform:translateY(10px); }} "
        f"to {{ opacity:1; transform:translateY(0); }} }}"
        f"@keyframes {uid}lbl {{ from {{ opacity:0; }} to {{ opacity:1; }} }}"
        f".{uid}-f1 {{ animation:{uid}face 0.4s ease-out both; }}"
        f".{uid}-f2 {{ animation:{uid}face 0.4s ease-out 0.2s both; }}"
        f".{uid}-f3 {{ animation:{uid}face 0.4s ease-out 0.4s both; }}"
        f".{uid}-lbl {{ animation:{uid}lbl 0.3s ease-out 0.7s both; }}",
        reduced=f"#{uid} * {{ animation:none !important; opacity:1; transform:none; }}",
    )
    return f"""<svg id="{uid}" width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
        {style}
        <polygon class="{uid}-f3" points="{pts(top)}" fill="#ffe0b2" stroke="{STROKE}" stroke-width="2"/>
        <polygon class="{uid}-f2" points="{pts(side)}" fill="#ffb74d" stroke="{STROKE}" stroke-width="2"/>
        <polygon class="{uid}-f1" points="{pts(front)}" fill="#ffcc80" stroke="{STROKE}" stroke-width="2"/>
        <text class="{uid}-lbl" x="{ox+L/2:.1f}" y="{oy+18:.1f}" text-anchor="middle" font-size="13" font-weight="bold" fill="{STROKE}">{t('visual.length_abbr')}={l}{unit}</text>
        <text class="{uid}-lbl" x="{ox-14:.1f}" y="{oy-H/2:.1f}" text-anchor="middle" font-size="13" font-weight="bold" fill="{STROKE}">{t('visual.height_abbr')}={h}{unit}</text>
        <text class="{uid}-lbl" x="{ox+L+W*dx/2+8:.1f}" y="{oy-W*dy/2+4:.1f}" text-anchor="middle" font-size="13" font-weight="bold" fill="{STROKE}">{t('visual.width_abbr')}={w}{unit}</text>
    </svg>"""


def speed_diagram_svg(distance, unit_d, time, unit_t, width=280, height=90):
    """A simple travel diagram: start -> end with distance/time labels."""
    y = height * 0.5
    x0, x1 = 30, width - 30
    uid = _uid()
    # The marker id has to be unique per render: two speed diagrams on one
    # page both defining id="arrow" would leave the second one pointing at
    # the first one's marker (duplicate ids in a document are resolved to
    # whichever came first).
    style = _anim_style(
        uid,
        f"@keyframes {uid}road {{ from {{ transform:scaleX(0); }} to {{ transform:scaleX(1); }} }}"
        f"@keyframes {uid}drive {{ from {{ transform:translateX(0); }} to {{ transform:translateX({x1 - x0 - 24:.0f}px); }} }}"
        f"@keyframes {uid}fade {{ from {{ opacity:0; }} to {{ opacity:1; }} }}"
        f".{uid}-road {{ transform-origin:{x0}px {y}px; animation:{uid}road 0.6s ease-out both; }}"
        f".{uid}-car {{ animation:{uid}drive 1.5s cubic-bezier(0.4,0,0.5,1) 0.4s both; }}"
        f".{uid}-lbl {{ animation:{uid}fade 0.35s ease-out 0.5s both; }}",
        reduced=f".{uid}-road {{ animation:none !important; transform:scaleX(1); }} "
        f".{uid}-car {{ animation:none !important; transform:none; }} "
        f".{uid}-lbl {{ animation:none !important; opacity:1; }}",
    )
    return f"""<svg id="{uid}" width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
        {style}
        <defs>
            <marker id="{uid}-arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
                <path d="M0,0 L0,6 L9,3 z" fill="{STROKE}"/>
            </marker>
        </defs>
        <line class="{uid}-road" x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{STROKE}" stroke-width="3" marker-end="url(#{uid}-arrow)"/>
        <text class="{uid}-car" x="{x0}" y="{y-14}" font-size="22">&#128663;</text>
        <text x="{x1-18}" y="{y-14}" font-size="22">&#127937;</text>
        <text class="{uid}-lbl" x="{(x0+x1)/2:.1f}" y="{y+24}" text-anchor="middle" font-size="14" font-weight="bold" fill="{STROKE}">{distance} {unit_d} {t('visual.in_time')} {time} {unit_t}</text>
    </svg>"""
