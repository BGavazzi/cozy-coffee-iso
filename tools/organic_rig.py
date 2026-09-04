#!/usr/bin/env python3
"""The cylinder/sphere character rig: `styles/snes_rpg`'s organic geometry,
built for real for the first time.

    python tools/organic_rig.py --check     # silhouette-swing measurement
    python tools/organic_rig.py --demo      # -> proof/organic_rig.png

`character.py`'s whole rig is `add_box`/`add_prism` -- flat facets, chosen
over boxes specifically because a box's silhouette swings 53% between a
face-on and corner-on camera (see `add_prism`'s docstring in `mesh.py`), while
an octagon holds within ~8%. `add_cylinder`/`add_sphere` already exist in that
same file and are already load-bearing elsewhere (cups, teapots, lamp shades
in `assetlib.py`; steam and droplets in `fx.py`) -- `character.py` simply
never reaches for them. This file does, for the style that actually wants a
rounder silhouette: `styles/snes_rpg/bible.yaml` declares
`rig.primitive: cylinder_sphere`.

The payoff is not "rounder-looking," it's a stronger version of the same
silhouette-stability property the prism rewrite was for. A true circle's
projected width is IDENTICAL at every azimuth, not just close -- there are no
facets for the camera to catch edge-on. `check_direction_stability` below is
`character.py`'s own `check_direction_stability`, run against this rig
instead, and it is the actual test of that claim rather than an assertion
of it.

Scope, stated once rather than re-argued per function: this builds a static
standing figure -- legs, torso, arms, head, minimal face and hair -- through
`character.build()`'s "upright, unposed" case only. It does not reimplement
`character.py`'s pose system (15 animation clips), its seated/perched leg
rigs, or its six hairstyles. Those are real, separate authoring passes, each
sized like this one -- porting all of them in one change would be exactly
the kind of unreviewed, unlooked-at-before-shipping batch this repo's own
`tools/README.md` process argues against. What's here is the smallest real
proof that the primitive choice works, rendered and looked at, the same way
`portrait.py` proved its own face detail before anything else built on it.

Reads `styles/snes_rpg/bible.yaml`'s `rig:` block directly via `tools/style.py`
-- it does not go through `character.py`'s module-level constants at all, so
it is not blocked by the import-order problem `NEXT.md` documents for
`assetlib.py`/`character.py` (their constants bind as function defaults at
`def` time, before any `--style` flag can be parsed). A second style with
`primitive: cylinder_sphere` can reuse this file unmodified by name alone;
`--style` defaults to `snes_rpg` only because it is the one that exists.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))

import character as C  # noqa: E402
from assetlib import merge  # noqa: E402
from mesh import Mesh  # noqa: E402
from pixelize import load_palette  # noqa: E402
from render_batch import frame_all, render_sprite  # noqa: E402
from style import load_style  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

SKIN = "skin"
HAIR_MAT = "wood-3"
SHIRT = "sky-1"
TROUSERS = "neutral-1"


def _rig(style_name: str) -> dict:
    return load_style(style_name).rig


def leg(sx: float, mat: str, rig: dict) -> Mesh:
    """Leg shaft only, ankle to hip -- same authoring split as
    `character.leg`, for the same reason: a walk cycle needs each leg posable
    on its own."""
    m = Mesh()
    m.add_cylinder((sx, 0.0, rig["ankle_z"]), rig["leg_radius"],
                   rig["hip_z"] - rig["ankle_z"], mat, segments=16)
    return m


def foot(sx: float, rig: dict) -> Mesh:
    """Kept as a box, deliberately. A foot is a flat sole on a flat floor --
    `character.foot` makes the same call for the prism rig, and rounding a
    part that is supposed to read as flat would be a regression, not organic
    styling."""
    m = Mesh()
    m.add_box((sx - 0.108, -0.095, 0.0), (sx + 0.108, 0.145, rig["ankle_z"]),
              "neutral-1")
    return m


def torso(mat: str, rig: dict, bulk: float = 1.0) -> Mesh:
    m = Mesh()
    r = rig["torso_radius"] * bulk
    m.add_cylinder((0.0, 0.0, rig["hip_z"]), r,
                   rig["shoulder_z"] - rig["hip_z"], mat, segments=20)
    # Shoulder cap: a short, slightly wider cylinder one step lighter, same
    # idiom as `character.torso`'s cap prism -- it gives the torso a top
    # plane that reads as separate from the head above it.
    m.add_cylinder((0.0, 0.0, rig["shoulder_z"] - 0.02), r * 1.02, 0.05,
                   mat + "+1", segments=20)
    return m


def arm(sx: float, mat: str, skin: str, rig: dict) -> Mesh:
    m = Mesh()
    r = rig["arm_radius"]
    shoulder = rig["shoulder_z"]
    y = 0.045
    m.add_cylinder((sx, y, shoulder - 0.33), r, 0.33, mat + "-1", segments=12)
    m.add_sphere((sx, y, shoulder - 0.40), r * 1.05, skin, segments=12, rings=8)
    return m


def arms(mat: str, skin: str, rig: dict, bulk: float = 1.0) -> Mesh:
    x = rig["torso_radius"] * bulk + 0.050
    return merge(arm(-x, mat, skin, rig), arm(x, mat, skin, rig))


def head(skin: str, rig: dict) -> tuple[Mesh, float, float]:
    """Returns the mesh plus the sphere's own centre-z and radius, so
    `face`/`hair` can place detail proud of the actual curved surface rather
    than a re-guessed one."""
    r = rig["head_radius"]
    cz = rig["head_z"] + r
    m = Mesh()
    m.add_sphere((0.0, 0.0, cz), r, skin, segments=20, rings=14)
    return m, cz, r


def _proud_y(radius: float, centre_z: float, at_z: float, margin: float) -> float:
    """How far forward (+y) the sphere's own surface sits at a given height.

    A prism has a flat facet to measure from (`FACET`, `character.py`);
    a sphere does not, so `face`/`hair` need the real surface equation --
    `y = sqrt(r^2 - dz^2)` at `x=0` -- rather than a constant borrowed from
    the prism rig, which would sit inside the surface at the pole and
    needlessly proud at the equator.
    """
    dz = at_z - centre_z
    return math.sqrt(max(radius * radius - dz * dz, 0.0)) + margin


def face(skin: str, head_cz: float, head_r: float, blush: bool = True) -> Mesh:
    """Eyes and blush as tone-offset boxes, same idiom as `character.face` --
    value detail, not geometry detail, still holds at sprite scale for a
    round head exactly as it does for a faceted one. Placement differs only
    in how "proud of the surface" is computed (`_proud_y`)."""
    m = Mesh()
    ez = head_cz + head_r * 0.22   # eye line, above centre for a cozy read
    y = _proud_y(head_r, head_cz, ez, 0.006)
    for sx in (-0.072, 0.072):
        m.add_box((sx - 0.036, y, ez - 0.036), (sx + 0.036, y + 0.013, ez + 0.036),
                  C.EYE)
    if blush:
        bz = head_cz + head_r * 0.02
        yb = _proud_y(head_r, head_cz, bz, 0.005)
        for sx in (-0.130, 0.130):
            m.add_box((sx - 0.034, yb, bz - 0.030), (sx + 0.034, yb + 0.009, bz + 0.030),
                      "rose+1")
    return m


HAIR_STYLES = ("short", "long", "bun", "cap", "bob", "curly")


def hair(mat: str, head_cz: float, head_r: float, style: str = "short") -> Mesh:
    """All six of `character.hair`'s styles, ported to sphere/cylinder.

    `bob` and `curly` were held back from the first pass (PR #22) on the
    claim that both need a partial, non-360deg ring the box/prism original
    has, which `add_cylinder`/`add_sphere` cannot express. That claim was
    wrong, found wrong by actually trying it rather than by re-reading the
    original geometry more carefully: `character.hair`'s `curly` never used
    a partial ring at all (two small full-sphere puffs, same idiom as
    `bun`), and `bob`'s box panel only ever occupies the region a full
    cylinder ALSO occupies once the head sphere's own opacity is accounted
    for -- a centred, head-sized-or-bigger cylinder is invisible wherever it
    falls inside the head's own silhouette (the head simply draws in front
    of it) and visible only where it pokes past that silhouette, which is
    exactly "hair wraps around the sides and back, not the front" without
    needing to clip anything. No new primitive code was needed for either.

    Every style is built from full rings placed either well above the eye
    line (the crown) or well behind it (negative y, the back of the skull) --
    never a ring that spans both, which is what made the first `short` cap
    swallow the whole head before it was rendered and fixed. `long`'s and
    `bun`'s extra geometry sits at y <= -0.55 * head_r specifically so it
    cannot reach forward far enough to compete with `face`'s proud-of-surface
    eyes, the same margin discipline `_proud_y` exists for.

    `short` -- crown cap only. A smaller, back-and-up-offset sphere reads as
    a rounded crop over the crown and back of the skull, leaving the face
    clear -- the first version used a radius/offset large enough to swallow
    the whole head (1.08x at +0.28 head radii), which looked like a metal
    helmet rather than hair once actually rendered and looked at.
    """
    m = Mesh()
    cap_c = (0.0, -0.020, head_cz + head_r * 0.16)
    cap_r = head_r * 0.86
    m.add_sphere(cap_c, cap_r, mat, segments=20, rings=14)

    if style == "long":
        # A cylinder hanging from the back of the crown down past the chin,
        # offset far enough back (-0.75 head_r) that its front edge still
        # sits behind y=-0.35 head_r -- clear of the face by the same margin
        # `character.hair`'s own back-only box keeps (drawn from -ry to
        # -0.09, never past centre). The first version (bottom at
        # head_cz-0.55r, offset -0.65r) barely poked past the head sphere's
        # own silhouette and read as identical to `short` once actually
        # rendered -- the sphere's back edge is already at -1.0 head_r at
        # crown height, so anything short of clearing that by a visible
        # margin, at a length that actually reaches below the head, is
        # invisible rather than subtle.
        bottom_z = head_cz - 0.85 * head_r
        m.add_cylinder((0.0, -0.75 * head_r, bottom_z), 0.38 * head_r,
                       1.15 * head_r, mat, segments=14)
    elif style == "bun":
        # A second, smaller sphere behind and above the crown -- the one
        # style where the extra volume is a knot, not length, so it stays
        # close to the head rather than hanging. Two corrections from the
        # first cut: pushed further out (-0.85r, was -0.62r, then -0.70r)
        # and shrunk (0.34r, was 0.40-0.42r) -- a bun reads as a distinct
        # round knot only if it clearly protrudes past the crown cap's own
        # silhouette rather than mostly overlapping it; a bigger sphere
        # closer in just thickened the cap instead of adding a second shape.
        m.add_sphere((0.0, -0.85 * head_r, head_cz + head_r * 0.62),
                     0.34 * head_r, mat + "+1", segments=14, rings=10)
    elif style == "bob":
        # Centred, not offset back -- relies on the head sphere's own
        # opacity to hide the front, the same reasoning that makes this
        # style possible without a partial-ring primitive (see docstring).
        # Radius bigger than the head itself (1.05x) so the sides visibly
        # poke past the head's own silhouette rather than staying tucked
        # inside it; bottom at -0.55r reaches toward the jaw, top at +0.30r
        # near the crown, roughly the same span `character.hair`'s own bob
        # box covers (HEAD_Z+0.02 to top-0.28).
        m.add_cylinder((0.0, 0.0, head_cz - 0.55 * head_r), head_r * 1.05,
                       0.85 * head_r, mat, segments=18)
    elif style == "curly":
        # Two small full spheres at the outer edges of the crown -- exactly
        # `character.hair`'s own curly idiom (two small full prisms flanking
        # a bigger cap), not a stand-in for something a partial ring would
        # do differently.
        for sx in (-1.0, 1.0):
            m.add_sphere((sx * head_r * 0.88, -0.05 * head_r,
                         head_cz + head_r * 0.20), head_r * 0.40, mat,
                         segments=14, rings=10)
    elif style == "cap":
        # A literal hat: a short wide cylinder for the brim, a smaller one
        # for the crown -- the one style a cylinder is the obviously correct
        # primitive for, not a stand-in for a box.
        m.add_cylinder((0.0, 0.0, head_cz + head_r * 0.30), head_r * 1.05,
                       head_r * 0.18, mat, segments=20)
        m.add_cylinder((0.0, -0.10 * head_r, head_cz + head_r * 0.28),
                       head_r * 1.30, head_r * 0.07, mat + "-1", segments=20)
    return m


def build(rig: dict, skin: str = SKIN, shirt: str = SHIRT,
         trousers: str = TROUSERS, hair_mat: str = HAIR_MAT,
         hair_style: str = "short", bulk: float = 1.0,
         blush: bool = True) -> Mesh:
    """Upright, unposed. See module docstring for what this deliberately
    does not attempt yet (poses, seated/perched legs)."""
    spread = 0.105
    head_m, head_cz, head_r = head(skin, rig)
    parts = [
        torso(shirt, rig, bulk),
        head_m,
        face(skin, head_cz, head_r, blush),
        hair(hair_mat, head_cz, head_r, hair_style),
        arms(shirt, skin, rig, bulk),
    ]
    for sx in (-spread, spread):
        parts.append(leg(sx, trousers, rig))
        parts.append(foot(sx, rig))
    out = merge(*parts)
    # Ground-clamp, same reasoning as `character.build`'s own clamp: author
    # everything about the rig's own z=0 and let the lowest vertex define the
    # floor, rather than trusting every part's offsets to agree on it exactly.
    low = min(v[2] for v in out.verts)
    if low:
        from assetlib import transformed
        out = transformed(out, at=(0.0, 0.0, -low))
    return out


# --- checks -------------------------------------------------------------------

MIN_SILHOUETTE_PX = 6  # same floor character.check_direction_stability uses


def silhouette(mesh: Mesh, azimuths=C.SPRITE_AZIMUTHS) -> tuple:
    """`character.silhouette`, run against this mesh instead of a
    `CharacterSpec`-built one -- same measurement, same span target."""
    from isorender import DimetricCamera, dot
    widths = []
    for az in azimuths:
        cam = DimetricCamera(az)
        us = [dot(v, cam.right) for v in mesh.verts]
        widths.append(max(us) - min(us))
    return tuple(widths)


def check_direction_stability(style_name: str = "snes_rpg",
                              min_px: int = MIN_SILHOUETTE_PX) -> list[str]:
    """The actual claim under test: a true-circle cross-section should swing
    LESS across azimuths than `character.py`'s own octagonal prism rig does
    for the same spec, not just "some amount." Both are measured here, on the
    same 8 azimuths, so the comparison is apples to apples rather than two
    numbers computed differently."""
    rig = _rig(style_name)
    mesh = build(rig)
    widths = silhouette(mesh)
    swing = (max(widths) - min(widths)) / max(widths) if max(widths) else 0.0

    prism_widths = silhouette(C.build(C.BARISTA))
    prism_swing = ((max(prism_widths) - min(prism_widths)) / max(prism_widths)
                   if max(prism_widths) else 0.0)

    problems = []
    if swing >= prism_swing:
        problems.append(f"organic rig swing {swing:.4f} did not beat the prism "
                        f"rig's {prism_swing:.4f} -- the whole point of a circular "
                        f"cross-section is a smaller swing, not just a different one")
    lo, hi = mesh.bounds()
    span = 1.25  # DimetricCamera default
    px_per_unit = 64 / (2 * span)
    min_width_px = min(widths) * px_per_unit
    if min_width_px < min_px:
        problems.append(f"narrowest silhouette {min_width_px:.1f}px < {min_px}px "
                        f"at 64px target -- figure disappears at some azimuth")
    return problems


def check(style_name: str = "snes_rpg") -> list[str]:
    return check_direction_stability(style_name)


# --- demo -----------------------------------------------------------------

TARGET, FACTOR = 64, 4


def demo(style_name: str = "snes_rpg", out: Path | None = None) -> str:
    """8-azimuth contact sheet plus a hairstyle row -- the visual half of
    the silhouette-swing claim `check_direction_stability` measures
    numerically, and of whether `HAIR_STYLES` actually read as different
    from each other. Same rigor as `preview_characters.py`'s own two-row
    "roster" / "one archetype, all 8 directions" pattern."""
    style = load_style(style_name)
    ramps = load_palette(style.palette_path)
    mesh = build(style.rig)
    span, centre = frame_all(mesh)

    pad, label, scale = 8, 20, 3
    cell = TARGET * scale
    sheet = Image.new("RGB", (8 * (cell + pad) + pad,
                              2 * (cell + label + pad) + pad + 24),
                      (18, 16, 22))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 6), f"organic_rig ({style_name}): 8 azimuths, cylinder/sphere",
           fill=(214, 208, 218))

    y0 = 24 + pad
    for k in range(8):
        az = k * 45.0
        img, _ = render_sprite(mesh, az, TARGET, FACTOR, ramps, span=span,
                               centre=centre)
        bg = Image.new("RGB", (TARGET, TARGET), (30, 27, 36))
        bg.paste(img, (0, 0), img)
        x = pad + k * (cell + pad)
        sheet.paste(bg.resize((cell, cell), Image.NEAREST), (x, y0))
        d.text((x + 2, y0 + cell + 2), f"az{az:.0f}", fill=(214, 208, 218))

    # az225: a back-left corner view. `long`/`bun`'s extra geometry sits
    # behind the head (negative y) specifically so it clears the face at
    # az90 -- which also means az90 is the one azimuth that CANNOT show what
    # makes them different from `short`. Found by rendering the first cut
    # of this row at az90 and every style looking identical.
    HAIR_DEMO_AZIMUTH = 225.0
    y1 = y0 + cell + label + pad + 14
    d.text((pad, y1 - 16), f"hairstyles, azimuth {HAIR_DEMO_AZIMUTH:.0f} (back-left corner)",
           fill=(150, 145, 158))
    for k, sty in enumerate(HAIR_STYLES):
        hm = build(style.rig, hair_style=sty)
        hspan, hcentre = frame_all(hm)
        img, _ = render_sprite(hm, HAIR_DEMO_AZIMUTH, TARGET, FACTOR, ramps,
                               span=hspan, centre=hcentre)
        bg = Image.new("RGB", (TARGET, TARGET), (30, 27, 36))
        bg.paste(img, (0, 0), img)
        x = pad + k * (cell + pad)
        sheet.paste(bg.resize((cell, cell), Image.NEAREST), (x, y1))
        d.text((x + 2, y1 + cell + 2), sty, fill=(214, 208, 218))

    out = out or ROOT / "proof" / "organic_rig.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return str(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", default="snes_rpg")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--lock", action="store_true")
    args = ap.parse_args()

    if args.demo:
        path = demo(args.style)
        print(f"-> {path}")
        return 0

    problems = check(args.style)
    if problems:
        print(f"{len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
    else:
        print("organic rig: silhouette stability holds, beats the prism rig")

    if args.lock:
        import lockfile
        gate_names = ["check_direction_stability (organic_rig.py)"]
        entry = lockfile.record(load_style(args.style), "organic_rig.py",
                                "silhouette", gate_names, approved=not problems)
        state = "approved" if entry["approved"] else "REJECTED"
        print(f"lock: {state} at {entry['style_hash']}")

    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
