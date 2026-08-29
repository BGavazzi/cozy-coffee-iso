#!/usr/bin/env python3
"""A bitmap font, generated from stroke skeletons rather than drawn as pixels.

    python tools/bitmap_font.py                  # build the shipping sizes
    python tools/bitmap_font.py --sample "Flat White  $4.50"
    python tools/bitmap_font.py --check          # sizes, collisions, counters

`NEXT.md` item 3: "No font, no bitmap glyph set, nothing that renders a word in
the palette. Every UI mockup in this repo has ruled lines where text would go,
including the drawn `ui_ticket`, and that is a placeholder rather than a style
decision." This is that.

Why skeletons and not a pixel grid
----------------------------------
A pixel font is normally authored by placing pixels, one glyph at a time, at one
size. That is drawing, and it is drawing that has to be redone for every size --
which is why bitmap fonts ship as "8px", "16px" and nothing between.

Every glyph here is instead a set of POLYLINES on a shared metric grid: six
units from baseline to cap height, four from baseline to x-height, two below for
descenders. A rasteriser scales those to a requested cap height and strokes them
with an integer line algorithm. Size, stroke weight, letterspacing and the
palette are therefore parameters, and the letterforms are the only data.

That is the same split every other producer in this repo makes. `assetlib`
describes a chair as geometry and lets one renderer turn it into pixels;
`ui_chrome` describes a frame as rects and discs for the same reason. A
letterform is the irreducible part -- 'A' is a cultural convention and cannot be
derived from a rule -- so it is the part that gets written down, and nothing
else is.

Curves are polylines on purpose
-------------------------------
At a 7px cap height the round side of an 'o' is three pixels. Tessellating a
real arc at that size produces the same three pixels as a four-point polyline
and costs a curve primitive, an angle convention and a flattening tolerance. The
polyline IS the curve at this resolution. Stated rather than glossed, because it
stops being true somewhere above cap 20 and this font does not go there.

Which sizes ship is measured, not chosen
----------------------------------------
`--check` rasterises the whole set at a range of cap heights and reports, per
size, whether any two glyphs collide and whether every countered glyph still has
a hole in it. A font whose 'e' has filled in is not a smaller font, it is a
broken one. The shipping sizes are the ones that pass; see `SIZES` for what that
turned out to be.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))

# --- metrics -----------------------------------------------------------------
#
# One grid, in units. Baseline is 0 and up is positive, which is the opposite of
# the pixel convention and the right way round for describing letters.
CAP = 6.0        # cap height: A B C D 0 1 2
XH = 4.0         # x-height:  a c e m n o
DESC = -2.0      # descender: g j p q y
SPACING = 1.0    # units of gap built into each glyph's advance

# Ink material and its shadow. `neutral` reads as the ruled-line ink the mockups
# already use, and it is the one ramp that does not carry a hue the parchment
# fill will fight with.
INK = "neutral+1"
INK_DIM = "neutral"


def _dot(x, y):
    """A degenerate stroke: one brush stamp. Periods, dots on i and j."""
    return [(x, y), (x, y)]


# --- the letterforms ---------------------------------------------------------
#
# Each entry is a list of polylines. Ink starts at x=0 and the advance is NOT
# declared -- it is measured off the rasterised ink and one spacing constant,
# per size, by `glyph_box`.
#
# That started as three separate bugs. Hand-declared advances had '1' and 'Q'
# putting ink outside their own cell at cap 9 and 17 (rounding lands the ink one
# pixel further right than it lands the advance), and every advance was one unit
# too tight, so "HH" set the two facing stems adjacent and read as a single
# 2px bar. Measuring the ink cannot be inconsistent with the ink, and it makes
# the font proportional for free: 'i' is narrow because 'i' IS narrow, not
# because someone typed a smaller number next to it.
#
# Capitals run 0..4 in x and 0..6 in y. Lowercase runs 0..4 and 0..4, with
# descenders to -2.

GLYPHS: dict[str, list] = {
    " ": [],

    # --- capitals ---
    "A": [[(0, 0), (2, 6), (4, 0)], [(0.67, 2), (3.33, 2)]],
    "B": [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)],
                [(3, 3), (4, 2), (4, 1), (3, 0), (0, 0)]],
    "C": [[(4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0), (3, 0), (4, 1)]],
    "D": [[(0, 0), (0, 6), (2.5, 6), (4, 4.5), (4, 1.5), (2.5, 0), (0, 0)]],
    "E": [[(4, 6), (0, 6), (0, 0), (4, 0)], [(0, 3), (3, 3)]],
    "F": [[(4, 6), (0, 6), (0, 0)], [(0, 3), (3, 3)]],
    "G": [[(4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0), (3, 0), (4, 1),
                 (4, 2.5), (2.4, 2.5)]],
    "H": [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]],
    "I": [[(0.5, 6), (2.5, 6)], [(1.5, 6), (1.5, 0)], [(0.5, 0), (2.5, 0)]],
    "J": [[(3, 6), (3, 1), (2, 0), (1, 0), (0, 1)]],
    "K": [[(0, 0), (0, 6)], [(3.6, 6), (0.2, 2.6)], [(1.4, 3.8), (4, 0)]],
    "L": [[(0, 6), (0, 0), (4, 0)]],
    "M": [[(0, 0), (0, 6), (3, 3), (6, 6), (6, 0)]],
    "N": [[(0, 0), (0, 6), (4, 0), (4, 6)]],
    "O": [[(1, 6), (3, 6), (4, 5), (4, 1), (3, 0), (1, 0), (0, 1), (0, 5),
                 (1, 6)]],
    "P": [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)]],
    "Q": [[(1, 6), (3, 6), (4, 5), (4, 1), (3, 0), (1, 0), (0, 1), (0, 5),
                 (1, 6)], [(2.6, 1.6), (4.2, 0)]],
    "R": [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)],
                [(2.2, 3), (4, 0)]],
    "S": [[(4, 5), (3, 6), (1, 6), (0, 5), (0, 4), (1, 3), (3, 3), (4, 2),
                 (4, 1), (3, 0), (1, 0), (0, 1)]],
    "T": [[(0, 6), (4, 6)], [(2, 6), (2, 0)]],
    "U": [[(0, 6), (0, 1), (1, 0), (3, 0), (4, 1), (4, 6)]],
    "V": [[(0, 6), (2, 0), (4, 6)]],
    "W": [[(0, 6), (1, 0), (3, 3), (5, 0), (6, 6)]],
    "X": [[(0, 6), (4, 0)], [(0, 0), (4, 6)]],
    "Y": [[(0, 6), (2, 3), (4, 6)], [(2, 3), (2, 0)]],
    "Z": [[(0, 6), (4, 6), (0, 0), (4, 0)]],

    # --- lowercase ---
    "a": [[(4, 4), (4, 0)],
                [(4, 3), (3, 4), (1, 4), (0, 3), (0, 1), (1, 0), (3, 0), (4, 1)]],
    "b": [[(0, 6), (0, 0)],
                [(0, 3), (1, 4), (3, 4), (4, 3), (4, 1), (3, 0), (1, 0), (0, 1)]],
    "c": [[(4, 3), (3, 4), (1, 4), (0, 3), (0, 1), (1, 0), (3, 0), (4, 1)]],
    "d": [[(4, 6), (4, 0)],
                [(4, 3), (3, 4), (1, 4), (0, 3), (0, 1), (1, 0), (3, 0), (4, 1)]],
    "e": [[(0, 2), (4, 2), (4, 3), (3, 4), (1, 4), (0, 3), (0, 1), (1, 0),
                 (3, 0), (4, 1)]],
    "f": [[(3, 5), (2.4, 6), (1.6, 6), (1, 5), (1, 0)], [(0, 4), (2.8, 4)]],
    "g": [[(4, 3), (3, 4), (1, 4), (0, 3), (0, 1), (1, 0), (3, 0), (4, 1)],
                [(4, 4), (4, -1), (3, -2), (1, -2), (0, -1)]],
    "h": [[(0, 6), (0, 0)], [(0, 3), (1, 4), (3, 4), (4, 3), (4, 0)]],
    "i": [_dot(1, 5.6), [(1, 4), (1, 0)]],
    "j": [_dot(2, 5.6), [(2, 4), (2, -1), (1, -2), (0, -1)]],
    "k": [[(0, 6), (0, 0)], [(3.4, 4), (0.2, 1.4)], [(1.4, 2.6), (3.6, 0)]],
    "l": [[(1, 6), (1, 0.8), (2, 0)]],
    "m": [[(0, 0), (0, 4)], [(0, 3.4), (0.8, 4), (2.2, 4), (3, 3.4), (3, 0)],
                [(3, 3.4), (3.8, 4), (5.2, 4), (6, 3.4), (6, 0)]],
    "n": [[(0, 0), (0, 4)], [(0, 3), (1, 4), (3, 4), (4, 3), (4, 0)]],
    "o": [[(1, 4), (3, 4), (4, 3), (4, 1), (3, 0), (1, 0), (0, 1), (0, 3),
                 (1, 4)]],
    "p": [[(0, -2), (0, 4)],
                [(0, 3), (1, 4), (3, 4), (4, 3), (4, 1), (3, 0), (1, 0), (0, 1)]],
    "q": [[(4, -2), (4, 4)],
                [(4, 3), (3, 4), (1, 4), (0, 3), (0, 1), (1, 0), (3, 0), (4, 1)]],
    "r": [[(0, 0), (0, 4)], [(0, 3), (1, 4), (3, 4)]],
    "s": [[(4, 3.4), (3, 4), (1, 4), (0, 3.2), (1, 2), (3, 2), (4, 0.8),
                 (3, 0), (1, 0), (0, 0.6)]],
    "t": [[(1, 6), (1, 1), (2, 0), (3, 0.6)], [(0, 4), (2.8, 4)]],
    "u": [[(0, 4), (0, 1), (1, 0), (3, 0), (4, 1)], [(4, 4), (4, 0)]],
    "v": [[(0, 4), (2, 0), (4, 4)]],
    "w": [[(0, 4), (1, 0), (2.5, 2.6), (4, 0), (5, 4)]],
    "x": [[(0, 4), (4, 0)], [(0, 0), (4, 4)]],
    "y": [[(0, 4), (2.2, 0)], [(4, 4), (1, -2)]],
    "z": [[(0, 4), (4, 4), (0, 0), (4, 0)]],

    # --- digits ---
    # '0' is deliberately NARROWER than 'O' rather than slashed. A slash across
    # a 3px counter fills it, which trades a collision with 'O' for a collision
    # with a solid block -- and `check_counters` would then fail the glyph. The
    # width difference is what `check_distinct` measures, and it holds at every
    # size in SIZES.
    "0": [[(1, 6), (2, 6), (3, 5), (3, 1), (2, 0), (1, 0), (0, 1), (0, 5),
                 (1, 6)]],
    "1": [[(0.6, 4.6), (2, 6), (2, 0)], [(0.6, 0), (3.4, 0)]],
    "2": [[(0, 5), (1, 6), (3, 6), (4, 5), (4, 4), (0, 0), (4, 0)]],
    "3": [[(0, 5.4), (1, 6), (3, 6), (4, 5), (4, 4), (3, 3), (1.6, 3)],
                [(3, 3), (4, 2), (4, 1), (3, 0), (1, 0), (0, 0.6)]],
    "4": [[(3, 0), (3, 6), (0, 2), (4, 2)]],
    "5": [[(4, 6), (0.6, 6), (0.4, 3.4), (3, 3.6), (4, 2.6), (4, 1),
                 (3, 0), (1, 0), (0, 0.6)]],
    "6": [[(3.6, 5.6), (2.6, 6), (1, 6), (0, 5), (0, 1), (1, 0), (3, 0),
                 (4, 1), (4, 2), (3, 3), (1, 3), (0, 2)]],
    "7": [[(0, 6), (4, 6), (1.6, 0)]],
    "8": [[(1, 3), (0, 2), (0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (3, 3),
                 (1, 3), (0, 4), (0, 5), (1, 6), (3, 6), (4, 5), (4, 4), (3, 3)]],
    "9": [[(0.4, 0.4), (1.4, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6),
                 (0, 5), (0, 4), (1, 3), (3, 3), (4, 4)]],

    # --- punctuation and symbols ---
    ".": [_dot(0.5, 0)],
    ",": [[(1, 0.8), (1, 0), (0, -1)]],
    ":": [_dot(0.5, 3), _dot(0.5, 0)],
    ";": [_dot(1, 3), [(1, 0.8), (1, 0), (0, -1)]],
    "!": [[(0.5, 6), (0.5, 1.6)], _dot(0.5, 0)],
    "?": [[(0, 5), (1, 6), (3, 6), (4, 5), (4, 4), (2, 2.6), (2, 1.8)],
                _dot(2, 0)],
    "'": [[(0.5, 6), (0.5, 4.6)]],
    '"': [[(0.4, 6), (0.4, 4.6)], [(2.6, 6), (2.6, 4.6)]],
    "-": [[(0, 2.6), (3, 2.6)]],
    "_": [[(0, -1), (4, -1)]],
    "+": [[(0, 2.6), (4, 2.6)], [(2, 0.6), (2, 4.6)]],
    "=": [[(0, 1.6), (4, 1.6)], [(0, 3.6), (4, 3.6)]],
    "/": [[(0, 0), (3, 6)]],
    "\\": [[(0, 6), (3, 0)]],
    "(": [[(2, 6), (0.6, 4.4), (0.6, 1.6), (2, 0)]],
    ")": [[(0, 6), (1.4, 4.4), (1.4, 1.6), (0, 0)]],
    "[": [[(2, 6), (0.6, 6), (0.6, 0), (2, 0)]],
    "]": [[(0, 6), (1.4, 6), (1.4, 0), (0, 0)]],
    "*": [[(2, 2.4), (2, 6)], [(0.4, 3.2), (3.6, 5.2)],
                [(3.6, 3.2), (0.4, 5.2)]],
    "#": [[(1.2, 0), (1.8, 6)], [(3.2, 0), (3.8, 6)],
                [(0.4, 2), (4.6, 2)], [(0.6, 4), (4.8, 4)]],
    "$": [[(4, 5), (3, 6), (1, 6), (0, 5), (0, 4), (1, 3), (3, 3), (4, 2),
                 (4, 1), (3, 0), (1, 0), (0, 1)], [(2, 0), (2, 6)]],
    "%": [[(0, 0), (4, 6)], _dot(0.4, 5), _dot(3.6, 1)],
    "<": [[(3, 5), (0, 3), (3, 1)]],
    ">": [[(0, 5), (3, 3), (0, 1)]],

    # Currency and arrows. A shop UI needs a price and a direction, and both are
    # cheaper here than as separate icon assets.
    "@": [[(3.4, 1), (2, 1), (1.4, 2), (1.4, 3), (2, 4), (3.4, 4), (3.4, 1),
                 (4.4, 1), (5, 2), (5, 4), (4, 5.4), (2, 5.4), (0.6, 4), (0.6, 2),
                 (2, 0.6), (4, 0.6)]],
    "^": [[(0, 4), (2, 6), (4, 4)]],
    "~": [[(0, 2.6), (1, 3.6), (3, 1.6), (4, 2.6)]],
}


# --- rasteriser --------------------------------------------------------------

def scale_for(cap: int) -> float:
    """Units to pixels.

    Six units span baseline to cap, and a cap height of `cap` PIXELS is `cap - 1`
    pixel steps between the baseline row and the cap row -- an inclusive count,
    because both rows carry ink. At cap 7 this is exactly 1.0, which is why the
    grid was written in the units it was: the reference size needs no rounding
    anywhere, and 13 and 19 are exact doublings and triplings of it.
    """
    return (cap - 1) / CAP


def _r(v: float) -> int:
    """Round half UP, always.

    Python's `round` is banker's rounding: round(1.5) is 2 but round(2.5) is 2
    and round(4.5) is 4. A letterform is full of coordinates that are symmetric
    about its centre, and a rounding rule that treats .5 differently depending
    on the integer beside it breaks that symmetry at some sizes and not others.
    'W' came out with its two halves different widths and '^' with one leg
    shorter than the other, at cap 7 only, for exactly this reason.
    """
    return int(math.floor(v + 0.5))


def _brush(mark, x: int, y: int, weight: int) -> None:
    for dy in range(weight):
        for dx in range(weight):
            mark(x + dx, y + dy)


def _line(mark, x0: int, y0: int, x1: int, y1: int, weight: int) -> None:
    """Integer Bresenham. No anti-aliasing, ever.

    A blended edge pixel is a colour that is not on the palette, which every
    other producer here is checked for. Text is the place that temptation is
    strongest and the place it would be most visible, so the line algorithm
    simply cannot produce one.
    """
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        _brush(mark, x0, y0, weight)
        if x0 == x1 and y0 == y1:
            return
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def cell_height(cap: int) -> tuple[int, int]:
    """(height, baseline_row) of the shared line cell, in pixels.

    Every glyph gets the same vertical cell -- ascender space above, descender
    space below -- because a line of text has one baseline and the cell is what
    puts every glyph on it.
    """
    s = scale_for(cap)
    asc = _r(CAP * s)
    return asc + _r(-DESC * s) + 1, asc


def _ink(ch: str, cap: int, weight: int) -> tuple[set, int, int]:
    """Stroke the skeleton. Returns (ink, cell height, baseline row).

    y counts DOWN from the top of the cell, which is the pixel convention; the
    skeleton counts up from the baseline, which is the type convention. The
    single conversion lives here so nothing else has to hold both in mind.
    """
    s = scale_for(cap)
    h, base = cell_height(cap)
    ink: set = set()

    def mark(x, y):
        ink.add((x, y))

    for poly in GLYPHS[ch]:
        pts = [(_r(x * s), base - _r(y * s)) for x, y in poly]
        if len(pts) == 1:
            _brush(mark, pts[0][0], pts[0][1], weight)
            continue
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            _line(mark, x0, y0, x1, y1, weight)
    return ink, h, base


_CACHE: dict = {}


def raster(ch: str, cap: int, weight: int = 1) -> tuple[set, int, int, int]:
    """One glyph as a set of (x, y) ink pixels, plus (advance, height, baseline).

    The advance is the ink's own right edge plus the spacing gap, MEASURED
    rather than declared. A declared advance can disagree with the ink it is
    supposed to contain -- it did, on '1' and 'Q', and only at the sizes where
    rounding pushed them apart -- and a measured one cannot.
    """
    if ch not in GLYPHS:
        ch = "?"
    key = (ch, cap, weight)
    if key in _CACHE:
        return _CACHE[key]
    ink, h, base = _ink(ch, cap, weight)
    gap = max(1, _r(SPACING * scale_for(cap)))
    if ink:
        adv = max(x for x, _ in ink) + 1 + gap
    else:
        # A space has no ink to measure, so it is the one glyph whose width is a
        # decision. Set from the lowercase 'n' width, which is the standard
        # typographic answer and keeps it proportional to everything else.
        n_ink, _, _ = _ink("n", cap, weight)
        adv = max(x for x, _ in n_ink) + 1
    out = (ink, adv, h, base)
    _CACHE[key] = out
    return out


def glyph_box(ch: str, cap: int, weight: int = 1) -> tuple[int, int, int]:
    """(advance, height, baseline_row) in pixels for one glyph cell."""
    _, adv, h, base = raster(ch if ch in GLYPHS else "?", cap, weight)
    return adv, h, base


# --- text --------------------------------------------------------------------

def measure(text: str, cap: int, tracking: int = 0) -> tuple[int, int, int]:
    """(width, height, baseline_row) of a single line, in pixels."""
    _, h, base = glyph_box("A", cap)
    w = 0
    for ch in text:
        adv, _, _ = glyph_box(ch, cap)
        w += adv + tracking
    return max(0, w - tracking), h, base


def ink_of(text: str, cap: int, weight: int = 1, tracking: int = 0) -> tuple[set, int, int, int]:
    """A whole line as one ink set, in line-local pixel coordinates."""
    out: set = set()
    x = 0
    _, h, base = glyph_box("A", cap)
    for ch in text:
        g, adv, _, _ = raster(ch if ch in GLYPHS else "?", cap, weight)
        for px, py in g:
            out.add((x + px, py))
        x += adv + tracking
    return out, max(0, x - tracking), h, base


def wrap(text: str, cap: int, width: int, tracking: int = 0) -> list[str]:
    """Greedy word wrap to a pixel width.

    Words longer than the line are placed alone and allowed to overrun rather
    than being broken mid-word: a hyphenation rule is a typographic decision
    this font has no basis for making, and an overrun is visible where a silent
    mid-word break is not.
    """
    lines: list[str] = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split(" "):
            trial = f"{cur} {word}".strip()
            if cur and measure(trial, cap, tracking)[0] > width:
                lines.append(cur)
                cur = word
            else:
                cur = trial
        lines.append(cur)
    return lines


def draw(canvas, text: str, x: int, y: int, cap: int, *, weight: int = 1,
         tracking: int = 0, ink: str = INK, shadow: str | None = None) -> int:
    """Stamp a line onto a `ui_chrome.Canvas` at (x, y) = top-left of the cell.

    Returns the advance so callers can chain. `shadow` draws the same ink offset
    one pixel down-right FIRST, which is the cheapest legibility win available
    when text lands on a fill whose value is close to the ink's -- and unlike an
    outline it costs one extra material rather than a second pass over the
    palette.
    """
    marks, w, _, _ = ink_of(text, cap, weight, tracking)
    if shadow:
        for px, py in marks:
            canvas.put(x + px + 1, y + py + 1, shadow)
    for px, py in marks:
        canvas.put(x + px, y + py, ink)
    return w


def block(canvas, text: str, x: int, y: int, cap: int, width: int, *,
          leading: int = 2, **kw) -> int:
    """Wrapped, multi-line. Returns the height consumed."""
    _, h, _ = glyph_box("A", cap)
    lines = wrap(text, cap, width, kw.get("tracking", 0))
    for i, line in enumerate(lines):
        draw(canvas, line, x, y + i * (h + leading), cap, **kw)
    return len(lines) * (h + leading) - leading


# --- checks ------------------------------------------------------------------
#
# Every one of these was verified to fail before it was believed: see
# `_selftest` at the bottom, which perturbs the font and requires each check to
# notice.

COUNTERED = set("ABDOPQRabdegopq0468")
DESCENDING = set("gjpqy,;_")


def check_distinct(cap: int, weight: int = 1) -> list[str]:
    """Do any two glyphs rasterise to the same pixels?

    The classic collisions are I/l/1 and O/0, and they are collisions a font
    ships with unless someone looks. Comparing the ink set AND the advance,
    because two glyphs that differ only in width are still two glyphs -- that is
    exactly how '0' is kept apart from 'O' here.
    """
    seen: dict = {}
    for ch in GLYPHS:
        if not GLYPHS[ch]:
            continue
        ink, adv, _, _ = raster(ch, cap, weight)
        seen.setdefault((adv, frozenset(ink)), []).append(ch)
    return [f"cap {cap}: {sorted(v)!r} rasterise identically"
            for v in seen.values() if len(v) > 1]


def _counters(ink: set, w: int, h: int) -> int:
    """Enclosed background regions, by flooding the outside and counting what
    the flood could not reach."""
    outside = set()
    stack = [(x, -1) for x in range(-1, w + 1)]
    stack += [(x, h) for x in range(-1, w + 1)]
    stack += [(-1, y) for y in range(h)] + [(w, y) for y in range(h)]
    while stack:
        p = stack.pop()
        if p in outside or p in ink:
            continue
        x, y = p
        if not (-1 <= x <= w and -1 <= y <= h):
            continue
        outside.add(p)
        stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    holes = 0
    seen = set()
    for y in range(h):
        for x in range(w):
            if (x, y) in ink or (x, y) in outside or (x, y) in seen:
                continue
            holes += 1
            st = [(x, y)]
            while st:
                q = st.pop()
                if q in seen or q in ink or not (0 <= q[0] < w and 0 <= q[1] < h):
                    continue
                seen.add(q)
                st += [(q[0] + 1, q[1]), (q[0] - 1, q[1]),
                       (q[0], q[1] + 1), (q[0], q[1] - 1)]
    return holes


def check_counters(cap: int, weight: int = 1) -> list[str]:
    """Does every glyph that should have a hole still have one?

    This is the check that decides how small the font can go. An 'e' whose
    aperture has closed is not a smaller 'e', it is a blob, and no palette or
    coverage metric can see the difference -- both measure colour, and this is a
    question about topology.
    """
    out = []
    for ch in sorted(COUNTERED):
        ink, adv, h, _ = raster(ch, cap, weight)
        if _counters(ink, adv, h) < 1:
            out.append(f"cap {cap}: {ch!r} has no counter left -- the hole has "
                       f"filled in")
    return out


def check_bounds(cap: int, weight: int = 1) -> list[str]:
    """Ink inside its own cell, on the baseline, and descending only where
    declared."""
    out = []
    for ch, polys in GLYPHS.items():
        if not polys:
            continue
        ink, adv, h, base = raster(ch, cap, weight)
        xs = [p[0] for p in ink]
        ys = [p[1] for p in ink]
        if min(xs) < 0 or max(xs) >= adv:
            out.append(f"cap {cap}: {ch!r} ink spans x {min(xs)}..{max(xs)} "
                       f"outside its {adv}px advance")
        if min(ys) < 0 or max(ys) >= h:
            out.append(f"cap {cap}: {ch!r} ink spans y {min(ys)}..{max(ys)} "
                       f"outside its {h}px cell")
        descends = max(ys) > base
        if descends and ch not in DESCENDING:
            out.append(f"cap {cap}: {ch!r} drops below the baseline and is not "
                       f"declared a descender")
        if not descends and ch in DESCENDING:
            out.append(f"cap {cap}: {ch!r} is declared a descender and does not "
                       f"descend")
    return out


def check_pairs(cap: int, weight: int = 1) -> list[str]:
    """No two adjacent glyphs' ink may touch, in any ordered pair.

    Advances are per-glyph rather than a monospaced cell, which is what makes
    the setting proportional. Every ordered pair is rendered, because the pair
    that collides is never the pair anyone thinks to try.

    What this can and cannot catch, established by perturbing it rather than
    assumed. Setting `SPACING` to zero does NOT trip it: `raster` floors the gap
    at `max(1, ...)`, so a clear column survives however the spacing constant is
    tuned. Removing one pixel from the computed advance trips it on 5923 of the
    7921 pairs. So this is a guard on the ADVANCE RULE, not on the spacing
    parameter -- which is worth stating, because "true by construction" is a
    claim a later edit to that rule would invalidate silently, and it is the
    only reason to run 7921 renders.
    """
    cache = {ch: raster(ch, cap, weight) for ch in GLYPHS}
    out = []
    for a, (ia, aa, _, _) in cache.items():
        if not ia:
            continue
        for b, (ib, _, _, _) in cache.items():
            if not ib:
                continue
            shifted = {(x + aa, y) for x, y in ib}
            for x, y in ia:
                if any((x + dx, y + dy) in shifted
                       for dx in (0, 1) for dy in (-1, 0, 1)):
                    out.append(f"cap {cap}: {a!r}{b!r} ink touches -- the pair "
                               f"reads as one glyph")
                    break
    return out


def check(cap: int, weight: int = 1) -> list[str]:
    return (check_distinct(cap, weight) + check_counters(cap, weight)
            + check_bounds(cap, weight) + check_pairs(cap, weight))


# The sizes that pass every check above. Filled in from a measured sweep rather
# than picked; `--check` reprints the sweep so the claim stays falsifiable.
SIZES = (7, 9, 11, 13)


def survey(lo: int = 5, hi: int = 20, weight: int = 1) -> dict[int, list[str]]:
    return {cap: check(cap, weight) for cap in range(lo, hi + 1)}


# --- output ------------------------------------------------------------------

def _canvas(w: int, h: int):
    from ui_chrome import Canvas
    return Canvas(w, h)


def render_line(text: str, cap: int, *, weight: int = 1, tracking: int = 0,
                ink: str = INK, shadow: str | None = None, pad: int = 1):
    """One line as a resolved RGB pixel list, via `ui_chrome`'s own Canvas.

    Deliberately the same Canvas and the same `resolve` the drawn chrome uses,
    rather than a second path that writes colours directly. Text on a UI panel
    is the same kind of object as the panel, and sharing the resolve step is
    what keeps it palette-exact without a second implementation to check.
    """
    from ui_chrome import resolve
    from pixelize import load_palette
    w, h, _ = measure(text, cap, tracking)
    extra = 1 if shadow else 0
    c = _canvas(w + pad * 2 + extra, h + pad * 2 + extra)
    draw(c, text, pad, pad, cap, weight=weight, tracking=tracking, ink=ink,
         shadow=shadow)
    return resolve(c, load_palette())


def save_png(px, w: int, h: int, path: Path) -> None:
    from PIL import Image
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    img.putdata([(c[0], c[1], c[2], 255) if c else (0, 0, 0, 0) for c in px])
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def atlas(cap: int, weight: int = 1, columns: int = 16):
    """The whole glyph set on one sheet, plus the metrics to cut it back up.

    A grid rather than a tight pack: every cell is the same size, so a consumer
    reads a glyph's rect from its index by arithmetic instead of from a table.
    The per-glyph ADVANCE still has to travel, because the cells are uniform and
    the font is not -- that is the whole difference between this and a
    monospaced sheet.
    """
    from ui_chrome import resolve
    from pixelize import load_palette
    chars = [ch for ch in GLYPHS if ch != " "]
    cw = max(glyph_box(ch, cap, weight)[0] for ch in chars)
    ch_h, base = cell_height(cap)
    rows = (len(chars) + columns - 1) // columns
    c = _canvas(cw * columns, ch_h * rows)
    metrics = {}
    for i, g in enumerate(chars):
        gx, gy = (i % columns) * cw, (i // columns) * ch_h
        ink, adv, _, _ = raster(g, cap, weight)
        for px, py in ink:
            c.put(gx + px, gy + py, INK)
        metrics[g] = {"index": i, "advance": adv}
    metrics[" "] = {"index": -1, "advance": glyph_box(" ", cap, weight)[0]}
    px, w, h = resolve(c, load_palette())
    return px, w, h, {
        "cap": cap, "weight": weight, "cell": [cw, ch_h], "columns": columns,
        "baseline": base, "ascent": base, "descent": ch_h - base - 1,
        "glyphs": metrics,
    }


def fit_cap(text: str, width: int, sizes=SIZES, weight: int = 1,
            tracking: int = 0) -> int | None:
    """The largest shipping size at which `text` fits `width` pixels.

    `ui_chrome.ticket` carries two ruled lines with the comment "which is what
    reads as an order written on it without drawing text that would be mush at
    this size". That was an assertion about a font that did not exist. It is now
    measurable, and the answer is: partly. A 36px writing area takes a short
    order at cap 7 and does not take a long one, so the caller gets the size
    that fits or None, and can decide.
    """
    for cap in sorted(sizes, reverse=True):
        if measure(text, cap, tracking)[0] <= width:
            return cap
    return None


def check_render(px, w: int, h: int) -> list[str]:
    """Rendered text held to the UI gate, at the same threshold.

    `ui_chrome` imports `ui_forge`'s thresholds rather than restating them so
    drawn art clears the bar generated art had to. Text is drawn art, and
    `MAX_ISOLATED` is imported here for the same reason and at the same value.

    Two deliberate differences, and both are about what the metric MEANS rather
    than about how strict it is:

    `MIN_ICON_COVERAGE` is skipped. It asserts an icon fills its box; a line of
    text is mostly background by design, and applying it would be asserting
    something false about a different kind of object.

    Isolation is measured over EIGHT neighbours, not four. The metric asks "is
    this pixel part of a stroke, or is it speckle from quantizing a
    photograph?" A one-pixel diagonal stroke -- which is what 'X', '/' and 'V'
    are at cap 7 -- has no orthogonal neighbour at all and is nonetheless
    perfectly good art. Measured, on the same images:

        font sheet cap 7     4-conn 11.5%    8-conn  1.5%
        ui_dialogue_frame    4-conn  0.3%    8-conn  0.0%
        chair_wood_dir0      4-conn  1.1%    8-conn  0.0%
        random palette noise 4-conn 90.3%    8-conn 80.6%

    The last row is the one that matters: the reading that stops punishing a
    diagonal still separates real art from real noise by fifty-fold, so this is
    a correction to the metric and not a threshold raised to fit the art. The
    4-neighbour reading is left alone everywhere else, because for filled art a
    pixel with no orthogonal neighbour genuinely is a downsample artefact.
    """
    from pixelize import audit
    from ui_forge import MAX_ISOLATED
    out = []
    rep = audit(px, load_ramps())
    if rep["off_palette"]:
        out.append(f"{rep['off_palette_pct']}% off-palette, which drawing "
                   f"straight from a ramp index should make impossible")
    solid = [i for i, c in enumerate(px) if c is not None]
    neighbours = ((1, 0), (-1, 0), (0, 1), (0, -1),
                  (1, 1), (1, -1), (-1, 1), (-1, -1))
    iso = sum(
        1 for i in solid
        if not any(0 <= (i % w) + dx < w and 0 <= (i // w) + dy < h
                   and px[((i // w) + dy) * w + (i % w) + dx] == px[i]
                   for dx, dy in neighbours)
    )
    ratio = iso / max(1, len(solid))
    if ratio > MAX_ISOLATED:
        out.append(f"{ratio:.1%} of ink pixels match none of their four "
                   f"neighbours (cap {MAX_ISOLATED:.1%})")
    return out


def load_ramps():
    from pixelize import load_palette
    return load_palette()


def demo(out: Path) -> str:
    """Text inside the chrome that was drawn with ruled lines standing in for it.

    This is the pairing the two producers were always for: `ui_chrome` declares
    which rows and columns of a frame may be stretched, so one 64px source
    serves a dialogue box of any size, and the font fills it. Neither half is
    much use alone -- a frame with nothing in it, or text floating on nothing.
    """
    from PIL import Image
    from pixelize import load_palette, material
    import ui_chrome as U

    ramps = load_palette()

    def rgb(tok):
        name, idx = material(tok)
        return ramps[name][max(0, min(len(ramps[name]) - 1, idx))]

    panels = []

    # A dialogue frame stretched to hold three lines, via the real nine-slice.
    src = U.dialogue_frame(1.0)
    spx, sw, sh = U.resolve(src, ramps)
    ins = U.CHROME["ui_dialogue_frame"][1]
    bw, bh = 208, 76
    bpx = U.expand(spx, sw, sh, ins, bw, bh)
    c = U.Canvas(bw, bh)
    body = ("Morning! The usual, or are we being adventurous today? "
            "The single origin just landed.")
    block(c, body, ins[0] + 3, ins[1] + 3, 7, bw - ins[0] - ins[2] - 6)
    panels.append(("dialogue", bpx, bw, bh, c))

    # A nameplate with a name in it, at its drawn size.
    npc = U.nameplate(1.5)
    npx, nw, nh = U.resolve(npc, ramps)
    c2 = U.Canvas(nw, nh)
    name = "Marisol"
    sx, span, _ = U.nameplate_span(1.5)
    cap = fit_cap(name, span) or min(SIZES)
    tw = measure(name, cap)[0]
    draw(c2, name, sx + (span - tw) // 2,
         (nh - cell_height(cap)[0]) // 2 + 1, cap)
    panels.append(("nameplate", npx, nw, nh, c2))

    # The ticket, with the order the ruled lines were standing in for.
    tpx_src = U.ticket(1.5, ruled=False)
    tpx, tw2, th = U.resolve(tpx_src, ramps)
    c3 = U.Canvas(tw2, th)
    tx, ty, tspan, pitch = U.ticket_span(1.5)
    for i, line in enumerate(("Latte", "Oat, x2")):
        cap = fit_cap(line, tspan) or min(SIZES)
        draw(c3, line, tx, ty + i * pitch, cap)
    panels.append(("ticket", tpx, tw2, th, c3))

    pad, gap = 8, 10
    W = pad * 2 + sum(p[2] for p in panels) + gap * (len(panels) - 1)
    H = pad * 2 + max(p[3] for p in panels)
    img = Image.new("RGB", (W, H), rgb("wood-2"))
    x = pad
    for _, bg, w, h, overlay in panels:
        y = pad + (H - pad * 2 - h) // 2
        base = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        base.putdata([(c[0], c[1], c[2], 255) if c else (0, 0, 0, 0) for c in bg])
        ink_px, _, _ = U.resolve(overlay, ramps)
        top = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        top.putdata([(c[0], c[1], c[2], 255) if c else (0, 0, 0, 0) for c in ink_px])
        base.alpha_composite(top)
        img.paste(base, (x, y), base)
        x += w + gap
    path = out / "font_in_chrome.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    img.resize((img.width * 3, img.height * 3), Image.NEAREST).save(path)
    return str(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="sweep cap heights and report which are legible")
    ap.add_argument("--sample", default=None, help="render one string and exit")
    ap.add_argument("--demo", action="store_true",
                    help="text inside the nine-slice chrome, as a PNG")
    ap.add_argument("--cap", type=int, default=7)
    ap.add_argument("--weight", type=int, default=1)
    # Its own directory under out/ui/, not loose beside the icons.
    # `package_godot.stage_ui` globs `out/ui/*.png` and treats every hit as an
    # icon; a font sheet is not an icon and a demo render is not an asset, and
    # relying on the `_` prefix convention to keep them apart is one careless
    # filename away from staging a preview into the game.
    ap.add_argument("--out", default=str(ROOT / "out" / "ui" / "font"))
    args = ap.parse_args()

    if args.check:
        results = survey(weight=args.weight)
        ok = [c for c, p in results.items() if not p]
        print(f"cap heights 5..20 at weight {args.weight}")
        for cap, problems in results.items():
            mark = "ok  " if not problems else "FAIL"
            note = "" if not problems else f"  {len(problems)} problem(s): {problems[0]}"
            print(f"  cap {cap:>2}  {mark}{note}")
        print(f"\nlegible: {ok}")
        print(f"SIZES declares: {list(SIZES)}")
        if set(SIZES) - set(ok):
            print(f"  BLOCKER  SIZES claims {sorted(set(SIZES) - set(ok))} "
                  f"which do not pass", file=sys.stderr)
            return 1
        return 0

    out = Path(args.out)
    if args.demo:
        print(demo(out))
        return 0
    if args.sample:
        px, w, h = render_line(args.sample, args.cap, weight=args.weight)
        save_png(px, w, h, out / "font_sample.png")
        print(f"{args.sample!r} at cap {args.cap}: {w}x{h} -> "
              f"{out / 'font_sample.png'}")
        for p in check_render(px, w, h):
            print(f"  {p}")
        return 0

    print(f"{len(GLYPHS)} glyphs; shipping cap heights {list(SIZES)}")
    problems = []
    written = []
    for cap in SIZES:
        bad = check(cap, args.weight)
        problems += bad
        px, w, h, meta = atlas(cap, args.weight)
        name = f"font_cap{cap}"
        save_png(px, w, h, out / f"{name}.png")
        meta["file"] = f"{name}.png"
        meta["sheet_size"] = [w, h]
        bad += [f"cap {cap} sheet: {m}" for m in check_render(px, w, h)]
        problems += [p for p in bad if p.startswith(f"cap {cap} sheet")]
        written.append((cap, w, h, meta))
        print(f"  cap {cap:>2}  {w:>3}x{h:<3} sheet  "
              f"{'ok' if not bad else bad}")

    index = {"sizes": {str(cap): meta for cap, _, _, meta in written},
             "ink": INK}
    (out / "font.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    print(f"\n-> {out / 'font.json'} and {len(written)} sheet(s)")
    for p in problems:
        print(f"  BLOCKER  {p}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
