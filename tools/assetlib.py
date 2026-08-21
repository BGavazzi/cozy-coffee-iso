"""Procedural blockout meshes for the tier-1 asset set.

These are **placeholders**, not final art. They stand in for what stages 1-4
(concept -> mesh -> rig -> motion) will eventually deliver, so the rest of the
factory -- layout, camera, shading, palette, review -- can be exercised at room
scale before any generative stage exists.

Blockouts are the right placeholder specifically because the pipeline's
guarantees are geometric: if the projection, lighting and palette read correctly
on boxes and cylinders, they will read correctly on detailed meshes, and if they
do not, no amount of mesh detail rescues them.

One world unit = one tile.
"""
from __future__ import annotations

import math

from mesh import Mesh

# Semantic material names, mapped to palette ramps in pixelize.MATERIAL_RAMPS.
WOOD, CERAMIC, PLANT, FABRIC, METAL = (
    "wood", "cream", "foliage", "rose", "neutral")

# Glass is the sky ramp read HIGH, not at its middle. Mid-lightness sky over a
# whole pane is a saturated blue slab -- which is exactly what review called
# "windows that do not look like glass". Real glass is nearly the value of what
# is behind it, with the colour arriving only at the edges, so panes sit two
# steps up (pale, barely tinted) and only the rims and mullions carry the hue.
GLASS = "sky+2"
GLASS_EDGE = "sky"

# The wall field, two steps down from plain cream. At full cream the far wall
# measured 0.77-0.78 mean lightness -- the brightest thing in the frame by a
# wide margin -- so the eye was pulled to the top edge and off everything the
# room is actually about. A backdrop should be the quietest surface present.
WALL_FIELD = "cream-2"

# The floor field, one step down from bare wood. Not a colour choice -- a value
# choice. With the floor at plain wood, the whole interior lived in one narrow
# band (floor, walls, and nearly every prop between L 0.55 and 0.75), so props
# had nothing to sit against and the service counter could only lead the frame
# by +0.09 local contrast. Dropping the ground one step gives the composition a
# floor in the literal sense: a value everything else is measured up from.
FLOOR_FIELD = "wood-1"


def transformed(m: Mesh, rot_z: float = 0.0, at: tuple = (0.0, 0.0, 0.0),
                scale: float = 1.0) -> Mesh:
    """Rotate about Z (degrees), scale, then translate."""
    c, s = math.cos(math.radians(rot_z)), math.sin(math.radians(rot_z))
    out = Mesh()
    out.verts = [((x * c - y * s) * scale + at[0],
                  (x * s + y * c) * scale + at[1],
                  z * scale + at[2]) for x, y, z in m.verts]
    out.normals = list(m.normals)
    out.faces = list(m.faces)
    return out


def pivot_rot(m: Mesh, axis: str, degrees: float, pivot: tuple) -> Mesh:
    """Rotate a mesh about an arbitrary pivot -- the primitive posing needs.

    `transformed` rotates about the world origin, which is fine for placing a
    prop and useless for swinging a limb: a leg has to turn about its hip, not
    about the floor.
    """
    if not degrees:
        return m
    a = math.radians(degrees)
    c, s_ = math.cos(a), math.sin(a)
    px, py, pz = pivot
    out = Mesh()
    out.normals = list(m.normals)
    out.faces = list(m.faces)
    verts = []
    for x, y, z in m.verts:
        x, y, z = x - px, y - py, z - pz
        if axis == "x":
            y, z = y * c - z * s_, y * s_ + z * c
        elif axis == "y":
            x, z = x * c + z * s_, -x * s_ + z * c
        else:
            x, y = x * c - y * s_, x * s_ + y * c
        verts.append((x + px, y + py, z + pz))
    out.verts = verts
    return out


def merge(*meshes: Mesh) -> Mesh:
    out = Mesh()
    for m in meshes:
        off = len(out.verts)
        out.verts += m.verts
        out.faces += [((a + off, b + off, c + off), None, mat)
                      for (a, b, c), _, mat in m.faces]
    return out


# --- structure ---------------------------------------------------------------

def floor(w: int, d: int, tone_a=FLOOR_FIELD, tone_b=CERAMIC, checker=False) -> Mesh:
    """Board flooring: one slab, with flat tone overlays for planks and seams.

    A single unbroken quad was 63% of the frame at one ramp step, the clearest
    tell of a blockout -- every comparable in the genre breaks its floor with
    plank seams, worn patches or tiling.

    Two traps here, both hit in review. First, restraint: half-tile boards with
    a two-step-dark seam turned the floor into a barcode that pulled the eye off
    every prop in the room. Second, and less obvious: laying planks as separate
    boxes leaves a 0.06 vertical face at every joint. Those faces are turned
    away from the key light, so they shaded to ramp step 0 and put 15% of the
    floor at the darkest colour in the palette -- a black grid, produced by
    geometry that was only ever meant to be a tone change.

    So: one slab, and the variation is flat overlays a thousandth of a unit
    above it, with no vertical extent to catch a shadow.
    """
    m = Mesh()
    if checker:
        for x in range(w):
            for y in range(d):
                m.add_box((x, y, -0.06), (x + 1, y + 1, 0.0),
                          tone_a if (x + y) % 2 == 0 else tone_b)
        return m
    m.add_box((0, 0, -0.06), (w, d, 0.0), tone_a)
    # Tone varies per BOARD, not per course. Both earlier versions assigned the
    # tone to a whole course, so every change was a stripe one unit deep and the
    # full width of the room -- five ruled lines that cut the composite into
    # bands stronger than any prop in it. Darker stripes were worse than lighter
    # ones, but the defect was never the direction of the offset; it was that
    # the unit of variation was the wrong shape. Real board flooring varies
    # board to board, which scatters the tone instead of banding it.
    board = 1.0

    def flat(x0, y0, x1, y1, z, mat):
        """Zero-thickness overlay, not a thin box.

        A box 0.0018 tall still has four side faces, and their normals point
        sideways, so they shade to the BOTTOM of the ramp. Subpixel or not, they
        win the depth test along the entire run: measured, the seams put ramp
        step 0 across 7.6% of open floor and drew a near-black grid. A quad has
        no sides, so the seam can only ever be the one step it asks for.
        """
        m.add_quad((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z), mat)

    # Offsets come from a fixed LCG, not `random`, so the floor is byte-identical
    # on every run: a floor that reshuffles between renders makes every
    # before/after comparison in ART_CRITIQUE.md meaningless.
    seed = 12345

    def nxt():
        nonlocal seed
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        return seed / 0x7FFFFFFF

    for i in range(int(d / board)):
        y0, y1 = i * board, min(d, (i + 1) * board)
        x = 0.0
        while x < w:
            x1 = min(w, x + 1.6 + 2.6 * nxt())       # one board, staggered ends
            r = nxt()
            t = "+1" if r < 0.16 else ("-1" if r < 0.30 else "")
            if t:
                flat(x, y0, x1, y1 - 0.03, 0.0012, tone_a + t)
            if x1 < w:                                # butt joint at the end
                flat(x1, y0 + 0.04, x1 + 0.035, y1 - 0.04, 0.0018, tone_a + "-1")
            x = x1
        flat(0, y1 - 0.03, w, y1, 0.0018, tone_a + "-1")                 # long seam
    return m


