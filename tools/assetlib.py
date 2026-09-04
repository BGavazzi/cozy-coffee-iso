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
    # Same field `ingest.fit` records losing in transit: a reconstructor that
    # copies three of Mesh's four fields drops vertex colours silently. Empty
    # for everything in this file, which is exactly why it would go unnoticed
    # until a generated mesh came through here.
    out.vcolors = list(m.vcolors)
    return out


def merge(*meshes: Mesh) -> Mesh:
    # `vcolors` is parallel to `verts`, so it can only be concatenated when
    # EVERY input carries it -- one mesh without colours would shift every
    # later mesh's colours onto the wrong vertices, which is worse than not
    # carrying them at all. All-or-nothing, decided before the loop.
    keep = all(len(m.vcolors) == len(m.verts) for m in meshes)
    out = Mesh()
    for m in meshes:
        off = len(out.verts)
        out.verts += m.verts
        if keep:
            out.vcolors += m.vcolors
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

# Counter front treatments.
#
# Each takes `put(u0, u1, v0, v1, material)`, where u runs along the face and v
# up it. They do not know which face they are drawing on, because the service
# run tiles along x and the window bar tiles along y -- so the bar's front is
# its +x face, and detail put on +y would be sandwiched between two modules and
# never seen. `counter` supplies the mapping.
def _front_plain(put, rnd):
    """A framed panel. The default, and the one a run can carry six of."""
    put(0.0, 1.0, 0.0, 1.0, "wood-2")


def _front_drawers(put, rnd):
    """Two drawer fronts with a reveal between them."""
    mid = 0.42 + rnd() * 0.14
    for a, b in ((0.0, mid - 0.02), (mid + 0.02, 1.0)):
        put(0.0, 1.0, a, b, "wood-2")
        # A pull, drawn as one lighter band. At 27 px a knob is a pixel and a
        # handle is a line, so it may as well be the line.
        h = (a + b) / 2
        put(0.34, 0.66, h - 0.035, h + 0.035, "wood+1")


def _front_shelf(put, rnd):
    """An open recess: the darkest module, and the one that breaks a long run."""
    put(0.0, 1.0, 0.0, 1.0, "wood-2")
    put(0.10, 0.90, 0.13, 0.88, "wood-4")
    put(0.10, 0.90, 0.50, 0.55, "wood")


def _front_beaded(put, rnd):
    """Vertical beadboard. Five strips, so each clears two pixels at room scale."""
    put(0.0, 1.0, 0.0, 1.0, "wood-1")
    for k in (0, 2, 4):
        put(k / 5.0, (k + 1) / 5.0 - 0.014, 0.0, 1.0, "wood-3")


FRONT_STYLES = (_front_plain, _front_drawers, _front_shelf, _front_beaded,
                _front_drawers, _front_plain)


def counter(kick=True, seed: int | None = None, front: str = "y",
            h: float = 0.92) -> Mesh:
    """Modular: the body spans the FULL tile so a run tiles seamlessly.
    Insetting it left a seam between every adjacent module.

    The room's service run is six of these and the window bar three more, so
    nine identical boxes make the single largest mass in frame -- and the front
    was one flat face at one ramp step, which is the most blockout-looking thing
    the room can show at that size.

    `seed` picks a front treatment. All of them are drawn as value, never as
    geometry: the modules have to keep tiling flush, and anything modelled proud
    of the front would be the first thing a customer walks into. `FRONT_STYLES`
    lists plain twice, because a run with four distinct fronts in six modules
    reads as a showroom rather than as a fitted counter.

    `front` is which face the customer sees, and it is not always +y. The
    service run tiles along x so its front is +y; the window bar tiles along y,
    so its +y face is a joint between two modules and its front is +x. Detail on
    the wrong one is sealed inside the run.

    `h` raises the whole unit. A back bar built at the service counter's own
    0.92 is HALF HIDDEN behind it -- `screen_occlusion` measured 52-55% on
    every tile of every island and peninsula -- because two equal boxes 1.1
    apart in depth stack to one silhouette in this projection. Real back bars
    are taller than the counter in front of them for exactly that reason. The
    default is unchanged, so every existing counter is byte-identical.
    """
    m = Mesh()
    # Without a plinth the carcass must reach the floor itself. It did not, so
    # every kick=False counter -- the whole window bar run -- hovered 0.10 above
    # the ground. Invisible at a glance and caught by Layout.grounded().
    base = 0.10 if kick else 0.0
    # Rounded because 0.92 - 0.10 is 0.8200000000000001 and the literal it
    # replaces was 0.82. Every counter in the library changed hash on a
    # parameter whose default was supposed to change nothing.
    top = round(h - 0.10, 10)                                   # worktop underside
    m.add_box((0.0, 0.06, base), (1.0, 0.94, top), WOOD)        # carcass, full width
    if kick:
        m.add_box((0.0, 0.12, 0.0), (1.0, 0.88, 0.10), "neutral")  # recessed plinth
    m.add_box((0.0, 0.0, top), (1.0, 1.0, h), CERAMIC)          # worktop, overhangs
    if seed is None:
        return m

    st = _mix(seed)

    def rnd():
        nonlocal st
        st = _mix(st)
        return st / 0x7FFFFFFF

    # Inset from the module edges so two neighbours never share a reveal, which
    # would read as one four-tile cabinet rather than as two.
    lo, hi = 0.035, 0.965
    z0, z1 = base + 0.03, round(top - 0.03, 10)
    face, n = (0.9412, (0.0, 1.0, 0.0)) if front == "y" else (0.9412, (1.0, 0.0, 0.0))

    def put(u0, u1, v0, v1, mat):
        a, b = lo + (hi - lo) * u0, lo + (hi - lo) * u1
        c, d = z0 + (z1 - z0) * v0, z0 + (z1 - z0) * v1
        if front == "y":
            m.add_quad((a, face, c), (b, face, c), (b, face, d), (a, face, d),
                       mat, facing=n)
        else:
            m.add_quad((face, a, c), (face, b, c), (face, b, d), (face, a, d),
                       mat, facing=n)

    FRONT_STYLES[int(rnd() * len(FRONT_STYLES)) % len(FRONT_STYLES)](put, rnd)
    return m


def espresso_machine(seed: int | None = None) -> Mesh:
    """The largest object on the counter, so it carries the most detail.

    Every part of it used to be plain METAL, which at 1.8 tiles wide made the
    centre of the focal zone a single featureless grey mass -- the biggest prop
    in the room and the one with the least to look at. The geometry barely
    changed; what changed is that the parts now sit at different steps of the
    neutral ramp, plus a warm drip tray and wood portafilter handles. Detail by
    value, not by polygon count, exactly as the material tone offsets are for.

    Detail goes on the +y and +x faces, because those are the only two this
    camera will ever see. The group heads were at y=0.28 inside a body that
    spans y 0.15-0.85 -- fully enclosed, contributing not one pixel, which is
    the most expensive kind of detail there is.

    `seed` varies the group count, the top shell and how many cups are warming
    on it. The width is deliberately NOT varied: the machine is fitted to a
    counter run whose modules are one tile each, and a generator free to resize
    a built-in is a generator that will eventually hang it off the end.
    """
    st = None if seed is None else _mix(seed)

    def rnd():
        nonlocal st
        st = _mix(st)
        return st / 0x7FFFFFFF

    m = Mesh()
    # Shell height, because the width is fixed and the height is therefore the
    # only dimension left that reaches the outline. Two of eight seeds rendered
    # PIXEL-IDENTICAL machines while the generator's mean spread read 33%: the
    # group count and cup count are all interior, and a machine with no back
    # panel had nothing else to distinguish it.
    lift = 0.0 if seed is None else (rnd() - 0.5) * 0.13
    m.add_box((0.10, 0.15, 0.0), (1.90, 0.85, 0.46 + lift), METAL)
    m.add_box((0.10, 0.15, 0.40 + lift), (1.90, 0.85, 0.46 + lift),
              "neutral-2")                                           # shadow line
    m.add_box((0.20, 0.20, 0.46 + lift), (1.80, 0.80, 0.60 + lift),
              "neutral+1")                                           # lit top shell
    m.add_box((0.24, 0.20, 0.60 + lift), (1.76, 0.76, 0.635 + lift),
              "neutral+2")                                           # cup warmer
    if seed is None:
        cups, groups = (0.50, 0.90, 1.30), (0.55, 1.30)
    else:
        # A two-group machine is a cafe; a one-group is a kiosk and a
        # three-group is a busy morning. The cup count follows the groups,
        # because a machine that pulls more shots warms more cups -- variation
        # that agrees with itself reads as a different shop rather than as
        # noise.
        n = (1, 2, 2, 3)[int(rnd() * 4) % 4]
        span = 1.30
        groups = tuple(0.35 + span * (i + 0.5) / n for i in range(n))
        k = n + int(rnd() * 2)
        cups = tuple(0.40 + 1.00 * (i + 0.5) / k for i in range(k))
        if rnd() < 0.45:
            # A raised back panel. The one part of the outline that is free to
            # grow, since it sits against the wall behind the counter.
            m.add_box((0.30, 0.22, 0.635 + lift),
                      (1.70, 0.62, 0.635 + lift + 0.10 + rnd() * 0.10),
                      "neutral")
    for cx in cups:
        m.add_cylinder((cx, 0.46, 0.635 + lift), 0.075, 0.09, CERAMIC, 8)
    m.add_box((0.30, 0.85, 0.10), (1.70, 0.91, 0.16), "wood-1")      # drip tray
    for gx in groups:
        m.add_cylinder((gx, 0.88, 0.30), 0.09, 0.16, "neutral-3", 10)
        m.add_box((gx - 0.045, 0.86, 0.255), (gx + 0.045, 1.02, 0.29), WOOD)
    m.add_box((0.42, 0.855, 0.50 + lift), (0.68, 0.88, 0.56 + lift),
              "neutral-3")                                           # gauge
    m.add_cylinder((1.93, 0.60, 0.20), 0.05, 0.30 + lift, "neutral-1", 8)  # wand
    if seed is not None and rnd() < 0.5:
        # Two wands, one each side. Both stand outside the body, so this is one
        # of the few parts of this machine that is outline rather than infill.
        m.add_cylinder((0.07, 0.60, 0.20), 0.05, 0.30 + lift, "neutral-1", 8)
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


