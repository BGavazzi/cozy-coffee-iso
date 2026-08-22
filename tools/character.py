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
from dataclasses import dataclass, replace as _replace

from assetlib import merge, pivot_rot, transformed
from mesh import Mesh

# Total height in tile units, matching assets.yaml.
H = 1.59

SKIN = "skin"          # wood_3..6 are the flesh tones; see style_bible.yaml

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

# The tallest seat this rig can sit on with its feet on the floor. Above it a
# person perches -- feet on a rail, weight on the hips -- and that is a
# different rig and a different support model, not a longer shin. `grounded`
# asks whether an object's underside meets a surface, which is the wrong
# question for a figure held up by its backside: a customer put on a 0.70 bar
# stool is ground-clamped, does not float, and sits in mid-air beside it at
# dining height, with no check in the ratchet able to see it.
MAX_SEAT_Z = 0.58

# Above MAX_SEAT_Z a figure perches instead. The rig is different in kind, not
# in degree: sitting folds the leg into a right angle and puts the foot on the
# floor, perching hangs the leg nearly straight and puts the foot on a rail or
# on nothing. The tell is where the weight goes -- a seated figure carries it
# on the thighs and a perched one on the backside, which is why a perched
# figure's feet can be in mid-air and the pose still be correct.
PERCH_LEG = 0.52       # hip to sole, hanging; the leg cannot reach past this
MAX_PERCH_Z = 0.85


def leg(sx: float, mat: str, hip: float = HIP_Z) -> Mesh:
    """Leg shaft only, hip to ankle. Built per side so a walk cycle can swing
    them independently -- a single two-leg mesh can only ever stand still.

    `hip` rather than the module constant, because leg length is the one
    proportion that changes a standing figure's outline without changing any
    of its parts. The ankle stays where it is and the hip moves, which is what
    varies between two adults; scaling the whole figure instead would scale the
    head, and a scaled head reads as a child rather than as a tall person.
    """
    m = Mesh()
    m.add_prism((sx, 0.0, ANKLE_Z), 0.100, 0.098, hip - ANKLE_Z, mat, segments=8)
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


def _ankle_offset(sx: float, degrees: float, hip: float = HIP_Z):
    """Where the ankle lands once the shaft has swung, as a translation."""
    probe = Mesh()
    probe.verts = [(sx, 0.0, ANKLE_Z)]
    moved = pivot_rot(probe, "x", -degrees, (sx, 0.0, hip))
    ax, ay, az = moved.verts[0]
    return (0.0, ay, az - ANKLE_Z)


def legs(mat: str, spread: float = 0.105, seated: bool = False,
         hip: float = HIP_Z, seat: float = SEAT_Z, perch=None) -> Mesh:
    if seated:
        # Thighs forward (+y, the side the camera sees), shins down: a standing
        # figure parked at seat height reads as standing *on* the chair.
        # Authored about the HIP at z=0, with the shins reaching down to
        # -SEAT_Z so the feet land on the floor when a chair seat is at SEAT_Z.
        # Shins reach the seat height they are sitting on, rather than the
        # one dining chairs happen to have. An armchair's cushion lands
        # anywhere from 0.46 to 0.52 once its base style and seat jitter are
        # applied, so a figure authored for 0.45 sat up to 0.07 inside it.
        seat = min(seat, MAX_SEAT_Z)
        m = Mesh()
        for sx in (-spread, spread):
            m.add_box((sx - 0.098, -0.10, -0.10), (sx + 0.098, 0.34, 0.04), mat)
            m.add_box((sx - 0.098, 0.16, -seat + 0.06),
                      (sx + 0.098, 0.34, -0.10), mat)
            m.add_box((sx - 0.105, 0.16, -seat),
                      (sx + 0.105, 0.40, -seat + 0.08), "neutral-1")
        return m
    if perch is not None:
        # Hip at z=0, as the seated rig is. The thigh drops rather than running
        # level, and the shin hangs from it: that steeper hip angle is the
        # whole read, because a level thigh at 0.72 is a person sitting on air
        # beside the stool rather than on it.
        seat = min(perch[0], MAX_PERCH_Z)
        rail = perch[1]
        # Feet reach the rail if the leg is long enough, and hang at full
        # stretch if it is not -- which is what happens on a stool with no
        # ring, and is a pose, not a failure to find support.
        drop = PERCH_LEG if rail is None else min(PERCH_LEG, seat - rail)
        knee = -drop * 0.42
        m = Mesh()
        for sx in (-spread, spread):
            m.add_box((sx - 0.098, -0.10, knee), (sx + 0.098, 0.22, 0.04), mat)
            m.add_box((sx - 0.094, 0.04, -drop + 0.06),
                      (sx + 0.094, 0.21, knee), mat)
            m.add_box((sx - 0.102, 0.04, -drop),
                      (sx + 0.102, 0.28, -drop + 0.08), "neutral-1")
        return m
    return merge(leg(-spread, mat, hip), leg(spread, mat, hip))


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


