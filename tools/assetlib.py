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

def floor(w: int, d: int, tone_a=WOOD, tone_b=CERAMIC, checker=False) -> Mesh:
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
    board, tones = 1.0, ("", "", "-1", "", "")

    def flat(y0, y1, z, mat):
        """Zero-thickness overlay, not a thin box.

        A box 0.0018 tall still has four side faces, and their normals point
        sideways, so they shade to the BOTTOM of the ramp. Subpixel or not, they
        win the depth test along the entire run: measured, the seams put ramp
        step 0 across 7.6% of open floor and drew a near-black grid. A quad has
        no sides, so the seam can only ever be the one step it asks for.
        """
        m.add_quad((0, y0, z), (w, y0, z), (w, y1, z), (0, y1, z), mat)

    for i in range(int(d / board)):
        y0, y1 = i * board, min(d, (i + 1) * board)
        t = tones[i % len(tones)]
        if t:
            flat(y0, y1 - 0.03, 0.0012, tone_a + t)
        flat(y1 - 0.03, y1, 0.0018, tone_a + "-1")                       # seam
    return m


def rug(w: float, d: float, mat=FABRIC) -> Mesh:
    """A rug is the cheapest way to give a seating cluster its own ground and to
    put a second hue into a floor that is otherwise all one material."""
    m = Mesh()
    m.add_box((0, 0, 0.001), (w, d, 0.012), mat + "-2")
    m.add_box((0.18, 0.18, 0.012), (w - 0.18, d - 0.18, 0.020), mat + "-1")
    return m


def wall_run(start, along: str, length: int, height=1.6,
             openings: tuple = ()) -> Mesh:
    """A wall along +x or +y, with tile indices left open for doors/windows."""
    m = Mesh()
    x0, y0 = start
    t = 0.12
    for i in range(length):
        if i in openings:
            # A bare aperture reads as a hole punched in a wall. Glass needs a
            # frame, a bright pane, and mullions to catch the light.
            a, b = 0.38, 1.22                       # sill height, head height
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
    m = Mesh()
    m.add_box((0.10, 0.15, 0.0), (1.90, 0.85, 0.46), METAL)
    m.add_box((0.20, 0.20, 0.46), (1.80, 0.80, 0.60), METAL)
    for gx in (0.55, 1.30):                                     # group heads
        m.add_cylinder((gx, 0.28, 0.30), 0.09, 0.16, METAL, 10)
    m.add_cylinder((1.75, 0.50, 0.20), 0.05, 0.30, METAL, 8)    # steam wand
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
    m.add_box((0.33, 0.33, 0.30), (0.67, 0.35, 0.46), GLASS)    # screen face
    return m


def pastry_case() -> Mesh:
    m = Mesh()
    m.add_box((0.05, 0.10, 0.0), (1.95, 0.90, 0.34), WOOD)          # carcass
    m.add_box((0.10, 0.15, 0.34), (1.90, 0.85, 0.40), CERAMIC)      # shelf
    for px in (0.45, 0.95, 1.45):                                    # pastries
        m.add_cylinder((px, 0.50, 0.40), 0.15, 0.11, FABRIC, 10)
    m.add_box((0.10, 0.15, 0.66), (1.90, 0.85, 0.685), GLASS)       # top pane
    for (ax, ay, bx, by) in ((0.10, 0.15, 1.90, 0.19), (0.10, 0.81, 1.90, 0.85),
                             (0.10, 0.15, 0.14, 0.85), (1.86, 0.15, 1.90, 0.85)):
        m.add_box((ax, ay, 0.685), (bx, by, 0.72), GLASS_EDGE)      # rim only
    m.add_box((0.10, 0.15, 0.40), (0.14, 0.85, 0.66), GLASS)
    m.add_box((1.86, 0.15, 0.40), (1.90, 0.85, 0.66), GLASS)
    m.add_box((0.14, 0.15, 0.40), (1.86, 0.17, 0.66), GLASS)        # front pane
    for mx in (0.68, 1.32):                                          # mullions
        m.add_box((mx, 0.15, 0.40), (mx + 0.035, 0.18, 0.66), GLASS_EDGE)
    return m


def table_round(top=WOOD) -> Mesh:
    m = Mesh()
    m.add_cylinder((0.5, 0.5, 0.0), 0.13, 0.58, WOOD, 12)       # thicker column
    m.add_cylinder((0.5, 0.5, 0.58), 0.44, 0.11, top, 20)       # thicker top
    m.add_cylinder((0.5, 0.5, 0.0), 0.30, 0.06, WOOD, 14)       # base
    return m