def pastry_case(seed: int | None = None) -> Mesh:
    """`seed` varies the carcass height, the number of shelves and what is on
    them. The footprint stays 2.0 x 0.8 for the same reason the espresso
    machine keeps its width: this is a fitted piece."""
    st = None if seed is None else _mix(seed)

    def rnd():
        nonlocal st
        st = _mix(st)
        return st / 0x7FFFFFFF

    m = Mesh()
    carcass = 0.34 if seed is None else 0.28 + rnd() * 0.14
    m.add_box((0.05, 0.10, 0.0), (1.95, 0.90, carcass), WOOD)       # carcass
    m.add_box((0.10, 0.15, carcass), (1.90, 0.85, carcass + 0.06), CERAMIC)
    top = carcass + 0.32 if seed is None else carcass + 0.26 + rnd() * 0.14
    tiers = [carcass + 0.06]
    if seed is not None and rnd() < 0.5 and top - carcass > 0.34:
        # A second tier. Two shelves of pastry behind glass is the shape a
        # display case has when the shop is doing well, and it is the only
        # change here that reaches the interior rather than the outline --
        # which is allowed, because a glass case is the one prop whose interior
        # is the point.
        mid = carcass + 0.06 + (top - carcass - 0.12) * 0.5
        m.add_box((0.12, 0.17, mid), (1.88, 0.83, mid + 0.025), "cream+1")
        tiers.append(mid + 0.025)
    for z in tiers:
        if seed is None:
            xs, r = (0.45, 0.95, 1.45), 0.15
        else:
            n = 2 + int(rnd() * 3)
            xs = tuple(0.30 + 1.40 * (i + 0.5) / n for i in range(n))
            r = min(0.15, 0.62 / n)
        for px in xs:
            m.add_cylinder((px, 0.50, z), r, 0.11, FABRIC, 10)
    # The top pane is the one glass surface a dimetric camera sees face-on, and
    # at GLASS ("sky+2") it was a 1.8 x 0.7 slab of saturated cyan -- the case
    # read as a lit swimming pool and outcompeted everything else on the counter
    # for attention. The constant's own rule says glass is nearly the value of
    # what is behind it with colour only at the edges; a horizontal pane is
    # where that rule matters most. So the pane takes the interior's tone and
    # the glass arrives as two specular streaks across it.
    m.add_box((0.10, 0.15, top), (1.90, 0.85, top + 0.025), "cream+1")
    for sx in (0.34, 1.12):
        m.add_box((sx, 0.20, top + 0.025), (sx + 0.42, 0.36, top + 0.0295), GLASS)
    for (ax, ay, bx, by) in ((0.10, 0.15, 1.90, 0.19), (0.10, 0.81, 1.90, 0.85),
                             (0.10, 0.15, 0.14, 0.85), (1.86, 0.15, 1.90, 0.85)):
        m.add_box((ax, ay, top + 0.025), (bx, by, top + 0.06), GLASS_EDGE)
    m.add_box((0.10, 0.15, carcass + 0.06), (0.14, 0.85, top), GLASS)
    m.add_box((1.86, 0.15, carcass + 0.06), (1.90, 0.85, top), GLASS)
    # Solid back, open front. The pane here used to be GLASS at y 0.15-0.17 --
    # the side AWAY from the camera, so it was 69 triangles of glass nobody
    # could see, backed by a view straight through to the wall. The camera-facing
    # side stays open on purpose: this renderer has no transparency, so a pane
    # across the front would replace the pastries with a flat blue rectangle.
    # Glass reads here the way it does on the top -- as rim and highlight only.
    m.add_box((0.14, 0.15, carcass + 0.06), (1.86, 0.19, top), WOOD)  # back panel
    for mx in (0.68, 1.32):                                          # mullions
        m.add_box((mx, 0.83, carcass + 0.06), (mx + 0.035, 0.86, top), GLASS_EDGE)
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


def _base_tripod(m, f, x0, x1, y0, y1, h, r):
    """Three raked legs to a small hub. The other round-table base.

    Round tops used to send the trestle style to the pedestal, which meant a
    disc had three bases with one of them drawn twice, and `table_round`'s
    closest pair over eight seeds measured 2.9%. Collapsing a style onto
    another style is how a generator loses range without losing a branch --
    the code still has four cases and the output has three.
    """
    import math as _m
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    reach = min(x1 - x0, y1 - y0) * 0.44
    m.add_cylinder((mx, my, h - 0.10), r * 1.3, 0.10, f, 10)
    for i in range(3):
        a = _m.radians(90 + i * 120)
        fx, fy = mx + reach * _m.cos(a), my + reach * _m.sin(a)
        # Two segments, because a rake drawn as one box is a vertical box.
        m.add_box((min(fx, mx) - r, min(fy, my) - r, 0.0),
                  (min(fx, mx) + r * 0.2 + abs(fx - mx) * 0.5,
                   min(fy, my) + r * 0.2 + abs(fy - my) * 0.5, r * 1.2), f)
        m.add_box((mx - r * 0.9, my - r * 0.9, r * 0.9),
                  (mx + r * 0.9, my + r * 0.9, h - 0.09), f)
        m.add_box((min(fx, mx + r) - r * 0.8, min(fy, my + r) - r * 0.8, 0.0),
                  (max(fx, mx - r) + r * 0.8, max(fy, my - r) + r * 0.8,
                   r * 0.95), f)


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
    # Height, which is the biggest silhouette lever a table has and was the one
    # it did not pull. Thickness varies by 0.045 and overhang by 0.05 -- one and
    # two pixels at room scale -- so two seeds that drew the same base style
    # were the same table: `table_4top`'s closest pair over eight seeds measured
    # 0.3% disagreement while its mean read 30%. `m.top_z` already reports the
    # surface, and everything that puts a cup or a vase on a table reads it, so
    # a taller table is a taller table all the way through rather than a change
    # that has to be matched somewhere else.
    if seed is not None:
        h = h * (0.93 + rnd() * 0.14)
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
        # A trestle under a disc is a chair with two left legs -- so it becomes
        # a tripod, not a second pedestal. Sending it to the pedestal left a
        # disc with three bases one of which was drawn twice, and the closest
        # pair of eight round tables measured 2.9%.
        style = _base_tripod
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


def _legs_square(m, f, cx, cy, r, top):
    m.add_box((cx - r, cy - r, 0), (cx + r, cy + r, top), f)


def _legs_tapered(m, f, cx, cy, r, top):
    # Wider at the floor, narrower under the seat. Two boxes, because a taper
    # rendered as one is a taper nobody sees at 27 px per tile.
    m.add_box((cx - r * 1.35, cy - r * 1.35, 0),
              (cx + r * 1.35, cy + r * 1.35, top * 0.34), f)
    m.add_box((cx - r * 0.80, cy - r * 0.80, top * 0.34),
              (cx + r * 0.80, cy + r * 0.80, top), f)


def _legs_splayed(m, f, cx, cy, r, top):
    # Foot pushed outward from the seat's centre, which is the one leg style
    # that changes the chair's FOOTPRINT and so its silhouette from every
    # azimuth rather than only from the side.
    ox = 0.10 if cx > 0.5 else -0.10
    oy = 0.10 if cy > 0.5 else -0.10
    m.add_box((cx - r + ox, cy - r + oy, 0), (cx + r + ox, cy + r + oy,
                                              top * 0.30), f)
    m.add_box((cx - r + ox * 0.5, cy - r + oy * 0.5, top * 0.30),
              (cx + r + ox * 0.5, cy + r + oy * 0.5, top), f)


def _legs_turned(m, f, cx, cy, r, top):
    m.add_cylinder((cx, cy, 0), r * 1.15, top * 0.62, f, 8)
    m.add_cylinder((cx, cy, top * 0.62), r * 1.45, top * 0.10, f, 8)
    m.add_cylinder((cx, cy, top * 0.72), r * 0.95, top * 0.28, f, 8)


