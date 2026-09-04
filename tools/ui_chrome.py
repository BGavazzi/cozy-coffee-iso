#!/usr/bin/env python3
"""UI chrome, drawn rather than generated. The other half of `ui_forge.py`.

`ui_forge.py` ran all fourteen `cat: ui` entries through SDXL and the result
split on an axis none of its checks measure: every icon that depicts an
*object* came out usable, and every piece of abstract *chrome* came out
wrong. Asked for a speech bubble, SDXL renders a photographed tablet with a
picture in it. Asked for a nameplate banner, a framed panel. Asked for a
five-pointed star, an eight-pointed burst. Three of those passed the
isolated-pixel check comfortably -- they are wrong-shape failures, and no
metric in this repo can see shape.

The reason is structural, and it is the one that caps the character work
(`ART_CRITIQUE.md`, "The character ceiling is stage 2"): this pipeline makes
things, not abstractions. A cup is a thing SDXL has seen a million of. A
nine-slice dialogue frame is *geometry with a semantic role* -- defined
corners, a border of known width, a fill region that must tile -- and a
diffusion model has no reason to produce that rather than a photograph of
something frame-shaped. It is not a prompt to tune. It is the wrong tool.

So chrome takes the third path in this repo, next to 3D props and 2D icons:
authored procedurally, the same answer `assetlib.py` gives for furniture. A
rounded rect with a two-pixel border is a few lines of code and is exactly
right every time, at any size, on any seed, with no GPU.

    python tools/ui_chrome.py                 # all seven
    python tools/ui_chrome.py --only ui_coin
    python tools/ui_chrome.py --target 32     # scales, unlike a 1024px render

What this buys beyond correctness is the thing generation cannot give at
all: **nine-slice metadata**. A generated 64x64 speech bubble is a 64x64
speech bubble forever. A drawn one declares which rows and columns may be
stretched, so one source serves every dialogue box in the game. Those insets
are checked, not asserted -- `check_nine_slice` verifies the stretch bands
really are uniform along the axis they claim to tile on, because "this
region repeats" is exactly the kind of claim a later edit invalidates
silently.

Output lands in `out/ui/` beside the generated icons and deliberately
overwrites the chrome ids `ui_forge` produced badly. `out/ui/nine_slice.json`
carries the insets. Every piece is held to `ui_forge`'s own thresholds --
`MIN_ICON_COVERAGE` and `MAX_ISOLATED`, imported rather than restated -- so
drawn art clears the same bar generated art had to, not a softer one written
to make this file look good. Measured across three sizes, worst
isolated-pixel ratio of the seven against that 6.2% cap:

    32 px   6.1%      64 px   3.6%      128 px   1.6%

The 32px column is the honest one. It only reads that way after the star's
edge was floored at 2px; at a freely-scaling thickness the same drawing came
back at 7.8% and 13.3%. See `_star`.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from style import DEFAULT_STYLE, load_style  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
UI_DIR = ROOT / "out" / "ui"

# Chrome's own material vocabulary, named for the role rather than the ramp,
# so a palette revision changes one line each instead of forty call sites.
#
# The "+n" offsets are read as absolute ramp indices here, and that is not a
# reinterpretation of `pixelize.material()` -- it is that function evaluated
# at the only lighting flat art has. `shade_toon` computes
# `lam * (n - 1) + tone`; with no renderer there is no lambert, lam is 0, and
# the offset *is* the index. Flat art is the lam=0 case of the shaded path,
# not a parallel convention.
BORDER = "wood+1"     # dark warm brown -- the frame edge
BORDER_HI = "wood+3"  # two steps up, for a bevel
FILL = "cream+3"      # parchment, the panel interior
FILL_DIM = "cream+1"  # a recessed interior
INK = "neutral+1"     # ruled lines, tick marks
GOLD = "gold_coin"    # the one spot gold; 1-step, so it needs a drawn edge
GLOW = "lamp_glow"


class Canvas:
    """A grid of material tokens. Not pixels -- resolution happens once, at
    the end, so every shape here composes without caring about colour."""

    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.mat: list[str | None] = [None] * (w * h)

    def put(self, x: int, y: int, m: str | None) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            self.mat[y * self.w + x] = m

    def get(self, x: int, y: int) -> str | None:
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.mat[y * self.w + x]
        return None

    def rect(self, x0, y0, x1, y1, m) -> None:
        """Inclusive box."""
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.put(x, y, m)

    def disc(self, cx: float, cy: float, r: float, m) -> None:
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                    self.put(x, y, m)

    def round_rect(self, x0, y0, x1, y1, r: float, m) -> None:
        """Rect with the four corners cut to a circle of radius `r`.

        Corner-cutting is by distance to the corner circle's centre rather
        than by a lookup table, so any radius works and a 32px build is not a
        separately-authored asset.
        """
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                px, py = x + 0.5, y + 0.5
                cx = min(max(px, x0 + r), x1 + 1 - r)
                cy = min(max(py, y0 + r), y1 + 1 - r)
                if (px - cx) ** 2 + (py - cy) ** 2 <= r * r:
                    self.put(x, y, m)

    def poly(self, pts, m) -> None:
        """Even-odd scanline fill. Used for the star and the bubble tail."""
        ys = [p[1] for p in pts]
        n = len(pts)
        for y in range(int(math.floor(min(ys))), int(math.ceil(max(ys))) + 1):
            sy = y + 0.5
            xs = []
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= sy < y1) or (y1 <= sy < y0):
                    xs.append(x0 + (sy - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for a, b in zip(xs[0::2], xs[1::2]):
                for x in range(int(math.floor(a)), int(math.ceil(b))):
                    self.put(x, y, m)


def _star_pts(cx, cy, r_out, r_in, points=5, phase=-math.pi / 2):
    out = []
    for i in range(points * 2):
        r = r_out if i % 2 == 0 else r_in
        a = phase + i * math.pi / points
        out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return out


# --- the pieces --------------------------------------------------------------
#
# Each takes a scale `s` (1.0 == the declared default size) and returns a
# Canvas. Every dimension is computed from `s` rather than hard-coded, so
# `--target 32` is the same drawing at half size, not a second asset.

def dialogue_frame(s: float) -> Canvas:
    """Nine-slice speech bubble. The tail lives inside the LEFT inset.

    That placement is the whole reason this is worth drawing. A tail in the
    centre band would stretch horizontally along with the body and turn into
    a wedge as the box widens; parked in the left corner piece it stays the
    size it was drawn at, whatever the dialogue box grows to.
    """
    w, h = int(64 * s), int(48 * s)
    c = Canvas(w, h)
    body_b = int(35 * s)                     # last row of the bubble body
    b = max(1, int(round(2 * s)))            # border thickness
    r = max(2.0, 5 * s)
    c.round_rect(0, 0, w - 1, body_b, r, BORDER)
    c.round_rect(b, b, w - 1 - b, body_b - b, max(1.0, r - b), FILL)
    # Tail: a triangle hanging off the underside, left of centre. Drawn as a
    # border triangle with a smaller fill triangle inside it, so the two
    # pixel edge continues around the tail rather than stopping at the body.
    tx0, tx1 = int(9 * s), int(21 * s)
    ty = h - 1
    c.poly([(tx0, body_b - b), (tx1, body_b - b), (tx0 + 3 * s, ty)], BORDER)
    c.poly([(tx0 + 1.5 * s, body_b - b - 1), (tx1 - 2.5 * s, body_b - b - 1),
            (tx0 + 3 * s, ty - 3 * s)], FILL)
    return c


def nameplate(s: float) -> Canvas:
    """Horizontal banner with fixed end caps and a stretchable middle."""
    w, h = int(64 * s), int(24 * s)
    c = Canvas(w, h)
    b = max(1, int(round(2 * s)))
    r = max(1.0, 3 * s)
    inset = int(round(4 * s))
    c.round_rect(0, inset, w - 1, h - 1 - inset, r, BORDER)
    c.round_rect(b, inset + b, w - 1 - b, h - 1 - inset - b,
                 max(1.0, r - b), FILL)
    # End caps: a taller block at each end, which is what makes a banner read
    # as a banner rather than as a rounded rectangle.
    cap = int(round(9 * s))
    for x0 in (0, w - cap):
        c.round_rect(x0, 0, x0 + cap - 1, h - 1, r, BORDER)
        c.round_rect(x0 + b, b, x0 + cap - 1 - b, h - 1 - b,
                     max(1.0, r - b), FILL_DIM)
    return c


def nameplate_span(s: float) -> tuple[int, int, int]:
    """(x, width, baseline-ish y) of the banner's writable middle.

    The end caps are drawn OVER the band, so the space a name can occupy is not
    the canvas width and is not the canvas width less a guessed margin -- it is
    the gap between the two caps. `bitmap_font.demo` guessed `w - 16` and put
    the 'l' of "Marisol" underneath the right cap. Published from the same
    numbers the drawing uses so the two cannot drift.
    """
    w, h = int(64 * s), int(24 * s)
    cap = int(round(9 * s))
    pad = max(1, int(round(2 * s)))
    return cap + pad, w - 2 * (cap + pad), h // 2


def upgrade_frame(s: float) -> Canvas:
    """Square badge, corners notched off at 45 degrees, with a bevel line."""
    n = int(64 * s)
    c = Canvas(n, n)
    cut = int(round(9 * s))
    b = max(2, int(round(3 * s)))
    for y in range(n):
        for x in range(n):
            dx, dy = min(x, n - 1 - x), min(y, n - 1 - y)
            if dx + dy < cut:
                continue          # the 45-degree corner notch
            if dx >= b and dy >= b and dx + dy >= cut + b:
                c.put(x, y, FILL)
            else:
                c.put(x, y, BORDER)
    # Bevel: the ring of fill pixels touching the border, one step brighter.
    bevel = [i for i, m in enumerate(c.mat) if m == FILL
             and any(c.get(i % n + dx, i // n + dy) == BORDER
                     for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for i in bevel:
        c.mat[i] = BORDER_HI
    return c


def ticket(s: float, ruled: bool = True) -> Canvas:
    """Order ticket: torn top edge, a perforation, two ruled lines.

    `ruled=False` leaves the writing area empty for real text. The two lines
    were only ever standing in for an order, on the reasoning that text "would
    be mush at this size" -- an assertion about a font that did not exist yet.
    It is now measurable, and `bitmap_font.fit_cap` says it was half right: a
    36px writing area takes "Latte" at cap 9 and does not take "Flat White" at
    any shipping size. So the rules stay the default and become an option
    rather than a fact.

    The tear is a fixed-period sawtooth rather than noise. Random tearing at
    64px produces exactly the isolated pixels `check_icon` blocks on, and a
    regular sawtooth is what hand-drawn pixel art uses anyway, because at
    this size the eye reads "torn" from the silhouette and cannot resolve
    anything finer.
    """
    w, h = int(52 * s), int(64 * s)
    c = Canvas(w, h)
    b = max(1, int(round(2 * s)))
    period = max(4, int(round(6 * s)))
    tooth = max(1, int(round(3 * s)))
    top = tooth + 1
    c.rect(0, top, w - 1, h - 1, BORDER)
    c.rect(b, top + b, w - 1 - b, h - 1 - b, FILL)
    for x in range(w):
        # Distance from this column up to the tear line: a triangle wave.
        d = tooth - abs((x % period) - period // 2)
        for y in range(top - d, top):
            c.put(x, y, BORDER)
        for y in range(top - d + b, top + b):
            c.put(x, y, FILL)
    # Perforation: the dashed fold a real ticket tears on.
    py = int(round(44 * s))
    for x in range(int(round(4 * s)), w - int(round(4 * s)),
                   max(2, int(round(3 * s)))):
        c.put(x, py, INK)
    # Two ruled lines, the second short, which is what reads as "an order
    # written on it" without drawing text that would be mush at this size.
    lh = max(1, int(round(2 * s)))
    if ruled:
        for i, ly in enumerate((int(round(18 * s)), int(round(28 * s)))):
            c.rect(int(round(8 * s)), ly,
                   w - 1 - int(round(8 * s)) - i * int(round(9 * s)),
                   ly + lh - 1, INK)
    return c


def ticket_span(s: float) -> tuple[int, int, int, int]:
    """(x, y, width, line pitch) of the ticket's writing area."""
    w = int(52 * s)
    x = int(round(8 * s))
    return x, int(round(16 * s)), w - 2 * x, int(round(10 * s))


