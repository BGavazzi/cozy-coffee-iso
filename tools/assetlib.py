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
WOOD, CERAMIC, PLANT, FABRIC, METAL, GLASS = (
    "wood", "cream", "foliage", "rose", "neutral", "sky")


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
    m = Mesh()
    if not checker:
        m.add_box((0, 0, -0.06), (w, d, 0.0), tone_a)
        return m
    for x in range(w):
        for y in range(d):
            m.add_box((x, y, -0.06), (x + 1, y + 1, 0.0),
                      tone_a if (x + y) % 2 == 0 else tone_b)
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
            m.add_box((x0 + i, y0, 0.5), (x0 + i + 1, y0 + t, height), CERAMIC)
        else:
            m.add_box((x0, y0 + i, 0), (x0 + t, y0 + i + 1, 0.5), WOOD)
            m.add_box((x0, y0 + i, 0.5), (x0 + t, y0 + i + 1, height), CERAMIC)
    return m


# --- props -------------------------------------------------------------------

def counter(kick=True) -> Mesh:
    """Modular: the body spans the FULL tile so a run tiles seamlessly.
    Insetting it left a seam between every adjacent module."""
    m = Mesh()
    m.add_box((0.0, 0.06, 0.10), (1.0, 0.94, 0.82), WOOD)       # carcass, full width
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
    m.add_box((0.10, 0.15, 0.66), (1.90, 0.85, 0.72), GLASS)        # glass rim only
    m.add_box((0.10, 0.15, 0.40), (0.14, 0.85, 0.66), GLASS)
    m.add_box((1.86, 0.15, 0.40), (1.90, 0.85, 0.66), GLASS)
    return m


def table_round() -> Mesh:
    m = Mesh()
    m.add_cylinder((0.5, 0.5, 0.0), 0.13, 0.58, WOOD, 12)       # thicker column
    m.add_cylinder((0.5, 0.5, 0.58), 0.44, 0.11, WOOD, 20)      # thicker top
    m.add_cylinder((0.5, 0.5, 0.0), 0.30, 0.06, WOOD, 14)       # base
    return m


def table_4top() -> Mesh:
    m = Mesh()
    m.add_box((0.05, 0.05, 0.58), (1.95, 0.95, 0.70), WOOD)
    for cx, cy in ((0.22, 0.18), (1.78, 0.18), (0.22, 0.82), (1.78, 0.82)):
        m.add_box((cx - 0.085, cy - 0.085, 0), (cx + 0.085, cy + 0.085, 0.58), WOOD)
    return m


def chair(cushion=None) -> Mesh:
    m = Mesh()
    m.add_box((0.20, 0.20, 0.40), (0.80, 0.80, 0.52), WOOD)     # seat, thicker
    m.add_box((0.20, 0.66, 0.52), (0.80, 0.80, 1.00), WOOD)     # back, taller
    for cx, cy in ((0.28, 0.28), (0.72, 0.28), (0.28, 0.72), (0.72, 0.72)):
        m.add_box((cx - 0.075, cy - 0.075, 0), (cx + 0.075, cy + 0.075, 0.40), WOOD)
    if cushion:
        m.add_box((0.23, 0.23, 0.52), (0.77, 0.77, 0.58), cushion)
    return m


def stool() -> Mesh:
    m = Mesh()
    m.add_cylinder((0.5, 0.5, 0.62), 0.24, 0.08, FABRIC, 14)
    m.add_cylinder((0.5, 0.5, 0.0), 0.07, 0.62, METAL, 10)
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
    stuff on them."""
    m = Mesh()
    if kind == "cafe":
        m.add_cylinder((0.42, 0.46, 0.0), 0.115, 0.02, CERAMIC, 12)   # saucer
        m.add_cylinder((0.42, 0.46, 0.02), 0.075, 0.115, CERAMIC, 12)  # cup
        m.add_cylinder((0.62, 0.40, 0.0), 0.055, 0.09, CERAMIC, 10)    # second cup
        m.add_box((0.30, 0.62, 0.0), (0.50, 0.76, 0.05), FABRIC)       # napkin
        m.add_box((0.60, 0.62, 0.0), (0.70, 0.70, 0.10), WOOD)         # caddy
    elif kind == "work":
        m.add_box((0.26, 0.34, 0.0), (0.66, 0.62, 0.03), METAL)        # laptop base
        m.add_box((0.26, 0.60, 0.03), (0.66, 0.64, 0.30), GLASS)       # screen
        m.add_cylinder((0.74, 0.42, 0.0), 0.07, 0.12, CERAMIC, 10)
    elif kind == "books":
        m.add_box((0.28, 0.36, 0.0), (0.62, 0.64, 0.06), FABRIC)
        m.add_box((0.30, 0.38, 0.06), (0.60, 0.62, 0.11), CERAMIC)
        m.add_cylinder((0.72, 0.48, 0.0), 0.075, 0.12, CERAMIC, 10)
    elif kind == "counter":
        for cx in (0.24, 0.44, 0.64):
            m.add_cylinder((cx, 0.5, 0.0), 0.055, 0.09, CERAMIC, 8)
    return m