LEG_STYLES = (_legs_square, _legs_tapered, _legs_splayed, _legs_turned)


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
    # Three independent axes, not one. With only the back style, any two of
    # eight seeds that drew the same style were the same chair to the pixel --
    # measured at 3.0% disagreement for the closest pair while the generator's
    # MEAN spread read a healthy 34%. The leg radius was varying by 0.01, which
    # is a third of a pixel at room scale: variation that exists in the mesh
    # and dies in the raster is not variation.
    #
    # Seat height is the most valuable of the three because it moves the back,
    # the legs and the cushion together, and because `chair` already publishes
    # `seat_z` and the seated rig already takes it -- so a shorter chair seats
    # a person correctly rather than needing a matching change anywhere else.
    seat_z = 0.45 if seed is None else 0.415 + rnd() * 0.075
    leg_r = 0.090 + ((rnd() - 0.5) * 0.020 if seed is not None else 0.0)
    legs = (_legs_square if seed is None
            else LEG_STYLES[int(rnd() * len(LEG_STYLES)) % len(LEG_STYLES)])
    for cx, cy in ((0.28, 0.28), (0.72, 0.28), (0.28, 0.72), (0.72, 0.72)):
        legs(m, frame, cx, cy, leg_r, seat_z - 0.07)
    m.add_box((0.18, 0.18, seat_z - 0.07), (0.82, 0.82, seat_z), frame)     # seat
    style = (_back_low if seed is None
             else BACK_STYLES[int(rnd() * len(BACK_STYLES)) % len(BACK_STYLES)])
    style(m, frame, seat_z, 0.19, 0.83, 0.19, 0.34)
    if cushion:
        m.add_box((0.21, 0.21, seat_z), (0.79, 0.79, seat_z + 0.06), cushion)
    # The seat SURFACE, reported the way `table` reports `top_z`. A placement's
    # bounding box tops out at the backrest, so anything reading z1 for a seat
    # height gets 0.95 and sits a figure a third of a metre in the air -- the
    # same class of mistake as the clutter that sat at a hardcoded z while the
    # table thickness varied underneath it.
    m.seat_z = seat_z + (0.06 if cushion else 0.0)
    return m


def stool(seed: int | None = None, cushion=FABRIC) -> Mesh:
    """A bar stool. Height is the only thing about one that reads at this size.

    A row of three along a window bar is the most obviously repeated thing in
    the room after the counter run, and unlike the counter a row of stools has
    no reason to match -- they are pulled about and swapped between tables.
    """
    st = None if seed is None else _mix(seed)

    def rnd():
        nonlocal st
        if st is None:
            return 0.5
        st = _mix(st)
        return st / 0x7FFFFFFF

    m = Mesh()
    h = 0.62 if seed is None else 0.54 + rnd() * 0.14
    r = 0.24 if seed is None else 0.20 + rnd() * 0.07
    m.add_cylinder((0.5, 0.5, h), r, 0.08, cushion, 14)
    m.add_cylinder((0.5, 0.5, 0.0), 0.095, h, METAL, 10)
    m.add_cylinder((0.5, 0.5, 0.0), r * 0.92, 0.03, METAL, 12)
    m.rail_z = None
    if seed is not None and rnd() > 0.45:
        # A foot ring, on about half of them. It is four pixels of detail and
        # the only thing that distinguishes two stools of the same height.
        m.add_cylinder((0.5, 0.5, h * 0.34), 0.17, 0.028, METAL, 12)
        m.rail_z = h * 0.34 + 0.028
    # Published for the same reason `chair` publishes `seat_z`: the height a
    # person meets is not the height of the bounding box, and the rail is the
    # difference between a perched figure whose feet are on something and one
    # whose feet are in the air. Half these stools have no rail, which is not a
    # gap -- people do let their feet hang.
    m.seat_z = h + 0.08
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

    st = _mix(seed)

    def rnd():
        nonlocal st
        st = _mix(st)
        return st / 0x7FFFFFFF

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


def succulent(seed: int | None = None) -> Mesh:
    """A rosette in a small pot. Deliberately NOT `leafy_plant`.

    `leafy_plant` grows branching stems, and every parameter it has makes a
    plant that spreads. Asked for a 0.25-tall succulent it produced a green
    sprawl three times wider than its pot, with the pot as a sliver underneath
    -- a plant, correctly grown, of the wrong species.

    A succulent's geometry is the opposite: leaves radiate from a single point
    at a steep angle and stay inside the pot's own diameter, which is why the
    silhouette is a compact dome rather than an outline with gaps in it. Built
    as `strut` beams from a shared hub, in two tiers, because the tier is what
    stops a dome from reading as one blob.
    """
    st = None if seed is None else _mix(seed)

    def rnd():
        nonlocal st
        if st is None:
            return 0.5
        st = _mix(st)
        return st / 0x7FFFFFFF

    m = Mesh()
    pot_r, pot_h = 0.20, 0.16
    m.add_prism((0.5, 0.5, 0.0), pot_r * 0.80, pot_r * 0.80, pot_h * 0.75,
                FABRIC, 10)
    m.add_prism((0.5, 0.5, pot_h * 0.75), pot_r, pot_r, pot_h * 0.25,
                FABRIC, 10)
    m.add_prism((0.5, 0.5, pot_h * 0.92), pot_r * 0.86, pot_r * 0.86, 0.02,
                "wood-2", 10)                                        # soil

    hub = (0.5, 0.5, pot_h + 0.02)
    # Outer tier lies nearly flat and inner tier stands up. Both stay within
    # the pot radius: a leaf that overhangs the pot is what made the last
    # version read as a shrub.
    for n, reach, rise, thick, mat in ((7, 0.94, 0.30, 0.030, PLANT),
                                       (5, 0.55, 0.85, 0.026, "foliage+1")):
        phase = rnd() * math.tau
        for i in range(n):
            a = phase + i * math.tau / n
            tip = (hub[0] + math.cos(a) * pot_r * reach,
                   hub[1] + math.sin(a) * pot_r * reach,
                   hub[2] + pot_r * rise * (0.7 + rnd() * 0.6))
            strut(m, hub, tip, thick, mat)
    return m


def plant_large(seed: int = 3) -> Mesh:
    return leafy_plant(height=1.05, seed=seed, stems=6)


def plant_small(seed: int = 7) -> Mesh:
    return leafy_plant(height=0.52, seed=seed, stems=4)


# Book spine colours. Deliberately drawn from four different ramps: a shelf of
# books is the one place in a cafe where a dozen unrelated hues sit together,
# and it is the cheapest hue variety the room can buy, since the shelf is small
# enough that no single spine ever becomes a mass.
BOOK_SPINES = ("rose-1", "foliage-2", "cream-1", "wood+1", "neutral-1",
               "rose-3", "foliage", "sky-1", "wood-1", "cream-3")


def _books(m: Mesh, x0: float, x1: float, y0: float, y1: float,
           z: float, rnd, mats=BOOK_SPINES) -> None:
    """A row of books, as a stepped block with the spines drawn in value.

    The obvious approach is one box per book, and it does not survive the room.
    `check_member_thickness` puts the floor at 4 px, which at 27.2 px per unit
    is 0.147 of a tile -- so a modelled book spine is as wide as a hand, and a
    shelf holds four of them. What that renders is a shelf of ledgers.

    So the crate's idiom, which was invented for exactly this: the block is
    real geometry, and the individual spines are flat quads a thousandth of a
    unit proud of its face at different ramp steps. Nothing can be thinner than
    a pixel because nothing is being modelled, the result cannot leave the
    palette because a ramp step is all a spine ever is, and the block still
    steps in height so the row keeps a silhouette.
    """
    span = x1 - x0
    # Height steps first, so the silhouette is decided by geometry. Three is
    # enough to read as "not a slab" and few enough that each stays well over
    # the member floor.
    edges = [x0, x0 + span * (0.42 + rnd() * 0.18), x1]
    for i in range(2):
        h = 0.15 + rnd() * 0.085
        m.add_box((edges[i], y0, z), (edges[i + 1], y1, z + h), "wood-1")
        # Spines on the +y face and the top, the two this camera can see.
        #
        # Divided, not accumulated. Laying spines left to right until the next
        # one would not fit left up to a third of every section bare, which on
        # a shelf reads as a gap rather than as a book. Choosing the count
        # first and splitting the width fills it exactly.
        #
        # At the room's 27.2 px per unit a spine narrower than 0.074 is under
        # two pixels. The first version ran 0.018-0.048 and was sub-pixel
        # throughout: invisible in the room, aliasing between azimuths, and
        # correctly reported by `check_generator_range` as a generator whose
        # output does not vary -- because at the scale that matters, it did
        # not. Being value rather than geometry exempts a detail from
        # `check_member_thickness`, not from the pixel grid.
        eps, run = 0.0012, edges[i + 1] - edges[i] - 0.012
        n = max(2, int(run / 0.115))
        w = run / n
        for k in range(n):
            x = edges[i] + 0.006 + k * w
            mat = mats[int(rnd() * len(mats)) % len(mats)]
            # A spine shorter than its neighbours is a book pushed in, which is
            # most of what stops a row reading as a printed pattern.
            top = z + h - (0.0 if rnd() > 0.30 else 0.02 + rnd() * 0.03)
            # `facing` rather than a hand-ordered winding. Written the obvious
            # way (left, right, up, back) this quad's normal pointed -y, into
            # the carcass: culled by every visibility check in the tree, lit
            # against a normal facing away from the key light in the passes
            # that do not cull, and still perfectly convincing on a contact
            # sheet, which is how it survived being written.
            m.add_quad((x, y1 + eps, z + 0.012), (x + w - 0.006, y1 + eps, z + 0.012),
                       (x + w - 0.006, y1 + eps, top), (x, y1 + eps, top), mat,
                       facing=(0.0, 1.0, 0.0))
            m.add_quad((x, y0, top + eps), (x + w - 0.006, y0, top + eps),
                       (x + w - 0.006, y1, top + eps), (x, y1, top + eps), mat,
                       facing=(0.0, 0.0, 1.0))


