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

from assetlib import merge, pivot_rot, transformed
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

HIP_Z, SHOULDER_Z = 0.46, 0.92     # limb pivots, for posing


ANKLE_Z = 0.10
SEAT_Z = 0.45          # chair seat height; assetlib.chair() must agree


def leg(sx: float, mat: str) -> Mesh:
    """Leg shaft only, hip to ankle. Built per side so a walk cycle can swing
    them independently -- a single two-leg mesh can only ever stand still."""
    m = Mesh()
    m.add_prism((sx, 0.0, ANKLE_Z), 0.100, 0.098, HIP_Z - ANKLE_Z, mat, segments=8)
    return m


def foot(sx: float) -> Mesh:
    """Separate from the shaft, and posed by translation rather than rotation.

    An ankle keeps the foot flat while the leg swings. Rotating the foot rigidly
    with the leg drives its rear corner into the floor, and since the figure is
    ground-clamped, that lifted the whole body -- INVERTING the walk bob, so
    mid-stride rode higher than legs-together instead of lower. That is the most
    visible thing a walk cycle can get wrong after contralateral swing.
    """
    m = Mesh()
    m.add_box((sx - 0.108, -0.095, 0.0), (sx + 0.108, 0.145, ANKLE_Z), "neutral-1")
    return m


def _ankle_offset(sx: float, degrees: float):
    """Where the ankle lands once the shaft has swung, as a translation."""
    probe = Mesh()
    probe.verts = [(sx, 0.0, ANKLE_Z)]
    moved = pivot_rot(probe, "x", -degrees, (sx, 0.0, HIP_Z))
    ax, ay, az = moved.verts[0]
    return (0.0, ay, az - ANKLE_Z)


def legs(mat: str, spread: float = 0.105, seated: bool = False) -> Mesh:
    if seated:
        # Thighs forward (+y, the side the camera sees), shins down: a standing
        # figure parked at seat height reads as standing *on* the chair.
        # Authored about the HIP at z=0, with the shins reaching down to
        # -SEAT_Z so the feet land on the floor when a chair seat is at SEAT_Z.
        m = Mesh()
        for sx in (-spread, spread):
            m.add_box((sx - 0.098, -0.10, -0.10), (sx + 0.098, 0.34, 0.04), mat)
            m.add_box((sx - 0.098, 0.16, -SEAT_Z + 0.06),
                      (sx + 0.098, 0.34, -0.10), mat)
            m.add_box((sx - 0.105, 0.16, -SEAT_Z),
                      (sx + 0.105, 0.40, -SEAT_Z + 0.08), "neutral-1")
        return m
    return merge(leg(-spread, mat), leg(spread, mat))


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


def arm(sx: float, mat: str, skin: str = SKIN) -> Mesh:
    """One arm, toned a step down from the shirt so it separates from the torso
    by value. Modelling it as a different shape would not survive the
    downsample; a value step does.

    ARM_FORWARD: arms hang slightly forward of the torso rather than flat at its
    sides. That is the natural idle stance, and it is also what fixes the
    silhouette: arms held straight out sideways add half the figure's width in x
    and nothing in y, so the side views collapsed to a slab.
    """
    m = Mesh()
    y = 0.052
    m.add_prism((sx, y, 0.60), 0.078, 0.082, 0.33, mat + "-1", segments=8)
    m.add_prism((sx, y, 0.47), 0.072, 0.076, 0.14, skin, segments=8)   # hand
    return m


def arms(mat: str, skin: str = SKIN, bulk: float = 1.0) -> Mesh:
    x = TORSO_RX * bulk + 0.052
    return merge(arm(-x, mat, skin), arm(x, mat, skin))


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


@dataclass
class Pose:
    """A character pose, as limb swings about their own pivots.

    Deliberately tiny. Six numbers cover every clip this game needs, because at
    46 px of figure a pose is read from limb *direction* and body height, not
    from joint articulation -- an elbow is one pixel. Adding a spine chain would
    cost render time and change nothing on screen.
    """
    leg_l: float = 0.0      # degrees, + swings the limb forward (+y)
    leg_r: float = 0.0
    arm_l: float = 0.0
    arm_r: float = 0.0
    bob: float = 0.0        # vertical offset of everything above the hips
    lean: float = 0.0       # forward tilt of the upper body, degrees
    out_l: float = 0.0      # arm abduction, + swings the limb away from the body
    out_r: float = 0.0
    turn: float = 0.0       # upper-body twist about the spine, degrees


REST = Pose()


