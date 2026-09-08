"""
Small SVG visualization library used across the games. Every function
returns a plain SVG string (rendered with st.markdown(..., unsafe_allow_html=True))
so kids get an immediate visual for the math they're working with, instead
of just numbers on a screen.
"""
import math

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
    cx = cy = size / 2
    r = size / 2 - 6
    parts = []
    for i in range(denominator):
        a0 = -90 + i * (360 / denominator)
        a1 = -90 + (i + 1) * (360 / denominator)
        x0, y0 = _polar(cx, cy, r, a0)
        x1, y1 = _polar(cx, cy, r, a1)
        large_arc = 1 if (360 / denominator) > 180 else 0
        color = FILL if i < numerator else EMPTY
        d = f"M {cx},{cy} L {x0:.2f},{y0:.2f} A {r},{r} 0 {large_arc} 1 {x1:.2f},{y1:.2f} Z"
        parts.append(f'<path d="{d}" fill="{color}" stroke="{STROKE}" stroke-width="2"/>')
    pct = round(100 * numerator / denominator)
    label = f"{numerator}/{denominator} = {pct}%"
    return f"""<svg width="{size}" height="{size + 34}" viewBox="0 0 {size} {size + 34}" xmlns="http://www.w3.org/2000/svg">
        {''.join(parts)}
        <text x="{cx}" y="{size + 24}" text-anchor="middle" font-size="18" font-weight="bold" fill="{STROKE}">{label}</text>
    </svg>"""


def fraction_bar_svg(numerator, denominator, width=280, height=50):
    """A row of `denominator` equal blocks, `numerator` filled. Used for
    fractions with too many pieces to show clearly as a pizza."""
    denominator = max(1, int(denominator))
    numerator = max(0, min(int(numerator), denominator))
    gap = 3
    block_w = (width - gap * (denominator - 1)) / denominator
    blocks = []
    for i in range(denominator):
        x = i * (block_w + gap)
        color = FILL if i < numerator else EMPTY
        blocks.append(f'<rect x="{x:.1f}" y="0" width="{block_w:.1f}" height="{height}" fill="{color}" stroke="{STROKE}" stroke-width="2" rx="4"/>')
    pct = round(100 * numerator / denominator)
    return f"""<svg width="{width}" height="{height + 30}" viewBox="0 0 {width} {height + 30}" xmlns="http://www.w3.org/2000/svg">
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
    fill_w = width * percent / 100
    ticks = "".join(
        f'<line x1="{width * p / 100:.1f}" y1="0" x2="{width * p / 100:.1f}" y2="{height}" stroke="{STROKE}" stroke-width="1" stroke-dasharray="3,3"/>'
        for p in (25, 50, 75)
    )
    text = label if label is not None else f"{percent}%"
    return f"""<svg width="{width}" height="{height + 26}" viewBox="0 0 {width} {height + 26}" xmlns="http://www.w3.org/2000/svg">
        <rect x="0" y="0" width="{width}" height="{height}" fill="{EMPTY}" stroke="{STROKE}" stroke-width="2" rx="6"/>
        <rect x="0" y="0" width="{fill_w:.1f}" height="{height}" fill="{ACCENT}" rx="6"/>
        {ticks}
        <text x="{width / 2}" y="{height + 20}" text-anchor="middle" font-size="16" font-weight="bold" fill="{STROKE}">{text}</text>
    </svg>"""


def array_grid_svg(a, b, max_dots=100, dot_r=7, gap=22):
    """A rows-x-cols dot array for multiplication (a x b). Falls back to a
    labeled grid outline (no individual dots) when a*b is too big to read."""
    a, b = int(a), int(b)
    if a * b <= max_dots:
        width = b * gap
        height = a * gap
        dots = []
        for row in range(a):
            for col in range(b):
                cx = col * gap + gap / 2
                cy = row * gap + gap / 2
                dots.append(f'<circle cx="{cx}" cy="{cy}" r="{dot_r}" fill="{FILL}" stroke="{STROKE}" stroke-width="1.5"/>')
        return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
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
    hour_angle = ((hour % 12) + minute / 60) * 30 - 90
    minute_angle = minute * 6 - 90
    hx, hy = _polar(cx, cy, r * 0.5, hour_angle)
    mx, my = _polar(cx, cy, r * 0.8, minute_angle)
    label = f"{hour:02d}:{minute:02d}"
    return f"""<svg width="{size}" height="{size + 26}" viewBox="0 0 {size} {size + 26}" xmlns="http://www.w3.org/2000/svg">
        <circle cx="{cx}" cy="{cy}" r="{r}" fill="{EMPTY}" stroke="{STROKE}" stroke-width="3"/>
        {''.join(ticks)}
        <line x1="{cx}" y1="{cy}" x2="{hx:.1f}" y2="{hy:.1f}" stroke="{STROKE}" stroke-width="4" stroke-linecap="round"/>
        <line x1="{cx}" y1="{cy}" x2="{mx:.1f}" y2="{my:.1f}" stroke="{highlight}" stroke-width="3" stroke-linecap="round"/>
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
    total_label = total_label if total_label is not None else f"{total:g}"
    part_label = part_label if part_label is not None else f"{part:g}"
    rest_label = rest_label if rest_label is not None else f"{total - part:g}"
    return f"""<svg width="{width}" height="{height + 46}" viewBox="0 0 {width} {height + 46}" xmlns="http://www.w3.org/2000/svg">
        <rect x="0" y="20" width="{width}" height="{height}" fill="{EMPTY}" stroke="{STROKE}" stroke-width="2" rx="6"/>
        <rect x="0" y="20" width="{part_w:.1f}" height="{height}" fill="{ACCENT2}" rx="6"/>
        <line x1="{part_w:.1f}" y1="14" x2="{part_w:.1f}" y2="{height + 26}" stroke="{STROKE}" stroke-width="2" stroke-dasharray="4,3"/>
        <text x="{width / 2}" y="14" text-anchor="middle" font-size="14" fill="{STROKE}">totaal: {total_label}</text>
        <text x="{max(24, part_w / 2):.1f}" y="{20 + height / 2 + 5}" text-anchor="middle" font-size="14" font-weight="bold" fill="#ffffff">{part_label}</text>
        <text x="{part_w + max(24, (width - part_w) / 2):.1f}" y="{20 + height / 2 + 5}" text-anchor="middle" font-size="14" font-weight="bold" fill="{STROKE}">{rest_label}</text>
    </svg>"""