def bookshelf(seed: int | None = None) -> Mesh:
    """Open at +y, which is the only side this camera can see into.

    It used to be a solid carcass box with the shelves and books modelled inside
    it -- 86% of its camera-facing triangles fully occluded, and on screen a
    plain wooden slab standing where a bookcase was supposed to be. All the
    detail existed; none of it was reachable. Building the carcass as a back,
    two sides and a top instead of one filled box is the entire fix.

    The books were then one `FABRIC` box per shelf: three coloured slabs, in the
    one object in the room that has an obvious reason to carry a dozen hues.
    `_books` generates them.
    """
    st = None if seed is None else _mix(seed)

    def rnd():
        nonlocal st
        if st is None:
            return 0.5
        st = _mix(st)
        return st / 0x7FFFFFFF

    m = Mesh()
    m.add_box((0.10, 0.55, 0.0), (0.90, 0.66, 1.45), WOOD)        # back panel
    for x0, x1 in ((0.10, 0.20), (0.80, 0.90)):                   # side panels
        m.add_box((x0, 0.55, 0.0), (x1, 0.92, 1.45), WOOD)
    m.add_box((0.10, 0.55, 1.36), (0.90, 0.92, 1.45), WOOD)       # top
    m.add_box((0.10, 0.55, 0.0), (0.90, 0.92, 0.10), WOOD)        # plinth
    for z in (0.34, 0.70, 1.06):
        m.add_box((0.20, 0.55, z), (0.80, 0.92, z + 0.05), CERAMIC)   # shelf
        if seed is None:
            m.add_box((0.23, 0.62, z + 0.05), (0.77, 0.90, z + 0.26), FABRIC)
        else:
            _books(m, 0.23, 0.77, 0.62, 0.90, z + 0.05, rnd)
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


def crate(seed: int | None = None) -> Mesh:
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

    `seed` varies height, how far the carcass is inset, and how many bands
    divide it. A crate has no silhouette to speak of -- it is a box -- so those
    three are the whole of what one crate has that another does not.
    """
    st = None if seed is None else _mix(seed)

    def rnd():
        nonlocal st
        if st is None:
            return 0.5
        st = _mix(st)
        return st / 0x7FFFFFFF

    m = Mesh()
    # A stack of crates in a store room is not a stack of one crate. Height and
    # slat count are what a crate has instead of a silhouette: it is a box, and
    # the only things about it that can differ are how tall it is and how the
    # bands divide it.
    top = 0.52 if seed is None else 0.40 + rnd() * 0.22
    inset = 0.12 if seed is None else 0.09 + rnd() * 0.05
    lo, hi = inset, 1.0 - inset
    m.add_box((lo, lo, 0.0), (hi, hi, top), "wood-2")          # carcass, in shadow
    e = 0.0014
    bands = 4 if seed is None else 3 + int(rnd() * 2.99)
    gap = top / bands
    h = gap * 0.72
    for i in range(bands):
        z = gap * i + gap * 0.14
        band = "wood" if i % 2 == 0 else "wood+1"
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
    # Crates get stacked, and the height now varies, so the stack has to be
    # told where the lid ended up. Exactly the table's `top_z` problem: a
    # generator that changes a dimension without saying so leaves whatever
    # sits on it floating, and `grounded` reports that as a placement bug.
    m.top_z = top
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

# --- soft seating ------------------------------------------------------------
#
# The armchair and the bench were the last two seats in the library that were
# one mesh each. They are also the two the eye spends longest on, because they
# are the largest single objects on the floor after the counter run, and a
# lounge corner furnished from one catalogue entry twice is the tell.
#
# What varies is the arms, the back and the base -- the three things that ARE
# the outline. What does not vary is anything inside it, for the reason the
# chair backs recorded two passes ago.


def _arm_panel(m, f, x0, x1, y0, y1, sz, t):
    """Solid panel arms. The heaviest reading: a club chair."""
    for ax in (x0, x1 - t):
        m.add_box((ax, y0 + 0.18, sz - 0.14), (ax + t, y1, sz + 0.13), f)


def _arm_open(m, f, x0, x1, y0, y1, sz, t):
    """A post at each end under a rail. The gap beneath the rail is the whole
    point -- it is the one place an armchair can show floor through itself,
    which is worth more to a silhouette than any amount of surface."""
    for ax in (x0 + 0.02, x1 - t):
        for ay in (y0 + 0.21, y1 - 0.17):
            m.add_box((ax, ay, sz - 0.14), (ax + t * 0.7, ay + 0.15, sz + 0.05), f)
        m.add_box((ax, y0 + 0.21, sz + 0.05), (ax + t * 0.7, y1, sz + 0.14), f)


def _arm_rolled(m, f, x0, x1, y0, y1, sz, t):
    """Stepped in two heights. A roll is a curve, and a curve is one pixel at
    room scale, so it is drawn as a value step instead."""
    for ax in (x0, x1 - t):
        m.add_box((ax + 0.03, y0 + 0.18, sz - 0.14), (ax + t - 0.03, y1, sz + 0.10), f)
        m.add_box((ax, y0 + 0.22, sz + 0.10), (ax + t, y1 - 0.05, sz + 0.20), f + "+1")


def _arm_none(m, f, x0, x1, y0, y1, sz, t):
    """A slipper chair. This has to be an option: a generator every output of
    which has arms is a generator with three settings, and the armless
    silhouette is the furthest of the four from the other three."""
    return


ARM_STYLES = (_arm_panel, _arm_open, _arm_rolled, _arm_none)


def _seat_base_plinth(m, f, x0, x1, y0, y1, sz):
    """A skirt to the floor. Reads as mass, which upholstery should."""
    m.add_box((x0, y0, 0.0), (x1, y1, sz - 0.14), f)


def _seat_base_legs(m, f, x0, x1, y0, y1, sz):
    """Four posts. Lifting the mass off the floor is the single biggest change
    available to a seat's outline, because it puts floor underneath it."""
    r = 0.055
    for cx in (x0 + 0.10, x1 - 0.10 - r * 2):
        for cy in (y0 + 0.10, y1 - 0.10 - r * 2):
            m.add_box((cx, cy, 0.0), (cx + r * 2, cy + r * 2, sz - 0.14), f + "-1")
    m.add_box((x0 + 0.04, y0 + 0.04, sz - 0.20), (x1 - 0.04, y1 - 0.04, sz - 0.14), f)


def _seat_base_splay(m, f, x0, x1, y0, y1, sz):
    """Raked posts, which no axis-aligned box can draw -- this is what `strut`
    was added for when the tables needed it."""
    r, inset = 0.048, 0.16
    for sx, ex in ((x0 + inset, x0 + 0.05), (x1 - inset, x1 - 0.05)):
        for sy, ey in ((y0 + inset, y0 + 0.05), (y1 - inset, y1 - 0.05)):
            strut(m, (ex, ey, 0.0), (sx, sy, sz - 0.14), r, f + "-1")
    m.add_box((x0 + 0.04, y0 + 0.04, sz - 0.20), (x1 - 0.04, y1 - 0.04, sz - 0.14), f)


SEAT_BASES = (_seat_base_plinth, _seat_base_legs, _seat_base_splay,
              _seat_base_plinth)


def armchair(cushion=FABRIC, frame=WOOD, seed: int | None = None) -> Mesh:
    """Back at -y, matching `chair`, so both face a table at +y under rot=0.

    `seed=None` reproduces the fixed mesh exactly, so callers that have not
    opted in keep their sprites.
    """
    st = None if seed is None else _mix(seed)

    def rnd():
        nonlocal st
        st = _mix(st)
        return st / 0x7FFFFFFF

    m = Mesh()
    if seed is None:
        m.add_box((0.10, 0.10, 0.0), (0.90, 0.90, 0.34), frame)
        m.add_box((0.16, 0.16, 0.34), (0.84, 0.84, 0.48), cushion)
        m.add_box((0.10, 0.10, 0.34), (0.90, 0.28, 0.92), frame)
        m.add_box((0.14, 0.26, 0.40), (0.86, 0.32, 0.86), cushion)
        for ax in (0.10, 0.72):
            m.add_box((ax, 0.28, 0.34), (ax + 0.18, 0.88, 0.60), frame)
        m.seat_z = 0.48
        return m

    x0, x1, y0, y1 = 0.10, 0.90, 0.10, 0.90
    sz = 0.46 + rnd() * 0.06                      # seat top
    SEAT_BASES[int(rnd() * len(SEAT_BASES)) % len(SEAT_BASES)](
        m, frame, x0, x1, y0, y1, sz)
    m.add_box((x0 + 0.06, y0 + 0.06, sz - 0.14), (x1 - 0.06, y1 - 0.06, sz), cushion)
    # Back. Height is the loudest single number in the outline, so it gets the
    # widest range of any parameter here.
    bh = sz + 0.34 + rnd() * 0.26
    m.add_box((x0, y0, sz - 0.14), (x1, y0 + 0.18, bh), frame)
    m.add_box((x0 + 0.04, y0 + 0.16, sz + 0.02), (x1 - 0.04, y0 + 0.22, bh - 0.06),
              cushion)
    if rnd() < 0.34:
        # Wings, only sometimes: a wing on every chair is not a wing.
        for ax in (x0, x1 - 0.10):
            m.add_box((ax, y0, sz + 0.10), (ax + 0.10, y0 + 0.34, bh - 0.02),
                      frame + "-1")
    ARM_STYLES[int(rnd() * len(ARM_STYLES)) % len(ARM_STYLES)](
        m, frame, x0, x1, y0 + 0.18, y1, sz, 0.16 + rnd() * 0.06)
    m.seat_z = sz
    return m