def rug(w: float, d: float, mat=FABRIC) -> Mesh:
    """A rug is the cheapest way to give a seating cluster its own ground and to
    put a second hue into a floor that is otherwise all one material."""
    m = Mesh()
    m.add_box((0, 0, 0.001), (w, d, 0.012), mat + "-2")
    m.add_box((0.18, 0.18, 0.012), (w - 0.18, d - 0.18, 0.020), mat + "-1")
    return m


def warp(m: Mesh, amount: float = 0.030, scale: float = 1.9,
         seed: int = 0) -> Mesh:
    """Nudge vertices by a smooth function of WORLD POSITION, not per vertex.

    Every prop in the library is a perfect axis-aligned primitive, so six chairs
    are six pixel-identical chairs and every edge in the room is machine
    straight. The SNES backgrounds this project cites are full of stock that
    sags, leans and wears; that irregularity is most of what separates a drawn
    interior from a blockout.

    The offset is a function of position, which is the whole trick. Displacing
    each vertex independently would split every shared corner -- `add_box` emits
    its own eight vertices per box, so a counter run would open seams between
    modules and a chair would come apart at the joints. Two coincident vertices
    evaluate the same function and therefore move together, so connectivity is
    preserved without the mesh ever needing to know about it.

    It also means variation is free: the same chair placed at two positions in
    the room samples the field at two places and warps differently, with no
    per-instance seed to thread through.

    `amount` is in world units. At the room's 27.2 px per unit, 0.03 is about a
    pixel -- enough to break a straight run without turning it to noise.
    """
    import math

    def off(v, k):
        h = (math.floor(v[0] * scale) * 73856093
             ^ math.floor(v[1] * scale) * 19349663
             ^ math.floor(v[2] * scale) * 83492791
             ^ (seed + k) * 26183)
        h = (h * 1103515245 + 12345) & 0x7FFFFFFF
        h ^= h >> 15
        return ((h & 0xFFFF) / 0xFFFF - 0.5) * 2.0

    out = Mesh()
    out.verts = [(v[0] + amount * off(v, 1),
                  v[1] + amount * off(v, 2),
                  v[2] + amount * off(v, 3) * 0.5) for v in m.verts]
    out.faces = list(m.faces)
    out.normals = []
    return out


def wall_run(start, along: str, length: int, height=2.45,
             openings: tuple = ()) -> Mesh:
    """A wall along +x or +y, with tile indices left open for doors/windows.

    Head height is 1.59 units, and the wall used to be 1.6 -- a ceiling exactly
    at the top of everyone's head, which is why the room read as a dollhouse
    tray rather than an interior. Real cafes run about 1.6x head height. Only
    the two far walls are ever drawn, and they sit behind every object in the
    scene, so raising them cannot occlude anything: it costs nothing and it is
    what gives signage, shelving and the window heads somewhere to live.
    """
    m = Mesh()
    x0, y0 = start
    t = 0.12
    for i in range(length):
        if i in openings:
            # A bare aperture reads as a hole punched in a wall. Glass needs a
            # frame, a bright pane, and mullions to catch the light.
            # Sill and head, raised with the wall. Left at 0.38/1.22 against a
            # 2.45 ceiling the windows sat in the bottom third with a blank
            # metre of plaster above them, which is what a wall looks like when
            # the openings were sized for a shorter room and never revisited.
            a, b = 0.58, 1.82                       # sill height, head height
            if along == "x":
                m.add_box((x0 + i, y0, 0), (x0 + i + 1, y0 + t, a), WOOD)
                m.add_box((x0 + i, y0, b), (x0 + i + 1, y0 + t, height), WOOD)
                m.add_box((x0 + i, y0 + t * 0.30, a), (x0 + i + 1, y0 + t * 0.70, b), GLASS)
                for fx in (0.0, 0.94):              # jambs
                    m.add_box((x0 + i + fx, y0, a), (x0 + i + fx + 0.06, y0 + t, b), WOOD)
                m.add_box((x0 + i + 0.47, y0 + t * 0.2, a), (x0 + i + 0.53, y0 + t * 0.8, b), WOOD)
                m.add_box((x0 + i, y0 - 0.05, a - 0.05), (x0 + i + 1, y0 + t, a), WOOD)  # sill
            else:
                m.add_box((x0, y0 + i, 0), (x0 + t, y0 + i + 1, a), WOOD)
                m.add_box((x0, y0 + i, b), (x0 + t, y0 + i + 1, height), WOOD)
                m.add_box((x0 + t * 0.30, y0 + i, a), (x0 + t * 0.70, y0 + i + 1, b), GLASS)
                for fy in (0.0, 0.94):
                    m.add_box((x0, y0 + i + fy, a), (x0 + t, y0 + i + fy + 0.06, b), WOOD)
                m.add_box((x0 + t * 0.2, y0 + i + 0.47, a), (x0 + t * 0.8, y0 + i + 0.53, b), WOOD)
                m.add_box((x0 - 0.05, y0 + i, a - 0.05), (x0 + t, y0 + i + 1, a), WOOD)
            continue
        if along == "x":
            m.add_box((x0 + i, y0, 0), (x0 + i + 1, y0 + t, 0.5), WOOD)      # wainscot
            m.add_box((x0 + i, y0, 0.5), (x0 + i + 1, y0 + t, height), WALL_FIELD)
        else:
            m.add_box((x0, y0 + i, 0), (x0 + t, y0 + i + 1, 0.5), WOOD)
            m.add_box((x0, y0 + i, 0.5), (x0 + t, y0 + i + 1, height), WALL_FIELD)
    # Picture rail. The taller wall doubled the area of unbroken WALL_FIELD, and
    # a single flat field that large goes back to being the biggest quiet mass
    # in the frame -- the exact failure that pulled the eye to the top edge when
    # the wall was plain cream. One horizontal trim splits it into a lower band
    # the windows belong to and an upper band that reads as ceiling.
    # The trim must stand proud on the ROOM side. The first attempt extended it
    # to y0 - 0.03, which is outside the room and behind the wall face, so all
    # that reached the camera was a subpixel sliver that dithered into a dashed
    # line -- a defect that looks like a rendering bug and is really a sign
    # error. The room is at y > 0 for the x-wall and x > 0 for the y-wall.
    rail = min(2.02, height - 0.30)
    if rail > 0.6:
        if along == "x":
            m.add_box((x0, y0, rail), (x0 + length, y0 + t + 0.07, rail + 0.11), WOOD)
        else:
            m.add_box((x0, y0, rail), (x0 + t + 0.07, y0 + length, rail + 0.11), WOOD)
    return m


