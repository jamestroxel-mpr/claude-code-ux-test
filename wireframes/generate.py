"""Generate the respondent-journey dashboard wireframes as Figma-importable SVGs.

Run:  python3 wireframes/generate.py
Output: wireframes/svg/*.svg  (one 1440x1024 frame per screen/state)

Every logical piece of UI is wrapped in a <g id="..."> so it arrives in Figma
as a named layer group. Text is emitted as real <text> so it stays editable.
"""

import os
from datetime import date, timedelta
from xml.sax.saxutils import escape

W, H = 1440, 1024
FONT = "Inter, 'Helvetica Neue', Arial, sans-serif"

# Wireframe palette: greys, one accent for interaction/selection, one red for deadlines.
BG = "#F4F5F7"
SURFACE = "#FFFFFF"
BORDER = "#D9DCE1"
FAINT = "#ECEEF1"
TEXT = "#1F2328"
MUTED = "#6B7280"
SUBTLE = "#9AA1AC"
DARK = "#5B6472"
BOX = "#C9CED6"
ACCENT = "#2F6FEB"
ACCENT_SOFT = "#E6EEFD"
RED = "#D93F3F"
RED_SOFT = "#FBE7E7"

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

STARTED = 1248
# name, deadline (days allowed from step start), completed count,
# duration percentiles (p5, p25, median, p75, p95) in days, % completed on time
STEPS = [
    ("Registration", 3, 1098, (0.5, 1, 2, 4, 8), 78),
    ("Eligibility screening", 7, 941, (2, 4, 6, 9, 15), 71),
    ("Document upload", 14, 820, (4, 10, 15, 19, 27), 44),
    ("Interview", 10, 702, (2, 5, 8, 12, 19), 69),
    ("Case review", 14, 640, (5, 9, 12, 17, 24), 72),
    ("Final decision", 5, 612, (1, 2, 4, 6, 11), 58),
]

ENROLLED = date(2026, 3, 12)
TODAY_DAY = 33
# Selected respondent's journey: (start day, end day or None, state)
INDIVIDUAL = [
    (0, 2, "done"),
    (2, 8, "done"),
    (8, 24, "done"),
    (24, None, "current"),
    (None, None, "not_started"),
    (None, None, "not_started"),
]

# id, age, gender, region, per-step states, status, enrolled
# o = on time, l = late, c = current, d = dropped, n = not started
RESPONDENTS = [
    ("R-10427", 34, "Female", "Northeast", "oolcnn", "Step 4 · In progress", "12 Mar"),
    ("R-10412", 29, "Male", "South", "oooooo", "Completed", "10 Mar"),
    ("R-10398", 41, "Female", "South", "oldnnn", "Dropped · Step 3", "09 Mar"),
    ("R-10385", 38, "Nonbinary", "Northeast", "oooocn", "Step 5 · In progress", "07 Mar"),
    ("R-10371", 27, "Male", "Northeast", "lololo", "Completed", "05 Mar"),
    ("R-10366", 44, "Female", "South", "odnnnn", "Dropped · Step 2", "04 Mar"),
    ("R-10359", 31, "Male", "South", "ooocnn", "Step 4 · In progress", "02 Mar"),
    ("R-10340", 36, "Female", "Northeast", "oooool", "Completed", "28 Feb"),
    ("R-10333", 25, "Female", "South", "ocnnnn", "Step 2 · In progress", "27 Feb"),
    ("R-10321", 42, "Male", "Northeast", "oolldn", "Dropped · Step 5", "25 Feb"),
]

DEMOGRAPHICS = [
    ("Age", "34"),
    ("Gender", "Female"),
    ("Race / ethnicity", "Hispanic or Latino"),
    ("Region", "Northeast"),
    ("State", "New York"),
    ("Urban / rural", "Urban"),
    ("Education", "Bachelor's degree"),
    ("Employment", "Employed full-time"),
    ("Household income", "$50k – $75k"),
    ("Household size", "3"),
    ("Primary language", "Spanish"),
    ("Referral source", "Community partner"),
]


def fmt_day(day):
    d = ENROLLED + timedelta(days=day)
    return d.strftime("%d %b").lstrip("0")


def fmt_int(n):
    return f"{n:,}"


# ---------------------------------------------------------------------------
# SVG primitives
# ---------------------------------------------------------------------------


class Svg:
    def __init__(self, name):
        self.name = name
        self.parts = []

    def add(self, s):
        self.parts.append(s)

    def g(self, gid):
        self.add(f'<g id="{escape(gid)}">')

    def end(self):
        self.add("</g>")

    def rect(self, x, y, w, h, fill="none", stroke=None, rx=0, sw=1, dash=None, gid=None):
        a = f'x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"'
        if rx:
            a += f' rx="{rx}"'
        if stroke:
            a += f' stroke="{stroke}" stroke-width="{sw}"'
        if dash:
            a += f' stroke-dasharray="{dash}"'
        if gid:
            a += f' id="{escape(gid)}"'
        self.add(f"<rect {a}/>")

    def line(self, x1, y1, x2, y2, stroke=BORDER, sw=1, dash=None):
        a = f'x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"'
        if dash:
            a += f' stroke-dasharray="{dash}"'
        self.add(f"<line {a}/>")

    def circle(self, cx, cy, r, fill="none", stroke=None, sw=1, dash=None):
        a = f'cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"'
        if stroke:
            a += f' stroke="{stroke}" stroke-width="{sw}"'
        if dash:
            a += f' stroke-dasharray="{dash}"'
        self.add(f"<circle {a}/>")

    def path(self, d, stroke=TEXT, sw=1.5, fill="none"):
        self.add(
            f'<path d="{d}" stroke="{stroke}" stroke-width="{sw}" fill="{fill}" '
            'stroke-linecap="round" stroke-linejoin="round"/>'
        )

    def text(self, x, y, s, size=13, fill=TEXT, weight=400, anchor="start"):
        a = f'x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" fill="{fill}"'
        if weight != 400:
            a += f' font-weight="{weight}"'
        if anchor != "start":
            a += f' text-anchor="{anchor}"'
        self.add(f"<text {a}>{escape(s)}</text>")

    def write(self):
        out = os.path.join(HERE, "svg", f"{self.name}.svg")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        body = "\n".join(self.parts)
        with open(out, "w") as f:
            f.write(
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
                f'viewBox="0 0 {W} {H}">\n'
                f'<rect id="Frame background" width="{W}" height="{H}" fill="{BG}"/>\n'
                f"{body}\n</svg>\n"
            )
        return out


