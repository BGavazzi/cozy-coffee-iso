#!/usr/bin/env python3
"""Ground tiles, as a tileset an engine can lay down.

`render_room.py` composites a whole shop into one image, and that image is a
*proof*, not a shippable level -- a game lays floors tile by tile, from a set
whose pieces are guaranteed to abut without a seam. This repo had no such
set. `NEXT.md`'s "what a game still needs" list puts it first for a reason: a
room is mostly floor, and the floor was the one large surface with no
per-tile output at all.

    python tools/tileset.py                  # -> out/tiles/
    python tools/tileset.py --width 32
    python tools/tileset.py --proof          # also write the 3x3 tiling proof

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
from assetlib import CERAMIC, FLOOR_FIELD  # noqa: E402
from isorender import DimetricCamera, camera_light, dot, verify_projection  # noqa: E402


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

    Lambert is constant across the tile: a ground plane has one normal, and
    the key is fixed in camera space (`isorender.LIGHT_CAM`). So the value
    variation you see is entirely the material's own tone offsets, which is
    exactly how `assetlib.floor()` breaks up its slab and why the two agree.
    """
    from pixelize import material
    to_ground, (w, h), _ = _basis(width)
    lam = max(0.0, dot((0.0, 0.0, 1.0), camera_light(DimetricCamera(45.0))))

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


def build(width: int, proof: bool) -> int:
    from PIL import Image
    from pixelize import load_palette

    problems = check_lattice(width)
    if problems:
        for p in problems:
            print(f"  BLOCKER  {p}", file=sys.stderr)
        return 1

    ramps = load_palette()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
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
        atlas.save(OUT_DIR / f"{name}.png")
        meta["tiles"][name] = {"file": f"{name}.png", "variants": variants,
                               "regions": [[v * w, 0, w, h]
                                           for v in range(variants)]}
        print(f"  {name:14s} {variants} variant(s)  {w}x{h}")

        if proof:
            img, probs = tiling_proof(fn, variants, width, ramps)
            img.save(OUT_DIR / f"_proof_{name}.png")
            if probs:
                for p in probs:
                    print(f"  BLOCKER  {name}: {p}", file=sys.stderr)
                problems += probs
            else:
                print(f"  {'':14s} 3x3 proof: every interior pixel covered "
                      f"exactly once")

    (OUT_DIR / "tileset.json").write_text(json.dumps(meta, indent=2),
                                          encoding="utf-8")
    print(f"\n{len(meta['tiles'])} tile types -> {OUT_DIR}")
    return 1 if problems else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--width", type=int, default=64,
                    help="tile width in pixels; height is half (default 64, "
                         "must be a multiple of 4)")
    ap.add_argument("--proof", action="store_true",
                    help="also write a 3x3 tiling proof per tile type and "
                         "verify every interior pixel is covered once")
    args = ap.parse_args()
    return build(args.width, args.proof)


if __name__ == "__main__":
    raise SystemExit(main())