def accessory(kind: str, mat: str, sx: float = 0.0) -> Mesh:
    m = Mesh()
    if kind == "apron":
        f = TORSO_RY * FACET
        m.add_box((-0.235, f - 0.020, 0.30), (0.235, f + 0.015, 0.86), mat)
        m.add_box((-0.10, f - 0.015, 0.86), (0.10, f + 0.015, 0.95), mat)  # bib
        m.add_box((-0.235, f + 0.008, 0.56),
                  (0.235, f + 0.018, 0.59), mat + "-2")                    # tie
    elif kind == "scarf":
        # Drawn at 0.86 of the torso this was inside the body at all eight
        # azimuths -- zero pixels of silhouette, a colour swatch rather than a
        # thing worn. Filling the neck notch is not enough either: a collar at
        # 0.202 still measured 0.0%, because the head above and the shoulder
        # cap below already close that gap at every angle. An accessory only
        # exists in outline once it beats the widest part of the figure, so the
        # collar runs past the 0.2475 shoulder and reads as a knitted wrap.
        m.add_prism((0, 0, 0.88), 0.295, 0.272, 0.13, mat, segments=8)
        f = TORSO_RY * FACET
        m.add_box((0.045, f - 0.03, 0.54), (0.155, f + 0.075, 0.95),
                  mat + "-1")                                            # tail
    elif kind == "bag":
        m.add_box((0.27, -0.08, 0.50), (0.42, 0.12, 0.78), mat)
        m.add_box((0.27, -0.02, 0.78), (0.42, 0.02, 0.96), mat + "-2")   # strap
    elif kind == "cup":
        # Authored in arm-local space around the hand, because `build` merges
        # held accessories into the arm before posing it. Sitting in the body
        # mesh, the cup stayed at the hip through every frame of a walk while
        # the hand that was supposedly holding it swung away.
        m.add_prism((sx, 0.092, 0.455), 0.072, 0.072, 0.155, mat, segments=8)
        m.add_prism((sx, 0.092, 0.610), 0.085, 0.085, 0.030, mat + "-2",
                    segments=8)                                          # lid
    return m


# Accessories a hand carries rather than a body wears. These are merged into
# the arm mesh and posed with it, and the arm takes a standing forward swing so
# the object is held in front of the chest instead of buried against the hip.
HELD_ACCESSORIES = ("cup",)
CARRY_SWING = -34.0     # degrees; negative is forward, see Pose

# --- assembly ----------------------------------------------------------------

@dataclass
class CharacterSpec:
    name: str
    shirt: str = "sky"
    trousers: str = "neutral"
    hair_style: str = "short"
    hair_mat: str = "neutral"
    # Leg length and stance width, as multipliers. Before these, `bulk` was
    # the only continuous shape parameter a character had, and seven of the
    # nine hand-written archetypes sit at exactly 1.0 of it -- so two extras
    # with the same hair and accessory had almost nothing left to differ by.
    # Both are deliberately small ranges: this is a cast of adults in a cafe,
    # not a fantasy party.
    leg_len: float = 1.0
    stance: float = 1.0
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
    # Sign convention, measured rather than assumed: *negative* swings the
    # limb forward (+y, toward the camera at azimuth 45). Legs, arms and the
    # foot offset all agree; only this comment used to say the opposite, and no
    # clip caught it because a walk cycle swings symmetrically.
    leg_l: float = 0.0      # degrees, - swings the limb forward (+y)
    leg_r: float = 0.0
    arm_l: float = 0.0      # - forward, as above
    arm_r: float = 0.0
    bob: float = 0.0        # vertical offset of everything above the hips
    lean: float = 0.0       # forward tilt of the upper body, degrees
    out_l: float = 0.0      # arm abduction, + swings the limb away from the body
    out_r: float = 0.0
    turn: float = 0.0       # upper-body twist about the spine, degrees