# --- props -------------------------------------------------------------------

def counter(kick=True) -> Mesh:
    """Modular: the body spans the FULL tile so a run tiles seamlessly.
    Insetting it left a seam between every adjacent module."""
    m = Mesh()
    # Without a plinth the carcass must reach the floor itself. It did not, so
    # every kick=False counter -- the whole window bar run -- hovered 0.10 above
    # the ground. Invisible at a glance and caught by Layout.grounded().
    base = 0.10 if kick else 0.0
    m.add_box((0.0, 0.06, base), (1.0, 0.94, 0.82), WOOD)       # carcass, full width
    if kick:
        m.add_box((0.0, 0.12, 0.0), (1.0, 0.88, 0.10), "neutral")  # recessed plinth
    m.add_box((0.0, 0.0, 0.82), (1.0, 1.0, 0.92), CERAMIC)      # worktop, overhangs
    return m


def espresso_machine() -> Mesh:
    """The largest object on the counter, so it carries the most detail.

    Every part of it used to be plain METAL, which at 1.8 tiles wide made the
    centre of the focal zone a single featureless grey mass -- the biggest prop
    in the room and the one with the least to look at. The geometry barely
    changed; what changed is that the parts now sit at different steps of the
    neutral ramp, plus a warm drip tray and wood portafilter handles. Detail by
    value, not by polygon count, exactly as the material tone offsets are for.
    """
    m = Mesh()
    m.add_box((0.10, 0.15, 0.0), (1.90, 0.85, 0.46), METAL)
    m.add_box((0.10, 0.15, 0.40), (1.90, 0.85, 0.46), "neutral-2")   # shadow line
    m.add_box((0.20, 0.20, 0.46), (1.80, 0.80, 0.60), "neutral+1")   # lit top shell
    m.add_box((0.24, 0.20, 0.60), (1.76, 0.76, 0.635), "neutral+2")  # cup warmer
    for cx in (0.50, 0.90, 1.30):                                    # cups on top
        m.add_cylinder((cx, 0.46, 0.635), 0.075, 0.09, CERAMIC, 8)
    # Detail goes on the +y and +x faces, because those are the only two this
    # camera will ever see. The group heads were at y=0.28 inside a body that
    # spans y 0.15-0.85 -- fully enclosed, contributing not one pixel, which is
    # the most expensive kind of detail there is. `art_review.check_buried_detail`
    # now measures exactly this.
    m.add_box((0.30, 0.85, 0.10), (1.70, 0.91, 0.16), "wood-1")      # drip tray
    for gx in (0.55, 1.30):                                          # group heads
        m.add_cylinder((gx, 0.88, 0.30), 0.09, 0.16, "neutral-3", 10)
        m.add_box((gx - 0.045, 0.86, 0.255), (gx + 0.045, 1.02, 0.29), WOOD)
    m.add_box((0.42, 0.855, 0.50), (0.68, 0.88, 0.56), "neutral-3")  # gauge
    m.add_cylinder((1.93, 0.60, 0.20), 0.05, 0.30, "neutral-1", 8)   # steam wand
    return m


def grinder() -> Mesh:
    m = Mesh()
    m.add_box((0.28, 0.30, 0.0), (0.72, 0.70, 0.46), METAL)
    m.add_cylinder((0.50, 0.50, 0.46), 0.17, 0.34, WOOD, 12)    # hopper
    return m


def register() -> Mesh:
    m = Mesh()
    m.add_box((0.22, 0.25, 0.0), (0.78, 0.75, 0.26), METAL)
    m.add_box((0.30, 0.34, 0.26), (0.70, 0.44, 0.50), CERAMIC)  # screen bezel
    # Screen on the +y face of the bezel. At y 0.33-0.35 it sat against the
    # bezel's far side and never reached a pixel: a till with no display.
    m.add_box((0.33, 0.43, 0.30), (0.67, 0.455, 0.46), GLASS)   # screen face
    return m


def pastry_case() -> Mesh:
    m = Mesh()
    m.add_box((0.05, 0.10, 0.0), (1.95, 0.90, 0.34), WOOD)          # carcass
    m.add_box((0.10, 0.15, 0.34), (1.90, 0.85, 0.40), CERAMIC)      # shelf
    for px in (0.45, 0.95, 1.45):                                    # pastries
        m.add_cylinder((px, 0.50, 0.40), 0.15, 0.11, FABRIC, 10)
    # The top pane is the one glass surface a dimetric camera sees face-on, and
    # at GLASS ("sky+2") it was a 1.8 x 0.7 slab of saturated cyan -- the case
    # read as a lit swimming pool and outcompeted everything else on the counter
    # for attention. The constant's own rule says glass is nearly the value of
    # what is behind it with colour only at the edges; a horizontal pane is
    # where that rule matters most. So the pane takes the interior's tone and
    # the glass arrives as two specular streaks across it.
    m.add_box((0.10, 0.15, 0.66), (1.90, 0.85, 0.685), "cream+1")   # top pane
    for sx in (0.34, 1.12):
        m.add_box((sx, 0.20, 0.685), (sx + 0.42, 0.36, 0.6895), GLASS)  # highlight
    for (ax, ay, bx, by) in ((0.10, 0.15, 1.90, 0.19), (0.10, 0.81, 1.90, 0.85),
                             (0.10, 0.15, 0.14, 0.85), (1.86, 0.15, 1.90, 0.85)):
        m.add_box((ax, ay, 0.685), (bx, by, 0.72), GLASS_EDGE)      # rim only
    m.add_box((0.10, 0.15, 0.40), (0.14, 0.85, 0.66), GLASS)
    m.add_box((1.86, 0.15, 0.40), (1.90, 0.85, 0.66), GLASS)
    # Solid back, open front. The pane here used to be GLASS at y 0.15-0.17 --
    # the side AWAY from the camera, so it was 69 triangles of glass nobody
    # could see, backed by a view straight through to the wall. The camera-facing
    # side stays open on purpose: this renderer has no transparency, so a pane
    # across the front would replace the pastries with a flat blue rectangle.
    # Glass reads here the way it does on the top -- as rim and highlight only.
    m.add_box((0.14, 0.15, 0.40), (1.86, 0.19, 0.66), WOOD)         # back panel
    for mx in (0.68, 1.32):                                          # mullions
        m.add_box((mx, 0.83, 0.40), (mx + 0.035, 0.86, 0.66), GLASS_EDGE)
    return m