def _star(s: float, fill) -> Canvas:
    """Two nested star polygons: the outer one is the border, the inner the
    fill, and the difference in radii is the edge thickness.

    That thickness has a floor of 2px rather than scaling freely, and the
    floor was measured rather than guessed. At `--target 32` a proportional
    2.2*s edge is 1.1px, and a one-pixel-wide *diagonal* run has no
    four-neighbour of its own colour anywhere along it -- so the star came
    back at 7.8% isolated (13.3% for the empty one) against a 6.2% cap that
    the 64px version clears at 3.2%.

    Two readings of that were available and only one is honest. The cap is
    calibrated on generated icons, where isolated pixels really are speckle,
    and a deliberate 1px diagonal outline is not speckle -- so the metric is
    arguably over-strict here. Raising the cap to let this through would be
    tuning the check to fit the art, which is the exact mistake
    `ART_CRITIQUE.md` records twice already. Thickening the edge is what a
    pixel artist does at 32px anyway, so the art moved and the cap did not.
    """
    n = int(64 * s)
    c = Canvas(n, n)
    cx, cy = n / 2.0, n / 2.0 - n * 0.02
    edge = max(2.0, 2.2 * s)
    c.poly(_star_pts(cx, cy, n * 0.47, n * 0.21), BORDER)
    c.poly(_star_pts(cx, cy, n * 0.47 - edge, n * 0.21 - edge * 0.55), fill)
    return c