def _bench_back_solid(m, f, x0, x1, y0, sz, bh):
    m.add_box((x0, y0, sz - 0.08), (x1, y0 + 0.16, bh), f)


def _bench_back_slat(m, f, x0, x1, y0, sz, bh):
    """Horizontal rails with air between them."""
    m.add_box((x0, y0, sz - 0.08), (x1, y0 + 0.16, sz + 0.06), f)
    m.add_box((x0, y0, bh - 0.10), (x1, y0 + 0.16, bh), f)
    n = 3
    h = ((bh - 0.10) - (sz + 0.06)) / (n * 2 - 1)
    for i in range(n):
        z = sz + 0.06 + i * 2 * h
        m.add_box((x0 + 0.03, y0 + 0.03, z), (x1 - 0.03, y0 + 0.13, z + h), f + "-1")


def _bench_back_spindle(m, f, x0, x1, y0, sz, bh):
    """Vertical spindles, divided across the run rather than accumulated, so a
    longer bench gets more of them and not wider ones -- the book spines
    learned this rule the expensive way."""
    m.add_box((x0, y0, sz - 0.08), (x1, y0 + 0.16, sz + 0.06), f)
    m.add_box((x0, y0, bh - 0.09), (x1, y0 + 0.16, bh), f)
    run = (x1 - 0.06) - (x0 + 0.06)
    n = max(2, int(run / 0.30))
    w = run / n
    for i in range(n):
        cx = x0 + 0.06 + (i + 0.5) * w
        m.add_box((cx - 0.045, y0 + 0.04, sz + 0.06),
                  (cx + 0.045, y0 + 0.12, bh - 0.09), f + "-1")


def _bench_back_rail(m, f, x0, x1, y0, sz, bh):
    """One rail on two posts: the most open of the four, and the only one that
    leaves the wall behind it visible."""
    for ax in (x0 + 0.02, x1 - 0.14):
        m.add_box((ax, y0 + 0.02, sz - 0.08), (ax + 0.12, y0 + 0.14, bh), f)
    m.add_box((x0, y0 + 0.02, bh - 0.14), (x1, y0 + 0.14, bh), f)


BENCH_BACKS = (_bench_back_solid, _bench_back_slat, _bench_back_spindle,
               _bench_back_rail)


def bench(length: float = 2.0, cushion=FABRIC, frame=WOOD,
          seed: int | None = None) -> Mesh:
    """Banquette seating: reads as one mass, which is what a wall run wants."""
    m = Mesh()
    if seed is None:
        m.add_box((0.08, 0.14, 0.0), (length - 0.08, 0.82, 0.38), frame)
        m.add_box((0.08, 0.16, 0.38), (length - 0.08, 0.80, 0.46), cushion)
        m.add_box((0.08, 0.14, 0.46), (length - 0.08, 0.30, 1.02), frame)
        m.add_box((0.12, 0.28, 0.50), (length - 0.12, 0.34, 0.94), cushion)
        return m

    st = _mix(seed)

    def rnd():
        nonlocal st
        st = _mix(st)
        return st / 0x7FFFFFFF

    x0, x1, y0, y1 = 0.08, length - 0.08, 0.14, 0.82
    sz = 0.44 + rnd() * 0.06
    if rnd() < 0.5:
        m.add_box((x0, y0, 0.0), (x1, y1, sz - 0.08), frame)
    else:
        for cx in (x0 + 0.06, x1 - 0.20):
            m.add_box((cx, y0 + 0.08, 0.0), (cx + 0.14, y1 - 0.08, sz - 0.08),
                      frame + "-1")
        m.add_box((x0, y0 + 0.02, sz - 0.16), (x1, y1 - 0.02, sz - 0.08), frame)
    m.add_box((x0, y0 + 0.02, sz - 0.08), (x1, y1 - 0.02, sz), cushion)
    bh = sz + 0.46 + rnd() * 0.20
    BENCH_BACKS[int(rnd() * len(BENCH_BACKS)) % len(BENCH_BACKS)](
        m, frame, x0, x1, y0, sz, bh)
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


def _aframe_panel(slate_side: float) -> Mesh:
    """One upright panel, hinged at the top, slate on the given face."""
    m = Mesh()
    # Solid panels, not quads. A zero-thickness plane is right for a floor
    # overlay and wrong for anything standing up: seen near edge-on it collapses
    # to a 1 px line, which is how this shipped at 3 px and read as a stray mark.
    m.add_box((0.12, 0.485, 0.0), (0.88, 0.515, 0.90), WOOD)
    if slate_side > 0:
        m.add_box((0.17, 0.515, 0.16), (0.83, 0.527, 0.78), "neutral-2")
    else:
        m.add_box((0.17, 0.473, 0.16), (0.83, 0.485, 0.78), "neutral-2")
    return m


A_FRAME_LEAN = 17.0


def sandwich_board() -> Mesh:
    """A-frame chalkboard. The lean is the whole silhouette, so it is generous.

    The lean has to be a ROTATION. This shipped as two axis-aligned boxes at
    different y with a hinge across the top, which is a docstring describing a
    lean over geometry that has none -- and it rendered as exactly what it is:
    a closed rectangular box, read in review as a doorway rather than a board.
    `add_box` cannot lean, so each panel is built upright at the hinge plane and
    swung about the hinge line with `pivot_rot`, the same primitive the rig uses
    to turn a leg about its hip.

    The slate sits on each panel's OUTWARD face and is rotated with it, so the
    two boards splay apart the way a real A-frame's do -- which is what makes
    the silhouette read from the sides as well as from the front.
    """
    hinge = (0.5, 0.5, 0.90)
    front = pivot_rot(_aframe_panel(+1.0), "x", A_FRAME_LEAN, hinge)
    back = pivot_rot(_aframe_panel(-1.0), "x", -A_FRAME_LEAN, hinge)
    cap = Mesh()
    cap.add_box((0.12, 0.44, 0.88), (0.88, 0.56, 0.96), WOOD)              # hinge
    return merge(front, back, cap)


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


def basket(fill=FABRIC, seed: int | None = None) -> Mesh:
    """A woven basket with something heaped in it.

    Sides taper, because a basket that does not is a bucket, and the taper is
    most of what the outline says at this size.
    """
    st = None if seed is None else _mix(seed)

    def rnd():
        nonlocal st
        if st is None:
            return 0.5
        st = _mix(st)
        return st / 0x7FFFFFFF

    m = Mesh()
    r = 0.28 if seed is None else 0.23 + rnd() * 0.08
    h = 0.30 if seed is None else 0.22 + rnd() * 0.14
    m.add_prism((0.5, 0.5, 0.0), r * 0.82, r * 0.82, h * 0.55, WOOD, 12)
    m.add_prism((0.5, 0.5, h * 0.55), r, r, h * 0.45, WOOD, 12)
    # A rim one step lighter, which is what reads as "woven" at 27 px -- the
    # weave itself is a texture no pixel in this frame is large enough to hold.
    m.add_prism((0.5, 0.5, h), r * 1.04, r * 1.04, 0.035, "wood+1", 12)
    m.add_prism((0.5, 0.5, h - 0.02), r * 0.88, r * 0.88,
                0.05 + rnd() * 0.06, fill, 10)
    return m


def trash_bin() -> Mesh:
    m = Mesh()
    m.add_cylinder((0.5, 0.5, 0.0), 0.24, 0.56, "neutral-1", 12)
    m.add_cylinder((0.5, 0.5, 0.56), 0.26, 0.06, METAL, 12)
    return m


VASE_BLOOMS = ("rose+1", "rose+2", "cream+1", "rose", "cream+2")