def text_w(s, size=13):
    """Rough text width estimate, used only for chip/badge sizing."""
    return len(s) * size * 0.56


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------


def chevron(s, x, y, color=MUTED):
    s.path(f"M{x - 4} {y - 2} L{x} {y + 2} L{x + 4} {y - 2}", stroke=color, sw=1.5)


def dropdown(s, x, y, w, value, h=36, label=None):
    s.g(f"Dropdown / {label or value}")
    s.rect(x, y, w, h, fill=SURFACE, stroke=BORDER, rx=6)
    s.text(x + 12, y + h / 2 + 4.5, value, size=13)
    chevron(s, x + w - 16, y + h / 2)
    s.end()


def field_label(s, x, y, label):
    s.text(x, y, label, size=12, fill=MUTED, weight=600)


def checkbox(s, x, y, label, checked):
    s.g(f"Checkbox / {label}")
    if checked:
        s.rect(x, y, 16, 16, fill=ACCENT, rx=3)
        s.path(f"M{x + 4} {y + 8} L{x + 7} {y + 11} L{x + 12} {y + 5}", stroke=SURFACE, sw=2)
    else:
        s.rect(x, y, 16, 16, fill=SURFACE, stroke=BORDER, rx=3, sw=1.5)
    s.text(x + 24, y + 12.5, label, size=13)
    s.end()


def button(s, x, y, w, label, primary=False, h=36):
    s.g(f"Button / {label}")
    if primary:
        s.rect(x, y, w, h, fill=ACCENT, rx=6)
        s.text(x + w / 2, y + h / 2 + 4.5, label, size=13, fill=SURFACE, weight=600, anchor="middle")
    else:
        s.rect(x, y, w, h, fill=SURFACE, stroke=BORDER, rx=6)
        s.text(x + w / 2, y + h / 2 + 4.5, label, size=13, weight=500, anchor="middle")
    s.end()


def segmented(s, x, y, options, active, w_each=88, h=34, name="View toggle"):
    s.g(name)
    s.rect(x, y, w_each * len(options), h, fill=FAINT, rx=7)
    for i, opt in enumerate(options):
        ox = x + i * w_each
        if opt == active:
            s.rect(ox + 3, y + 3, w_each - 6, h - 6, fill=SURFACE, stroke=BORDER, rx=5)
            s.text(ox + w_each / 2, y + h / 2 + 4.5, opt, size=13, weight=600, anchor="middle")
        else:
            s.text(ox + w_each / 2, y + h / 2 + 4.5, opt, size=13, fill=MUTED, weight=500, anchor="middle")
    s.end()


def chip(s, x, y, label):
    w = text_w(label, 12) + 36
    s.g(f"Filter chip / {label}")
    s.rect(x, y, w, 28, fill=ACCENT_SOFT, rx=14)
    s.text(x + 12, y + 18, label, size=12, fill=ACCENT, weight=500)
    cx, cy = x + w - 14, y + 14
    s.path(f"M{cx - 3.5} {cy - 3.5} L{cx + 3.5} {cy + 3.5} M{cx + 3.5} {cy - 3.5} L{cx - 3.5} {cy + 3.5}", stroke=ACCENT)
    s.end()
    return w


def card(s, x, y, w, h, name):
    s.rect(x, y, w, h, fill=SURFACE, stroke=BORDER, rx=10, gid=f"{name} / container")


def step_badge(s, cx, cy, n, fill=FAINT, color=TEXT):
    s.circle(cx, cy, 11, fill=fill)
    s.text(cx, cy + 4, str(n), size=11, fill=color, weight=600, anchor="middle")


def pill(s, x, y, label, kind):
    colors = {
        "on_time": (FAINT, TEXT),
        "late": (RED_SOFT, RED),
        "current": (ACCENT_SOFT, ACCENT),
        "not_started": (SURFACE, MUTED),
    }
    fill, fg = colors[kind]
    w = text_w(label, 12) + 20
    s.g(f"Status pill / {label}")
    s.rect(x, y, w, 22, fill=fill, rx=11, stroke=BORDER if kind == "not_started" else None)
    s.text(x + w / 2, y + 15, label, size=12, fill=fg, weight=600, anchor="middle")
    s.end()