def star_rating(s: float) -> Canvas:
    """A five-pointed star, which is the shape that was asked for.

    Drawn as an explicit two-colour ring because `gold_coin` is a one-step
    ramp: `apply_outline` tints a silhouette with `ramps[name][0]`, which for
    a one-step ramp is the fill colour itself, so a gold shape outlines
    invisibly. Spot colours need their edge authored. That is a property of
    the palette rather than a gap in the outliner -- a one-step ramp means
    "emits itself regardless of lighting", and an emissive surface having no
    darker step is the entire point of it.
    """
    return _star(s, GOLD)


def star_rating_empty(s: float) -> Canvas:
    """The unfilled counterpart. A rating widget needs both, and the pair
    costs one argument -- which is a thing generation cannot do at all,
    because two SDXL draws of "a star" are two different stars."""
    return _star(s, FILL_DIM)


def coin(s: float) -> Canvas:
    """Gold coin: brown rim, gold face, an inner ring, one highlight crescent.

    Same one-step-ramp problem as the star, plus the reason the generated
    version came out muddy and gated -- SDXL shades a gold coin with a dozen
    browns and yellows, all of which either snap to the single gold or wander
    into the wood ramp, and the result is a speckled blob. Drawn, it is three
    values and reads instantly.
    """
    n = int(64 * s)
    c = Canvas(n, n)
    cx = cy = n / 2.0
    c.disc(cx, cy, n * 0.46, BORDER)
    c.disc(cx, cy, n * 0.46 - max(1.5, 2 * s), GOLD)
    c.disc(cx, cy, n * 0.30, BORDER_HI)
    c.disc(cx, cy, n * 0.30 - max(1.0, 1.2 * s), GOLD)
    # Highlight: a thin crescent hugging the upper-left rim, made by
    # subtracting a slightly offset disc of the same radius, and painted only
    # where the face is already gold so it never spills over the rim.
    #
    # The first version used a small disc near the centre, and at 64px it
    # read as a crescent moon sitting on a yellow circle rather than as
    # light falling on metal. A specular has to hug the edge it is reflecting
    # off; anything drawn inland is a shape, not a highlight. Nothing here
    # measured that -- the coin passed every check at 1.1% isolated pixels
    # both times. It is the same class of defect as the generated frames,
    # caught the same way, by looking.
    hi = Canvas(n, n)
    hi.disc(cx, cy, n * 0.42, GLOW)
    hi.disc(cx + n * 0.05, cy + n * 0.05, n * 0.42, None)
    for i, m in enumerate(hi.mat):
        if m is not None and c.mat[i] == GOLD:
            c.mat[i] = m
    return c