REST = Pose()


def build(spec: CharacterSpec, seated: bool = False,
          pose: Pose | None = None, seat: float = SEAT_Z, perch=None) -> Mesh:
    p = pose or REST
    spread = 0.105 * spec.stance
    hip = ANKLE_Z + (HIP_Z - ANKLE_Z) * spec.leg_len
    dz = hip - HIP_Z          # how far the whole upper body rides up or down
    x = TORSO_RX * spec.bulk + 0.052

    upper = [
        torso(spec.shirt, spec.bulk),
        head(spec.skin),
        face(spec.skin, spec.blush),
        hair(spec.hair_style, spec.hair_mat),
    ]
    held = spec.accessory_kind in HELD_ACCESSORIES
    if spec.accessory_kind and not held:
        upper.append(accessory(spec.accessory_kind, spec.accessory_mat))
    body = merge(*upper)
    if dz:
        body = transformed(body, at=(0.0, 0.0, dz))
    if p.turn:
        body = pivot_rot(body, "z", p.turn, (0.0, 0.0, hip))
    if p.lean:
        body = pivot_rot(body, "x", -p.lean, (0.0, 0.0, hip))

    def posed_arm(sx, swing, out, carried=None):
        a = arm(sx, spec.shirt, spec.skin)
        if carried is not None:
            a = merge(a, carried)
        if dz:
            a = transformed(a, at=(0.0, 0.0, dz))
        sz = SHOULDER_Z + dz
        if out:
            a = pivot_rot(a, "y", out if sx > 0 else -out, (sx, 0.0, sz))
        return pivot_rot(a, "x", -swing, (sx, 0.0, sz))

    limbs = [posed_arm(-x, p.arm_l + (CARRY_SWING if held else 0.0), p.out_l,
                       accessory(spec.accessory_kind, spec.accessory_mat, -x)
                       if held else None),
             posed_arm(x, p.arm_r, p.out_r)]
    if perch is not None:
        # Same assembly as the seated branch, and one deliberate difference:
        # NO ground clamp. The seated rig lifts the figure until its lowest
        # vertex touches z=0, which is right for feet on a floor and wrong for
        # feet on a rail -- clamping a perched figure drags it down the stool
        # until it is standing beside it. So the parts are authored about the
        # hip and the whole thing is raised to the seat instead, which is the
        # literal statement of what perching is: the hips are supported and
        # the feet are wherever they end up.
        top = min(perch[0], MAX_PERCH_Z)
        drop = (0.0, 0.0, -HIP_Z)
        out = merge(legs(spec.trousers, spread, perch=perch),
                    transformed(body, at=(0.0, 0.0, -HIP_Z - dz)),
                    *(transformed(l, at=drop) for l in limbs))
        return transformed(out, at=(0.0, 0.0, top + p.bob))
    if seated:
        # Drop the upper body to the seated hip. The torso and arms are authored
        # for a standing figure whose hips sit at HIP_Z, while the seated leg rig
        # is authored about the hip at z=0. Merging them untranslated stacked a
        # standing torso on top of folded legs and produced a seated figure
        # 2.24 tall against a standing 1.72 -- taller sitting down than up.
        drop = (0.0, 0.0, -HIP_Z)
        out = merge(legs(spec.trousers, spread, seated=True, seat=seat),
                    transformed(body, at=(0.0, 0.0, -HIP_Z - dz)),
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
        limbs.append(pivot_rot(leg(sx, spec.trousers, hip), "x", -ang,
                               (sx, 0.0, hip)))
        limbs.append(transformed(foot(sx), at=_ankle_offset(sx, ang, hip)))
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
    # Every part of this one used to come off the neutral ramp -- shirt,
    # trousers, hair and bag. Four neutrals stacked read as one dark silhouette
    # with no internal edges, which in the room composite made the customer at
    # the till a hole in the frame rather than a person. `check_palette_spread`
    # now refuses any spec that spends more than half its parts on one ramp.
    CharacterSpec("commuter", shirt="neutral+1", trousers="wood-2", hair_style="cap",
                  hair_mat="neutral-3", accessory_kind="bag",  accessory_mat="rose-1",
                  bulk=1.12),
    CharacterSpec("artist",   shirt="cream",   trousers="sky",     hair_style="curly",
                  hair_mat="neutral-2", accessory_kind="scarf", accessory_mat="foliage"),
    # Trousers were plain `neutral`, which sits 0.004 in value from a plain
    # `wood` shirt: two legal, well-separated ramps landing on the same step,
    # so the figure rendered as one column with no waist. Found by
    # `check_waistline`, which was itself promoted off the generated-extras
    # sheet -- the generator turned up a defect in the hand-written roster.
    CharacterSpec("elder",    shirt="wood",    trousers="neutral-2", hair_style="short",
                  hair_mat="cream+1", accessory_kind=None,     bulk=1.08),
    CharacterSpec("writer",   shirt="sky",     trousers="wood",    hair_style="bun",
                  hair_mat="wood-4",  accessory_kind="cup",    accessory_mat="cream"),
    # As `elder`: foliage over rose was 0.020 apart in value. And `friend` was
    # a bob at bulk 1.0 with no accessory, which is `reader` without the scarf:
    # 4.3% of outline apart over the eight sprite directions, against a roster
    # median of 19%. A slighter build under a cap puts it at 14.2%.
    CharacterSpec("friend",   shirt="foliage", trousers="rose-2",  hair_style="cap",
                  hair_mat="wood-3",  accessory_kind=None, bulk=0.90),
]

