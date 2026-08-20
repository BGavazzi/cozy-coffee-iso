"""Animated effects, as meshes that are a function of phase.

Characters animate by posing one rig. Effects have no rig -- steam has no
skeleton -- so they animate by *rebuilding* geometry each frame. Same contract
either way: give the renderer a mesh, get a palette-exact sprite back.

**Radial means segments divide 8.** Azimuths step 45 degrees, so a primitive
only survives a rotation if its own symmetry order is a multiple of 8 (or of the
class it claims). A 10-segment hub inside a 4-blade fan makes the whole fan
direction-dependent, and the render budget silently multiplies by eight. This is
verified, not trusted: `art_review.check_symmetry_claims` renders every azimuth
and compares.

Two conventions carry most of the readability here:

**Fade with the ramp, not with alpha.** A wisp of steam thins out by climbing to
a paler step of its own ramp (`cream+2`), not by going translucent. Sprites are
composited by a game engine that may not blend, and more importantly a dithered
alpha edge is exactly the noise the pixelize stage exists to prevent.

**Loop by construction.** Every generator below is periodic in phase, so frame N
and frame 0 are continuous by algebra rather than by an artist matching them.
That is the single most common defect in hand-made loops.
"""
from __future__ import annotations

import math

from mesh import Mesh

TAU = 2 * math.pi


# --- steam -------------------------------------------------------------------

def steam(phase: float, puffs: int = 4, height: float = 0.42,
          spread: float = 0.055, base=(0.5, 0.5, 0.0)) -> Mesh:
    """Wisps rising and thinning. Each puff is offset in phase so the column
    reads as continuous rather than as a pulse."""
    m = Mesh()
    bx, by, bz = base
    for i in range(puffs):
        t = (phase + i / puffs) % 1.0
        z = bz + t * height
        # Drift sideways as it rises, the way real steam curls.
        # No sideways drift. Curling wisps look better and cost eight times the
        # storage, because any horizontal offset destroys the radial symmetry
        # that lets one render serve every direction. Steam sits on every cup in
        # the game, so this is the one place that trade is clearly not worth it;
        # the life comes from radius and ramp step instead, both of which are
        # rotation-invariant.
        r = 0.030 + 0.055 * t                     # expands as it cools
        r *= 1.0 + 0.18 * math.sin(TAU * (t + i * 0.37))
        step = min(3, int(t * 4))                 # and climbs the ramp as it thins
        m.add_sphere((bx, by, z), r, f"cream+{step}", 8, 5)
    return m


def steam_machine(phase: float) -> Mesh:
    """Two jets from a group head, wider and faster than a cup."""
    m = Mesh()
    for i, bx in enumerate((0.38, 0.62)):
        sub = steam((phase + i * 0.5) % 1.0, puffs=3, height=0.5, spread=0.075,
                    base=(bx, 0.5, 0.0))
        m.verts += sub.verts
        off = len(m.verts) - len(sub.verts)
        m.faces += [((a + off, b + off, c + off), None, mat)
                    for (a, b, c), _, mat in sub.faces]
    return m


# --- pours -------------------------------------------------------------------

def pour(phase: float, mat: str = "wood", height: float = 0.34) -> Mesh:
    """A falling stream plus the splash it lands in.

    The stream is broken into beads rather than drawn as a solid column: at 3 px
    wide a continuous cylinder reads as a static rod, and the eye needs the
    beads' motion to see it as liquid at all.
    """
    m = Mesh()
    beads = 5
    for i in range(beads):
        t = (phase + i / beads) % 1.0
        z = height * (1.0 - t)
        # Accelerating fall, so the beads bunch at the top and stretch below.
        z = height * (1.0 - t * t)
        m.add_sphere((0.5, 0.5, z), 0.026, mat, 8, 4)
    ring = 0.055 + 0.045 * abs(math.sin(TAU * phase))
    m.add_cylinder((0.5, 0.5, 0.0), ring, 0.018, mat + "+1", 8)
    return m


# --- door --------------------------------------------------------------------

def door_swing(phase: float, opening: bool = True) -> Mesh:
    """Hinged at x=0. Eased rather than linear: a door that moves at constant
    speed reads as mechanical, and the ease is free in a closed form."""
    t = phase if opening else 1.0 - phase
    t = 0.5 - 0.5 * math.cos(math.pi * min(1.0, max(0.0, t)))
    a = math.radians(82.0 * t)
    c, s = math.cos(a), math.sin(a)
    m = Mesh()
    w, th, h = 0.9, 0.08, 1.5

    def hinge(x, y, z):
        return (x * c - y * s, x * s + y * c, z)

    lo = [hinge(0.0, 0.0, 0.0), hinge(w, 0.0, 0.0),
          hinge(w, th, 0.0), hinge(0.0, th, 0.0)]
    hi = [(x, y, h) for x, y, _ in lo]
    for i in range(4):
        j = (i + 1) % 4
        m.add_quad(lo[i], lo[j], hi[j], hi[i], "wood")
    m.add_quad(hi[0], hi[1], hi[2], hi[3], "wood")
    # Glass panel, inset, so the door does not read as a plank.
    gl = [hinge(0.14, th * 0.45, 0.62), hinge(w - 0.14, th * 0.45, 0.62),
          hinge(w - 0.14, th * 0.55, 1.30), hinge(0.14, th * 0.55, 1.30)]
    m.add_quad(gl[0], gl[1], gl[2], gl[3], "sky+2")
    return m