def flower_vase(seed: int | None = None) -> Mesh:
    """Stems in a vase, with the blooms as low-poly spheres.

    Three identical vases on three tables is the same tell as three identical
    plants, and this one is worse, because a vase of flowers is the object in a
    cafe that most obviously came from somebody choosing them.
    """
    import math
    st = None if seed is None else _mix(seed)

    def rnd():
        nonlocal st
        if st is None:
            return 0.5
        st = _mix(st)
        return st / 0x7FFFFFFF

    m = Mesh()
    neck = 0.09 if seed is None else 0.075 + rnd() * 0.035
    tall = 0.22 if seed is None else 0.17 + rnd() * 0.11
    m.add_cylinder((0.5, 0.5, 0.0), neck, tall, CERAMIC, 10)
    if seed is None:
        heads = ((0.0, 0.0, 0.30, 0.10), (0.07, 0.04, 0.38, 0.08),
                 (-0.06, 0.05, 0.36, 0.08))
        for dx, dy, dz, r in heads:
            m.add_sphere((0.5 + dx, 0.5 + dy, dz), r, "rose+1", 8, 6)
        return m
    n = 2 + int(rnd() * 2.99)
    bloom = VASE_BLOOMS[int(rnd() * len(VASE_BLOOMS)) % len(VASE_BLOOMS)]
    turn = rnd() * math.tau
    for i in range(n):
        a = turn + i * math.tau / n
        lean = 0.02 + rnd() * 0.075
        z = tall + 0.06 + rnd() * 0.14
        r = 0.065 + rnd() * 0.035
        # A stem, so the head is attached to something rather than hovering.
        strut(m, (0.5, 0.5, tall - 0.02),
              (0.5 + math.cos(a) * lean, 0.5 + math.sin(a) * lean, z - r * 0.5),
              0.012, PLANT)
        m.add_sphere((0.5 + math.cos(a) * lean, 0.5 + math.sin(a) * lean, z),
                     r, bloom if i else bloom, 8, 6)
    return m


# --- back-of-house fixtures --------------------------------------------------
#
# Everything below exists because `furnish.py`'s registry made the gap countable:
# `assets.yaml` declares these ids, no builder made them, and the honest report
# said so. They are written to the same rule the rest of this file follows --
# the SILHOUETTE carries the object, and interior detail is drawn as a value
# step rather than as geometry, because interior detail is gone by the time the
# frame is downsampled and the outline is not.


def fridge_under(seed: int | None = None) -> Mesh:
    """Under-counter fridge. A door line and a handle, and nothing else.

    A closed appliance is a box, and pretending otherwise by modelling a vent
    grille would spend geometry on something two pixels tall. What makes it
    read as a fridge rather than as a cabinet is the full-height door reveal and
    the horizontal handle -- both drawn as value on the front face, which is the
    same technique `counter`'s front treatments use.

    `seed` took a parameter and did nothing with it until this pass (found
    alongside the identical `tip_jar` bug -- see `ART_CRITIQUE.md`). Handle
    height and length vary, plus a barely-there plinth height -- the same
    scale of change `counter`'s own front treatments get, because this is
    still "a fitted module... the seed has to do something, not a lot".
    """
    st = None if seed is None else _mix(seed)

    def rnd():
        nonlocal st
        if st is None:
            return 0.5
        st = _mix(st)
        return st / 0x7FFFFFFF

    m = Mesh()
    m.add_box((0.14, 0.14, 0.04), (0.86, 0.86, 0.92), METAL)
    # +y is the front. `counter` draws its front treatments at y=0.9412 and
    # every room placement rotates props to suit, so a detail on -y is a detail
    # the camera cannot see in the direction the prop is meant to face -- which
    # is how this first shipped, as a featureless grey box at dir0.
    m.add_box((0.16, 0.86, 0.06), (0.84, 0.88, 0.90), "neutral+1")     # door
    hz = 0.66 + rnd() * 0.10                                           # handle height
    hlen = 0.09 + rnd() * 0.05
    m.add_box((0.50 - hlen, 0.87, hz), (0.50 + hlen, 0.90, hz + 0.06),
              "neutral+2")                                             # handle
    plinth = 0.03 + rnd() * 0.02
    m.add_box((0.14, 0.14, 0.0), (0.86, 0.86, plinth), "neutral-2")    # plinth
    return m


def ice_machine() -> Mesh:
    """A lid that overhangs is the whole tell -- otherwise this is `fridge_under`
    in a different size, and two boxes with different declared heights are one
    asset wearing two names."""
    m = Mesh()
    m.add_box((0.18, 0.18, 0.0), (0.82, 0.82, 0.78), METAL)
    m.add_box((0.14, 0.14, 0.78), (0.86, 0.86, 0.90), "neutral+1")     # lid
    m.add_box((0.22, 0.81, 0.24), (0.78, 0.84, 0.58), "neutral-1")     # hatch
    return m


def sink_double() -> Mesh:
    """Two basins. `Mesh` is additive, so the recess is built as a rim rather
    than cut out of a solid.

    Four walls and a floor per basin is the whole of it -- and it is the right
    shape anyway, because from this camera the only part of a basin anyone sees
    is the rim and the far inside wall. A subtractive model would spend
    triangles on a bottom the camera cannot reach.
    """
    m = Mesh()
    top, wall, depth = 0.86, 0.05, 0.18
    m.add_box((0.0, 0.10, 0.0), (2.0, 0.90, top - depth), METAL)       # carcass
    for x0 in (0.16, 1.06):
        x1 = x0 + 0.78
        m.add_box((x0, 0.18, top - depth), (x1, 0.82, top - depth + 0.02),
                  "neutral-2")                                        # basin floor
        for a, b in ((x0, x0 + wall), (x1 - wall, x1)):               # side walls
            m.add_box((a, 0.18, top - depth), (b, 0.82, top), "neutral+1")
        for a, b in ((0.18, 0.18 + wall), (0.82 - wall, 0.82)):       # end walls
            m.add_box((x0, a, top - depth), (x1, b, top), "neutral+1")
    m.add_cylinder((1.0, 0.30, top), 0.035, 0.26, "neutral+2", 8)     # tap column
    m.add_box((0.96, 0.30, top + 0.22), (1.04, 0.58, top + 0.28), "neutral+2")
    return m


def cup_warmer() -> Mesh:
    """A heated plate with cups upended on it. The cups are the object: a bare
    plate is a tray, and at three pixels tall the difference has to be the
    thing standing on top."""
    m = Mesh()
    m.add_box((0.16, 0.24, 0.0), (0.84, 0.76, 0.10), METAL)
    m.add_box((0.18, 0.26, 0.10), (0.82, 0.74, 0.12), "neutral+2")     # hot plate
    for cx in (0.32, 0.50, 0.68):
        for cy in (0.38, 0.62):
            m.add_cylinder((cx, cy, 0.12), 0.065, 0.11, CERAMIC, 8)
    return m


def bean_hopper() -> Mesh:
    """An inverted cone on a collar. The taper IS the object -- a cylinder of
    beans is a tin."""
    m = Mesh()
    m.add_prism((0.5, 0.5, 0.0), 0.16, 0.16, 0.10, METAL, 10)          # collar
    # The BEANS are the outer surface, not the glass. A hopper modelled as a
    # glass shell with beans inside draws the shell over the beans -- this
    # rasteriser has no transparency -- and a whole vessel of `sky+2` came out
    # as a pale blue tank, which is the same reading GLASS's own comment records
    # for windows. So the wall is beans, and the glass is two narrow bands that
    # read as the empty top of the vessel.
    for r, z0, z1 in ((0.20, 0.10, 0.26), (0.26, 0.26, 0.42), (0.31, 0.42, 0.56)):
        m.add_prism((0.5, 0.5, z0), r, r, z1 - z0, "wood-1", 10)       # beans
    m.add_prism((0.5, 0.5, 0.36), 0.265, 0.265, 0.03, "wood-2", 10)    # band
    m.add_prism((0.5, 0.5, 0.56), 0.31, 0.31, 0.06, GLASS, 10)         # empty top
    m.add_prism((0.5, 0.5, 0.62), 0.33, 0.33, 0.06, "neutral+1", 10)   # rim
    return m


def drip_brewer() -> Mesh:
    """Body, basket, carafe on a plate. The overhang of the brew head over the
    carafe is what separates this from a kettle at this size."""
    m = Mesh()
    m.add_box((0.20, 0.22, 0.0), (0.80, 0.78, 0.20), METAL)            # base
    m.add_box((0.22, 0.24, 0.20), (0.78, 0.42, 0.92), "neutral+1")     # column
    m.add_box((0.22, 0.24, 0.62), (0.80, 0.74, 0.78), "neutral+1")     # brew head
    m.add_box((0.24, 0.26, 0.20), (0.76, 0.72, 0.23), "neutral-1")     # warm plate
    m.add_prism((0.52, 0.54, 0.23), 0.20, 0.20, 0.34, GLASS, 10)       # carafe
    m.add_prism((0.52, 0.54, 0.23), 0.17, 0.17, 0.18, "wood-2", 10)    # coffee
    m.add_box((0.70, 0.50, 0.26), (0.76, 0.58, 0.52), "neutral-1")     # handle
    return m


def pourover_stand() -> Mesh:
    """A cone held over a carafe by an arm. Every part of this is air except the
    arm, which is why it is built with `strut` -- an axis-aligned bracket reads
    as a box with a hole and loses the cantilever the object is named for."""
    m = Mesh()
    m.add_box((0.16, 0.30, 0.0), (0.84, 0.70, 0.06), WOOD)             # foot
    strut(m, (0.24, 0.50, 0.06), (0.24, 0.50, 0.86), 0.035, METAL)     # post
    strut(m, (0.24, 0.50, 0.82), (0.58, 0.50, 0.78), 0.030, METAL)     # arm
    m.add_prism((0.58, 0.50, 0.66), 0.10, 0.10, 0.06, METAL, 8)        # ring
    m.add_prism((0.58, 0.50, 0.60), 0.06, 0.06, 0.20, CERAMIC, 10)     # cone
    m.add_prism((0.58, 0.50, 0.80), 0.16, 0.16, 0.04, CERAMIC, 10)
    m.add_prism((0.58, 0.50, 0.06), 0.17, 0.17, 0.30, GLASS, 10)       # carafe
    m.add_prism((0.58, 0.50, 0.06), 0.14, 0.14, 0.12, "wood-2", 10)
    return m