ROSTER = [BARISTA] + CUSTOMERS


# --- generated characters ----------------------------------------------------

# The parts library, as the generator sees it. Kept beside the roster rather
# than derived from `hair()` and `accessory()` by regex, because a list that
# reads itself out of an implementation silently loses an option the day
# somebody renames a branch.
HAIR_STYLES = ("short", "bob", "long", "bun", "cap", "curly")
ACCESSORIES = (None, "scarf", "bag", "cup", None)

# Shirts and trousers may take any ramp; hair may not. Hair on `sky` or
# `foliage` is a costume choice this art direction does not make.
GARMENT_RAMPS = ("wood", "cream", "foliage", "rose", "sky", "neutral")

# Three ramps, every offset. The ramps are an art-direction choice -- black,
# grey, brown, blonde and white are hair; pink is a costume, and the generator
# put pink hair on an extra the first time `rose` was in this list. The
# OFFSETS deliberately are not filtered.
#
# That distinction is the whole point. An earlier version listed seven hair
# tones hand-picked to pass `check_contrast` against a mid-wood skin, and
# across 200 generated specs the contrast check fired exactly zero times: the
# constraint had been solved by hand and the check was decoration hanging off a
# random draw. A solver whose search space is pre-filtered to the answer is not
# solving anything. Offering every offset -- including the mid browns that
# vanish into a face -- makes the check reject 47% of proposals, and it is the
# check rather than a person that decides which tones are usable.
HAIR_MATS = tuple(f"{r}{o:+d}" if o else r
                  for r in ("neutral", "wood", "cream")
                  for o in (-4, -3, -2, -1, 0, 1, 2))


MIN_SILHOUETTE = 0.10


SPRITE_AZIMUTHS = (0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0)


def silhouette(spec: CharacterSpec, azimuths=SPRITE_AZIMUTHS) -> tuple:
    """The screen pixels a character covers in each sprite direction, materials
    ignored.

    Shirt colour is what a viewer notices first and the last thing that
    survives being one figure among eight in a room -- at 46 px a crowd is read
    as shapes, and two extras with the same build are the same person in a
    different jumper.

    This started life as `silhouette_key`, a tuple of the parameters believed
    to change the outline: hair style, accessory, and bulk in 0.06 buckets. It
    did nothing. Twenty extras produced twenty distinct keys, so the rejection
    never fired once, while the rendered cast still contained a pair whose
    outlines matched to the pixel -- they differed by an accessory, and the
    accessory turned out to be invisible in silhouette at every azimuth.

    The key was not mistuned, it was the wrong kind of thing: a guess at which
    parameters reach the outline, standing in for the outline. At 3.6 ms a view
    there is no reason to guess. `screen_materials` already renders the figure
    the checks are going to grade, so the generator grades the same render.

    All eight directions, not the canonical one. The sheet turns the character
    rather than the camera, so those azimuths are the eight frames a player
    actually sees, and judging a cast from azimuth 45 alone grades one of them.
    That is not a hypothetical: `reader` and `friend` differ by a scarf, which
    at azimuth 45 is worth 1.3% and over the eight views is worth 4.3%.
    """
    from art_review import screen_materials
    m = build(spec)
    return tuple(frozenset(i for i, x in enumerate(screen_materials(m, a, 2.0)) if x)
                 for a in azimuths)