# id -> (draw fn, nine-slice insets or None).
#
# Insets are (left, top, right, bottom) at scale 1.0 and are VERIFIED by
# `check_nine_slice`, not trusted.
CHROME = {
    "ui_dialogue_frame":    (dialogue_frame, (24, 12, 14, 17)),
    "ui_nameplate":         (nameplate, (11, 8, 11, 8)),
    "ui_upgrade_frame":     (upgrade_frame, (14, 14, 14, 14)),
    "ui_ticket":            (ticket, None),
    "ui_star_rating":       (star_rating, None),
    "ui_star_rating_empty": (star_rating_empty, None),
    "ui_coin":              (coin, None),
}


def check_nine_slice(px, w: int, h: int, insets) -> list[str]:
    """Do the declared stretch bands actually tile?

    A nine-slice's centre column band must be constant along x for every row,
    and its centre row band constant along y for every column -- otherwise
    stretching smears whatever detail is in there. Checked rather than
    asserted in a comment because insets are numbers a future edit will
    silently invalidate, and a frame that stretches wrong is the kind of
    defect that only shows up in the game. It caught its own author on the
    first run: the speech bubble's bottom inset was set from where the body
    ends and not from where the rounded corner ends, so four rows of corner
    fell inside the vertical stretch band.

    Deliberately run on the RESOLVED pixels rather than on the material
    Canvas. The materials are what was drawn; the pixels are what ships, and
    `apply_outline` runs in between and can turn a uniform band into a
    non-uniform one at its edges. Checking the earlier of the two would be
    checking the easier thing.
    """
    left, top, right, bottom = insets
    x0, x1 = left, w - right
    y0, y1 = top, h - bottom
    if x1 <= x0 or y1 <= y0:
        return [f"insets {tuple(insets)} leave no centre band in {w}x{h}"]
    out = []
    for y in range(h):
        if len({px[y * w + x] for x in range(x0, x1)}) > 1:
            out.append(f"row {y} is not constant across the horizontal "
                       f"stretch band x=[{x0},{x1}) -- it would smear when "
                       f"the frame widens")
            break
    for x in range(w):
        if len({px[y * w + x] for y in range(y0, y1)}) > 1:
            out.append(f"column {x} is not constant across the vertical "
                       f"stretch band y=[{y0},{y1}) -- it would smear when "
                       f"the frame grows taller")
            break
    return out


