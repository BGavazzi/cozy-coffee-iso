"""Modular character construction.

Characters are assembled from swappable parts rather than authored whole. That
matters for the manifest maths: 8 customer archetypes as separate meshes is 8
authoring jobs, but as part combinations it is one parts library plus 8 short
specs. The render budget is unchanged; the *authoring* budget collapses.

Part slots are deliberately finer than "body and head", because the parts that
carry recognisability at 46 px are hair silhouette and torso colour far more
than face detail:

    legs · torso · arms · head · hair · accessory

Proportions are chibi-leaning by design. A realistic 7.5-head figure loses its
head to three pixels at this scale; cozy games all push the head toward a
quarter of total height so the character reads at a glance.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from assetlib import merge, transformed
from mesh import Mesh

# Total height in tile units, matching assets.yaml.
H = 1.46

SKIN = "wood"          # wood_3..6 are the flesh tones; see style_bible.yaml


# --- parts -------------------------------------------------------------------

def legs(mat: str, spread: float = 0.105, seated: bool = False) -> Mesh:
    m = Mesh()
    if seated:
        # Thighs forward, shins down: a standing figure parked at seat height
        # reads as standing *on* the chair.
        for sx in (-spread, spread):
            m.add_box((sx - 0.095, -0.34, -0.10), (sx + 0.095, 0.10, 0.04), mat)
            m.add_box((sx - 0.095, -0.34, -0.46), (sx + 0.095, -0.16, -0.10), mat)
            m.add_box((sx - 0.10, -0.40, -0.52), (sx + 0.10, -0.16, -0.44), "neutral")
        return m
    for sx in (-spread, spread):
        m.add_box((sx - 0.095, -0.095, 0.0), (sx + 0.095, 0.095, 0.44), mat)
        m.add_box((sx - 0.105, -0.135, 0.0), (sx + 0.105, 0.095, 0.09), "neutral")
    return m


def torso(mat: str, bulk: float = 1.0) -> Mesh:
    """Chunky by design. A 4:1 height-to-width figure reads as a pole at 40 px;
    cozy games sit nearer 2.5:1."""
    m = Mesh()
    w, d = 0.265 * bulk, 0.175 * bulk
    m.add_box((-w, -d, 0.40), (w, d, 0.94), mat)
    return m


def arms(mat: str, skin: str = SKIN, bulk: float = 1.0) -> Mesh:
    m = Mesh()
    x = 0.265 * bulk + 0.075
    for sx in (-x, x):
        m.add_box((sx - 0.075, -0.075, 0.60), (sx + 0.075, 0.075, 0.92), mat)
        m.add_box((sx - 0.07, -0.07, 0.47), (sx + 0.07, 0.07, 0.61), skin)   # hand
    return m


def head(skin: str = SKIN) -> Mesh:
    m = Mesh()
    m.add_box((-0.085, -0.06, 0.94), (0.085, 0.06, 1.00), skin)             # neck
    m.add_box((-0.215, -0.175, 1.00), (0.215, 0.175, H - 0.03), skin)       # big head
    return m


def hair(style: str, mat: str) -> Mesh:
    """Silhouette is what identifies a character at this size, so styles differ
    in outline rather than in surface detail."""
    m = Mesh()
    top = H - 0.03
    if style == "short":
        m.add_box((-0.235, -0.195, top - 0.15), (0.235, 0.195, top + 0.05), mat)
    elif style == "bob":
        m.add_box((-0.245, -0.205, top - 0.28), (0.245, 0.205, top + 0.05), mat)
        m.add_box((-0.245, 0.12, 1.02), (0.245, 0.205, top - 0.26), mat)
    elif style == "long":
        m.add_box((-0.24, -0.20, top - 0.18), (0.24, 0.20, top + 0.05), mat)
        m.add_box((-0.23, 0.11, 0.82), (0.23, 0.20, top - 0.16), mat)
    elif style == "bun":
        m.add_box((-0.235, -0.195, top - 0.14), (0.235, 0.195, top + 0.05), mat)
        m.add_box((-0.115, 0.14, top - 0.02), (0.115, 0.30, top + 0.16), mat)
    elif style == "cap":
        m.add_box((-0.245, -0.205, top - 0.10), (0.245, 0.205, top + 0.07), mat)
        m.add_box((-0.22, -0.34, top - 0.08), (0.22, -0.18, top - 0.01), mat)  # brim
    elif style == "curly":
        m.add_box((-0.255, -0.215, top - 0.19), (0.255, 0.215, top + 0.08), mat)
        m.add_box((-0.30, -0.17, top - 0.25), (-0.22, 0.17, top - 0.05), mat)
        m.add_box((0.22, -0.17, top - 0.25), (0.30, 0.17, top - 0.05), mat)
    return m


def accessory(kind: str, mat: str) -> Mesh:
    m = Mesh()
    if kind == "apron":
        m.add_box((-0.25, -0.195, 0.30), (0.25, -0.16, 0.86), mat)
        m.add_box((-0.10, -0.195, 0.86), (0.10, -0.165, 0.95), mat)        # bib
    elif kind == "scarf":
        m.add_box((-0.21, -0.18, 0.88), (0.21, 0.18, 0.99), mat)
    elif kind == "bag":
        m.add_box((0.29, -0.08, 0.52), (0.43, 0.12, 0.78), mat)
    elif kind == "cup":
        m.add_box((-0.40, -0.10, 0.52), (-0.28, 0.04, 0.66), mat)
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


def build(spec: CharacterSpec, seated: bool = False) -> Mesh:
    parts = [
        legs(spec.trousers, seated=seated),
        torso(spec.shirt, spec.bulk),
        arms(spec.shirt, spec.skin, spec.bulk),
        head(spec.skin),
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
                        hair_style="bun", hair_mat="wood",
                        accessory_kind="apron", accessory_mat="rose")

# Eight archetypes, all combinations of the same parts library.
CUSTOMERS = [
    CharacterSpec("reader",   shirt="foliage", trousers="wood",    hair_style="bob",
                  hair_mat="neutral", accessory_kind="scarf",  accessory_mat="rose"),
    CharacterSpec("student",  shirt="sky",     trousers="neutral", hair_style="short",
                  hair_mat="wood",    accessory_kind="bag",    accessory_mat="wood"),
    CharacterSpec("regular",  shirt="rose",    trousers="wood",    hair_style="long",
                  hair_mat="wood",    accessory_kind="cup",    accessory_mat="cream"),
    CharacterSpec("commuter", shirt="neutral", trousers="neutral", hair_style="cap",
                  hair_mat="foliage", accessory_kind="bag",    accessory_mat="neutral",
                  bulk=1.12),
    CharacterSpec("artist",   shirt="cream",   trousers="sky",     hair_style="curly",
                  hair_mat="neutral", accessory_kind="scarf",  accessory_mat="foliage"),
    CharacterSpec("elder",    shirt="wood",    trousers="neutral", hair_style="short",
                  hair_mat="cream",   accessory_kind=None,     bulk=1.08),
    CharacterSpec("writer",   shirt="sky",     trousers="wood",    hair_style="bun",
                  hair_mat="neutral", accessory_kind="cup",    accessory_mat="cream"),
    CharacterSpec("friend",   shirt="foliage", trousers="rose",    hair_style="bob",
                  hair_mat="wood",    accessory_kind=None),
]