def silhouette_distance(a: tuple, b: tuple) -> float:
    """Mean Jaccard distance over the sprite directions: 0 is the same figure."""
    v = [len(x ^ y) / max(1, len(x | y)) for x, y in zip(a, b)]
    return sum(v) / len(v)


def generate_spec(seed: int, ramps=None, tries: int = 60) -> CharacterSpec:
    """A character built by proposing and testing, not by being typed out.

    The roster is nine hand-written specs, and characters are what this factory
    exists to produce -- so it is the largest remaining piece of the library
    that is an *asset* rather than a tool. A game wants forty extras and no
    person should be choosing forty pairs of trousers.

    What makes this more than a random draw is that the checks come first.
    `check_contrast` and `check_palette_spread` were both promoted from human
    rejections -- hair vanishing into a face, and a customer built entirely
    from one ramp reading as a silhouette-shaped hole at the till -- and both
    are predicates on a finished spec. Run them *before* accepting a proposal
    rather than after, and they stop being graders and become a solver. That is
    the same move `Layout.scatter` made with `collisions` and `grounded`, and
    it is the strongest argument this repo has that the checks were worth
    writing.

    `taken` carries the silhouette keys already used by this cast, so a
    proposal that would be shape-identical to an accepted one is rejected
    before it is accepted rather than after. That makes the solver
    order-dependent, which is the same property `Layout.scatter` has and for
    the same reason: a cast is a set, and whether a member fits is a question
    about the members already in it.

    Raising `tries` cannot make an unsatisfiable palette satisfiable, so a
    proposal that never passes falls back to the last one tried and is left for
    the checks to report. Silently returning something invalid would be worse
    than the hand-written roster it replaces.
    """
    ramps = ramps or _palette()
    st = (seed * 2654435761 + 1013904223) & 0xFFFFFFFF

    def rnd():
        nonlocal st
        st ^= st >> 16
        st = (st * 2246822519) & 0xFFFFFFFF
        st ^= st >> 13
        st = (st * 3266489917) & 0xFFFFFFFF
        st = (st ^ (st >> 16)) & 0xFFFFFFFF
        return st / 0xFFFFFFFF

    def pick(seq):
        return seq[int(rnd() * len(seq)) % len(seq)]

    spec = None
    for _ in range(tries):
        shirt = pick(GARMENT_RAMPS)
        # Offsets on garments, because two characters in flat `sky` and flat
        # `rose` still read as two poster-paint blocks. A step either way is
        # what separates a shirt from a swatch.
        shirt += pick(("", "", "+1", "-1", "-2"))
        trousers = pick(GARMENT_RAMPS) + pick(("", "-1", "-2", "-2"))
        acc = pick(ACCESSORIES)
        spec = CharacterSpec(
            f"extra{seed:02d}", shirt=shirt, trousers=trousers,
            hair_style=pick(HAIR_STYLES), hair_mat=pick(HAIR_MATS),
            accessory_kind=acc,
            accessory_mat=pick(GARMENT_RAMPS) + pick(("", "-1", "+1")),
            bulk=0.90 + rnd() * 0.30,
            # Measured against the outline before being given a range, the way
            # the accessories had to be. Over the eight sprite directions a
            # leg_len of 0.88 is worth 4.5% against a default figure and a
            # stance of 1.40 about 4%, which is the same order as an accessory
            # and enough to separate two extras that share hair and hands.
            leg_len=0.88 + rnd() * 0.26,
            stance=0.82 + rnd() * 0.58)
        if not (check_contrast(ramps, [spec]) + check_palette_spread([spec])
                + check_waistline(ramps, [spec])):
            return spec
    return spec