def expand(px, w: int, h: int, insets, out_w: int, out_h: int):
    """Nine-slice a piece up to `out_w` x `out_h`.

    The corners are copied, the edges repeated along one axis, the centre
    along both. Repeated -- not interpolated -- because interpolation invents
    colours and would break the palette-exactness every other tool here
    depends on; and because the bands are verified uniform by
    `check_nine_slice`, repeating a row of the band is indistinguishable from
    repeating any other, which is what makes the operation lossless.

    This exists so the insets are exercised rather than merely written down.
    A number in a JSON file that nothing reads is a number nobody has
    checked, and the engine exporter will want exactly this function when
    `out/ui/` finally gets one (`NEXT.md`, the export gap).
    """
    left, top, right, bottom = insets
    if out_w < left + right or out_h < top + bottom:
        raise ValueError(f"{out_w}x{out_h} is smaller than the fixed borders "
                         f"({left + right}x{top + bottom}) -- a nine-slice "
                         f"can grow but not shrink past its own corners")

    def src_x(x):
        if x < left:
            return x
        if x >= out_w - right:
            return w - (out_w - x)
        span = w - left - right
        return left + (x - left) % span

    def src_y(y):
        if y < top:
            return y
        if y >= out_h - bottom:
            return h - (out_h - y)
        span = h - top - bottom
        return top + (y - top) % span

    return [px[src_y(y) * w + src_x(x)]
            for y in range(out_h) for x in range(out_w)]


def resolve(c: Canvas, ramps: dict):
    """Materials -> palette-exact pixels, then the shared outline pass.

    Reuses `pixelize.apply_outline` rather than drawing edges by hand, so
    chrome gets the same per-surface tinted outline every sprite gets. Its
    selective mode adds internal lines only where two materials sit within
    0.14 OKLab lightness of each other, which here means the deliberate
    high-contrast border/fill boundaries are left alone and the near-value
    ones (bevel against fill) get the line they need.

    Returns (pixels, w, h).
    """
    from pixelize import apply_outline, material
    px = []
    for m in c.mat:
        if m is None:
            px.append(None)
            continue
        rname, idx = material(m)
        ramp = ramps[rname]
        px.append(ramp[max(0, min(len(ramp) - 1, idx))])
    if c.w == c.h:
        return apply_outline(px, list(c.mat), c.w, ramps, selective=True), \
            c.w, c.h
    # `apply_outline` assumes a square grid, because it was written for the
    # sprite path where everything is. Pad to a square, outline, crop back --
    # cheaper and safer than generalising a function four other tools depend
    # on. The pad is transparent, so the silhouette pass sees the same edges.
    n = max(c.w, c.h)
    ox, oy = (n - c.w) // 2, (n - c.h) // 2
    sq_px: list = [None] * (n * n)
    sq_mat: list = [None] * (n * n)
    for y in range(c.h):
        for x in range(c.w):
            sq_px[(y + oy) * n + x + ox] = px[y * c.w + x]
            sq_mat[(y + oy) * n + x + ox] = c.mat[y * c.w + x]
    sq_px = apply_outline(sq_px, sq_mat, n, ramps, selective=True)
    out = [sq_px[(y + oy) * n + x + ox]
           for y in range(c.h) for x in range(c.w)]
    return out, c.w, c.h