def grinder_hand() -> Mesh:
    """The crank is the silhouette. Everything under it is a box, and a box
    without the crank is a canister."""
    m = Mesh()
    m.add_box((0.30, 0.30, 0.0), (0.70, 0.70, 0.44), WOOD)             # body
    m.add_box((0.32, 0.32, 0.44), (0.68, 0.68, 0.50), "wood+1")        # collar
    m.add_prism((0.50, 0.50, 0.50), 0.15, 0.15, 0.14, METAL, 10)       # hopper
    strut(m, (0.50, 0.50, 0.64), (0.50, 0.50, 0.78), 0.020, METAL)     # shaft
    strut(m, (0.50, 0.50, 0.76), (0.74, 0.50, 0.74), 0.022, METAL)     # crank arm
    m.add_cylinder((0.74, 0.50, 0.60), 0.030, 0.14, WOOD, 8)           # knob
    m.add_box((0.34, 0.28, 0.06), (0.66, 0.31, 0.24), "wood+2")        # drawer
    return m


def kettle_gooseneck() -> Mesh:
    """The spout arcs up and over, which no single beam draws -- it is three
    struts, because the curve is the entire reason this object has a name."""
    m = Mesh()
    m.add_prism((0.44, 0.50, 0.0), 0.22, 0.22, 0.26, METAL, 12)        # body
    m.add_prism((0.44, 0.50, 0.26), 0.17, 0.17, 0.06, "neutral+1", 12)  # shoulder
    m.add_prism((0.44, 0.50, 0.32), 0.09, 0.09, 0.05, "neutral+2", 10)  # lid
    strut(m, (0.62, 0.50, 0.12), (0.74, 0.50, 0.30), 0.024, "neutral+1")
    strut(m, (0.74, 0.50, 0.30), (0.80, 0.50, 0.40), 0.022, "neutral+1")
    strut(m, (0.80, 0.50, 0.40), (0.84, 0.50, 0.30), 0.020, "neutral+1")
    strut(m, (0.22, 0.50, 0.06), (0.14, 0.50, 0.26), 0.022, "neutral-1")  # handle
    strut(m, (0.14, 0.50, 0.26), (0.26, 0.50, 0.34), 0.022, "neutral-1")
    return m


# --- tabletop ----------------------------------------------------------------
#
# These are the smallest objects the factory makes, and small is the reason
# they are geometry rather than SDXL output: a 0.15-tile mug quantized from a
# photograph is a speckle field, which is the same ceiling `bread_loaf` and the
# laminated pastry hit. Built as boxes and prisms, they downsample to clean
# flats because there was never any high-frequency detail to lose.


def cup_espresso() -> Mesh:
    """A demitasse differs from a latte cup by PROPORTION, not by size -- it is
    short and narrow on a saucer that is wide relative to it. `fit` scales
    uniformly, so this cannot be `cup_and_saucer` at a smaller height: that
    produced pixel-identical sprites, which is how the duplicate was caught."""
    m = Mesh()
    m.add_cylinder((0.5, 0.5, 0.0), 0.145, 0.018, CERAMIC, 12)         # saucer
    m.add_cylinder((0.5, 0.5, 0.0), 0.120, 0.030, "cream+1", 12)       # well
    # The cup was 0.055 against a 0.15 saucer and disappeared into it: the
    # sprite read as a flat disc. A demitasse is small in ABSOLUTE terms and
    # still most of what is on the saucer, and only the latter survives being
    # framed to fill 64 px.
    m.add_cylinder((0.5, 0.5, 0.018), 0.090, 0.115, CERAMIC, 10)       # cup
    m.add_cylinder((0.5, 0.5, 0.115), 0.070, 0.018, "wood-2", 10)      # crema
    strut(m, (0.585, 0.50, 0.085), (0.645, 0.50, 0.070), 0.016, CERAMIC)
    strut(m, (0.645, 0.50, 0.070), (0.615, 0.50, 0.040), 0.016, CERAMIC)
    return m


def cup_togo() -> Mesh:
    """Tapered body, lid wider than the rim, sleeve as a value band. The taper
    and the proud lid are the two things that separate a paper cup from a
    tumbler at eight pixels wide."""
    m = Mesh()
    m.add_prism((0.5, 0.5, 0.0), 0.115, 0.115, 0.10, CERAMIC, 12)
    m.add_prism((0.5, 0.5, 0.10), 0.135, 0.135, 0.12, CERAMIC, 12)
    m.add_prism((0.5, 0.5, 0.07), 0.140, 0.140, 0.09, "wood-1", 12)    # sleeve
    m.add_prism((0.5, 0.5, 0.22), 0.155, 0.155, 0.035, "neutral+1", 12)  # lid
    m.add_prism((0.5, 0.5, 0.255), 0.075, 0.075, 0.020, "neutral+1", 10)  # spout
    return m


def mug_ceramic() -> Mesh:
    """The handle is the silhouette. A mug without one is a tumbler, so the
    handle is built as three struts around a genuine hole rather than as a lump
    on the side -- the gap is what the eye reads."""
    m = Mesh()
    m.add_cylinder((0.46, 0.5, 0.0), 0.145, 0.20, CERAMIC, 12)
    m.add_cylinder((0.46, 0.5, 0.185), 0.115, 0.020, "wood-2", 12)     # coffee
    strut(m, (0.60, 0.50, 0.055), (0.70, 0.50, 0.070), 0.020, CERAMIC)
    strut(m, (0.70, 0.50, 0.070), (0.71, 0.50, 0.140), 0.020, CERAMIC)
    strut(m, (0.71, 0.50, 0.140), (0.60, 0.50, 0.160), 0.020, CERAMIC)
    return m


def milk_jug() -> Mesh:
    """A pitcher: straight-sided, with a pulled lip. The lip is one strut and it
    is the only thing that says "pour" rather than "cup"."""
    m = Mesh()
    m.add_prism((0.44, 0.5, 0.0), 0.130, 0.130, 0.23, METAL, 10)
    m.add_prism((0.44, 0.5, 0.23), 0.145, 0.145, 0.02, "neutral+2", 10)  # rim
    # A pitcher is a lip and a handle attached to a cylinder, and a cylinder on
    # its own is a tin. Both were built at strut radii that land under a pixel
    # once the sprite is framed, so neither reached the silhouette; they are
    # now sized to clear the library's own 4 px member floor.
    strut(m, (0.55, 0.50, 0.225), (0.70, 0.50, 0.185), 0.045, "neutral+2")  # lip
    strut(m, (0.31, 0.50, 0.045), (0.19, 0.50, 0.115), 0.034, "neutral+1")
    strut(m, (0.19, 0.50, 0.115), (0.32, 0.50, 0.200), 0.034, "neutral+1")
    return m


def sugar_caddy() -> Mesh:
    """An open box with sachets standing in it. The sachets are the object; an
    empty caddy is a matchbox."""
    m = Mesh()
    for a, b in ((0.26, 0.30), (0.70, 0.74)):
        m.add_box((0.26, a, 0.0), (0.74, b, 0.16), WOOD)
        m.add_box((a, 0.26, 0.0), (b, 0.74, 0.16), WOOD)
    m.add_box((0.28, 0.28, 0.0), (0.72, 0.72, 0.03), "wood-1")
    for i, x in enumerate((0.34, 0.42, 0.50, 0.58, 0.66)):
        mat = "cream+2" if i % 2 else "cream+1"
        m.add_box((x, 0.32, 0.03), (x + 0.055, 0.68, 0.22), mat)
    return m


def napkin_holder() -> Mesh:
    """Two uprights with a stack of paper wedged between them. The paper is a
    lighter step than the metal, which is the whole of the contrast."""
    m = Mesh()
    m.add_box((0.26, 0.30, 0.0), (0.74, 0.70, 0.025), METAL)
    for a, b in ((0.30, 0.345), (0.655, 0.70)):
        m.add_box((0.28, a, 0.025), (0.72, b, 0.24), "neutral+1")
    m.add_box((0.31, 0.36, 0.025), (0.69, 0.64, 0.27), "cream+3")      # napkins
    return m


def tip_jar(seed: int | None = None) -> Mesh:
    """A jar with coins in it and a label band. Glass reads as near-empty at
    this size, so what makes it a tip jar is the coin mass at the bottom.

    `seed` took a parameter and did nothing with it until this pass (found
    alongside the identical `fridge_under` bug -- see `ART_CRITIQUE.md`).
    Coin-fill height varies most -- a jar an hour into a shift and one at
    closing are the same object at different fill -- plus a small jar-radius
    and label-height wobble, both bounded well inside the outer glass so the
    label never pokes past the rim.
    """
    st = None if seed is None else _mix(seed)

    def rnd():
        nonlocal st
        if st is None:
            return 0.5
        st = _mix(st)
        return st / 0x7FFFFFFF

    r = 0.185 + rnd() * 0.015
    fill = 0.05 + rnd() * 0.14
    label_z = 0.13 + rnd() * 0.05
    m = Mesh()
    m.add_prism((0.5, 0.5, 0.0), r, r, 0.30, GLASS, 12)
    m.add_prism((0.5, 0.5, 0.0), r * 0.87, r * 0.87, fill, "gold_coin", 12)  # coins
    m.add_prism((0.5, 0.5, label_z), r * 1.03, r * 1.03, 0.07, "cream+2", 12)  # label
    m.add_prism((0.5, 0.5, 0.30), r * 1.05, r * 1.05, 0.035, "neutral+1", 12)  # ring
    return m