def generate_roster(n: int = 8, seed: int = 1, ramps=None,
                    distinct_shapes: bool = True,
                    floor: float = MIN_SILHOUETTE, tries: int = 6) -> list:
    """`n` extras from consecutive seeds, no two of them the same shape.

    Built incrementally rather than independently, because "is this character
    already in the cast?" cannot be answered by a function that has only seen
    one character.

    Each slot draws up to `tries` candidates and keeps the one whose outline is
    furthest from every extra already cast, stopping early once a candidate
    clears `floor`. Keeping the best rather than looping until one passes means
    a saturated cast degrades instead of hanging -- the same bargain
    `Layout.scatter` makes when a region runs out of room.
    """
    ramps = ramps or _palette()
    out: list = []
    seen: list = []
    for i in range(n):
        if not distinct_shapes:
            out.append(generate_spec(seed + i, ramps))
            continue
        best = best_sil = None
        best_score = -1.0
        for k in range(tries):
            # 977 is coprime with the stride, so a retry cannot collide with
            # the seed of another slot and hand two extras the same draw.
            spec = generate_spec(seed + i + 977 * k, ramps)
            sil = silhouette(spec)
            score = min((silhouette_distance(sil, s) for s in seen), default=1.0)
            if score > best_score:
                best, best_sil, best_score = spec, sil, score
            if score >= floor:
                break
        seen.append(best_sil)
        out.append(_replace(best, name=f"extra{seed + i:02d}"))
    return out


def _palette():
    from pixelize import load_palette
    return load_palette()


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


# A shirt and trousers this close in lightness give a figure no waistline.
# Measured in OKLab L, and set at one ramp step: the palette's ramps run about
# 0.10 apart, so anything under that is the two garments landing on the same or
# adjacent steps.
MIN_WAIST_GAP = 0.085


# Two characters closer than this on screen are the same person twice.
#
# Calibrated, not guessed. The first number here was 0.20, which would never
# have fired: the nine hand-written archetypes have a closest pair at 45%
# (reader/friend) and twenty generated extras at 48%, with both medians at 80%.
# A threshold at less than half the observed minimum is a check that cannot
# fail, which is the mistake the occlusion thresholds made two passes ago --
# defaults set looser than the scan that found the defect left the check blind.
# 0.38 sits under the evidence rather than at it, and still catches a collision
# the eye would.
#
# Worth recording that the generated cast came out *more* varied at its closest
# pair than the hand-written one. Nine archetypes written by a person include
# two that are nearly the same person, and nobody noticed across five passes.
MIN_PAIR_SPREAD = 0.38


def check_roster_variety(roster=None, azimuth: float = 45.0,
                         floor: float = MIN_PAIR_SPREAD) -> list[str]:
    """Are any two characters in this cast the same person?

    `check_contrast`, `check_palette_spread` and `check_waistline` are all
    predicates on ONE spec, and a generator that satisfies all three forty times
    can still return forty variations of one person -- each individually legal,
    and collectively a crowd the player reads as a single repeated extra. That
    is the character version of the failure `check_generator_range` catches in
    the furniture, and it needs the same instrument: a distance, applied
    pairwise.

    The MINIMUM pair, not the mean. A mean is dominated by the pairs that are
    already fine and says nothing about the two that collide, and it is exactly
    those two that a player notices -- forty extras of whom two are twins reads
    as a bug, whatever the average says.
    """
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from art_review import _screen_spread, screen_materials

    specs = list(roster or ROSTER)
    if len(specs) < 2:
        return []
    frames = [screen_materials(build(s), azimuth, 2.0) for s in specs]
    out = []
    for i, a in enumerate(frames):
        for j in range(i + 1, len(frames)):
            d = _screen_spread([a, frames[j]])
            if d < floor:
                out.append(f"{specs[i].name} and {specs[j].name} are "
                           f"{d:.0%} apart on screen (floor {floor:.0%}) -- "
                           f"the same person twice")
    return out