def build(spec: CharacterSpec, seated: bool = False,
          pose: Pose | None = None) -> Mesh:
    p = pose or REST
    spread = 0.105
    x = TORSO_RX * spec.bulk + 0.052

    upper = [
        torso(spec.shirt, spec.bulk),
        head(spec.skin),
        face(spec.skin, spec.blush),
        hair(spec.hair_style, spec.hair_mat),
    ]
    if spec.accessory_kind:
        upper.append(accessory(spec.accessory_kind, spec.accessory_mat))
    body = merge(*upper)
    if p.turn:
        body = pivot_rot(body, "z", p.turn, (0.0, 0.0, HIP_Z))
    if p.lean:
        body = pivot_rot(body, "x", -p.lean, (0.0, 0.0, HIP_Z))

    def posed_arm(sx, swing, out):
        a = arm(sx, spec.shirt, spec.skin)
        if out:
            a = pivot_rot(a, "y", out if sx > 0 else -out, (sx, 0.0, SHOULDER_Z))
        return pivot_rot(a, "x", -swing, (sx, 0.0, SHOULDER_Z))

    limbs = [posed_arm(-x, p.arm_l, p.out_l), posed_arm(x, p.arm_r, p.out_r)]
    if seated:
        # Drop the upper body to the seated hip. The torso and arms are authored
        # for a standing figure whose hips sit at HIP_Z, while the seated leg rig
        # is authored about the hip at z=0. Merging them untranslated stacked a
        # standing torso on top of folded legs and produced a seated figure
        # 2.24 tall against a standing 1.72 -- taller sitting down than up.
        drop = (0.0, 0.0, -HIP_Z)
        out = merge(legs(spec.trousers, seated=True),
                    transformed(body, at=drop),
                    *(transformed(l, at=drop) for l in limbs))
        # Ground-clamped like the standing rig. The seated parts are authored
        # around the hips, so the mesh hung 0.52 below the origin and every
        # sprite in the sheet had to be scaled down to accommodate it -- the
        # standing frames lost 30% of their tile to empty space under a pose
        # they never strike. Clamped, a seated figure is simply a person with
        # their feet on the floor and their hips at seat height, which is both
        # what it looks like and what makes the anchor consistent across clips.
        low = min(v[2] for v in out.verts)
        return transformed(out, at=(0.0, 0.0, p.bob - low))
    for sx, ang in ((-spread, p.leg_l), (spread, p.leg_r)):
        limbs.append(pivot_rot(leg(sx, spec.trousers), "x", -ang, (sx, 0.0, HIP_Z)))
        limbs.append(transformed(foot(sx), at=_ankle_offset(sx, ang)))
    out = merge(body, *limbs)
    # Ground-clamp. Swinging a leg about its hip arcs the foot below z=0, so a
    # posed figure sinks into the floor -- measured at -0.04 on a mid-stride
    # frame. Lifting the whole figure until its lowest point rests on the floor
    # fixes that, and it also *generates* the walk bob for nothing: the body
    # rides high when the legs are together and drops when they are spread,
    # which is exactly the vertical rhythm a hand-animated cycle is drawn with.
    low = min(v[2] for v in out.verts)
    dz = p.bob - low
    if dz:
        out = transformed(out, at=(0.0, 0.0, dz))
    return out


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


# --- clips -------------------------------------------------------------------
#
# Every clip is a function of phase in [0, 1). Frame counts come from
# assets.yaml, so a clip's length is a manifest decision rather than a hardcoded
# one, and the render budget stays honest.

import math as _math


def _s(phase, cycles=1.0, offset=0.0):
    return _math.sin(2 * _math.pi * (phase * cycles + offset))


def clip_idle(phase: float) -> Pose:
    """Breathing, plus a slow arm settle. Amplitudes are small on purpose: at
    sprite scale an idle that moves more than a pixel or two reads as fidgeting."""
    return Pose(arm_l=2.5 * _s(phase), arm_r=-2.5 * _s(phase),
                bob=0.012 * _s(phase, 1.0, 0.25))


def clip_walk(phase: float) -> Pose:
    """Contralateral swing: the arm opposite the forward leg leads. Getting this
    backwards is the single most recognisable animation error there is."""
    swing = _s(phase)
    return Pose(leg_l=26.0 * swing, leg_r=-26.0 * swing,
                arm_l=-19.0 * swing, arm_r=19.0 * swing,
                lean=3.0)


def clip_carry_walk(phase: float) -> Pose:
    """Walking with a tray: legs cycle, arms held forward and still."""
    swing = _s(phase)
    return Pose(leg_l=22.0 * swing, leg_r=-22.0 * swing,
                arm_l=-62.0, arm_r=-62.0, lean=5.0)


def clip_wave(phase: float) -> Pose:
    return Pose(arm_r=-115.0 + 16.0 * _s(phase, 2.0),
                arm_l=4.0 * _s(phase), bob=0.008 * _s(phase, 2.0))