def ratio_bar_svg(parts, colors=None, width=280, height=46, labels=None):
    """A bar split into proportional segments, one per ratio part."""
    total = sum(parts) or 1
    colors = colors or [FILL, ACCENT2, ACCENT, DANGER, "#ab47bc"]
    segments = []
    x = 0.0
    for i, p in enumerate(parts):
        w = width * p / total
        color = colors[i % len(colors)]
        segments.append(f'<rect x="{x:.1f}" y="0" width="{w:.1f}" height="{height}" fill="{color}" stroke="{STROKE}" stroke-width="2"/>')
        label = labels[i] if labels else str(p)
        segments.append(f'<text x="{x + w / 2:.1f}" y="{height / 2 + 5}" text-anchor="middle" font-size="14" font-weight="bold" fill="#ffffff">{label}</text>')
        x += w
    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
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
    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
        <polygon points="{cx-14},{height-20} {cx+14},{height-20} {cx},{fulcrum_y}" fill="{STROKE}"/>
        <line x1="{lx:.1f}" y1="{ly:.1f}" x2="{rx:.1f}" y2="{ry:.1f}" stroke="{STROKE}" stroke-width="5"/>
        <line x1="{lx:.1f}" y1="{ly:.1f}" x2="{lx:.1f}" y2="{ly+40:.1f}" stroke="{STROKE}" stroke-width="2"/>
        <line x1="{rx:.1f}" y1="{ry:.1f}" x2="{rx:.1f}" y2="{ry+40:.1f}" stroke="{STROKE}" stroke-width="2"/>
        <ellipse cx="{lx:.1f}" cy="{ly+44:.1f}" rx="{pan_r}" ry="12" fill="{FILL}" stroke="{STROKE}" stroke-width="2"/>
        <ellipse cx="{rx:.1f}" cy="{ry+44:.1f}" rx="{pan_r}" ry="12" fill="{ACCENT2}" stroke="{STROKE}" stroke-width="2"/>
        <text x="{lx:.1f}" y="{ly+40:.1f}" text-anchor="middle" font-size="16" font-weight="bold" fill="{STROKE}">{left_text}</text>
        <text x="{rx:.1f}" y="{ry+40:.1f}" text-anchor="middle" font-size="16" font-weight="bold" fill="{STROKE}">{right_text}</text>
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

    markers = []
    colors = [ACCENT2, ACCENT, DANGER]
    for i, (val, label) in enumerate(points):
        x = x_of(val)
        color = colors[i % len(colors)]
        markers.append(f'<circle cx="{x:.1f}" cy="{y}" r="7" fill="{color}" stroke="{STROKE}" stroke-width="2"/>')
        markers.append(f'<text x="{x:.1f}" y="{y-14}" text-anchor="middle" font-size="13" font-weight="bold" fill="{color}">{label}</text>')

    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
        <line x1="{margin}" y1="{y}" x2="{width-margin}" y2="{y}" stroke="{STROKE}" stroke-width="2"/>
        {''.join(ticks)}
        {''.join(markers)}
    </svg>"""


def rectangle_svg(w, h, unit="", width=260, height=180):
    """A labeled rectangle for perimeter/area questions."""
    pad = 40
    max_w, max_h = width - 2 * pad, height - 2 * pad
    scale = min(max_w / w, max_h / h)
    rw, rh = w * scale, h * scale
    x0, y0 = (width - rw) / 2, (height - rh) / 2 - 10
    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
        <rect x="{x0:.1f}" y="{y0:.1f}" width="{rw:.1f}" height="{rh:.1f}" fill="{FILL}" stroke="{STROKE}" stroke-width="3" rx="4"/>
        <text x="{x0+rw/2:.1f}" y="{y0-10:.1f}" text-anchor="middle" font-size="15" font-weight="bold" fill="{STROKE}">{w} {unit}</text>
        <text x="{x0+rw+22:.1f}" y="{y0+rh/2:.1f}" text-anchor="middle" font-size="15" font-weight="bold" fill="{STROKE}" transform="rotate(90 {x0+rw+22:.1f} {y0+rh/2:.1f})">{h} {unit}</text>
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
    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
        <polygon points="{x0:.1f},{y0:.1f} {x0+tb:.1f},{y0:.1f} {apex_x:.1f},{apex_y:.1f}" fill="{FILL}" stroke="{STROKE}" stroke-width="3"/>
        <line x1="{apex_x:.1f}" y1="{apex_y:.1f}" x2="{apex_x:.1f}" y2="{y0:.1f}" stroke="{STROKE}" stroke-width="1.5" stroke-dasharray="4,3"/>
        <text x="{x0+tb/2:.1f}" y="{y0+18:.1f}" text-anchor="middle" font-size="14" font-weight="bold" fill="{STROKE}">basis: {base} {unit}</text>
        <text x="{apex_x+10:.1f}" y="{(apex_y+y0)/2:.1f}" font-size="14" font-weight="bold" fill="{STROKE}">hoogte: {height_val} {unit}</text>
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

    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
        <polygon points="{pts(top)}" fill="#ffe0b2" stroke="{STROKE}" stroke-width="2"/>
        <polygon points="{pts(side)}" fill="#ffb74d" stroke="{STROKE}" stroke-width="2"/>
        <polygon points="{pts(front)}" fill="#ffcc80" stroke="{STROKE}" stroke-width="2"/>
        <text x="{ox+L/2:.1f}" y="{oy+18:.1f}" text-anchor="middle" font-size="13" font-weight="bold" fill="{STROKE}">l={l}{unit}</text>
        <text x="{ox-14:.1f}" y="{oy-H/2:.1f}" text-anchor="middle" font-size="13" font-weight="bold" fill="{STROKE}">h={h}{unit}</text>
        <text x="{ox+L+W*dx/2+8:.1f}" y="{oy-W*dy/2+4:.1f}" text-anchor="middle" font-size="13" font-weight="bold" fill="{STROKE}">b={w}{unit}</text>
    </svg>"""


def speed_diagram_svg(distance, unit_d, time, unit_t, width=280, height=90):
    """A simple travel diagram: start -> end with distance/time labels."""
    y = height * 0.5
    x0, x1 = 30, width - 30
    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
        <line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{STROKE}" stroke-width="3" marker-end="url(#arrow)"/>
        <defs>
            <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
                <path d="M0,0 L0,6 L9,3 z" fill="{STROKE}"/>
            </marker>
        </defs>
        <text x="{x0}" y="{y-14}" font-size="22">&#128663;</text>
        <text x="{x1-18}" y="{y-14}" font-size="22">&#127937;</text>
        <text x="{(x0+x1)/2:.1f}" y="{y+24}" text-anchor="middle" font-size="14" font-weight="bold" fill="{STROKE}">{distance} {unit_d} in {time} {unit_t}</text>
    </svg>"""