# Two characters whose OUTLINES are this close read as one figure recoloured.
#
# `check_roster_variety` sits at 0.38 and passed both casts comfortably while
# this was broken, because it compares materials as well as coverage: two
# identical shapes in different shirts disagree on most of their pixels and
# score as different people. Stripping the materials out drops the same casts
# by a factor of four, which is the measurement that mattered -- colour is what
# a viewer notices first and shape is what survives the downsample.
#
# Calibrated against the defects it was written for: a generated pair at 0.0%,
# `reader`/`friend` at 4.3%, and an accessory that moved zero pixels of outline
# at any azimuth. With those fixed the casts sit at 10.0% (hand) and 8.5%
# (generated), so 0.07 sits under the evidence rather than at it.
MIN_CAST_SILHOUETTE = 0.07


def check_cast_silhouette(roster=None,
                          floor: float = MIN_CAST_SILHOUETTE) -> list[str]:
    """Are any two characters in this cast the same SHAPE?

    The shape-only half of `check_roster_variety`, and the half that turned out
    to be doing the work. Run over the eight sprite directions rather than the
    canonical one, because the sheet turns the character under a fixed camera:
    those eight azimuths are the frames a player sees, and a pair that separates
    at 45 and collapses at 0 is a pair that collapses one frame in eight.
    """
    specs = list(roster or ROSTER)
    if len(specs) < 2:
        return []
    sils = [silhouette(s) for s in specs]
    out = []
    for i in range(len(sils)):
        for j in range(i + 1, len(sils)):
            d = silhouette_distance(sils[i], sils[j])
            if d < floor:
                out.append(f"{specs[i].name} and {specs[j].name} have "
                           f"{d:.1%} of outline between them (floor "
                           f"{floor:.0%}) -- one shape, two paint jobs")
    return out


def check_waistline(ramps, roster=None) -> list[str]:
    """A shirt and trousers that resolve to the same value have no edge between them.

    Promoted from the generated-extras sheet, which is what the sheet is for.
    `check_palette_spread` allows two of four parts on one ramp, and that is
    the right rule -- it exists to stop a figure being built entirely from one
    ramp. But it counts *ramps*, not values, so a rose shirt over rose trousers
    passes it at exactly the 50% limit and renders as a single pink column with
    no waist. At 46 px of figure the waist is one edge, and losing it costs
    more than any of the detail this pipeline spends triangles on.

    This is the same shape of gap as the one `check_palette_spread` itself
    filled: `check_contrast` was already comparing two parts for value
    separation, just the wrong two.
    """
    from oklab import srgb_to_oklab
    from pixelize import material

    out = []
    for s in roster or ROSTER:
        vals = []
        for part in (s.shirt, s.trousers):
            ramp, tone = material(part)
            steps = ramps[ramp]
            vals.append(srgb_to_oklab(
                steps[_clamp(len(steps) // 2 + tone, steps)])[0])
        gap = abs(vals[0] - vals[1])
        if gap < MIN_WAIST_GAP:
            out.append(f"{s.name}: shirt {s.shirt!r} and trousers "
                       f"{s.trousers!r} are {gap:.3f} apart in value "
                       f"(need {MIN_WAIST_GAP}) -- no waistline")
    return out


def check_palette_spread(roster=None, max_share: float = 0.5) -> list[str]:
    """No character may spend more than `max_share` of its parts on one ramp.

    Sibling check to `check_contrast`, and a strictly different failure. That one
    catches hair disappearing into a face; this catches a whole figure built from
    a single ramp, where every part is individually a legal, well-separated tone
    and the character still reads as one dark mass because there is no hue change
    anywhere on it to give the eye an edge.

    `commuter` shipped that way -- neutral shirt, neutral trousers, neutral hair,
    neutral bag -- and at the till it was a silhouette-shaped hole in the room.
    Tone offsets are stripped before counting: "neutral" and "neutral-3" are the
    same ramp and the same problem.
    """
    from pixelize import material
    out = []
    for s in roster or ROSTER:
        parts = [s.shirt, s.trousers, s.hair_mat, s.accessory_mat]
        ramps_used = [material(p)[0] for p in parts if p]
        if not ramps_used:
            continue
        top = max(set(ramps_used), key=ramps_used.count)
        share = ramps_used.count(top) / len(ramps_used)
        if share > max_share:
            out.append(f"{s.name}: {ramps_used.count(top)}/{len(ramps_used)} parts "
                       f"on the '{top}' ramp ({share:.0%}) -- reads as one mass")
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
    problems = (check_contrast(ramps) + check_palette_spread()
                + check_waistline(ramps)
                + check_direction_stability())
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