def laptop_open(angle: float = 100.0) -> Mesh:
    """Base and screen, hinged. The angle between them is the object -- flat it
    is a book, and vertical it is a picture frame -- so the screen is swung with
    `pivot_rot` about the hinge line rather than placed as a leaning box."""
    m = Mesh()
    m.add_box((0.18, 0.34, 0.0), (0.82, 0.78, 0.030), "neutral-1")     # base
    m.add_box((0.22, 0.40, 0.030), (0.78, 0.72, 0.036), "neutral+1")   # keys
    lid = Mesh()
    lid.add_box((0.18, 0.34, 0.030), (0.82, 0.36, 0.44), "neutral-1")
    lid.add_box((0.21, 0.355, 0.060), (0.79, 0.365, 0.41), GLASS)      # screen
    return merge(m, pivot_rot(lid, "x", angle - 90.0, (0.5, 0.35, 0.030)))


def book_stack(seed: int | None = None) -> Mesh:
    """Four volumes, each offset and rotated a little. A stack squared up is a
    block; the offsets are what make it a stack."""
    st = None if seed is None else _mix(seed)

    def rnd():
        nonlocal st
        if st is None:
            return 0.5
        st = _mix(st)
        return st / 0x7FFFFFFF

    m = Mesh()
    z = 0.0
    for i in range(4):
        t = 0.038 + rnd() * 0.026
        w, d = 0.30 - i * 0.012, 0.22 - i * 0.008
        one = Mesh()
        one.add_box((0.5 - w, 0.5 - d, z), (0.5 + w, 0.5 + d, z + t),
                    BOOK_SPINES[int(rnd() * len(BOOK_SPINES)) % len(BOOK_SPINES)])
        one.add_box((0.5 - w + 0.03, 0.5 - d, z + 0.008),
                    (0.5 + w, 0.5 + d, z + t - 0.008), "cream+3")      # pages
        m = merge(m, pivot_rot(one, "z", (rnd() - 0.5) * 26.0, (0.5, 0.5, 0.0)))
        z += t
    return m


def pastry_plate(seed: int | None = None) -> Mesh:
    """A plate with two pastries on it. Laminated pastry is high-frequency
    detail that quantizes to speckle -- the ceiling `ui_icon_pastry` hit -- so
    these are stepped blocks whose value change does the work instead."""
    st = None if seed is None else _mix(seed)

    def rnd():
        nonlocal st
        if st is None:
            return 0.5
        st = _mix(st)
        return st / 0x7FFFFFFF

    m = Mesh()
    m.add_cylinder((0.5, 0.5, 0.0), 0.28, 0.020, CERAMIC, 14)
    m.add_cylinder((0.5, 0.5, 0.020), 0.24, 0.012, "cream+3", 14)
    for cx, cy in ((0.42, 0.46), (0.58, 0.55)):
        r = 0.10 + rnd() * 0.03
        m.add_prism((cx, cy, 0.032), r, r * 0.72, 0.045, "wood+2", 8)
        m.add_prism((cx, cy, 0.077), r * 0.72, r * 0.52, 0.035, "wood+3", 8)
    return m


def bean_sack(seed: int | None = None) -> Mesh:
    """A sack slumps: wide at the base, cinched at the neck, with the top folded
    over. Three stacked prisms of falling radius, which is what a slump looks
    like once it has been quantized to a 64 px sprite anyway."""
    st = None if seed is None else _mix(seed)

    def rnd():
        nonlocal st
        if st is None:
            return 0.5
        st = _mix(st)
        return st / 0x7FFFFFFF

    m = Mesh()
    base = 0.30 + rnd() * 0.04
    m.add_prism((0.5, 0.5, 0.0), base, base * 0.86, 0.26, "wood+1", 10)
    m.add_prism((0.5, 0.5, 0.26), base * 0.86, base * 0.74, 0.20, "wood+1", 10)
    m.add_prism((0.5, 0.5, 0.46), base * 0.58, base * 0.50, 0.12, "wood", 10)
    m.add_prism((0.5, 0.5, 0.58), base * 0.70, base * 0.60, 0.06, "wood+2", 10)
    m.add_box((0.5 - base * 0.55, 0.5 - base * 0.10, 0.14),
              (0.5 + base * 0.55, 0.5 - base * 0.06, 0.34), "cream+2")  # stencil
    return m


# --- wall and light ----------------------------------------------------------

def wall_art_framed(seed: int | None = None) -> Mesh:
    """A frame, a mount, and a picture. Three concentric value steps: the frame
    dark, the mount at the top of the cream ramp, the picture somewhere else
    entirely -- which is the only way a 12 px rectangle says "art" rather than
    "panel"."""
    st = None if seed is None else _mix(seed)

    def rnd():
        nonlocal st
        if st is None:
            return 0.5
        st = _mix(st)
        return st / 0x7FFFFFFF

    y0, y1 = 0.12, 0.18
    m = Mesh()
    m.add_box((0.10, y0, 0.06), (0.90, y1, 0.94), "wood-1")            # frame
    m.add_box((0.16, y1, 0.12), (0.84, y1 + 0.010, 0.88), "cream+3")   # mount
    hue = ("sky-1", "foliage-1", "rose-1", "wood+1")[int(rnd() * 4) % 4]
    m.add_box((0.22, y1 + 0.010, 0.20), (0.78, y1 + 0.018, 0.80), hue)
    m.add_box((0.22, y1 + 0.018, 0.20), (0.78, y1 + 0.024, 0.42),
              hue.split("-")[0] + "+1")                                # horizon
    return m


def lamp_floor() -> Mesh:
    """A standard lamp: weighted base, thin stem, drum shade with a lit
    underside. The stem has to be thin -- a thick one reads as a column, and the
    gap either side of it is most of the silhouette."""
    m = Mesh()
    m.add_cylinder((0.5, 0.5, 0.0), 0.20, 0.045, "neutral-1", 12)      # base
    m.add_cylinder((0.5, 0.5, 0.045), 0.028, 1.02, METAL, 8)           # stem
    m.add_prism((0.5, 0.5, 1.02), 0.24, 0.24, 0.30, CERAMIC, 12)       # shade
    m.add_prism((0.5, 0.5, 0.995), 0.225, 0.225, 0.03, "cream+3", 12)  # lit rim
    return m


def lamp_table() -> Mesh:
    """The same three parts as `lamp_floor` in different proportion, which is
    what actually separates them: a table lamp is nearly all shade."""
    m = Mesh()
    m.add_cylinder((0.5, 0.5, 0.0), 0.13, 0.035, WOOD, 12)
    m.add_cylinder((0.5, 0.5, 0.035), 0.075, 0.14, CERAMIC, 10)        # body
    m.add_cylinder((0.5, 0.5, 0.175), 0.024, 0.06, METAL, 6)
    m.add_prism((0.5, 0.5, 0.235), 0.21, 0.21, 0.20, CERAMIC, 12)      # shade
    m.add_prism((0.5, 0.5, 0.215), 0.195, 0.195, 0.025, "cream+3", 12)
    return m


def plant_hanging(seed: int = 5) -> Mesh:
    """A pot on a hanger with the foliage trailing DOWNWARD. That direction is
    the entire difference from `leafy_plant`, which grows up -- and it is why
    the pot sits at the top of the sprite rather than the bottom.

    The hook terminating in mid-air is fine here and is not fine in a room
    render: this is a sprite with its own frame, the same way `pendant_lamp`
    already ships one.
    """
    st = _mix(seed)

    def rnd():
        nonlocal st
        st = _mix(st)
        return st / 0x7FFFFFFF

    m = Mesh()
    top = 1.00
    m.add_cylinder((0.5, 0.5, top - 0.04), 0.020, 0.04, METAL, 6)      # hook
    for a in (0.4, 2.5, 4.6):                                          # cords
        strut(m, (0.5, 0.5, top - 0.02),
              (0.5 + math.cos(a) * 0.15, 0.5 + math.sin(a) * 0.15, top - 0.34),
              0.010, METAL)
    m.add_prism((0.5, 0.5, top - 0.42), 0.18, 0.18, 0.08, FABRIC, 10)
    m.add_prism((0.5, 0.5, top - 0.34), 0.20, 0.20, 0.10, FABRIC, 10)  # pot
    m.add_prism((0.5, 0.5, top - 0.25), 0.185, 0.185, 0.02, "wood-2", 10)
    for i in range(7):                                                 # trailers
        a = rnd() * math.tau
        r0 = 0.10 + rnd() * 0.07
        drop = 0.26 + rnd() * 0.34
        x0, y0 = 0.5 + math.cos(a) * r0, 0.5 + math.sin(a) * r0
        x1, y1 = 0.5 + math.cos(a) * (r0 + 0.09), 0.5 + math.sin(a) * (r0 + 0.09)
        strut(m, (x0, y0, top - 0.25), (x1, y1, top - 0.25 - drop), 0.024,
              PLANT if i % 2 else "foliage+1")
    return m