# --- ceiling fan -------------------------------------------------------------

def ceiling_fan(phase: float, blades: int = 4, r: float = 0.86) -> Mesh:
    m = Mesh()
    m.add_cylinder((1.0, 1.0, 0.0), 0.13, 0.16, "neutral", 8)
    for i in range(blades):
        a = TAU * (phase / blades + i / blades)
        c, s = math.cos(a), math.sin(a)
        # Blade as a quad swept from hub to tip, twisted slightly for pitch.
        inner, outer, half = 0.16, r, 0.13
        p = [(1.0 + inner * c - half * s, 1.0 + inner * s + half * c, 0.05),
             (1.0 + outer * c - half * s, 1.0 + outer * s + half * c, 0.08),
             (1.0 + outer * c + half * s, 1.0 + outer * s - half * c, 0.03),
             (1.0 + inner * c + half * s, 1.0 + inner * s - half * c, 0.0)]
        # Underside offset below the top face, not coincident with it. Two
        # co-planar quads at identical depth z-fight, and the tie-break flips
        # with camera azimuth -- which made a blade that is exactly four-fold
        # symmetric measure as eight distinct directions, and would have cost
        # four times the render budget for nothing.
        m.add_quad(*p, material="wood")
        under = [(x, y, z - 0.022) for x, y, z in p]
        m.add_quad(under[3], under[2], under[1], under[0], material="wood-1")
        for i in range(4):
            j = (i + 1) % 4
            m.add_quad(under[i], under[j], p[j], p[i], "wood-1")
    return m


# --- order ready -------------------------------------------------------------

def order_ready(phase: float) -> Mesh:
    """A bobbing marker over a finished drink. Squash-and-stretch, because at
    this size a bounce with constant volume does not read as a bounce."""
    t = abs(math.sin(math.pi * phase))
    z = 0.30 + 0.16 * t
    sq = 1.0 + 0.18 * (1.0 - t)
    m = Mesh()
    m.add_prism((0.5, 0.5, z), 0.115 * sq, 0.115 * sq, 0.16 / sq,
                "gold_coin", segments=8)
    m.add_prism((0.5, 0.5, z + 0.16 / sq), 0.05, 0.05, 0.05, "cream+2", segments=8)
    return m


def rain_window(phase: float, drops: int = 7) -> Mesh:
    """Streaks on glass. Vertical only -- a diagonal streak at 2 px wide just
    reads as noise."""
    m = Mesh()
    for i in range(drops):
        t = (phase + i / drops) % 1.0
        x = 0.09 + 0.82 * ((i * 0.37) % 1.0)
        z = 1.32 * (1.0 - t)
        m.add_box((x - 0.018, 0.0, z), (x + 0.018, 0.02, z + 0.10 + 0.10 * t),
                  "sky+1")
    return m


FX = {
    "fx_steam_cup": (steam, {"loop": 4}),
    "fx_steam_machine": (steam_machine, {"loop": 4}),
    "fx_pour_coffee": (lambda p: pour(p, "wood"), {"loop": 4}),
    "fx_pour_milk": (lambda p: pour(p, "cream"), {"loop": 4}),
    "fx_door_swing": (door_swing, {"open": 4, "close": 4}),
    "fx_ceiling_fan": (ceiling_fan, {"loop": 4}),
    "fx_rain_window": (rain_window, {"loop": 6}),
    "fx_order_ready": (order_ready, {"loop": 4}),
}


def check_loops(tol: float = 0.02) -> list[str]:
    """A looping clip must return to its start. Verified by construction here,
    but verified anyway -- an off-by-one in a phase divisor is invisible in a
    still and glaring in motion.
    """
    out = []
    for name, (fn, clips) in FX.items():
        if "loop" not in clips:
            continue
        n = clips["loop"]
        a = fn(0.0)
        b = fn(n / n)          # phase 1.0 must equal phase 0.0
        if len(a.verts) != len(b.verts):
            out.append(f"{name}: vertex count changes across the loop seam")
            continue
        # Compare SETS of positions, not the vertex arrays in order. A 4-blade
        # fan advanced a quarter turn maps exactly onto itself: the geometry is
        # identical and only the labelling rotated. An ordered comparison called
        # that a 0.99-unit pop, which would have sent someone hunting a bug in
        # correct code.
        pa, pb = sorted(a.verts), sorted(b.verts)
        worst = max((max(abs(p[i] - q[i]) for i in range(3))
                     for p, q in zip(pa, pb)), default=0.0)
        if worst > tol:
            out.append(f"{name}: loop seam moves {worst:.3f} units "
                       f"(tol {tol}) - the loop will visibly pop")
    return out


if __name__ == "__main__":
    problems = check_loops()
    for p in problems:
        print(f"  BLOCKER  {p}")
    print(f"{len(problems)} blocker(s) across {len(FX)} effects")
    raise SystemExit(1 if problems else 0)