def clip_serve(phase: float) -> Pose:
    """Reach out and back once over the clip."""
    reach = 0.5 - 0.5 * _math.cos(2 * _math.pi * phase)
    return Pose(arm_r=-78.0 * reach, arm_l=-10.0 * reach, lean=7.0 * reach)


def clip_sip(phase: float) -> Pose:
    lift = 0.5 - 0.5 * _math.cos(2 * _math.pi * phase)
    return Pose(arm_r=-96.0 * lift, lean=2.0 * lift)


def clip_wipe(phase: float) -> Pose:
    """Cloth sweeping across a counter. Lateral, so it needs abduction rather
    than swing -- a purely fore-aft arm reads as reaching, not wiping."""
    sweep = _s(phase)
    return Pose(arm_r=-52.0, out_r=26.0 * sweep + 20.0,
                turn=7.0 * sweep, lean=9.0)


def clip_brew(phase: float) -> Pose:
    """Both hands at the machine, weight settling."""
    press = 0.5 - 0.5 * _math.cos(2 * _math.pi * phase)
    return Pose(arm_l=-58.0 - 8.0 * press, arm_r=-64.0 - 12.0 * press,
                out_l=8.0, out_r=8.0, lean=11.0, bob=-0.012 * press)


def clip_pour(phase: float) -> Pose:
    """Tilt in, hold, tilt back -- an ease rather than a loop, so the middle of
    the clip is the held pose."""
    t = _math.sin(_math.pi * phase) ** 0.6
    return Pose(arm_r=-84.0 - 22.0 * t, out_r=14.0 + 10.0 * t,
                arm_l=-24.0, lean=8.0 + 5.0 * t, turn=-6.0 * t)


def clip_talk(phase: float) -> Pose:
    return Pose(arm_r=-30.0 + 14.0 * _s(phase, 2.0), out_r=16.0,
                arm_l=3.0 * _s(phase), turn=3.0 * _s(phase, 2.0, 0.25))


def clip_sit_idle(phase: float) -> Pose:
    """Seated. Legs are posed by the seated rig, so only the upper body moves."""
    return Pose(arm_l=2.0 * _s(phase), arm_r=-2.0 * _s(phase),
                lean=2.0 + 1.5 * _s(phase, 1.0, 0.25))


def clip_wait_impatient(phase: float) -> Pose:
    """Weight shifts side to side, arms folded. The shift is the whole read."""
    shift = _s(phase)
    return Pose(leg_l=5.0 * shift, leg_r=-5.0 * shift,
                arm_l=-46.0, arm_r=-46.0, out_l=22.0, out_r=22.0,
                turn=4.0 * shift, bob=0.006 * abs(shift))


def clip_leave(phase: float) -> Pose:
    """Same gait as walk, a touch faster and more forward-committed."""
    swing = _s(phase)
    return Pose(leg_l=30.0 * swing, leg_r=-30.0 * swing,
                arm_l=-22.0 * swing, arm_r=22.0 * swing, lean=6.0)


def clip_sit(phase: float) -> Pose:
    """Standing to seated. The one clip that changes rig mid-way.

    There is no knee in this rig -- deliberately, since an elbow or a knee is
    one pixel at sprite scale -- so a continuous lowering cannot be posed. What
    reads instead is the two-part shape every low-resolution game uses: lean and
    drop on the standing rig, then cut to the seated rig and settle. At 12 fps
    the cut is invisible and the intent is completely legible.
    """
    if phase < 0.5:
        t = phase / 0.5
        return Pose(lean=6.0 + 12.0 * t, bob=-0.16 * t,
                    arm_l=-8.0 * t, arm_r=-8.0 * t)
    t = (phase - 0.5) / 0.5
    return Pose(lean=10.0 * (1.0 - t) + 2.0, bob=0.02 * (1.0 - t))


def is_seated(clip: str, phase: float = 0.0) -> bool:
    """Which rig a clip's frame is built on."""
    if clip == "sit":
        return phase >= 0.5
    return clip in SEATED_CLIPS


CLIPS = {
    "idle": clip_idle, "walk": clip_walk, "carry_walk": clip_carry_walk,
    "wave": clip_wave, "serve": clip_serve, "sip": clip_sip,
    "wipe": clip_wipe, "brew": clip_brew, "pour": clip_pour, "talk": clip_talk,
    "sit_idle": clip_sit_idle, "wait_impatient": clip_wait_impatient,
    "leave": clip_leave, "sit": clip_sit,
}

# Clips that must be built on the seated rig rather than the standing one.
SEATED_CLIPS = {"sit_idle", "sit"}
