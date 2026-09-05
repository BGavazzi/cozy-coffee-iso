#!/usr/bin/env python3
"""Ground and wall tiles, as a tileset an engine can lay down.

`render_room.py` composites a whole shop into one image, and that image is a
*proof*, not a shippable level -- a game lays floors tile by tile, from a set
whose pieces are guaranteed to abut without a seam. This repo had no such
set. `NEXT.md`'s "what a game still needs" list puts it first for a reason: a
room is mostly floor, and the floor was the one large surface with no
per-tile output at all.

    python tools/tileset.py                  # -> out/tiles/
    python tools/tileset.py --width 32
    python tools/tileset.py --proof          # tiling proofs + the room corner

Ground tiles are the third case for procedural authoring, after furniture
(`assetlib.py`) and UI chrome (`ui_chrome.py`), and for the same reason: a
tile is geometry with a semantic role. Its silhouette is not an artistic
choice, it is the projection of a unit square, and it either tessellates or
it does not.

**How the diamond is produced.** Not by rasterizing a quad and hoping. Each
screen pixel is inverse-projected onto the ground plane through the repo's
own `DimetricCamera` basis, and the pixel belongs to the tile when its
ground-plane coordinate lands in the half-open unit square. An affine map
sends every point to exactly one square, so the half-open test makes
coverage exact by construction -- no pixel can be claimed twice and none can
be missed.

That leaves one way to get it wrong, and it is the interesting one. The
tiles are placed on a lattice, and the lattice step must land on whole
pixels or the error accumulates into visible seams a few tiles out. At a
2:1 dimetric a `+1` step in world x moves the tile by `(-W/2, +W/4)` on
screen, so **W must be a multiple of 4**. That is checked rather than
assumed, and `--proof` renders a 3x3 patch and verifies every interior pixel
is covered exactly once.

**Walls too, with one property floors get free and walls do not.** A wall is
a vertical plane; horizontally it tiles exactly like a floor, and vertically
it cannot -- one world unit of height is `sqrt(6)/4 * W` pixels, which is
never a whole number at any width. So wall tiles carry their full height and
never stack. See `WALL_HEIGHT`.

**Four checks, in increasing order of what they can catch.**

    check_lattice     is the tile size legal at all
    tiling_proof      does a tile meet copies of itself, per-pixel
    check_collapse    do two materials resolve to the same colour on this
                      surface -- a detail that is invisible on the shadowed
                      wall and correct on the lit one
    check_manifest_placement
                      can a consumer rebuild the room from `tileset.json`
                      alone, pixel-identically to the projected one

The last is the only one that catches a wrong *published number* rather than
a wrong pixel, and it is the reason `origin_offset` can be trusted: a
one-pixel error in it moves 753 pixels of the reconstruction.

**No outline pass.** Every other producer here calls `apply_outline`,
because a sprite is an object against a background and wants a silhouette. A
floor tile is not an object; outlining it draws a dark diamond grid across
the entire ground, which is the "barcode" defect `assetlib.floor()` already
records hitting twice by other means. Tiles are shaded and left alone.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "out" / "tiles"

# The floor's tone, and the reasoning behind it, live in assetlib -- imported
# rather than restated so a tile and the room composite cannot drift apart.
# WOOD/WALL_FIELD are deliberately NOT imported here any more: the wall trim
# they used to hand `wall_plain`/`wall_panel` needs to vary per style (see
# `make_wall_patterns`), and assetlib's versions are the same def-time-bound
# literal every style shares, which is exactly the thing being fixed.
from assetlib import CERAMIC, FLOOR_FIELD  # noqa: E402
from isorender import (  # noqa: E402
    DimetricCamera, camera_light, dot, norm, verify_projection,
)


# Lighting terms, taken from `render_room.py`'s own call into
# `mesh.rasterize`, not re-chosen here.
#
# The first version of this file lit a tile with a bare `dot(normal, light)`,
# which is not what any other surface in this repo gets, and the wall tiles
# made that obvious rather than subtle: the key direction has a slightly
# negative y component, so a wall facing +y came back at lambert 0 -- pinned
# to the darkest step of every ramp it touched, skirting board included. That
# is the "black grid" defect `assetlib.floor()` records fighting twice,
# arrived at from a third direction.
#
# `mesh.rasterize` has three terms and the second exists precisely for this
# case: "a weak opposing fill lifts the fully-turned-away face off the bottom
# of the ramp, so mid steps get used instead of clamping." A tile that skipped
# it would be a tile that cannot sit next to a prop.
AMBIENT, KEY_GAIN, FILL, BOUNCE = 0.10, 0.80, 0.20, 0.26


def _lambert(normal) -> float:
    """`mesh.rasterize`'s lighting for one constant normal.

    A plane has one normal, so a whole tile shares one lambert and the value
    variation you see is entirely the material's tone offsets -- exactly how
    `assetlib.floor()` breaks up its slab, which is why the two agree.
    """
    cam = DimetricCamera(45.0)
    light = camera_light(cam)
    fill_dir = norm((-light[0], -light[1], 0.15))
    view = cam.dir
    lam = (AMBIENT
           + KEY_GAIN * max(0.0, dot(normal, light))
           + FILL * max(0.0, dot(normal, fill_dir))
           + BOUNCE * max(0.0, dot(normal, view)))
    return max(0.0, min(1.0, lam))


def _basis(width: int):
    """Screen<->ground mapping for one tile, plus the lattice step.

    Returns (to_ground, size, step) where `to_ground(px, py)` gives the
    ground-plane (x, y) of a pixel centre, `size` is (w, h) in pixels and
    `step` is the screen offset of a +1 world-x move.
    """
    verify_projection()          # the 2:1 claim this whole file rests on
    cam = DimetricCamera(45.0)
    corners = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0)]
    us = [dot(c, cam.right) for c in corners]
    vs = [dot(c, cam.up) for c in corners]
    umin, umax, vmin, vmax = min(us), max(us), min(vs), max(vs)
    s = width / (umax - umin)
    height = int(round((vmax - vmin) * s))

    rx, ry = cam.right[0], cam.right[1]
    ux, uy = cam.up[0], cam.up[1]
    det = rx * uy - ry * ux

    def to_ground(px: float, py: float) -> tuple[float, float]:
        u = umin + (px + 0.5) / s
        v = vmax - (py + 0.5) / s
        return ((u * uy - ry * v) / det, (rx * v - u * ux) / det)

    # Screen offset of a +1 world-x step, in pixels, y down.
    step = (int(round(rx * s)), int(round(-ux * s)))
    return to_ground, (width, height), step


# --- walls -------------------------------------------------------------------
#
# A wall is a vertical plane rather than a ground plane, and that difference
# costs one property the floor gets for free.
#
# Horizontally, walls tile exactly like floors: a `+1` step along the run is
# the same `(W/2, W/4)` screen move, and the same half-open test makes
# coverage exact.
#
# Vertically, they cannot. One world unit of height is `up_z * s` pixels, and
# `up_z` is `sqrt(3)/2` at this repo's 30-degree elevation, so the scale is
# `sqrt(6)/4 * W` -- irrational, and therefore never a whole number of pixels
# at any tile width. **Wall tiles cannot be stacked.** Rounding the step would
# drift exactly the way a non-multiple-of-4 floor width does, and faking it by
# rounding the elevation would put walls and floors on two different
# projections, which is worse than either.
#
# So a wall tile carries its full height and the set tiles along the run only.
# `WALL_HEIGHT` matches the room's own walls, and at W=64 it happens to land
# on 96.02 px -- close enough that the tile's own height rounds cleanly, which
# is a nicety rather than a requirement, since nothing stacks on it.
WALL_HEIGHT = 2.45

# The two runs a room's back walls take. With the camera at +x+y+z, an inward
# face is visible only when its normal has a positive component along the view
# direction, which is exactly the +y face of a wall at y=0 and the +x face of
# a wall at x=0 -- the two walls of the far corner, which is the pair every
# isometric room actually shows.
WALL_AXES = {"x": (0, (0.0, 1.0, 0.0)), "y": (1, (1.0, 0.0, 0.0))}


def _wall_basis(width: int, axis: str, height: float = WALL_HEIGHT):
    """Screen<->wall-plane mapping, in the same scale as the floor.

    `s` is derived exactly as `_basis` derives it, so a wall and a floor
    rendered at the same `--width` share one projection. Returns
    `(to_wall, size, run_step)`, where `to_wall(px, py)` gives (position along
    the run, height) for a pixel centre.
    """
    verify_projection()
    cam = DimetricCamera(45.0)
    ai = WALL_AXES[axis][0]
    pi = 1 - ai
    s = width / math.sqrt(2.0)

    pts = []
    for a in (0.0, 1.0):
        for z in (0.0, height):
            p = [0.0, 0.0, z]
            p[ai] = a
            pt = (p[0], p[1], p[2])
            pts.append((dot(pt, cam.right), dot(pt, cam.up)))
    umin, umax = min(u for u, _ in pts), max(u for u, _ in pts)
    vmin, vmax = min(v for _, v in pts), max(v for _, v in pts)
    w = int(round((umax - umin) * s))
    h = int(round((vmax - vmin) * s))

    def to_wall(px: float, py: float) -> tuple[float, float]:
        u = umin + (px + 0.5) / s
        v = vmax - (py + 0.5) / s
        # Orthographic, so the world point is `u*right + v*up + t*dir` for the
        # single t that puts it on the wall's plane.
        t = -(u * cam.right[pi] + v * cam.up[pi]) / cam.dir[pi]
        run = u * cam.right[ai] + v * cam.up[ai] + t * cam.dir[ai]
        z = v * cam.up[2] + t * cam.dir[2]     # right[2] is 0 by construction
        return run, z

    step = (int(round(cam.right[ai] * s)), int(round(-cam.up[ai] * s)))
    return to_wall, (w, h), step


def make_wall_patterns(materials: dict):
    """Build this style's `wall_plain`/`wall_panel` pattern functions.

    **The import-order fix, and why this shape rather than the other one.**
    `style.py`'s own docstring names two ways to make a semantic material
    role genuinely vary per style, given that `--style` is only known after
    `argparse` runs, well after any module-level code has already executed:
    an early `sys.argv` peek before the consuming module is imported, or
    converting bound-at-def-time defaults into a lazy, call-time lookup.

    This picks the second, same reasoning `style.py` gives for preferring
    it: an args-peek is a global side effect (parsing `sys.argv` a second
    time, out of band, before `main()` ever runs) that every future entry
    point has to remember exists, whereas a call-time lookup is local and
    testable -- calling `make_wall_patterns({...})` directly, by hand, with
    any materials dict, produces plain functions with no global state and
    no dependence on `sys.argv` ever having been parsed at all. It also
    composes with the one wrinkle unique to this file: `wall_plain`/
    `wall_panel` are not called directly, they are looked up out of a
    dict (`WALL_PATTERNS` before this change) by every one of
    `render_wall_tile`/`check_collapse`/`wall_proof`/`room_corner`, which
    all share the fixed `pattern(t, z, v)` calling convention. A bare
    `materials=None` default parameter on `wall_plain` itself would need
    every one of those call sites rewritten to pass it through -- this
    factory keeps that convention untouched: `build()` resolves the active
    style's materials ONCE, gets back two ordinary 3-argument functions
    already closed over the right tokens, and every existing call site is
    none the wiser.
    """
    field = materials["wall_field"]
    trim = materials["wall_trim"]
    trim_shadow = materials["wall_trim_shadow"]

    def wall_plain(t: float, z: float, v: int) -> str:
        """Flat field with a skirting board and a top rail.

        Both bands run the full length of the tile and depend only on z, so
        they continue across a join with nothing to align -- which is the
        whole reason a wall's detail wants to be horizontal rather than
        vertical.
        """
        if z < 0.16:
            return trim                          # skirting
        if z < 0.20:
            return trim_shadow                   # its shadow line
        if z > WALL_HEIGHT - 0.08:
            # A picture rail in timber, not a darker step of the wall. Under
            # `cozy_ghibli` this and the skirting-shadow line share one
            # token (`wood-2`) and it's fine; under `snes_rpg` that exact
            # token collided with the skirting board itself at this wall's
            # lambert (both clamped to the same ramp step) -- see
            # `styles/snes_rpg/bible.yaml`'s `wall_trim_shadow` comment for
            # the measured fix. `check_collapse` is what caught it.
            return trim_shadow
        return field

    def wall_panel(t: float, z: float, v: int) -> str:
        """Wainscot: skirting, a chair rail, and a vertical batten per unit.

        The batten sits at the tile's own edges rather than its middle, so a
        run of them lands one world unit apart -- a real interval a room can
        be measured in, instead of a pattern that only exists inside a tile.
        """
        base = wall_plain(t, z, v)
        if base != field:
            return base
        rail = 1.05
        if abs(z - rail) < 0.05:
            return trim                          # chair rail
        if z < rail:
            if t < 0.055 or t > 0.945:
                # The batten is a MATERIAL change, not a tone offset, and
                # that is the fix for a real defect rather than a
                # preference. It was `wall_field + "-1"` first, and on the
                # +y wall the panel face and the batten both clamped to the
                # same colour and the entire wainscot disappeared. It looked
                # fine on the +x wall, which is what makes it the kind of
                # defect `check_collapse` exists to catch. A different ramp
                # has its own headroom.
                return trim
            # No tone lift on the panel face, for the same reason: a tone
            # offset on `field` risks clamping into the same collapse this
            # file has already hit twice. The wainscot reads from its
            # battens and rails, which are timber and survive both walls.
            # A detail that exists on half a corner is worse than a detail
            # that does not exist.
            return base
        return base

    return {"wall_plain": (wall_plain, 1), "wall_panel": (wall_panel, 1)}


def render_wall_tile(pattern, variant: int, width: int, axis: str, ramps: dict):
    """One wall tile.

    Lambert is constant, as it is for a floor -- a plane has one normal -- but
    it is a *different* constant per axis, which is the point: the two walls
    of a corner must not read as the same surface. Both go through `_lambert`,
    and the +y wall is the reason that function exists.
    """
    from pixelize import material
    to_wall, (w, h), _ = _wall_basis(width, axis)
    lam = _lambert(WALL_AXES[axis][1])

    px: list = [None] * (w * h)
    for py in range(h):
        for pxi in range(w):
            t, z = to_wall(pxi, py)
            if not (0.0 <= t < 1.0 and 0.0 <= z < WALL_HEIGHT):
                continue
            rname, tone = material(pattern(t, z, variant))
            ramp = ramps[rname]
            n = len(ramp)
            idx = int(round(lam * (n - 1))) + tone
            px[py * w + pxi] = ramp[max(0, min(n - 1, idx))]
    return px, w, h


def wall_proof(pattern, width: int, axis: str, ramps: dict):
    """Three tiles along the run, with a per-pixel coverage count on the
    middle one. The same argument as `tiling_proof`, one dimension shorter,
    because a wall set only claims to tile along its run."""
    from PIL import Image
    px, w, h = render_wall_tile(pattern, 0, width, axis, ramps)
    dx, dy = _wall_basis(width, axis)[2]

    n = 3
    W = w + abs(dx) * (n - 1) + 4
    H = h + dy * (n - 1) + 4
    ox = 2 + (abs(dx) * (n - 1) if dx < 0 else 0)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cover = [0] * (W * H)
    for i in range(n):
        sx, sy = ox + i * dx, 2 + i * dy
        for ty in range(h):
            for tx in range(w):
                c = px[ty * w + tx]
                if c is None:
                    continue
                X, Y = sx + tx, sy + ty
                if not (0 <= X < W and 0 <= Y < H):
                    continue
                cover[Y * W + X] += 1
                img.putpixel((X, Y), (c[0], c[1], c[2], 255))

    cx, cy = ox + dx, 2 + dy
    holes = sum(1 for ty in range(h) for tx in range(w)
                if px[ty * w + tx] is not None
                and cover[(cy + ty) * W + cx + tx] == 0)
    overlaps = sum(1 for Y in range(H) for X in range(W)
                   if cover[Y * W + X] > 1)
    problems = []
    if holes:
        problems.append(f"{holes} pixel(s) of the middle tile are covered by "
                        f"no tile -- a seam along the run")
    if overlaps:
        problems.append(f"{overlaps} pixel(s) are covered twice -- an overlap "
                        f"along the run")
    return img, problems


# --- tile patterns -----------------------------------------------------------
#
# A pattern maps a point INSIDE the unit square to a material. Everything
# about tileability follows from where the pattern's features sit relative to
# the square's edges, so each one says out loud how its edges meet.

def plain(x: float, y: float, v: int) -> str:
    return FLOOR_FIELD


def plank(x: float, y: float, v: int) -> str:
    """Boards running along world x, two courses per tile.

    Course boundaries are at y = 0, 0.5, 1 -- on the tile edge and on its
    midline -- so a tile's top edge meets the next tile's bottom edge at a
    course seam either way round. Left and right edges match trivially,
    because a board's tone depends only on which course it is in and where
    along x it starts, and both are periodic in the tile.

    The variant index moves the butt joints, which is the whole point of
    shipping four of these. One tile repeated across a floor puts its joint
    on a perfect grid, and a grid is the first thing the eye finds. The
    engine picking at random from four scatters them.
    """
    course = 0 if y < 0.5 else 1
    # Joint positions per (variant, course). Kept off 0 and 1 so no joint ever
    # lands exactly on a tile edge, where two of them would meet and read as a
    # double-width seam.
    joints = ((0.38, 0.72), (0.61, 0.24), (0.29, 0.83), (0.75, 0.47))
    j = joints[v % len(joints)][course]
    seam = 0.035
    if abs(y - 0.5) < 0.018 or y < 0.018 or y > 0.982:
        return FLOOR_FIELD + "-1"          # long seam between courses
    if abs(x - j) < seam:
        return FLOOR_FIELD + "-1"          # butt joint
    # Board tone: one bit of variation per board, derived from the variant and
    # the course rather than from a random draw, so a given tile is
    # byte-identical on every run -- the same reason assetlib.floor() uses a
    # fixed LCG instead of `random`.
    board = 0 if x < j else 1
    tone = (v + course * 2 + board) % 5
    return FLOOR_FIELD + ("+1" if tone == 0 else ("-1" if tone == 1 else ""))


def checker(x: float, y: float, v: int) -> str:
    """Two-tone ceramic. Variant 0 is the light square, 1 the dark.

    A checker is a two-tile pattern, not a one-tile one, so it ships as two
    tiles and the engine alternates them by grid parity. Baking the
    alternation into a single tile would halve the effective tile size and
    make every other row of the pattern uneditable.
    """
    base = CERAMIC if v % 2 == 0 else FLOOR_FIELD
    edge = 0.028
    if x < edge or x > 1 - edge or y < edge or y > 1 - edge:
        return base + "-1"                  # grout line, one step down
    return base


PATTERNS = {
    "floor_plain":   (plain, 1),
    "floor_plank":   (plank, 4),
    "floor_checker": (checker, 2),
}


# --- rendering ---------------------------------------------------------------

def render_tile(pattern, variant: int, width: int, ramps: dict):
    """One tile, as a flat list of RGBA-or-None, plus its size.

    Lambert is constant across the tile -- a ground plane has one normal --
    and comes from `_lambert`, which is `mesh.rasterize`'s model rather than a
    bare dot product. See its comment for what skipping the fill term did.
    """
    from pixelize import material
    to_ground, (w, h), _ = _basis(width)
    lam = _lambert((0.0, 0.0, 1.0))

    px: list = [None] * (w * h)
    for py in range(h):
        for pxi in range(w):
            gx, gy = to_ground(pxi, py)
            if not (0.0 <= gx < 1.0 and 0.0 <= gy < 1.0):
                continue
            rname, tone = material(pattern(gx, gy, variant))
            ramp = ramps[rname]
            n = len(ramp)
            idx = int(round(lam * (n - 1))) + tone
            px[py * w + pxi] = ramp[max(0, min(n - 1, idx))]
    return px, w, h


def check_lattice(width: int) -> list[str]:
    """Does the tile size put the lattice step on whole pixels?

    At a 2:1 dimetric, a +1 world-x step moves the tile by (-W/2, +W/4). A
    width that is not a multiple of 4 rounds that step, and the rounding
    accumulates: the seam is invisible on two tiles and obvious on twenty,
    which is the worst place for it to become visible.
    """
    out = []
    if width % 4:
        out.append(f"tile width {width} is not a multiple of 4, so the "
                   f"lattice step ({width / 2}, {width / 4}) is not a whole "
                   f"number of pixels and tiles will drift apart")
    _, (w, h), step = _basis(width)
    if h * 2 != w:
        out.append(f"tile is {w}x{h}, which is not 2:1 -- the projection "
                   f"assumption this file rests on is broken")
    if abs(step[0]) * 2 != w or step[1] * 4 != w:
        out.append(f"lattice step {step} does not match a {w}x{h} tile")
    return out


def tiling_proof(pattern, variants: int, width: int, ramps: dict):
    """Lay a 3x3 patch and count how many tiles claim each pixel.

    This is the check that matters, and it is deliberately a *coverage*
    count rather than an eyeball: a seam is a pixel claimed zero times and an
    overlap is one claimed twice, and both are invisible at a glance on a
    flat-toned floor while being fatal on a real one. Returns (image,
    problems).
    """
    from PIL import Image
    _, (w, h), step = _basis(width)
    dx, dy = step                      # +1 world x
    tiles = [render_tile(pattern, v % variants, width, ramps)[0]
             for v in range(variants)]

    n = 3
    # Bounding box of a 3x3 patch, plus a margin so nothing is clipped.
    W = w * n + abs(dx) * n
    H = h * n + dy * n * 2
    ox, oy = abs(dx) * n, 0
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cover = [0] * (W * H)

    k = 0
    for gy in range(n):
        for gx in range(n):
            # +1 x -> (dx, dy); +1 y -> (-dx, dy). Both from the same basis.
            sx = ox + gx * dx - gy * dx
            sy = oy + gx * dy + gy * dy
            px = tiles[k % variants]
            k += 1
            for ty in range(h):
                for tx in range(w):
                    c = px[ty * w + tx]
                    if c is None:
                        continue
                    X, Y = sx + tx, sy + ty
                    if not (0 <= X < W and 0 <= Y < H):
                        continue
                    cover[Y * W + X] += 1
                    img.putpixel((X, Y), (c[0], c[1], c[2], 255))

    # Only the interior is meaningful: the patch's outer edge is genuinely
    # ragged, because a diamond grid has a ragged boundary. The interior is
    # the region covered by the middle tile's neighbourhood, and there every
    # pixel must be claimed exactly once.
    cx, cy = ox + dx - dx, oy + dy + dy      # the centre tile's origin
    problems = []
    holes = overlaps = 0
    for ty in range(h):
        for tx in range(w):
            X, Y = cx + tx, cy + ty
            c = cover[Y * W + X]
            if c == 0:
                holes += 1
            elif c > 1:
                overlaps += 1
    if holes:
        problems.append(f"{holes} pixel(s) in the centre tile's cell are "
                        f"covered by no tile -- a seam")
    if overlaps:
        problems.append(f"{overlaps} pixel(s) are covered by more than one "
                        f"tile -- an overlap")
    return img, problems


def wall_origin_offset(width: int, axis: str) -> list[int]:
    """Where a wall tile's top-left sits relative to the floor tile it stands on.

    A wall is taller than the cell it occupies and offset sideways on one of
    the two axes, so a consumer that pastes it at the floor tile's position
    puts it through the floor. The number is derived from the same projection
    that produced both tiles rather than measured off the preview, and
    `room_corner()` is the picture that shows it landing right.

    Returned in screen pixels, y down, relative to the floor tile at the same
    grid cell.
    """
    cam = DimetricCamera(45.0)
    s = width / math.sqrt(2.0)

    floor_pts = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0),
                 (0.0, 1.0, 0.0)]
    ai = WALL_AXES[axis][0]
    wall_pts = []
    for a in (0.0, 1.0):
        for z in (0.0, WALL_HEIGHT):
            p = [0.0, 0.0, z]
            p[ai] = a
            wall_pts.append((p[0], p[1], p[2]))

    def extent(pts):
        return (min(dot(p, cam.right) for p in pts),
                max(dot(p, cam.up) for p in pts))

    uf, vf = extent(floor_pts)
    uw, vw = extent(wall_pts)
    return [int(round((uw - uf) * s)), int(round((vf - vw) * s))]


def check_collapse(pattern, variants: int, width: int, ramps: dict,
                  lam: float, height: float | None = None) -> list[str]:
    """Do two materials in this pattern resolve to the same colour?

    A toon ramp is short, and a tone offset applied to a surface already near
    the bottom of one has nowhere to go. When that happens the offset does not
    produce a darker step, it produces *the same* step -- so a detail vanishes
    silently, on one surface, while looking correct on every other. That is
    exactly what happened to the wainscot batten on the +y wall, and nothing
    would have reported it: the tile passed its own tiling proof, was
    palette-exact, and had no speckle.

    So: sample the pattern, collect the distinct materials it asked for and
    the distinct colours it got, and complain when the second set is smaller.
    """
    from pixelize import material
    mats, cols = set(), set()
    n = 48
    hi = height if height is not None else 1.0
    for v in range(variants):
        for i in range(n):
            for j in range(n):
                a = (i + 0.5) / n
                b = (j + 0.5) / n * hi
                m = pattern(a, b, v)
                mats.add(m)
                rname, tone = material(m)
                ramp = ramps[rname]
                idx = int(round(lam * (len(ramp) - 1))) + tone
                cols.add(ramp[max(0, min(len(ramp) - 1, idx))])
    if len(cols) < len(mats):
        return [f"{len(mats)} materials resolve to only {len(cols)} colours "
                f"at lambert {lam:.3f} -- some detail is invisible on this "
                f"surface ({', '.join(sorted(mats))})"]
    return []


def room_corner(width: int, ramps: dict, n: int = 4,
                floor_type: str = "floor_plank",
                wall_type: str = "wall_panel",
                wall_patterns: dict | None = None):
    """Assemble an `n` x `n` floor patch with both wall runs behind it.

    The per-type proofs answer "does this tile meet a copy of itself", which
    is necessary and not sufficient. This answers the question they cannot:
    do the *floor* and the *wall* agree -- same projection, same scale, same
    lighting model, wall base sitting exactly on the floor edge it stands on.
    Every one of those is a place where two separately-derived pieces of
    arithmetic can disagree by a pixel and only a picture will say so.

    Placement is done in world space and projected once, rather than by
    accumulating per-tile screen offsets, because accumulation is how the
    two sets would drift apart while each still passed its own proof.

    `wall_patterns` is `None` by default and resolved here, lazily, against
    `cozy_ghibli` if the caller doesn't supply one -- the same call-time
    pattern `make_wall_patterns` itself exists for, applied one level up so
    this function's signature (today's only caller is `build()`, which
    always passes its own style's patterns explicitly) stays usable on its
    own, e.g. from a REPL or a future script, without silently rendering
    against the wrong style's trim.
    """
    from PIL import Image
    if wall_patterns is None:
        from style import DEFAULT_STYLE, load_style
        wall_patterns = make_wall_patterns(load_style(DEFAULT_STYLE).materials)
    cam = DimetricCamera(45.0)
    s = width / math.sqrt(2.0)

    def extent(pts):
        us = [dot(p, cam.right) for p in pts]
        vs = [dot(p, cam.up) for p in pts]
        return min(us), max(vs)

    floor_pts = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0),
                 (0.0, 1.0, 0.0)]
    wall_pts = {}
    for axis in WALL_AXES:
        ai = WALL_AXES[axis][0]
        pts = []
        for a in (0.0, 1.0):
            for z in (0.0, WALL_HEIGHT):
                p = [0.0, 0.0, z]
                p[ai] = a
                pts.append((p[0], p[1], p[2]))
        wall_pts[axis] = pts

    # (image, world translation) for everything in the scene. Walls first so
    # the floor paints over their base if they disagree -- a disagreement that
    # shows rather than hides is the point of an integration preview.
    placed = []
    fw, fh = _basis(width)[1]
    for axis in ("x", "y"):
        px, ww, wh = render_wall_tile(wall_patterns[wall_type][0], 0, width,
                                      axis, ramps)
        img = Image.new("RGBA", (ww, wh), (0, 0, 0, 0))
        img.putdata([(c[0], c[1], c[2], 255) if c else (0, 0, 0, 0)
                     for c in px])
        for i in range(n):
            t = (float(i), 0.0, 0.0) if axis == "x" else (0.0, float(i), 0.0)
            placed.append((img, wall_pts[axis], t))

    fn, variants = PATTERNS[floor_type]
    tiles = []
    for v in range(variants):
        px, _, _ = render_tile(fn, v, width, ramps)
        img = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
        img.putdata([(c[0], c[1], c[2], 255) if c else (0, 0, 0, 0)
                     for c in px])
        tiles.append(img)
    for gy in range(n):
        for gx in range(n):
            placed.append((tiles[(gx + gy * 3) % variants], floor_pts,
                           (float(gx), float(gy), 0.0)))

    spots = []
    for img, pts, t in placed:
        umin, vmax = extent(pts)
        spots.append((img, umin + dot(t, cam.right), vmax + dot(t, cam.up)))
    U0 = min(u for _, u, _ in spots)
    V0 = max(v for _, _, v in spots)
    W = max(int(round((u - U0) * s)) + im.width for im, u, _ in spots)
    H = max(int(round((V0 - v) * s)) + im.height for im, _, v in spots)

    sheet = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for im, u, v in spots:
        sheet.alpha_composite(im, (int(round((u - U0) * s)),
                                   int(round((V0 - v) * s))))
    return sheet


def check_manifest_placement(meta: dict, width: int, ramps: dict,
                             n: int = 4, out_dir: Path | None = None,
                             wall_patterns: dict | None = None) -> list[str]:
    """Can a consumer rebuild the room from the published numbers alone?

    `room_corner()` places tiles by projecting world coordinates, which is the
    right way to be sure the picture is correct and the wrong way to be sure
    the *manifest* is. An engine has no camera basis; it has `tile_size`, two
    lattice steps, `run_step` and `origin_offset`. If those are wrong or
    incomplete the tiles still render, just in the wrong places, and the only
    thing that catches it is building the same scene twice by two different
    routes and comparing.

    So this reassembles the corner using nothing but `tileset.json` and the
    atlas PNGs, and requires the result to be pixel-identical to the projected
    one. It is the difference between publishing numbers and publishing
    numbers that work.

    `wall_patterns` MUST be the caller's own style's patterns, threaded
    through to the `ref` projection below same as `build()`'s other calls --
    the `atlas` half of this comparison is real PNGs already on disk under
    `out_dir` (correctly style-specific), so if `ref` silently fell back to
    `room_corner`'s own `cozy_ghibli` default instead, this check would
    compare a non-default style's real tiles against the WRONG style's
    projection and fail for a reason that has nothing to do with placement.
    Caught by running this file's own `--style snes_rpg --proof` after the
    `wall_trim` fix below: `check_collapse` started passing and this check
    started failing with a full-corner-sized diff, which is exactly what a
    silent-cozy_ghibli-fallback looks like -- fixed by passing it through.
    """
    from PIL import Image
    out_dir = out_dir if out_dir is not None else OUT_DIR
    ref = room_corner(width, ramps, n=n, wall_patterns=wall_patterns)

    dx, dy = meta["lattice_step_x"]
    ex, ey = meta["lattice_step_y"]
    fw, fh = meta["tile_size"]
    info = meta["tiles"]["floor_plank"]
    atlas = Image.open(out_dir / info["file"]).convert("RGBA")
    variants = [atlas.crop((r[0], r[1], r[0] + r[2], r[1] + r[3]))
                for r in info["regions"]]

    placed = []
    for axis in ("x", "y"):
        w = meta["walls"][f"wall_panel_{axis}"]
        im = Image.open(out_dir / w["file"]).convert("RGBA")
        r = w["regions"][0]
        tile = im.crop((r[0], r[1], r[0] + r[2], r[1] + r[3]))
        ox, oy = w["origin_offset"]
        sx, sy = w["run_step"]
        for i in range(n):
            placed.append((i * sx + ox, i * sy + oy, tile, 0))
    for gy in range(n):
        for gx in range(n):
            placed.append((gx * dx + gy * ex, gx * dy + gy * ey,
                           variants[(gx + gy * 3) % len(variants)], 1))

    X0 = min(p[0] for p in placed)
    Y0 = min(p[1] for p in placed)
    W = max(p[0] - X0 + p[2].width for p in placed)
    H = max(p[1] - Y0 + p[2].height for p in placed)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for layer in (0, 1):                       # walls behind, floor in front
        for x, y, im, k in placed:
            if k == layer:
                out.alpha_composite(im, (x - X0, y - Y0))

    if out.size != ref.size:
        return [f"manifest placement gives a {out.size} scene where the "
                f"projection gives {ref.size} -- the published steps do not "
                f"describe the same layout"]
    diff = sum(1 for a, b in zip(ref.getdata(), out.getdata()) if a != b)
    if diff:
        return [f"{diff} pixel(s) differ between the projected room and the "
                f"one rebuilt from tileset.json alone -- a consumer using the "
                f"published numbers would not get this picture"]
    return []


def build(width: int, proof: bool, style_name: str | None = None) -> int:
    from PIL import Image
    from pixelize import load_palette
    from style import DEFAULT_STYLE, load_style

    problems = check_lattice(width)
    if problems:
        for p in problems:
            print(f"  BLOCKER  {p}", file=sys.stderr)
        return 1

    style_name = style_name or DEFAULT_STYLE
    style = load_style(style_name)
    ramps = load_palette(style.palette_path)
    # Resolved once per build, from THIS style's materials -- not a module
    # constant bound at import time. See `make_wall_patterns`.
    wall_patterns = make_wall_patterns(style.materials)
    out_dir = (OUT_DIR if style_name == DEFAULT_STYLE
              else OUT_DIR.parent / f"tiles_{style_name}")
    out_dir.mkdir(parents=True, exist_ok=True)
    _, (w, h), step = _basis(width)

    meta = {"tile_size": [w, h], "lattice_step_x": list(step),
            "lattice_step_y": [-step[0], step[1]], "tiles": {}}
    for name, (fn, variants) in sorted(PATTERNS.items()):
        # One atlas per tile type, variants in a row -- the shape Godot's
        # TileSetAtlasSource wants, and the shape that keeps a variant set
        # together as one import instead of four.
        atlas = Image.new("RGBA", (w * variants, h), (0, 0, 0, 0))
        for v in range(variants):
            px, _, _ = render_tile(fn, v, width, ramps)
            tile = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            tile.putdata([(c[0], c[1], c[2], 255) if c else (0, 0, 0, 0)
                          for c in px])
            atlas.paste(tile, (v * w, 0))
        atlas.save(out_dir / f"{name}.png")
        meta["tiles"][name] = {"file": f"{name}.png", "variants": variants,
                               "regions": [[v * w, 0, w, h]
                                           for v in range(variants)]}
        print(f"  {name:14s} {variants} variant(s)  {w}x{h}")
        for msg in check_collapse(fn, variants, width, ramps,
                                  _lambert((0.0, 0.0, 1.0))):
            print(f"  BLOCKER  {name}: {msg}", file=sys.stderr)
            problems.append(msg)

        if proof:
            img, probs = tiling_proof(fn, variants, width, ramps)
            img.save(out_dir / f"_proof_{name}.png")
            if probs:
                for p in probs:
                    print(f"  BLOCKER  {name}: {p}", file=sys.stderr)
                problems += probs
            else:
                print(f"  {'':14s} 3x3 proof: every interior pixel covered "
                      f"exactly once")

    # Walls go in the same manifest but a separate section, because they are a
    # different shape of claim: a floor tile tiles in two directions, a wall
    # tile in one, and flattening the two into one list would lose exactly the
    # distinction a consumer needs.
    meta["walls"] = {}
    for axis in sorted(WALL_AXES):
        _, (ww, wh), wstep = _wall_basis(width, axis)
        for name, (fn, variants) in sorted(wall_patterns.items()):
            tid = f"{name}_{axis}"
            atlas = Image.new("RGBA", (ww * variants, wh), (0, 0, 0, 0))
            for v in range(variants):
                px, _, _ = render_wall_tile(fn, v, width, axis, ramps)
                tile = Image.new("RGBA", (ww, wh), (0, 0, 0, 0))
                tile.putdata([(c[0], c[1], c[2], 255) if c else (0, 0, 0, 0)
                              for c in px])
                atlas.paste(tile, (v * ww, 0))
            atlas.save(out_dir / f"{tid}.png")
            meta["walls"][tid] = {
                "file": f"{tid}.png", "variants": variants, "axis": axis,
                "run_step": list(wstep), "tile_size": [ww, wh],
                "height_units": WALL_HEIGHT,
                "origin_offset": wall_origin_offset(width, axis),
                "regions": [[v * ww, 0, ww, wh] for v in range(variants)],
            }
            print(f"  {tid:14s} {variants} variant(s)  {ww}x{wh}  "
                  f"run step {wstep}")
            for msg in check_collapse(fn, variants, width, ramps,
                                      _lambert(WALL_AXES[axis][1]),
                                      WALL_HEIGHT):
                print(f"  BLOCKER  {tid}: {msg}", file=sys.stderr)
                problems.append(msg)
            if proof:
                img, probs = wall_proof(fn, width, axis, ramps)
                img.save(out_dir / f"_proof_{tid}.png")
                if probs:
                    for p in probs:
                        print(f"  BLOCKER  {tid}: {p}", file=sys.stderr)
                    problems += probs
                else:
                    print(f"  {'':14s} 3-tile run proof: no seam, no overlap")

    # Stated in the manifest rather than left for a consumer to discover the
    # hard way. See the WALL_HEIGHT comment for why it cannot be otherwise.
    meta["walls_stack"] = False
    meta["px_per_world_z"] = round(
        DimetricCamera(45.0).up[2] * width / math.sqrt(2.0), 4)

    if proof:
        # The per-type proofs answer "does this meet a copy of itself". This
        # answers the one they cannot: do the floor and the wall agree.
        room_corner(width, ramps, wall_patterns=wall_patterns).save(
            out_dir / "_room_corner.png")
        print("  room corner: floor + both wall runs, one projection")
        placement = check_manifest_placement(meta, width, ramps, out_dir=out_dir,
                                             wall_patterns=wall_patterns)
        for msg in placement:
            print(f"  BLOCKER  {msg}", file=sys.stderr)
            problems.append(msg)
        if not placement:
            print("  manifest placement: rebuilt from tileset.json alone, "
                  "pixel-identical")

    (out_dir / "tileset.json").write_text(json.dumps(meta, indent=2),
                                          encoding="utf-8")
    print(f"\n{len(meta['tiles'])} floor types, {len(meta['walls'])} wall "
          f"types -> {out_dir}")
    return 1 if problems else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--width", type=int, default=64,
                    help="tile width in pixels; height is half (default 64, "
                         "must be a multiple of 4)")
    ap.add_argument("--proof", action="store_true",
                    help="also write a 3x3 tiling proof per tile type and "
                         "verify every interior pixel is covered once")
    ap.add_argument("--style", default=None,
                    help="style pack to render against (default: cozy_ghibli); "
                         "writes to out/tiles_<style>/ for a non-default style")
    args = ap.parse_args()
    return build(args.width, args.proof, args.style)


if __name__ == "__main__":
    raise SystemExit(main())