def _check(px, w: int, h: int, ramps) -> tuple[list[str], float, float]:
    """`ui_forge.check_icon`'s two readings, generalised to a rectangle.

    Deliberately the same numbers rather than looser ones: a drawn piece and
    a generated one are the same kind of object once they are quantized
    pixels, and the point of running this at all is that procedural output
    should clear the generated gate by a wide margin rather than be exempt
    from it.
    """
    from pixelize import audit
    from ui_forge import MAX_ISOLATED, MIN_ICON_COVERAGE
    out = []
    rep = audit(px, ramps)
    cover = rep["pixels"] / float(w * h)
    if cover < MIN_ICON_COVERAGE:
        out.append(f"piece fills {cover * 100:.1f}% of frame (floor "
                   f"{MIN_ICON_COVERAGE * 100:.0f}%)")
    solid = [i for i, c in enumerate(px) if c is not None]
    iso = 0
    for i in solid:
        x, y = i % w, i // w
        if not any(0 <= x + dx < w and 0 <= y + dy < h
                   and px[(y + dy) * w + (x + dx)] == px[i]
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            iso += 1
    ratio = iso / max(1, len(solid))
    if ratio > MAX_ISOLATED:
        out.append(f"{ratio:.1%} of pixels match none of their four "
                   f"neighbours (cap {MAX_ISOLATED:.1%})")
    if rep["off_palette"]:
        out.append(f"{rep['off_palette_pct']}% off-palette, which drawing "
                   f"straight from ramp indices should make impossible")
    return out, ratio, rep["pixels"] / float(w * h)


def build(name: str, scale: float, ramps: dict, out_dir: Path | None = None) -> dict:
    fn, insets = CHROME[name]
    c = fn(scale)
    result = {"name": name, "ok": True, "detail": "", "procedural": True,
              "size": [c.w, c.h]}
    px, w, h = resolve(c, ramps)
    if insets:
        scaled = [max(1, int(round(v * scale))) for v in insets]
        result["nine_slice"] = scaled
        for msg in check_nine_slice(px, w, h, scaled):
            result["ok"] = False
            result["detail"] += msg + "; "
    msgs, iso, cover = _check(px, w, h, ramps)
    result["isolated"] = round(iso, 4)
    result["coverage"] = round(cover, 4)
    for msg in msgs:
        result["ok"] = False
        result["detail"] += msg + "; "
    out_dir = out_dir or UI_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    from PIL import Image
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    img.putdata([(p[0], p[1], p[2], 255) if p else (0, 0, 0, 0) for p in px])
    img.save(out_dir / f"{name}.png")
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated chrome ids")
    ap.add_argument("--target", type=int, default=64,
                    help="size of a square piece in px (default 64); "
                         "rectangular pieces scale by the same factor")
    ap.add_argument("--style", default=DEFAULT_STYLE,
                    help="which style pack's palette to draw against")
    args = ap.parse_args()

    from pixelize import load_palette
    style = load_style(args.style)
    ramps = load_palette(style.palette_path)
    ui_dir = (UI_DIR if args.style == DEFAULT_STYLE
             else UI_DIR.parent / f"ui_{args.style}")
    scale = args.target / 64.0

    wanted = list(CHROME)
    if args.only:
        keep = set(args.only.split(","))
        unknown = keep - set(CHROME)
        if unknown:
            print(f"unknown chrome ids: {sorted(unknown)}", file=sys.stderr)
            return 1
        wanted = [k for k in wanted if k in keep]

    results = []
    for name in wanted:
        r = build(name, scale, ramps, out_dir=ui_dir)
        results.append(r)
        tag = "OK" if r["ok"] else "FAIL"
        nine = f"  nine-slice {r['nine_slice']}" if "nine_slice" in r else ""
        print(f"{tag:4} {name:22} {r['size'][0]:>3}x{r['size'][1]:<3} "
              f"cover {r['coverage']:.2f}  isolated {r['isolated']:.3f}{nine}")
        if r["detail"]:
            print(f"     {r['detail']}")

    nine = {r["name"]: r["nine_slice"] for r in results if "nine_slice" in r}
    if nine:
        (ui_dir / "nine_slice.json").write_text(json.dumps(nine, indent=2),
                                                encoding="utf-8")
    (ui_dir / "chrome_report.json").write_text(json.dumps(results, indent=2),
                                               encoding="utf-8")
    ok = sum(1 for r in results if r["ok"])
    print(f"\n{ok}/{len(results)} chrome pieces -> {ui_dir}")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