def table_4top() -> Mesh:
    m = Mesh()
    m.add_box((0.05, 0.05, 0.58), (1.95, 0.95, 0.70), WOOD)
    for cx, cy in ((0.22, 0.18), (1.78, 0.18), (0.22, 0.82), (1.78, 0.82)):
        m.add_box((cx - 0.105, cy - 0.105, 0), (cx + 0.105, cy + 0.105, 0.58), WOOD)
    return m


def chair(cushion=None, frame=WOOD) -> Mesh:
    """Back at -y, so a chair at rot=0 has its back away from a table to its +y.

    The back is an open frame -- two stiles, a top rail, a mid slat -- rather
    than one filled panel. A solid back is 16 x 13 px of unbroken wood at room
    scale and reads as a partition wall, which is what review actually flagged.
    The gaps are what make the silhouette say "chair".

    `frame` exists because 67% of the room measured as the wood ramp, and when
    every object shares one ramp, furniture stops separating from furniture. A
    painted chair costs nothing -- the ramps already exist -- and buys object
    separation that no amount of extra geometry would.
    """
    m = Mesh()
    seat_z = 0.45                      # ~28% of character height; was 0.52
    for cx, cy in ((0.28, 0.28), (0.72, 0.28), (0.28, 0.72), (0.72, 0.72)):
        m.add_box((cx - 0.090, cy - 0.090, 0), (cx + 0.090, cy + 0.090, seat_z - 0.07),
                  frame)
    m.add_box((0.18, 0.18, seat_z - 0.07), (0.82, 0.82, seat_z), frame)     # seat
    for sx in (0.20, 0.68):                                                 # stiles
        m.add_box((sx - 0.01, 0.19, seat_z), (sx + 0.15, 0.34, 1.02), frame)
    m.add_box((0.19, 0.19, 0.86), (0.83, 0.34, 1.02), frame + "+1")         # top rail
    m.add_box((0.24, 0.20, 0.60), (0.78, 0.33, 0.75), frame + "-1")         # mid slat
    if cushion:
        m.add_box((0.21, 0.21, seat_z), (0.79, 0.79, seat_z + 0.06), cushion)
    return m


def stool() -> Mesh:
    m = Mesh()
    m.add_cylinder((0.5, 0.5, 0.62), 0.24, 0.08, FABRIC, 14)
    m.add_cylinder((0.5, 0.5, 0.0), 0.095, 0.62, METAL, 10)
    m.add_cylinder((0.5, 0.5, 0.0), 0.22, 0.03, METAL, 12)
    return m


def plant_large() -> Mesh:
    m = Mesh()
    m.add_cylinder((0.5, 0.5, 0.0), 0.24, 0.30, FABRIC, 12)     # terracotta pot
    for i, (dx, dy, dz, r) in enumerate((
            (0.0, 0.0, 0.34, 0.26), (0.18, 0.10, 0.58, 0.21),
            (-0.16, 0.12, 0.62, 0.19), (0.05, -0.16, 0.78, 0.17),
            (-0.06, -0.02, 0.94, 0.14))):
        m.add_sphere((0.5 + dx, 0.5 + dy, dz), r, PLANT, 10, 7)
    return m


def plant_small() -> Mesh:
    m = Mesh()
    m.add_cylinder((0.5, 0.5, 0.0), 0.13, 0.16, FABRIC, 10)
    m.add_sphere((0.5, 0.5, 0.26), 0.16, PLANT, 10, 7)
    return m


def bookshelf() -> Mesh:
    m = Mesh()
    m.add_box((0.10, 0.55, 0.0), (0.90, 0.92, 1.45), WOOD)
    for z in (0.34, 0.70, 1.06):
        m.add_box((0.14, 0.56, z), (0.86, 0.90, z + 0.05), CERAMIC)
        m.add_box((0.20, 0.60, z + 0.05), (0.74, 0.86, z + 0.26), FABRIC)
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
    m = Mesh()
    m.add_box((0.12, 0.12, 0.0), (0.88, 0.88, 0.52), WOOD)
    return m


def menu_board() -> Mesh:
    m = Mesh()
    m.add_box((0.10, 0.0, 0.55), (0.90, 0.06, 1.30), WOOD)
    m.add_box((0.16, 0.06, 0.61), (0.84, 0.08, 1.24), METAL)
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