def table(s, x, y, cols, rows, row_h=36, head_h=36, name="Table"):
    """cols: list of (label, width, align); rows: list of lists of str or callables."""
    total_w = sum(c[1] for c in cols)
    s.g(name)
    s.rect(x, y, total_w, head_h, fill=FAINT, rx=6)
    cx = x
    for label, w, align in cols:
        if align == "r":
            s.text(cx + w - 12, y + head_h / 2 + 4, label, size=12, fill=MUTED, weight=600, anchor="end")
        else:
            s.text(cx + 12, y + head_h / 2 + 4, label, size=12, fill=MUTED, weight=600)
        cx += w
    ry = y + head_h
    for r_i, row in enumerate(rows):
        s.g(f"Row {r_i + 1}")
        cx = x
        for (label, w, align), cell in zip(cols, row):
            if callable(cell):
                cell(s, cx, ry, w, row_h)
            else:
                val, color, weight = cell if isinstance(cell, tuple) else (cell, TEXT, 400)
                if align == "r":
                    s.text(cx + w - 12, ry + row_h / 2 + 4.5, val, size=13, fill=color, weight=weight, anchor="end")
                else:
                    s.text(cx + 12, ry + row_h / 2 + 4.5, val, size=13, fill=color, weight=weight)
            cx += w
        s.line(x, ry + row_h, x + total_w, ry + row_h, stroke=FAINT)
        s.end()
        ry += row_h
    s.end()
    return ry


def step_cell(n, name):
    def draw(s, x, y, w, h):
        step_badge(s, x + 23, y + h / 2, n)
        s.text(x + 42, y + h / 2 + 4.5, name, size=13, weight=500)

    return draw


# ---------------------------------------------------------------------------
# Shared chrome
# ---------------------------------------------------------------------------


def top_bar(s, active):
    s.g("Top bar")
    s.rect(0, 0, W, 64, fill=SURFACE)
    s.line(0, 64, W, 64)
    # logo placeholder
    s.rect(24, 18, 28, 28, fill=FAINT, stroke=BORDER, rx=6)
    s.line(24, 18, 52, 46, stroke=BORDER)
    s.line(52, 18, 24, 46, stroke=BORDER)
    s.text(66, 38, "Respondent Journey", size=17, weight=700)
    tabs = [("Aggregate journey", 360, 150), ("Individual respondents", 530, 176)]
    for label, tx, tw in tabs:
        on = label.startswith(active)
        s.g(f"Tab / {label}")
        s.text(tx + tw / 2, 38, label, size=14, fill=TEXT if on else MUTED, weight=600 if on else 500, anchor="middle")
        if on:
            s.rect(tx, 61, tw, 3, fill=ACCENT)
        s.end()
    s.text(1172, 37, "Data refreshed 14 Apr 2026, 08:00", size=12, fill=MUTED, anchor="end")
    button(s, 1188, 14, 92, "Export", h=36)
    s.circle(1400, 32, 16, fill=FAINT, stroke=BORDER)
    s.text(1400, 36.5, "AB", size=11, fill=MUTED, weight=600, anchor="middle")
    s.end()