def _mix(seed: int) -> int:
    """Scramble a small integer into a usable LCG state.

    Seeding an LCG with `seed * k + c` and reading its top bits leaves nearby
    seeds correlated: the table generator gave seeds 1, 3 and 5 the same base
    style and 2 and 4 another, because the seeds in a room are consecutive
    integers and a single multiply does not separate them. This is an
    avalanche step, so one bit of seed changes about half the bits of state.
    """
    h = (seed * 2654435761 + 1013904223) & 0xFFFFFFFF
    h ^= h >> 16
    h = (h * 2246822519) & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 3266489917) & 0xFFFFFFFF
    return (h ^ (h >> 16)) & 0x7FFFFFFF


def strut(m: Mesh, a: tuple, b: tuple, r: float, mat: str) -> None:
    """A square-section beam between two points.

    `add_box` is axis-aligned, which is why every leg in this library has so far
    been vertical. A splayed or raked member is most of what separates one
    furniture silhouette from another, and silhouette is the only thing that
    survives the downsample -- the same finding the chair backs turned up.

    The cross-section stays axis-aligned in x/y even when the member leans. That
    is deliberate: a rotated square section lands on the pixel grid at an angle
    and shimmers between the eight azimuths, and at 27 px per unit a leg is two
    pixels wide, so there is no cross-section detail to lose anyway.
    """
    lo = [(a[0] + dx * r, a[1] + dy * r, a[2])
          for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    hi = [(b[0] + dx * r, b[1] + dy * r, b[2])
          for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    for i in range(4):
        j = (i + 1) % 4
        m.add_quad(lo[i], lo[j], hi[j], hi[i], mat)
    m.add_quad(lo[3], lo[2], lo[1], lo[0], mat)
    m.add_quad(hi[0], hi[1], hi[2], hi[3], mat)


# Table base styles, on the same argument as the chair backs: vary the
# silhouette, because at room scale that is the whole of what a viewer reads.
# Each takes the footprint the top occupies and the height to reach.
def _base_posts(m, f, x0, x1, y0, y1, h, r):
    """Four square legs, inset from the top's edge. The plain one."""
    for cx in (x0 + r * 2.2, x1 - r * 2.2):
        for cy in (y0 + r * 2.2, y1 - r * 2.2):
            m.add_box((cx - r, cy - r, 0.0), (cx + r, cy + r, h), f)


def _base_splay(m, f, x0, x1, y0, y1, h, r):
    """Four legs raked outward. Reads instantly and cannot be mistaken for a box."""
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            strut(m, (mx + sx * (x1 - x0) * 0.44, my + sy * (y1 - y0) * 0.44, 0.0),
                  (mx + sx * (x1 - x0) * 0.28, my + sy * (y1 - y0) * 0.28, h),
                  r * 1.35, f)


def _base_pedestal(m, f, x0, x1, y0, y1, h, r):
    """Column on a splayed foot. The cafe two-top."""
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    m.add_cylinder((mx, my, 0.0), r * 1.7, h, f, 12)
    m.add_cylinder((mx, my, 0.0), min(x1 - x0, y1 - y0) * 0.30, 0.055, f, 14)


def _base_trestle(m, f, x0, x1, y0, y1, h, r):
    """Two end frames joined by a spine. The long communal table."""
    r *= 1.25
    for cx in (x0 + r * 2.6, x1 - r * 2.6):
        for cy in (y0 + r * 2.2, y1 - r * 2.2):
            m.add_box((cx - r, cy - r, 0.0), (cx + r, cy + r, h), f)
        # The foot, which is the whole reason a trestle looks like a trestle.
        m.add_box((cx - r * 1.3, y0 + r, 0.0), (cx + r * 1.3, y1 - r, r * 1.1), f)
    # The stretcher runs down the long axis at shin height, where it is visible
    # under the top rather than hidden behind an apron.
    my = (y0 + y1) / 2
    m.add_box((x0 + r * 2.6, my - r * 0.8, h * 0.42),
              (x1 - r * 2.6, my + r * 0.8, h * 0.42 + r * 1.4), f)


BASE_STYLES = (_base_posts, _base_splay, _base_pedestal, _base_trestle)


def table(w: float = 1.0, d: float = 1.0, h: float = 0.58, top=WOOD,
          frame=WOOD, round_top: bool | None = None,
          seed: int | None = None) -> Mesh:
    """A table grown from a base style and a top, rather than a fixed mesh.

    The room seats fourteen people at three tables and every one of them was one
    of two meshes. `leafy_plant` and `chair` had already made the argument; the
    tables are the largest pieces of furniture in frame and were still coming out
    of a catalogue of two.

    What varies is the base -- posts, splayed, pedestal, trestle -- plus top
    shape, thickness and overhang. What does NOT vary is anything inside the
    outline, for the reason the chair backs record: interior detail is gone by
    the time the frame is downsampled, and the silhouette is not.

    `seed=None` keeps a fixed table, so callers that have not opted in and every
    sprite sheet already rendered stay exactly as they were.
    """
    st = None if seed is None else _mix(seed)

    def rnd():
        nonlocal st
        if st is None:
            return 0.5
        # `_mix` per draw, not an LCG step. Mixing only the seed left the
        # *stream* weak: the chair's second draw picks the back style, and over
        # forty consecutive seeds one of four styles came up 3 times against an
        # expected 10. A generator whose variety is this lopsided is barely a
        # generator.
        st = _mix(st)
        return st / 0x7FFFFFFF

    m = Mesh()
    thick = 0.085 + rnd() * 0.045
    over = 0.03 + rnd() * 0.05                 # how far the top oversails the base
    if round_top is None:
        # A round top belongs on a small square footprint; a long table is not
        # round in any cafe. Derived, so the two never disagree.
        round_top = abs(w - d) < 0.25 * max(w, d) and max(w, d) < 1.4
    style = (_base_pedestal if round_top and seed is None else
             _base_posts if seed is None else
             BASE_STYLES[int(rnd() * len(BASE_STYLES)) % len(BASE_STYLES)])
    if round_top and style is _base_trestle:
        # A trestle under a disc is a chair with two left legs.
        style = _base_pedestal
    # 0.085 read as tree trunks under a disc; 0.052 read as wire. Each base
    # style scales this itself, because a lone raked leg carries more load --
    # and looks like it should -- than one of four posts.
    leg_r = 0.066 + rnd() * 0.022
    # The base's footprint comes from the TOP's outline, not from the table's
    # bounding box. Under a round top the two are not the same: a base laid out
    # on the box put the splayed feet at 0.57 from the centre of a disc of
    # radius 0.50, so they stuck out past the edge they were meant to hold up.
    if round_top:
        # The largest square that fits inside the disc, less the overhang.
        half = (min(w, d) / 2 - over) * 0.7071
        bx0, bx1 = w / 2 - half, w / 2 + half
        by0, by1 = d / 2 - half, d / 2 + half
    else:
        bx0, bx1, by0, by1 = over, w - over, over, d - over
    style(m, frame, bx0, bx1, by0, by1, h, leg_r)
    if round_top:
        m.add_cylinder((w / 2, d / 2, h), min(w, d) / 2, thick, top, 20)
    else:
        m.add_box((0.0, 0.0, h), (w, d, h + thick), top)
    # Callers put cups on this. Varying the top thickness without telling anyone
    # where the top ended up would leave every piece of clutter in the room
    # floating or sunk by up to 4 cm, which `grounded` would then report as a
    # placement bug rather than as the generator's.
    m.top_z = h + thick
    return m


def table_round(top=WOOD, seed: int | None = None) -> Mesh:
    return table(1.0, 1.0, 0.58, top=top, round_top=True, seed=seed)


def table_4top(seed: int | None = None) -> Mesh:
    return table(2.0, 1.0, 0.58, round_top=False, seed=seed)


# Chair back styles.
#
# The first version of these varied the *infill* -- slat, ladder, spindle,
# cross. Rendered at the room's 27 px per world unit, the gap between the two
# stiles is about six pixels wide and every infill inside it came out as the
# same two-pixel smudge: eight chairs that were identical apart from colour, for
# four styles' worth of code. This is the same lesson the rig learned at 46 px,
# where a pose reads from limb direction and not from articulation.
#
# So the styles vary the SILHOUETTE instead, and each one draws its own stiles
# because height and overhang are most of the difference. Outline survives
# downsampling; interior detail does not.
def _back_low(m, f, sz, x0, x1, y0, y1):
    """Short square back, cafe-bentwood height."""
    top = sz + 0.34
    for sx in (x0, x1 - 0.15):
        m.add_box((sx, y0, sz), (sx + 0.15, y1, top), f)
    m.add_box((x0, y0 + 0.005, top - 0.13), (x1, y1, top), f + "+1")


def _back_tall(m, f, sz, x0, x1, y0, y1):
    """Tall and open -- two stiles and one rail, with air between them."""
    top = sz + 0.68
    for sx in (x0 + 0.02, x1 - 0.17):
        m.add_box((sx, y0, sz), (sx + 0.15, y1, top), f)
    m.add_box((x0, y0 + 0.005, top - 0.12), (x1, y1, top), f + "+1")
    m.add_box((x0 + 0.06, y0 + 0.02, sz + 0.16), (x1 - 0.06, y1 - 0.02, sz + 0.26),
              f + "-1")


def _back_shoulder(m, f, sz, x0, x1, y0, y1):
    """Top rail overhangs the stiles, so the outline reads as a T."""
    top = sz + 0.55
    for sx in (x0 + 0.07, x1 - 0.22):
        m.add_box((sx, y0, sz), (sx + 0.15, y1, top - 0.11), f)
    m.add_box((x0 - 0.04, y0 + 0.005, top - 0.15), (x1 + 0.04, y1, top), f + "+1")


def _back_solid(m, f, sz, x0, x1, y0, y1):
    """Filled panel, but only to two-thirds height so it is not a wall."""
    top = sz + 0.44
    m.add_box((x0, y0, sz), (x1, y1 - 0.02, top - 0.10), f + "-1")
    m.add_box((x0, y0 + 0.005, top - 0.12), (x1, y1, top), f + "+1")


BACK_STYLES = (_back_low, _back_tall, _back_shoulder, _back_solid)


def chair(cushion=None, frame=WOOD, seed: int | None = None) -> Mesh:
    """Back at -y, so a chair at rot=0 has its back away from a table to its +y.

    The back is an open frame rather than one filled panel. A solid full-height
    back is 16 x 13 px of unbroken wood at room scale and reads as a partition
    wall, which is what review actually flagged. The gaps are what make the
    silhouette say "chair".

    `frame` exists because 67% of the room measured as the wood ramp, and when
    every object shares one ramp, furniture stops separating from furniture. A
    painted chair costs nothing -- the ramps already exist -- and buys object
    separation that no amount of extra geometry would.

    `seed` picks a back silhouette and jitters leg thickness. Without it every
    one of the fourteen chairs in the reference room is the same mesh, and a cafe
    furnished from a single catalogue entry is the tell that nothing here grew.
    The styles are a dozen lines each and compose with every frame and cushion
    option rather than multiplying against them.

    `seed=None` keeps a fixed chair, so callers that have not opted in are
    unaffected and existing sprite sheets stay stable.
    """
    st = None if seed is None else _mix(seed)

    def rnd():
        nonlocal st
        if st is None:
            return 0.5
        # `_mix` per draw, not an LCG step. Mixing only the seed left the
        # *stream* weak: the chair's second draw picks the back style, and over
        # forty consecutive seeds one of four styles came up 3 times against an
        # expected 10. A generator whose variety is this lopsided is barely a
        # generator.
        st = _mix(st)
        return st / 0x7FFFFFFF

    m = Mesh()
    seat_z = 0.45                      # ~28% of character height; was 0.52
    leg_r = 0.090 + ((rnd() - 0.5) * 0.020 if seed is not None else 0.0)
    for cx, cy in ((0.28, 0.28), (0.72, 0.28), (0.28, 0.72), (0.72, 0.72)):
        m.add_box((cx - leg_r, cy - leg_r, 0),
                  (cx + leg_r, cy + leg_r, seat_z - 0.07), frame)
    m.add_box((0.18, 0.18, seat_z - 0.07), (0.82, 0.82, seat_z), frame)     # seat
    style = (_back_low if seed is None
             else BACK_STYLES[int(rnd() * len(BACK_STYLES)) % len(BACK_STYLES)])
    style(m, frame, seat_z, 0.19, 0.83, 0.19, 0.34)
    if cushion:
        m.add_box((0.21, 0.21, seat_z), (0.79, 0.79, seat_z + 0.06), cushion)
    return m


def stool() -> Mesh:
    m = Mesh()
    m.add_cylinder((0.5, 0.5, 0.62), 0.24, 0.08, FABRIC, 14)
    m.add_cylinder((0.5, 0.5, 0.0), 0.095, 0.62, METAL, 10)
    m.add_cylinder((0.5, 0.5, 0.0), 0.22, 0.03, METAL, 12)
    return m


def leafy_plant(height: float = 0.85, seed: int = 1, stems: int = 5,
                pot=FABRIC, leaf=PLANT) -> Mesh:
    """A plant grown from rules instead of placed by hand.

    The two plants this replaces were a sphere on a pot and five spheres in a
    hand-typed list of offsets. That is a shrub-shaped object rather than a
    plant, and it was the same shrub everywhere in the room, which is the
    opposite of what foliage is for -- greenery is where an interior is supposed
    to look least manufactured.

    Growth is the standard recursion, cut down to what survives at 27 px per
    world unit: stems radiate from the rim, each segment shorter than the last
    and drooping harder as it goes, with a leaf mass at every node. Three things
    are deliberate at this scale:

    * **Leaves carry the mass, stems only imply direction.** A 0.02-unit stem is
      half a pixel. Stems are drawn as short beads between nodes and would fail
      `check_member_thickness` on their own; the leaf clusters are what the
      silhouette is made of.
    * **Droop compounds.** Each segment keeps 55% of the previous rise and all of
      the outward lean, so the tips fall away from the centre. Straight radiating
      stems read as a starburst, which is the one shape that never occurs in a
      pot.
    * **Leaves flatten toward the top.** Squashing the upper clusters in z stops
      the plant reading as a stack of balls, which is exactly what the old
      five-sphere version looked like.

    `seed` makes each instance different, so ten scattered plants are ten plants.
    Declared `sym: none` in assets.yaml, which is honest -- this is asymmetric by
    construction and would cost eight renders as a sprite. In the room it costs
    one.
    """
    import math

    st = (seed * 2654435761 + 1013904223) & 0x7FFFFFFF

    def rnd():
        nonlocal st
        st = (st * 1103515245 + 12345) & 0x7FFFFFFF
        return (st >> 8) / (0x7FFFFFFF >> 8)

    m = Mesh()
    pot_h = height * 0.30
    m.add_prism((0.5, 0.5, 0.0), 0.20, 0.20, pot_h, pot, segments=8)
    m.add_prism((0.5, 0.5, pot_h * 0.62), 0.215, 0.215, pot_h * 0.16,
                pot + "+1", segments=8)                      # rim catches light
    m.add_prism((0.5, 0.5, pot_h - 0.015), 0.175, 0.175, 0.02, "wood-3",
                segments=8)                                  # soil

    for i in range(stems):
        ang = 2 * math.pi * (i / stems) + (rnd() - 0.5) * 0.9
        lean = 0.09 + 0.10 * rnd()
        rise = height * (0.26 + 0.10 * rnd())
        x, y, z = 0.5, 0.5, pot_h
        dx, dy = math.cos(ang) * lean, math.sin(ang) * lean
        for seg in range(2 + int(rnd() * 2.0)):
            nx, ny, nz = x + dx, y + dy, z + rise
            m.add_cylinder(((x + nx) / 2, (y + ny) / 2, z), 0.019,
                           max(0.02, nz - z), leaf + "-2", 5)
            # Flatter and a little smaller the higher it gets.
            t = min(1.0, (nz - pot_h) / max(1e-6, height * 0.75))
            r = (0.155 - 0.045 * t) * (0.85 + 0.3 * rnd())
            m.add_prism((nx, ny, nz - r * 0.45), r, r * (0.92 + 0.16 * rnd()),
                        r * (1.15 - 0.45 * t), leaf, segments=6)
            rise *= 0.55
            x, y, z = nx, ny, nz
    # A low rosette at soil level. Without it the canopy floats clear of the pot
    # and the plant reads as a bouquet dropped into it rather than as something
    # growing out of it.
    for i in range(3):
        ang = 2 * math.pi * (i / 3) + rnd() * 1.2
        r = 0.10 + 0.035 * rnd()
        m.add_prism((0.5 + math.cos(ang) * 0.17, 0.5 + math.sin(ang) * 0.17,
                     pot_h + 0.01), r, r * 0.9, r * 0.75, leaf + "-1", segments=6)
    return m


def plant_large(seed: int = 3) -> Mesh:
    return leafy_plant(height=1.05, seed=seed, stems=6)


def plant_small(seed: int = 7) -> Mesh:
    return leafy_plant(height=0.52, seed=seed, stems=4)


def bookshelf() -> Mesh:
    """Open at +y, which is the only side this camera can see into.

    It used to be a solid carcass box with the shelves and books modelled inside
    it -- 86% of its camera-facing triangles fully occluded, and on screen a
    plain wooden slab standing where a bookcase was supposed to be. All the
    detail existed; none of it was reachable. Building the carcass as a back,
    two sides and a top instead of one filled box is the entire fix.
    """
    m = Mesh()
    m.add_box((0.10, 0.55, 0.0), (0.90, 0.66, 1.45), WOOD)        # back panel
    for x0, x1 in ((0.10, 0.20), (0.80, 0.90)):                   # side panels
        m.add_box((x0, 0.55, 0.0), (x1, 0.92, 1.45), WOOD)
    m.add_box((0.10, 0.55, 1.36), (0.90, 0.92, 1.45), WOOD)       # top
    m.add_box((0.10, 0.55, 0.0), (0.90, 0.92, 0.10), WOOD)        # plinth
    for z in (0.34, 0.70, 1.06):
        m.add_box((0.20, 0.55, z), (0.80, 0.92, z + 0.05), CERAMIC)   # shelf
        m.add_box((0.23, 0.62, z + 0.05), (0.77, 0.90, z + 0.26), FABRIC)
    return m


def pendant_lamp(drop=0.55) -> Mesh:
    m = Mesh()
    m.add_cylinder((0.5, 0.5, 1.62 - drop), 0.015, drop, METAL, 6)
    m.add_cylinder((0.5, 0.5, 1.62 - drop - 0.22), 0.20, 0.22, CERAMIC, 14)
    # The lit underside. A lamp that casts a pool but is not itself bright
    # reads as a hole; this is the step of cream that says "this is the source".
    m.add_cylinder((0.5, 0.5, 1.62 - drop - 0.25), 0.185, 0.03, "cream+3", 14)
    return m


def cup_and_saucer() -> Mesh:
    m = Mesh()
    m.add_cylinder((0.5, 0.5, 0.0), 0.13, 0.02, CERAMIC, 12)
    m.add_cylinder((0.5, 0.5, 0.02), 0.08, 0.10, CERAMIC, 12)
    return m


def crate() -> Mesh:
    """Slatted, with the slats drawn as value rather than as geometry.

    This was one box. A single `add_box` was defensible while crates sat in a
    corner, and stopped being defensible when the generated dressing pass began
    scattering them through the room: 0.76 tiles square of unbroken wood at one
    ramp step is the most blockout-looking object that could be put on screen.

    Slats are flat quads a thousandth of a unit proud of each face, alternating
    one step either side of the carcass, with corner posts a step lighter. Only
    the +x and +y faces and the top get them, because those are the three this
    camera can see -- `check_buried_detail` would report the rest as buried, and
    it would be right.
    """
    m = Mesh()
    lo, hi, top = 0.12, 0.88, 0.52
    m.add_box((lo, lo, 0.0), (hi, hi, top), "wood-2")          # carcass, in shadow
    e = 0.0014
    for i, z in enumerate((0.03, 0.16, 0.29, 0.42)):
        band = "wood" if i % 2 == 0 else "wood+1"
        h = 0.095
        m.add_quad((lo, hi + e, z), (hi, hi + e, z),
                   (hi, hi + e, z + h), (lo, hi + e, z + h), band)     # +y face
        m.add_quad((hi + e, lo, z), (hi + e, hi, z),
                   (hi + e, hi, z + h), (hi + e, lo, z + h), band)     # +x face
    for a, b in ((lo, lo + 0.09), (hi - 0.09, hi)):                    # corner posts
        m.add_quad((a, hi + 2 * e, 0.0), (b, hi + 2 * e, 0.0),
                   (b, hi + 2 * e, top), (a, hi + 2 * e, top), "wood+1")
        m.add_quad((hi + 2 * e, a, 0.0), (hi + 2 * e, b, 0.0),
                   (hi + 2 * e, b, top), (hi + 2 * e, a, top), "wood+1")
    m.add_quad((lo + 0.06, lo + 0.06, top + e), (hi - 0.06, lo + 0.06, top + e),
               (hi - 0.06, hi - 0.06, top + e), (lo + 0.06, hi - 0.06, top + e),
               "wood")                                                 # lid panel
    return m


def menu_board() -> Mesh:
    """A framed chalkboard, with chalk.

    The panel used to be a bare METAL rectangle, and a blank grey slab above the
    counter does not read as a menu -- it reads as an unexplained hole in the
    wall, which is how it looked in every composite. What makes it legible is
    not more geometry but chalk: flat quads a hundredth of a unit off the panel
    face, four steps up the neutral ramp. Same principle as the material tone
    offsets everywhere else -- the detail is a value change, so it stays
    palette-exact and cannot dither.

    Row lengths are uneven on purpose. Four bars of equal width read as a
    barcode; uneven ones read as a list of items and prices.
    """
    m = Mesh()
    m.add_box((0.10, 0.0, 0.55), (0.90, 0.06, 1.30), WOOD)
    m.add_box((0.16, 0.06, 0.61), (0.84, 0.08, 1.24), "neutral-2")
    chalk = 0.081                       # just proud of the panel face
    m.add_quad((0.26, chalk, 1.13), (0.74, chalk, 1.13),
               (0.74, chalk, 1.175), (0.26, chalk, 1.175), "neutral+3")  # heading
    for z, x1 in ((1.02, 0.62), (0.92, 0.70), (0.82, 0.57), (0.72, 0.66)):
        m.add_quad((0.23, chalk, z), (x1, chalk, z),
                   (x1, chalk, z + 0.035), (0.23, chalk, z + 0.035), "neutral+2")
        m.add_quad((0.755, chalk, z), (0.80, chalk, z),          # the price column
                   (0.80, chalk, z + 0.035), (0.755, chalk, z + 0.035), "neutral+2")
    return m


def table_clutter(kind: str = "cafe") -> Mesh:
    """Tables with one cup read as showroom furniture. Occupied tables need
    stuff on them.

    Sized up from a first pass where 23% of the cluster's mass fell under the
    4 px member floor. Tabletop items are small by nature, but below about 4 px
    they stop being a cup and start being a speck, and a table of specks reads
    as dirt rather than as an occupied table.
    """
    m = Mesh()
    if kind == "cafe":
        m.add_cylinder((0.42, 0.46, 0.0), 0.115, 0.02, CERAMIC, 12)   # saucer
        m.add_cylinder((0.42, 0.46, 0.02), 0.075, 0.115, CERAMIC, 12)  # cup
        m.add_cylinder((0.64, 0.38, 0.0), 0.085, 0.12, CERAMIC, 10)    # second cup
        m.add_box((0.28, 0.60, 0.0), (0.52, 0.78, 0.07), FABRIC)       # napkin
        m.add_box((0.58, 0.60, 0.0), (0.74, 0.74, 0.13), WOOD)         # caddy
    elif kind == "work":
        m.add_box((0.26, 0.34, 0.0), (0.66, 0.62, 0.03), METAL)        # laptop base
        m.add_box((0.26, 0.60, 0.03), (0.66, 0.64, 0.30), GLASS)       # screen
        m.add_cylinder((0.76, 0.40, 0.0), 0.095, 0.15, CERAMIC, 10)
    elif kind == "books":
        m.add_box((0.28, 0.36, 0.0), (0.62, 0.64, 0.06), FABRIC)
        m.add_box((0.30, 0.38, 0.06), (0.60, 0.62, 0.11), CERAMIC)
        m.add_cylinder((0.74, 0.46, 0.0), 0.095, 0.15, CERAMIC, 10)
    elif kind == "counter":
        for cx in (0.22, 0.46, 0.70):
            m.add_cylinder((cx, 0.5, 0.0), 0.085, 0.13, CERAMIC, 10)
    return m


# --- dressing ----------------------------------------------------------------
#
# Room occupancy measured 58% with an 8-tile bare rectangle, and the cause was
# not placement -- it was that every mesh in the library was already on the
# floor. A room reads as under-dressed long before it reads as under-lit, so
# these exist to give layout something to spend.
#
# All members are kept at or above 0.15 units. At the room's 27 px/unit that is
# a 4 px floor, below which a member stops reading as a shape and starts reading
# as a stray line.

def bench(length: float = 2.0, cushion=FABRIC) -> Mesh:
    """Banquette seating: reads as one mass, which is what a wall run wants."""
    m = Mesh()
    m.add_box((0.08, 0.14, 0.0), (length - 0.08, 0.82, 0.38), WOOD)
    m.add_box((0.08, 0.16, 0.38), (length - 0.08, 0.80, 0.46), cushion)
    m.add_box((0.08, 0.14, 0.46), (length - 0.08, 0.30, 1.02), WOOD)      # back
    m.add_box((0.12, 0.28, 0.50), (length - 0.12, 0.34, 0.94), cushion)
    return m


def armchair(cushion=FABRIC) -> Mesh:
    m = Mesh()
    m.add_box((0.10, 0.10, 0.0), (0.90, 0.90, 0.34), WOOD)
    m.add_box((0.16, 0.16, 0.34), (0.84, 0.84, 0.48), cushion)            # seat
    m.add_box((0.10, 0.10, 0.34), (0.90, 0.28, 0.92), WOOD)               # back
    m.add_box((0.14, 0.26, 0.40), (0.86, 0.32, 0.86), cushion)
    for ax in (0.10, 0.72):                                                # arms
        m.add_box((ax, 0.28, 0.34), (ax + 0.18, 0.88, 0.60), WOOD)
    return m


def side_table() -> Mesh:
    m = Mesh()
    m.add_cylinder((0.5, 0.5, 0.0), 0.10, 0.44, WOOD, 10)
    m.add_cylinder((0.5, 0.5, 0.44), 0.30, 0.09, WOOD, 16)
    m.add_cylinder((0.5, 0.5, 0.0), 0.22, 0.05, WOOD, 12)
    return m


def coat_rack(coat=None) -> Mesh:
    m = Mesh()
    m.add_cylinder((0.5, 0.5, 0.0), 0.18, 0.07, WOOD, 12)                 # base
    m.add_cylinder((0.5, 0.5, 0.07), 0.10, 1.42, WOOD, 8)
    for dx, dy in ((0.26, 0.0), (-0.26, 0.0), (0.0, 0.26), (0.0, -0.26)):
        m.add_box((0.5 + min(0, dx) - 0.085, 0.5 + min(0, dy) - 0.085, 1.28),
                  (0.5 + max(0, dx) + 0.085, 0.5 + max(0, dy) + 0.085, 1.40), WOOD)
    if coat:
        m.add_box((0.24, 0.34, 0.62), (0.52, 0.66, 1.30), coat)
    return m


def sandwich_board() -> Mesh:
    """A-frame chalkboard. The lean is the whole silhouette, so it is generous."""
    m = Mesh()
    # Solid panels, not quads. A zero-thickness plane is right for a floor
    # overlay and wrong for anything standing up: seen near edge-on it collapses
    # to a 1 px line, which is how this shipped at 3 px and read as a stray mark.
    for y0, y1 in ((0.16, 0.30), (0.70, 0.84)):
        m.add_box((0.12, y0, 0.0), (0.88, y1, 0.90), WOOD)
    m.add_box((0.17, 0.28, 0.16), (0.83, 0.34, 0.78), "neutral-2")        # slate
    m.add_box((0.17, 0.66, 0.16), (0.83, 0.72, 0.78), "neutral-2")
    m.add_box((0.12, 0.28, 0.86), (0.88, 0.72, 0.94), WOOD)               # hinge
    return m


def wall_shelf(length: float = 2.0, along: str = "x", rows=(0.34,)) -> Mesh:
    """Shelving on the far wall, where the eye lands behind the counter.

    Rows are a parameter because the wall is only 1.6 tall and the counter top
    is at 0.92, leaving 0.68 of usable wall. A two-row shelf overshot it by 0.07
    and the jars floated above the wall line -- geometry that is fine in
    isolation and wrong only against its host, which is the recurring shape of
    every placement bug in this project.
    """
    m = Mesh()
    for z in rows:
        if along == "x":
            m.add_box((0.06, 0.0, z), (length - 0.06, 0.30, z + 0.07), WOOD)
            n = int((length - 0.3) / 0.34)
            for i in range(n):
                x = 0.22 + i * 0.34
                m.add_cylinder((x, 0.15, z + 0.07), 0.10, 0.20,
                               (CERAMIC, FABRIC, PLANT)[i % 3], 10)
        else:
            m.add_box((0.0, 0.06, z), (0.30, length - 0.06, z + 0.07), WOOD)
            n = int((length - 0.3) / 0.34)
            for i in range(n):
                y = 0.22 + i * 0.34
                m.add_cylinder((0.15, y, z + 0.07), 0.10, 0.20,
                               (CERAMIC, FABRIC, PLANT)[i % 3], 10)
    return m


def wall_sign() -> Mesh:
    """Mounted above the service counter. This is a focal device, not
    decoration -- it is the one bright, high-contrast object over the
    interaction zone, which is how the composition tells the player where to
    look.

    Wall-mounted rather than ceiling-hung: an isometric room draws no ceiling,
    so a hanging sign's rods terminate in mid-air.
    """
    m = Mesh()
    z0, z1 = 1.02, 1.46
    m.add_box((0.06, 0.12, z0), (0.94, 0.20, z1), WOOD)                  # board
    m.add_box((0.12, 0.20, z0 + 0.05), (0.88, 0.23, z1 - 0.05), "cream+2")
    for sx in (0.10, 0.86):                                              # brackets
        m.add_box((sx, 0.12, z1), (sx + 0.06, 0.20, z1 + 0.08), "wood-1")
    return m


def cake_stand() -> Mesh:
    m = Mesh()
    m.add_cylinder((0.5, 0.5, 0.0), 0.09, 0.14, CERAMIC, 10)
    m.add_cylinder((0.5, 0.5, 0.14), 0.26, 0.05, CERAMIC, 14)
    m.add_cylinder((0.5, 0.5, 0.19), 0.20, 0.16, FABRIC, 12)              # cake
    m.add_cylinder((0.5, 0.5, 0.35), 0.21, 0.03, "cream+2", 14)           # icing
    return m


def basket(fill=FABRIC) -> Mesh:
    m = Mesh()
    m.add_cylinder((0.5, 0.5, 0.0), 0.28, 0.30, WOOD, 12)
    m.add_cylinder((0.5, 0.5, 0.30), 0.24, 0.08, fill, 12)
    return m


def trash_bin() -> Mesh:
    m = Mesh()
    m.add_cylinder((0.5, 0.5, 0.0), 0.24, 0.56, "neutral-1", 12)
    m.add_cylinder((0.5, 0.5, 0.56), 0.26, 0.06, METAL, 12)
    return m


def flower_vase() -> Mesh:
    m = Mesh()
    m.add_cylinder((0.5, 0.5, 0.0), 0.09, 0.22, CERAMIC, 10)
    for dx, dy, dz, r in ((0.0, 0.0, 0.30, 0.10), (0.07, 0.04, 0.38, 0.08),
                          (-0.06, 0.05, 0.36, 0.08)):
        m.add_sphere((0.5 + dx, 0.5 + dy, dz), r, "rose+1", 8, 6)
    return m
