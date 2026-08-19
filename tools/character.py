"""Modular character construction.

Characters are assembled from swappable parts rather than authored whole. That
matters for the manifest maths: 8 customer archetypes as separate meshes is 8
authoring jobs, but as part combinations it is one parts library plus 8 short
specs. The render budget is unchanged; the *authoring* budget collapses.

Part slots are deliberately finer than "body and head":

    legs · torso · arms · head · face · hair · accessory

Three rules earn their place here, each promoted from a failure we measured:

**Prisms, not boxes.** A box silhouette swings 53% in projected width between
its face-on and corner-on views, so a box character is fat in directions 1 and 5
and paper-thin in 3 and 7. Octagonal prisms hold within ~8%, so the figure keeps
one identity through all eight azimuths.

**Value detail, not geometry detail.** Eyes, brows and the seam under a collar
are drawn with the material tone offset (`"wood-4"` -- see pixelize.material),
because at 12 px of head there is no room to model them and a darker step of the
same ramp is exactly how a pixel artist would draw them.

**Contrast is a constraint, not a taste call.** Hair that sits within 0.10
lightness of skin merges into the face at sprite scale, so `check_contrast()`
verifies every spec and the manifest treats a failure as a blocker.

Proportions are chibi-leaning by design. A realistic 7.5-head figure loses its
head to three pixels at this scale; cozy games all push the head toward a
quarter of total height so the character reads at a glance.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from assetlib import merge, transformed
from mesh import Mesh

# Total height in tile units, matching assets.yaml.
H = 1.59

SKIN = "wood"          # wood_3..6 are the flesh tones; see style_bible.yaml

# Cross-section radii. Depth is kept near width -- the whole point of the prism
# rewrite -- rather than the 0.265 x 0.175 slab that broke the diagonals.
TORSO_RX, TORSO_RY = 0.250, 0.210
HEAD_RX, HEAD_RY = 0.205, 0.185
HEAD_Z = 1.00                       # chin height
# An 8-gon with phase pi/8 presents a flat facet on each axis at
# cos(pi/8) of the radius, not at the radius itself.
FACET = math.cos(math.pi / 8)
HEAD_TOP = H - 0.03


# --- parts -------------------------------------------------------------------

def legs(mat: str, spread: float = 0.105, seated: bool = False) -> Mesh:
    m = Mesh()
    if seated:
        # Thighs forward, shins down: a standing figure parked at seat height
        # reads as standing *on* the chair.
        for sx in (-spread, spread):
            m.add_box((sx - 0.098, -0.10, -0.10), (sx + 0.098, 0.34, 0.04), mat)
            m.add_box((sx - 0.098, 0.16, -0.46), (sx + 0.098, 0.34, -0.10), mat)
            m.add_box((sx - 0.105, 0.16, -0.52), (sx + 0.105, 0.40, -0.44),
                      "neutral-1")
        return m
    for sx in (-spread, spread):
        m.add_prism((sx, 0.0, 0.0), 0.100, 0.098, 0.46, mat, segments=8)
        # Shoe, a step darker so the leg does not run into the floor.
        m.add_box((sx - 0.108, -0.145, 0.0), (sx + 0.108, 0.095, 0.10),
                  "neutral-1")
    return m


def torso(mat: str, bulk: float = 1.0) -> Mesh:
    """Chunky by design. A 4:1 height-to-width figure reads as a pole at 40 px;
    cozy games sit nearer 2.5:1."""
    m = Mesh()
    rx, ry = TORSO_RX * bulk, TORSO_RY * bulk
    m.add_prism((0.0, 0.0, 0.42), rx, ry, 0.50, mat, segments=8)
    # Shoulder cap, one step lighter: gives the torso a top plane that separates
    # it from the head above and the arms beside it.
    m.add_prism((0.0, 0.0, 0.90), rx * 0.99, ry * 0.99, 0.04, mat + "+1",
                segments=8)
    return m


def arms(mat: str, skin: str = SKIN, bulk: float = 1.0) -> Mesh:
    """Arms are toned one step down from the shirt so they separate from the
    torso by value. Modelling them as a different shape would not survive the
    downsample; a value step does.

    ARM_FORWARD: they also hang slightly forward of the torso rather than flat
    at its sides. That is the natural idle stance, and it is also what fixes the
    silhouette: arms held straight out sideways add half the figure's width in x
    and nothing in y, so the side views collapsed to a slab. Carried forward,
    they contribute to both axes and the swing falls from 51% to single digits.
    """
    m = Mesh()
    x = TORSO_RX * bulk + 0.052
    y = 0.052         # arms carried slightly forward -- see ARM_FORWARD note
    for sx in (-x, x):
        m.add_prism((sx, y, 0.60), 0.078, 0.082, 0.33, mat + "-1", segments=8)
        m.add_prism((sx, y, 0.47), 0.072, 0.076, 0.14, skin, segments=8)  # hand
    return m


def head(skin: str = SKIN) -> Mesh:
    m = Mesh()
    m.add_prism((0.0, 0.0, 0.94), 0.085, 0.075, 0.07, skin + "-1", segments=8)
    m.add_prism((0.0, 0.0, HEAD_Z), HEAD_RX, HEAD_RY, HEAD_TOP - HEAD_Z, skin,
                segments=8)
    return m


def face(skin: str = SKIN, blush: bool = True) -> Mesh:
    """Eyes and blush, drawn in tone offsets on the front of the head.

    This is the single largest readability gain per unit of geometry. A blank
    box head reads as cargo; two dark pixels read as a person, and the eye finds
    them before it resolves anything else in the frame.
    """
    m = Mesh()
    # FRONT IS +y. The camera at azimuth 45 sees the +x and +y sides, so a
    # detail modelled at -y is on the far side of the head and never renders --
    # which is exactly why an earlier pass shipped characters with no visible
    # faces even though the eyes were in the mesh.
    y = HEAD_RY * FACET + 0.004                # just proud of the front facet
    ez = HEAD_Z + 0.62 * (HEAD_TOP - HEAD_Z)   # eye line, high for a cozy read
    for sx in (-0.080, 0.080):
        m.add_box((sx - 0.040, y, ez - 0.040),
                  (sx + 0.040, y + 0.014, ez + 0.040), skin + "-4")
    if blush:
        for sx in (-0.148, 0.148):
            m.add_box((sx - 0.038, y, ez - 0.110),
                      (sx + 0.038, y + 0.010, ez - 0.048), "rose+1")
    return m


def hair(style: str, mat: str) -> Mesh:
    """Silhouette is what identifies a character at this size, so styles differ
    in outline rather than in surface detail."""
    m = Mesh()
    top, rx, ry = HEAD_TOP, HEAD_RX + 0.022, HEAD_RY + 0.022
    if style == "short":
        m.add_prism((0, 0, top - 0.15), rx, ry, 0.20, mat, segments=8)
    elif style == "bob":
        m.add_prism((0, 0, top - 0.30), rx + 0.014, ry + 0.014, 0.35, mat,
                    segments=8)
        m.add_box((-rx, -ry, HEAD_Z + 0.02), (rx, -0.10, top - 0.28), mat)
    elif style == "long":
        m.add_prism((0, 0, top - 0.18), rx, ry, 0.23, mat, segments=8)
        m.add_box((-rx + 0.01, -ry, 0.80), (rx - 0.01, -0.09, top - 0.16), mat)
    elif style == "bun":
        m.add_prism((0, 0, top - 0.14), rx, ry, 0.19, mat, segments=8)
        m.add_prism((0, -0.14, top - 0.02), 0.115, 0.115, 0.18, mat + "+1",
                    segments=8)
    elif style == "cap":
        m.add_prism((0, 0, top - 0.10), rx + 0.014, ry + 0.014, 0.17, mat,
                    segments=8)
        m.add_box((-0.20, ry * FACET, top - 0.085),
                  (0.20, ry + 0.15, top - 0.010), mat + "-1")             # brim
    elif style == "curly":
        m.add_prism((0, 0, top - 0.19), rx + 0.028, ry + 0.028, 0.27, mat,
                    segments=8)
        for sx in (-rx - 0.03, rx + 0.03):
            m.add_prism((sx, 0, top - 0.25), 0.075, 0.075, 0.20, mat + "+1",
                        segments=8)
    return m


def accessory(kind: str, mat: str) -> Mesh:
    m = Mesh()
    if kind == "apron":
        f = TORSO_RY * FACET
        m.add_box((-0.235, f - 0.020, 0.30), (0.235, f + 0.015, 0.86), mat)
        m.add_box((-0.10, f - 0.015, 0.86), (0.10, f + 0.015, 0.95), mat)  # bib
        m.add_box((-0.235, f + 0.008, 0.56),
                  (0.235, f + 0.018, 0.59), mat + "-2")                    # tie
    elif kind == "scarf":
        m.add_prism((0, 0, 0.87), TORSO_RX * 0.86, TORSO_RY * 0.90, 0.12, mat,
                    segments=8)
    elif kind == "bag":
        m.add_box((0.27, -0.08, 0.50), (0.42, 0.12, 0.78), mat)
        m.add_box((0.27, -0.02, 0.78), (0.42, 0.02, 0.96), mat + "-2")   # strap
    elif kind == "cup":
        m.add_prism((-0.36, 0.05, 0.52), 0.062, 0.062, 0.13, mat, segments=8)
    return m


# --- assembly ----------------------------------------------------------------

@dataclass
class CharacterSpec:
    name: str
    shirt: str = "sky"
    trousers: str = "neutral"
    hair_style: str = "short"
    hair_mat: str = "neutral"
    accessory_kind: str | None = None
    accessory_mat: str = "rose"
    bulk: float = 1.0
    skin: str = SKIN
    blush: bool = True


def build(spec: CharacterSpec, seated: bool = False) -> Mesh:
    parts = [
        legs(spec.trousers, seated=seated),
        torso(spec.shirt, spec.bulk),
        arms(spec.shirt, spec.skin, spec.bulk),
        head(spec.skin),
        face(spec.skin, spec.blush),
        hair(spec.hair_style, spec.hair_mat),
    ]
    if spec.accessory_kind:
        parts.append(accessory(spec.accessory_kind, spec.accessory_mat))
    return merge(*parts)


def place(spec: CharacterSpec, at, facing: float = 0.0, seated: bool = False) -> Mesh:
    """`facing` in degrees; 0 faces +y (toward the camera at azimuth 45)."""
    return transformed(build(spec, seated=seated), rot_z=facing, at=at)


# --- the roster --------------------------------------------------------------

BARISTA = CharacterSpec("barista", shirt="cream", trousers="neutral",
                        hair_style="bun", hair_mat="neutral-2",
                        accessory_kind="apron", accessory_mat="rose")

# Eight archetypes, all combinations of the same parts library.
CUSTOMERS = [
    CharacterSpec("reader",   shirt="foliage", trousers="wood",    hair_style="bob",
                  hair_mat="neutral-2", accessory_kind="scarf",  accessory_mat="rose"),
    CharacterSpec("student",  shirt="sky",     trousers="neutral", hair_style="short",
                  hair_mat="wood-3",  accessory_kind="bag",    accessory_mat="wood"),
    CharacterSpec("regular",  shirt="rose",    trousers="wood",    hair_style="long",
                  hair_mat="wood-3",  accessory_kind="cup",    accessory_mat="cream"),
    CharacterSpec("commuter", shirt="neutral", trousers="neutral", hair_style="cap",
                  hair_mat="neutral-3", accessory_kind="bag",  accessory_mat="neutral",
                  bulk=1.12),
    CharacterSpec("artist",   shirt="cream",   trousers="sky",     hair_style="curly",
                  hair_mat="neutral-2", accessory_kind="scarf", accessory_mat="foliage"),
    CharacterSpec("elder",    shirt="wood",    trousers="neutral", hair_style="short",
                  hair_mat="cream+1", accessory_kind=None,     bulk=1.08),
    CharacterSpec("writer",   shirt="sky",     trousers="wood",    hair_style="bun",
                  hair_mat="wood-4",  accessory_kind="cup",    accessory_mat="cream"),
    CharacterSpec("friend",   shirt="foliage", trousers="rose",    hair_style="bob",
                  hair_mat="wood-3",  accessory_kind=None),
]

ROSTER = [BARISTA] + CUSTOMERS


# --- promoted checks ---------------------------------------------------------

MIN_HAIR_SKIN_GAP = 0.13


def _clamp(i, ramp):
    return max(0, min(len(ramp) - 1, i))


def check_contrast(ramps, roster=None) -> list[str]:
    """Hair that sits too close to skin in lightness merges into the face.

    Promoted from review: `commuter` shipped with foliage hair 0.004 from skin,
    which is invisible at sprite scale and was not caught by any per-pixel check
    because both colours are individually legal.
    """
    from oklab import srgb_to_oklab
    from pixelize import material
    def L(c):
        return srgb_to_oklab(c)[0]
    out = []
    for s in roster or ROSTER:
        sk_ramp, sk_tone = material(s.skin)
        skin_l = L(ramps[sk_ramp][_clamp(4 + sk_tone, ramps[sk_ramp])])
        hr_ramp, hr_tone = material(s.hair_mat)
        ramp = ramps[hr_ramp]
        hair_l = L(ramp[_clamp(min(3, len(ramp) - 1) + hr_tone, ramp)])
        gap = abs(hair_l - skin_l)
        if gap < MIN_HAIR_SKIN_GAP:
            out.append(f"{s.name}: hair '{s.hair_mat}' is {gap:.3f} from skin "
                       f"(need {MIN_HAIR_SKIN_GAP}) -- head reads as one lump")
    return out


# Room framing resolves 27.2 px per world unit (see ART_CRITIQUE); a limb or a
# body narrower than this many pixels there stops reading as a shape.
GAME_PX_PER_UNIT = 27.2
MIN_SILHOUETTE_PX = 9


def check_direction_stability(spec=None, min_px: int = MIN_SILHOUETTE_PX) -> list[str]:
    """Every direction must stay above a readable pixel width at game scale.

    The first version of this check compared the *widest* direction to the
    narrowest and failed anything over 15%. That was wrong, and worth recording:
    a humanoid seen from the side genuinely is about half as wide as from the
    front, so the swing it measured is correct behaviour, not a defect. Chasing
    it to zero would mean building a cylinder rather than a person.

    What actually broke in review was absolute, not relative -- the side views
    fell to a couple of pixels of body and the arms disappeared entirely. So the
    constraint is a floor in pixels at the scale the sprite is actually seen.
    """
    from isorender import DimetricCamera
    from mesh import rasterize
    res, span = 192, 0.95
    out, widths = [], []
    for k in range(8):
        cam = DimetricCamera(45.0 + k * 45.0)
        cam.span = span
        mat, _, _ = rasterize(build(spec or CUSTOMERS[2]), cam, res,
                              target=(0.0, 0.0, 0.70))
        cols = [i % res for i, m in enumerate(mat) if m is not None]
        world = (max(cols) - min(cols)) * (2 * span) / res
        widths.append(world * GAME_PX_PER_UNIT)
    for k, w in enumerate(widths):
        if w < min_px:
            out.append(f"dir{k}: silhouette is {w:.1f} px wide at game scale "
                       f"(floor {min_px}) -- reads as a sliver, not a figure")
    return out


def report_widths(spec=None) -> None:
    from isorender import DimetricCamera
    from mesh import rasterize
    res, span = 192, 0.95
    for k in range(8):
        cam = DimetricCamera(45.0 + k * 45.0)
        cam.span = span
        mat, _, _ = rasterize(build(spec or CUSTOMERS[2]), cam, res,
                              target=(0.0, 0.0, 0.70))
        cols = [i % res for i, m in enumerate(mat) if m is not None]
        w = (max(cols) - min(cols)) * (2 * span) / res * GAME_PX_PER_UNIT
        print(f"  dir{k}  {w:5.1f} px at game scale")


if __name__ == "__main__":
    from pixelize import load_palette
    ramps = load_palette()
    problems = check_contrast(ramps) + check_direction_stability()
    for p in problems:
        print(f"  BLOCKER  {p}")
    print(f"{len(problems)} blocker(s)")
    raise SystemExit(1 if problems else 0)