def aggregate_sidebar(s):
    s.g("Filter sidebar")
    s.rect(0, 65, 280, H - 65, fill=SURFACE)
    s.line(280, 65, 280, H)
    s.text(24, 104, "Filters", size=16, weight=700)
    s.text(256, 104, "Reset all", size=13, fill=ACCENT, weight=500, anchor="end")
    s.text(24, 126, "Applies to every chart and table", size=11, fill=MUTED)

    s.g("Filter / Age group")
    field_label(s, 24, 160, "Age group")
    ages = [("18–24", False), ("25–34", True), ("35–44", True), ("45–54", False), ("55–64", False), ("65+", False)]
    for i, (a, on) in enumerate(ages):
        checkbox(s, 24 + (i % 2) * 120, 172 + (i // 2) * 28, a, on)
    s.end()

    fields = [
        ("Gender", "All genders", 272),
        ("Race / ethnicity", "All (7 of 7)", 346),
        ("Region", "Northeast, South", 420),
        ("Education", "All levels", 494),
    ]
    for label, value, fy in fields:
        s.g(f"Filter / {label}")
        field_label(s, 24, fy, label)
        dropdown(s, 24, fy + 10, 232, value, label=label)
        s.end()

    s.g("Filter / Household income")
    field_label(s, 24, 568, "Household income")
    s.rect(24, 590, 232, 4, fill=FAINT, rx=2)
    s.rect(64, 590, 150, 4, fill=ACCENT, rx=2)
    for hx in (64, 214):
        s.circle(hx, 592, 8, fill=SURFACE, stroke=ACCENT, sw=2)
    s.text(24, 618, "$25k", size=12, fill=MUTED)
    s.text(256, 618, "$150k+", size=12, fill=MUTED, anchor="end")
    s.end()

    s.g("Filter / Primary language")
    field_label(s, 24, 648, "Primary language")
    dropdown(s, 24, 658, 232, "All languages", label="Primary language")
    s.end()

    s.g("Filter / Enrollment date")
    field_label(s, 24, 722, "Enrollment date")
    for i, v in enumerate(("1 Jan 2026", "30 Jun 2026")):
        s.rect(24 + i * 124, 732, 108, 36, fill=SURFACE, stroke=BORDER, rx=6)
        s.text(36 + i * 124, 754.5, v, size=12)
    s.text(140, 754.5, "–", size=12, fill=MUTED, anchor="middle")
    s.end()

    s.text(24, 806, "+ More filters", size=13, fill=ACCENT, weight=500)
    s.line(0, 930, 280, 930, stroke=FAINT)
    s.text(24, 956, "1,248 respondents match", size=12, fill=MUTED)
    button(s, 24, 968, 232, "Apply filters", primary=True, h=40)
    s.end()


def aggregate_header(s, view):
    s.g("Page header")
    s.text(304, 112, "Aggregate journey", size=24, weight=700)
    s.text(304, 138, "1,248 of 3,902 respondents · Enrolled 1 Jan – 30 Jun 2026", size=13, fill=MUTED)
    s.text(1210, 115, "View as", size=13, fill=MUTED, anchor="end")
    segmented(s, 1222, 94, ["Charts", "Tables"], view, w_each=97)
    s.end()

    s.g("Active filter chips")
    x = 304
    for label in ("Age: 25–44", "Region: Northeast, South", "Income: $25k – $150k+"):
        x += chip(s, x, 158, label) + 8
    s.text(x + 4, 176, "Clear all", size=12, fill=ACCENT, weight=500)
    s.end()

    s.g("KPI tiles")
    total_deadline = sum(st[1] for st in STEPS)
    kpis = [
        ("Respondents started", "1,248", "100% of filtered cohort"),
        ("Completed all steps", "612", "49% of starters"),
        ("Median time to finish", "38 days", f"Target: {total_deadline} days (sum of deadlines)"),
        ("Steps completed on time", "65%", "Across all completed steps"),
    ]
    for i, (label, value, note) in enumerate(kpis):
        kx = 304 + i * (266 + 16)
        s.g(f"KPI / {label}")
        s.rect(kx, 202, 266, 92, fill=SURFACE, stroke=BORDER, rx=10)
        s.text(kx + 20, 228, label, size=12, fill=MUTED, weight=600)
        s.text(kx + 20, 262, value, size=26, weight=700)
        s.text(kx + 20, 282, note, size=12, fill=MUTED)
        s.end()
    s.end()


# ---------------------------------------------------------------------------
# Screen 1a: Aggregate — charts
# ---------------------------------------------------------------------------


def aggregate_charts():
    s = Svg("01-aggregate-charts")
    top_bar(s, "Aggregate")
    aggregate_sidebar(s)
    aggregate_header(s, "Charts")

    px, py, pw, ph = 304, 312, 1112, 660
    s.g("Journey by step (chart)")
    card(s, px, py, pw, ph, "Journey by step")
    s.text(328, 344, "Journey by step", size=16, weight=700)
    s.text(
        328,
        366,
        "How many respondents complete each step, and how long completed steps took compared with the step deadline",
        size=13,
        fill=MUTED,
    )

    # Axis for duration distribution
    ax0, ax1, dmax = 896, 1296, 30

    def dx(d):
        return ax0 + (ax1 - ax0) * d / dmax

    # Legend
    s.g("Legend")
    lx, ly = 896, 396
    s.line(lx, ly, lx + 24, ly, stroke=DARK, sw=1.5)
    s.line(lx, ly - 5, lx, ly + 5, stroke=DARK, sw=1.5)
    s.line(lx + 24, ly - 5, lx + 24, ly + 5, stroke=DARK, sw=1.5)
    s.text(lx + 32, ly + 4, "5th–95th percentile", size=12, fill=MUTED)
    lx += 156
    s.rect(lx, ly - 8, 24, 16, fill=BOX, stroke=DARK, rx=2)
    s.text(lx + 32, ly + 4, "Middle 50%", size=12, fill=MUTED)
    lx += 112
    s.line(lx + 12, ly - 9, lx + 12, ly + 9, stroke=TEXT, sw=2.5)
    s.text(lx + 22, ly + 4, "Median", size=12, fill=MUTED)
    lx += 80
    s.line(lx + 6, ly - 10, lx + 6, ly + 10, stroke=RED, sw=2, dash="4 3")
    s.text(lx + 16, ly + 4, "Deadline", size=12, fill=MUTED)
    s.end()

    s.g("Column headers")
    s.text(328, 426, "Step & deadline", size=12, fill=MUTED, weight=600)
    s.text(540, 426, "Completed step (% of starters)", size=12, fill=MUTED, weight=600)
    s.text(896, 426, "Days to complete step (completers only)", size=12, fill=MUTED, weight=600)
    s.text(1392, 426, "On time", size=12, fill=MUTED, weight=600, anchor="end")
    s.line(328, 438, 1392, 438)
    s.end()

    rows_top, row_h = 444, 76
    rows_bottom = rows_top + row_h * len(STEPS)

    s.g("Gridlines")
    for d in range(0, dmax + 1, 5):
        s.line(dx(d), rows_top, dx(d), rows_bottom, stroke=FAINT)
    s.end()

    prev = STARTED
    for i, (name, deadline, completed, (p5, p25, med, p75, p95), on_time) in enumerate(STEPS):
        ry = rows_top + i * row_h
        cy = ry + row_h / 2
        s.g(f"Step {i + 1} / {name}")
        if i:
            s.line(328, ry, 1392, ry, stroke=FAINT)

        step_badge(s, 340, cy - 6, i + 1)
        s.text(360, cy - 1.5, name, size=14, weight=600)
        s.text(360, cy + 17, f"Deadline: {deadline} days", size=12, fill=MUTED)

        # Completion bar
        pct = completed / STARTED
        dropped = prev - completed
        s.g("Completion bar")
        s.rect(540, cy - 18, 260, 16, fill=FAINT, rx=3)
        s.rect(540, cy - 18, round(260 * pct, 1), 16, fill=DARK, rx=3)
        s.text(812, cy - 5, f"{pct:.0%}", size=14, weight=700)
        s.text(850, cy - 5, fmt_int(completed), size=12, fill=MUTED)
        s.text(540, cy + 17, f"▼ {fmt_int(dropped)} dropped here ({dropped / prev:.0%} of those who reached it)", size=12, fill=MUTED)
        s.end()
        prev = completed

        # Box plot
        s.g("Duration distribution")
        s.line(dx(p5), cy, dx(p25), cy, stroke=DARK, sw=1.5)
        s.line(dx(p75), cy, dx(p95), cy, stroke=DARK, sw=1.5)
        s.line(dx(p5), cy - 6, dx(p5), cy + 6, stroke=DARK, sw=1.5)
        s.line(dx(p95), cy - 6, dx(p95), cy + 6, stroke=DARK, sw=1.5)
        s.rect(dx(p25), cy - 11, dx(p75) - dx(p25), 22, fill=BOX, stroke=DARK, rx=2)
        s.line(dx(med), cy - 11, dx(med), cy + 11, stroke=TEXT, sw=2.5)
        s.line(dx(deadline), cy - 22, dx(deadline), cy + 22, stroke=RED, sw=2, dash="4 3")
        s.text(dx(deadline) + 5, cy - 16, f"{deadline}d", size=11, fill=RED, weight=600)
        s.end()

        s.text(1392, cy - 1.5, f"{on_time}%", size=14, weight=700, fill=RED if on_time < 50 else TEXT, anchor="end")
        s.text(1392, cy + 17, "of completers", size=12, fill=MUTED, anchor="end")
        s.end()

    s.g("Duration axis")
    s.line(ax0, rows_bottom, ax1, rows_bottom, stroke=MUTED)
    for d in range(0, dmax + 1, 5):
        s.line(dx(d), rows_bottom, dx(d), rows_bottom + 5, stroke=MUTED)
        s.text(dx(d), rows_bottom + 20, str(d), size=11, fill=MUTED, anchor="middle")
    s.text(ax1 + 12, rows_bottom + 20, "days", size=11, fill=MUTED)
    s.end()

    s.text(
        328,
        py + ph - 22,
        "Hover a row for exact values. Click a step to see the respondents who dropped out there in the Individual view.",
        size=12,
        fill=MUTED,
    )
    s.end()
    return s.write()


# ---------------------------------------------------------------------------
# Screen 1b: Aggregate — tables
# ---------------------------------------------------------------------------


def aggregate_tables():
    s = Svg("02-aggregate-tables")
    top_bar(s, "Aggregate")
    aggregate_sidebar(s)
    aggregate_header(s, "Tables")

    # Table 1: completion
    s.g("Completion by step (table)")
    card(s, 304, 312, 1112, 316, "Completion by step")
    s.text(328, 344, "Completion by step", size=16, weight=700)
    s.text(1392, 344, "Download CSV", size=13, fill=ACCENT, weight=500, anchor="end")
    cols = [
        ("Step", 284, "l"),
        ("Deadline", 120, "r"),
        ("Reached step", 130, "r"),
        ("Completed step", 140, "r"),
        ("% of starters", 130, "r"),
        ("Dropped at step", 130, "r"),
        ("Drop-off rate", 130, "r"),
    ]
    rows = []
    prev = STARTED
    for i, (name, deadline, completed, _, _) in enumerate(STEPS):
        dropped = prev - completed
        rows.append(
            [
                step_cell(i + 1, name),
                f"{deadline} days",
                fmt_int(prev),
                fmt_int(completed),
                (f"{completed / STARTED:.0%}", TEXT, 600),
                fmt_int(dropped),
                f"{dropped / prev:.1%}",
            ]
        )
        prev = completed
    table(s, 328, 360, cols, rows, name="Table / Completion")
    s.end()

    # Table 2: durations
    s.g("Time to complete (table)")
    card(s, 304, 644, 1112, 344, "Time to complete")
    s.text(328, 676, "Time to complete each step (days, completers only)", size=16, weight=700)
    s.text(1392, 676, "Download CSV", size=13, fill=ACCENT, weight=500, anchor="end")
    cols = [
        ("Step", 230, "l"),
        ("Completers", 104, "r"),
        ("5th pct", 80, "r"),
        ("25th pct", 80, "r"),
        ("Median", 80, "r"),
        ("75th pct", 80, "r"),
        ("95th pct", 80, "r"),
        ("Deadline", 90, "r"),
        ("On time", 90, "r"),
        ("Median vs deadline", 150, "r"),
    ]
    rows = []
    for i, (name, deadline, completed, (p5, p25, med, p75, p95), on_time) in enumerate(STEPS):
        diff = med - deadline
        rows.append(
            [
                step_cell(i + 1, name),
                fmt_int(completed),
                f"{p5:g}",
                f"{p25:g}",
                (f"{med:g}", TEXT, 700),
                f"{p75:g}",
                f"{p95:g}",
                f"{deadline}",
                (f"{on_time}%", RED if on_time < 50 else TEXT, 600),
                (f"{abs(diff):g}d over" if diff > 0 else f"{abs(diff):g}d under", RED if diff > 0 else TEXT, 600 if diff > 0 else 400),
            ]
        )
    end_y = table(s, 328, 692, cols, rows, name="Table / Durations")
    s.text(328, end_y + 24, "Deadline = days allowed from the start of each step. On time = completed within the deadline.", size=12, fill=MUTED)
    s.end()
    return s.write()


# ---------------------------------------------------------------------------
# Screen 2: Individual
# ---------------------------------------------------------------------------


def respondent_list(s):
    s.g("Respondent list panel")
    s.rect(0, 65, 440, H - 65, fill=SURFACE)
    s.line(440, 65, 440, H)
    s.text(24, 104, "Respondents", size=16, weight=700)
    s.text(416, 104, "214 match", size=13, fill=MUTED, anchor="end")

    s.g("Search")
    s.rect(24, 120, 392, 36, fill=SURFACE, stroke=BORDER, rx=6)
    s.circle(42, 137, 6, stroke=MUTED, sw=1.5)
    s.line(46.5, 141.5, 51, 146, stroke=MUTED, sw=1.5)
    s.text(60, 142.5, "Search by respondent ID…", size=13, fill=SUBTLE)
    s.end()

    s.g("Demographic filters")
    filt = [("Age", "25–44"), ("Gender", "All genders"), ("Region", "Northeast, South"), ("Status", "All statuses")]
    for i, (label, value) in enumerate(filt):
        fx = 24 + (i % 2) * 202
        fy = 168 + (i // 2) * 44
        s.g(f"Filter / {label}")
        s.rect(fx, fy, 190, 36, fill=SURFACE, stroke=BORDER, rx=6)
        s.text(fx + 12, fy + 22.5, f"{label}:", size=12, fill=MUTED)
        s.text(fx + 14 + text_w(label + ":", 12), fy + 22.5, value, size=12, weight=500)
        chevron(s, fx + 174, fy + 18)
        s.end()
    s.text(24, 276, "+ More filters (education, income, language…)", size=12, fill=ACCENT, weight=500)
    s.text(416, 276, "Clear", size=12, fill=ACCENT, weight=500, anchor="end")
    s.end()

    s.g("List header")
    s.rect(0, 292, 440, 32, fill=FAINT)
    s.text(24, 312, "Respondent", size=12, fill=MUTED, weight=600)
    s.text(190, 312, "Steps", size=12, fill=MUTED, weight=600)
    s.text(416, 312, "Status  ↓", size=12, fill=MUTED, weight=600, anchor="end")
    s.end()

    ry = 324
    for idx, (rid, age, gender, region, states, status, enrolled) in enumerate(RESPONDENTS):
        sel = idx == 0
        s.g(f"Respondent row / {rid}" + (" (selected)" if sel else ""))
        if sel:
            s.rect(0, ry, 440, 60, fill=ACCENT_SOFT)
            s.rect(0, ry, 3, 60, fill=ACCENT)
        s.text(24, ry + 25, rid, size=14, weight=600, fill=ACCENT if sel else TEXT)
        s.text(24, ry + 44, f"{age} · {gender} · {region}", size=12, fill=MUTED)
        for k, st in enumerate(states):
            cx, cy = 196 + k * 15, ry + 30
            if st == "o":
                s.circle(cx, cy, 5, fill=DARK)
            elif st == "l":
                s.circle(cx, cy, 5, fill=RED)
            elif st == "c":
                s.circle(cx, cy, 4.5, fill=SURFACE, stroke=ACCENT, sw=2)
            elif st == "d":
                s.path(f"M{cx - 4} {cy - 4} L{cx + 4} {cy + 4} M{cx + 4} {cy - 4} L{cx - 4} {cy + 4}", stroke=RED, sw=2)
            else:
                s.circle(cx, cy, 4.5, fill=SURFACE, stroke=BORDER, sw=1.5)
        color = RED if status.startswith("Dropped") else (ACCENT if "progress" in status else TEXT)
        s.text(416, ry + 25, status, size=12, weight=600, fill=color, anchor="end")
        s.text(416, ry + 44, f"Enrolled {enrolled}", size=12, fill=MUTED, anchor="end")
        s.line(0, ry + 60, 440, ry + 60, stroke=FAINT)
        s.end()
        ry += 60

    s.g("Step dot key")
    s.circle(28, 941, 4, fill=DARK)
    s.text(36, 945, "On time", size=11, fill=MUTED)
    s.circle(92, 941, 4, fill=RED)
    s.text(100, 945, "Late", size=11, fill=MUTED)
    s.circle(142, 941, 4, fill=SURFACE, stroke=ACCENT, sw=2)
    s.text(150, 945, "Current", size=11, fill=MUTED)
    s.path("M200 937 L208 945 M208 937 L200 945", stroke=RED, sw=2)
    s.text(214, 945, "Dropped", size=11, fill=MUTED)
    s.circle(274, 941, 4, fill=SURFACE, stroke=BORDER, sw=1.5)
    s.text(282, 945, "Not started", size=11, fill=MUTED)
    s.end()

    s.g("Pagination")
    s.text(24, 988, "1–10 of 214", size=12, fill=MUTED)
    button(s, 300, 970, 54, "‹ Prev", h=30)
    button(s, 362, 970, 54, "Next ›", h=30)
    s.end()
    s.end()


def individual_header(s):
    s.g("Respondent header")
    s.text(464, 116, "R-10427", size=24, weight=700)
    label = "In progress · Step 4 of 6"
    bw = text_w(label, 12) + 20
    s.rect(580, 97, bw, 24, fill=ACCENT_SOFT, rx=12)
    s.text(580 + bw / 2, 113, label, size=12, fill=ACCENT, weight=600, anchor="middle")
    s.text(
        464,
        142,
        f"Enrolled {fmt_day(0)} 2026 · Last activity {fmt_day(TODAY_DAY)} 2026 · Day {TODAY_DAY} of journey",
        size=13,
        fill=MUTED,
    )
    button(s, 1238, 94, 86, "‹ Previous", h=32)
    button(s, 1330, 94, 86, "Next ›", h=32)
    s.end()

    s.g("Demographics card")
    card(s, 464, 164, 952, 200, "Demographics")
    s.text(488, 196, "Demographics", size=16, weight=700)
    s.text(1392, 196, "All fields", size=12, fill=MUTED, anchor="end")
    for i, (label, value) in enumerate(DEMOGRAPHICS):
        gx = 488 + (i % 4) * 226
        gy = 228 + (i // 4) * 44
        s.g(f"Field / {label}")
        s.text(gx, gy, label, size=12, fill=MUTED)
        s.text(gx, gy + 19, value, size=14, weight=500)
        s.end()
    s.end()


def journey_card_top(s, view):
    card(s, 464, 380, 952, 620, "Journey")
    s.text(488, 412, "Journey", size=16, weight=700)
    s.text(488, 434, "Time spent on each step and whether it finished before or after the step deadline", size=13, fill=MUTED)
    s.text(1206, 417, "View as", size=13, fill=MUTED, anchor="end")
    segmented(s, 1218, 396, ["Chart", "Table"], view, w_each=87)

    s.g("Journey summary")
    stats = [
        ("Steps completed", "3 of 6", TEXT),
        ("Finished on time", "2 steps", TEXT),
        ("Finished late", "1 step · +2 days", RED),
        ("Current step", "Interview · due in 1 day", ACCENT),
    ]
    for i, (label, value, color) in enumerate(stats):
        tx = 488 + i * (217 + 12)
        s.rect(tx, 452, 217, 52, fill=FAINT, rx=8)
        s.text(tx + 14, 473, label, size=12, fill=MUTED)
        s.text(tx + 14, 493, value, size=14, weight=600, fill=color)
    s.end()


def individual_chart():
    s = Svg("03-individual-chart")
    top_bar(s, "Individual")
    respondent_list(s)
    individual_header(s)

    s.g("Journey (chart)")
    journey_card_top(s, "Chart")

    s.g("Legend")
    lx, ly = 488, 530
    items = [
        ("bar", DARK, "Completed within deadline"),
        ("bar", RED, "Time past deadline"),
        ("current", ACCENT, "In progress"),
        ("deadline", RED, "Step deadline"),
        ("today", ACCENT, "Today"),
    ]
    for kind, color, label in items:
        if kind == "bar":
            s.rect(lx, ly - 7, 20, 12, fill=color, rx=2)
            tx = lx + 28
        elif kind == "current":
            s.rect(lx, ly - 7, 20, 12, fill=ACCENT_SOFT, stroke=ACCENT, rx=2, dash="3 2", sw=1.5)
            tx = lx + 28
        elif kind == "deadline":
            s.line(lx + 4, ly - 9, lx + 4, ly + 7, stroke=RED, sw=2, dash="4 3")
            tx = lx + 14
        else:
            s.line(lx + 4, ly - 9, lx + 4, ly + 7, stroke=ACCENT, sw=2)
            tx = lx + 14
        s.text(tx, ly + 3.5, label, size=12, fill=MUTED)
        lx = tx + text_w(label, 12) + 24
    s.end()

    ax0, ax1, dmax = 720, 1260, 60

    def dx(d):
        return ax0 + (ax1 - ax0) * d / dmax

    s.g("Column headers")
    s.text(488, 564, "Step", size=12, fill=MUTED, weight=600)
    s.text(ax0, 564, "Days since enrollment", size=12, fill=MUTED, weight=600)
    s.text(1392, 564, "Duration", size=12, fill=MUTED, weight=600, anchor="end")
    s.line(488, 574, 1392, 574)
    s.end()

    rows_top, row_h = 588, 58
    rows_bottom = rows_top + row_h * len(STEPS)

    s.g("Gridlines")
    for d in range(0, dmax + 1, 10):
        s.line(dx(d), rows_top, dx(d), rows_bottom, stroke=FAINT)
    s.end()

    for i, ((name, deadline, *_), (start, end, state)) in enumerate(zip(STEPS, INDIVIDUAL)):
        ry = rows_top + i * row_h
        cy = ry + row_h / 2
        s.g(f"Step {i + 1} / {name}")
        if i:
            s.line(488, ry, 1392, ry, stroke=FAINT)
        muted_row = state == "not_started"
        step_badge(
            s,
            500,
            cy - 6,
            i + 1,
            fill=ACCENT if state == "current" else FAINT,
            color=SURFACE if state == "current" else (MUTED if muted_row else TEXT),
        )
        s.text(520, cy - 1.5, name, size=14, weight=600, fill=MUTED if muted_row else TEXT)
        if state == "done":
            dates = f"{fmt_day(start)} → {fmt_day(end)} · {deadline}d allowed"
        elif state == "current":
            dates = f"Started {fmt_day(start)} · {deadline}d allowed"
        else:
            dates = f"{deadline}d allowed"
        s.text(520, cy + 16, dates, size=12, fill=MUTED)

        if state == "done":
            due = start + deadline
            dur = end - start
            s.g("Bar")
            if end <= due:
                s.rect(dx(start), cy - 10, dx(end) - dx(start), 20, fill=DARK, rx=3)
            else:
                s.rect(dx(start), cy - 10, dx(due) - dx(start), 20, fill=DARK, rx=3)
                s.rect(dx(due), cy - 10, dx(end) - dx(due), 20, fill=RED, rx=3)
            s.line(dx(due), cy - 18, dx(due), cy + 18, stroke=RED, sw=2, dash="4 3")
            s.end()
            late = end - due
            s.text(1392, cy - 1.5, f"{dur} days", size=14, weight=600, anchor="end")
            if late > 0:
                s.text(1392, cy + 16, f"{late} days late", size=12, fill=RED, weight=600, anchor="end")
            else:
                s.text(1392, cy + 16, f"{-late} day early" if -late == 1 else f"{-late} days early", size=12, fill=MUTED, anchor="end")
        elif state == "current":
            due = start + deadline
            s.g("Bar")
            s.rect(dx(start), cy - 10, dx(TODAY_DAY) - dx(start), 20, fill=ACCENT_SOFT, stroke=ACCENT, rx=3, dash="4 3", sw=1.5)
            s.line(dx(due), cy - 18, dx(due), cy + 18, stroke=RED, sw=2, dash="4 3")
            s.end()
            s.text(1392, cy - 1.5, f"{TODAY_DAY - start} days so far", size=14, weight=600, fill=ACCENT, anchor="end")
            s.text(1392, cy + 16, f"Due in {due - TODAY_DAY} day", size=12, fill=MUTED, anchor="end")
        else:
            s.text(dx(TODAY_DAY) + 10, cy + 4, "Not started", size=12, fill=SUBTLE)
            s.text(1392, cy + 4, "—", size=14, fill=MUTED, anchor="end")
        s.end()

    s.g("Today marker")
    s.line(dx(TODAY_DAY), rows_top - 4, dx(TODAY_DAY), rows_bottom, stroke=ACCENT, sw=2)
    s.rect(dx(TODAY_DAY) - 30, rows_top - 16, 60, 18, fill=ACCENT, rx=9)
    s.text(dx(TODAY_DAY), rows_top - 3, f"Today", size=11, fill=SURFACE, weight=600, anchor="middle")
    s.end()

    s.g("Time axis")
    s.line(ax0, rows_bottom, ax1, rows_bottom, stroke=MUTED)
    for d in range(0, dmax + 1, 10):
        s.line(dx(d), rows_bottom, dx(d), rows_bottom + 5, stroke=MUTED)
        s.text(dx(d), rows_bottom + 20, str(d), size=11, fill=MUTED, anchor="middle")
    s.text(ax1 + 12, rows_bottom + 20, "days", size=11, fill=MUTED)
    s.end()

    s.text(488, 982, "Hover a bar for start/finish dates and days relative to deadline.", size=12, fill=MUTED)
    s.end()
    return s.write()


def individual_table():
    s = Svg("04-individual-table")
    top_bar(s, "Individual")
    respondent_list(s)
    individual_header(s)

    s.g("Journey (table)")
    journey_card_top(s, "Table")
    cols = [
        ("Step", 212, "l"),
        ("Started", 96, "r"),
        ("Completed", 104, "r"),
        ("Duration", 104, "r"),
        ("Deadline", 84, "r"),
        ("Due by", 90, "r"),
        ("vs. deadline", 108, "r"),
        ("Status", 106, "l"),
    ]
    rows = []
    for i, ((name, deadline, *_), (start, end, state)) in enumerate(zip(STEPS, INDIVIDUAL)):
        step = step_cell(i + 1, name)
        if state == "done":
            due = start + deadline
            late = end - due
            vs = (f"{late} days late", RED, 600) if late > 0 else (f"{-late} day{'s' if -late != 1 else ''} early", TEXT, 400)
            status = ("Late", "late") if late > 0 else ("On time", "on_time")
            row = [step, fmt_day(start), fmt_day(end), f"{end - start} days", f"{deadline} days", fmt_day(due), vs]
        elif state == "current":
            due = start + deadline
            row = [
                step,
                fmt_day(start),
                "—",
                (f"{TODAY_DAY - start} days so far", ACCENT, 600),
                f"{deadline} days",
                fmt_day(due),
                f"Due in {due - TODAY_DAY} day",
            ]
            status = ("In progress", "current")
        else:
            row = [(step), ("—", MUTED, 400), ("—", MUTED, 400), ("—", MUTED, 400), f"{deadline} days", ("—", MUTED, 400), ("—", MUTED, 400)]
            status = ("Not started", "not_started")
        label, kind = status
        row.append(lambda s, x, y, w, h, label=label, kind=kind: pill(s, x + 12, y + h / 2 - 11, label, kind))
        rows.append(row)
    end_y = table(s, 488, 528, cols, rows, row_h=48, head_h=36, name="Table / Journey")
    s.text(488, end_y + 26, "Deadline = days allowed from the start of each step. Due by = step start + deadline.", size=12, fill=MUTED)
    s.text(1392, end_y + 26, "Download CSV", size=13, fill=ACCENT, weight=500, anchor="end")
    s.end()
    return s.write()


if __name__ == "__main__":
    for fn in (aggregate_charts, aggregate_tables, individual_chart, individual_table):
        print(fn())
