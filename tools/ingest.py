#!/usr/bin/env python3
"""Bind an arbitrary mesh to the palette and the tile grid.

This is the seam where stages 1-3 attach. `PIPELINE.md` has always said stage 5
"consumes OBJ meshes", and that has always been true of meshes this repo wrote
itself, whose `usemtl` tokens are already palette materials like `wood-2`. It is
not true of anything a generator produces. A mesh out of TRELLIS arrives with

  - vertex colours or an MTL full of arbitrary RGB, not ramp references,
  - Y-up, because almost everything upstream of a game engine is,
  - an arbitrary scale and origin, centred on nothing in particular.

Every one of those is a hard stop for the rest of the pipeline, and none of them
needs a GPU to solve, so the adapter can be built and tested now against meshes
this repo already has. That is the point of building it: stages 1-3 stop being
hypothetical and become a thing that can be plugged in.

    python tools/ingest.py mesh.obj --height 0.9 --up y -o out.obj
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mesh import Mesh, load_obj, save_obj  # noqa: E402
from oklab import oklab_to_srgb255, srgb_to_oklab  # noqa: E402
from pixelize import load_palette, material as split_material  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# A source colour further than this from every step of its chosen ramp is not
# being represented, it is being replaced. Measured in OKLab dE, where 0.02 is
# roughly a just-noticeable difference on a flat field.
MAX_BIND_DE = 0.16

# Ramps a bound colour may land on. The spot accents are excluded on purpose:
# they are 1-step emissive ramps meaning "this thing is a light source", and
# nothing should acquire that by being coincidentally the right yellow.
BINDABLE = ("wood", "cream", "foliage", "rose", "sky", "neutral")


def _to_segment(p, a, b) -> float:
    """Distance from a point to a segment, in OKLab."""
    ab = [b[i] - a[i] for i in range(3)]
    denom = sum(c * c for c in ab)
    if denom < 1e-12:
        return math.dist(p, a)
    t = sum((p[i] - a[i]) * ab[i] for i in range(3)) / denom
    t = max(0.0, min(1.0, t))
    return math.dist(p, [a[i] + t * ab[i] for i in range(3)])


def ramp_distance(rgb_lab, ramps: dict, name: str) -> float:
    """How far a colour sits from a ramp, treated as a curve rather than a set.

    A ramp is a path through OKLab, not six unrelated colours, and "which ramp
    is this?" is a question about the path. Measuring to the nearest *step*
    instead is what broke the previous version: it matched a dark brown against
    `cream`'s darkest step, which sits at L 0.72 against the source's L 0.31,
    and then compared chromaticity between two colours 0.41 apart in lightness.
    A ramp that cannot reach the source's lightness was scoring as though it
    could. Distance to the polyline charges for that gap, because the nearest
    point on a curve that stops short IS its endpoint.
    """
    labs = [srgb_to_oklab(c) for c in ramps[name]]
    if len(labs) == 1:
        return math.dist(rgb_lab, labs[0])
    return min(_to_segment(rgb_lab, labs[i], labs[i + 1])
               for i in range(len(labs) - 1))


def bind_colour(rgb, ramps: dict, bindable=BINDABLE) -> tuple[str, float]:
    """Pick the palette material closest to an arbitrary colour.

    Ramp by distance to the ramp's CURVE, step by lightness within it.

    What this deliberately is not is nearest-colour-overall. Everything
    downstream is built on one material meaning one ramp -- grain resolves by
    ramp, tone offsets compose within a ramp, `check_palette_spread` counts
    ramps per character -- so the ramp has to be chosen as an identity and the
    step as a shade of it. Choosing by nearest step would let a colour that
    happens to coincide with one step of the wrong ramp beat the ramp it
    actually belongs to.

    Three versions to get here, and each failure is worth keeping:

    Matching hue angles, with anything under a chroma threshold forced to
    `neutral`. Wrong because `neutral` in this palette is not achromatic -- it
    is a cool violet-grey at chroma 0.016-0.022, so a threshold near its own
    chroma swallows every quiet colour. A warm off-white bound to `neutral+2`
    at dE 0.124 with `cream` two steps away.

    Comparing each ramp's chroma-weighted mean (a, b). Fixed the off-white and
    broke dark colours, because chroma is a function of lightness: a dark brown
    carries a third the chroma of a mid brown, so it scored nearer pale `cream`
    than `wood`.

    Comparing (a, b) at each ramp's nearest step in lightness. Still bound
    (60, 45, 35) to `cream-2` at dE 0.408, because `cream` has no dark end --
    its "nearest" step was 0.41 away in L, and a ramp that cannot reach the
    source's lightness was competing as though it could.

    Returns the material token and the OKLab distance it landed at, so a caller
    can tell representation from replacement.
    """
    src = srgb_to_oklab(tuple(int(c) for c in rgb))
    best = min(bindable, key=lambda n: ramp_distance(src, ramps, n))
    labs = [srgb_to_oklab(c) for c in ramps[best]]
    k = min(range(len(labs)), key=lambda i: abs(labs[i][0] - src[0]))
    de = math.dist(labs[k], src)
    # Ramps run dark to light and a material token's offset is measured from
    # the ramp's own name, which is its middle step.
    off = k - len(labs) // 2
    return (best if off == 0 else f"{best}{off:+d}"), de


def read_mtl(path: Path | str) -> dict:
    """`newmtl` name -> Kd as 0-255 RGB. Kd only; Ka and Ks are lighting."""
    out, cur = {}, None
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        p = line.split()
        if not p:
            continue
        if p[0] == "newmtl":
            cur = p[1]
        elif p[0] == "Kd" and cur:
            out[cur] = tuple(int(round(min(1.0, max(0.0, float(v))) * 255))
                             for v in p[1:4])
    return out


def orient(mesh: Mesh, up: str = "z") -> Mesh:
    """Bring a mesh into the pipeline's Z-up convention.

    Y-up is what almost everything upstream of a game engine emits, and getting
    it wrong is not subtle -- the object lies on its face -- so this is a flag
    rather than a guess. What is worth being careful about is handedness:
    rotating Y-up to Z-up by negating a component instead of swapping mirrors
    the mesh, and a mirrored asset renders perfectly right up until it is a
    character with a bag on the wrong shoulder in half of its directions.
    """
    if up == "z":
        return mesh
    if up != "y":
        raise ValueError(f"up must be 'y' or 'z', got {up!r}")
    out = Mesh()
    out.verts = [(v[0], -v[2], v[1]) for v in mesh.verts]
    out.normals = [(n[0], -n[2], n[1]) for n in mesh.normals]
    out.faces = list(mesh.faces)
    out.vcolors = list(mesh.vcolors)
    return out


def fit(mesh: Mesh, height: float | None = None,
        footprint: float | None = None) -> tuple[Mesh, dict]:
    """Sit the mesh on z=0, centre its footprint on a tile, and scale it.

    A generated mesh is centred on whatever its generator felt like, at whatever
    scale. `Layout` places things by their footprint on a 1.0 tile, and every
    placement, collision test and grounding check in the repo assumes both.

    Scaling by HEIGHT rather than by the longest axis is deliberate: a chair and
    a table are told apart by how tall they are relative to a person, and
    normalising a bounding cube instead would make a wide table short.
    """
    xs = [v[0] for v in mesh.verts]
    ys = [v[1] for v in mesh.verts]
    zs = [v[2] for v in mesh.verts]
    if not xs:
        return mesh, {"scale": 1.0, "height": 0.0, "footprint": 0.0}
    wide = max(max(xs) - min(xs), max(ys) - min(ys)) or 1e-9
    tall = (max(zs) - min(zs)) or 1e-9
    if height is not None:
        s = height / tall
    elif footprint is not None:
        s = footprint / wide
    else:
        s = 1.0
    cx, cy, z0 = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, min(zs)
    out = Mesh()
    out.verts = [((v[0] - cx) * s + 0.5, (v[1] - cy) * s + 0.5, (v[2] - z0) * s)
                 for v in mesh.verts]
    out.normals = list(mesh.normals)
    out.faces = list(mesh.faces)
    # Carried through every rebuild. Both of these functions construct a fresh
    # Mesh and copied three of its four fields, so the vertex colours survived
    # the reader and were dropped in transit -- the ingest path then fell
    # through to the MTL branch and bound an entire teapot to `neutral`
    # without a word. Adding a field to a dataclass adds it to every place
    # that reconstructs one.
    out.vcolors = list(mesh.vcolors)
    fx, fy = (max(xs) - min(xs)) * s, (max(ys) - min(ys)) * s
    # `footprint` stays the single scalar callers already read (the CLI
    # printout, `assets.yaml`'s convention of one number for round objects).
    # `footprint_xy` is the pair `Layout` actually needs: a mesh scaled by
    # HEIGHT is not generally square in plan, and collapsing an oval basket's
    # 0.34 x 0.23 footprint to one number of either value is a placement bug
    # waiting for a long thin object.
    return out, {"scale": s, "height": tall * s, "footprint": wide * s,
                "footprint_xy": [fx, fy]}


def _is_palette(mat: str) -> bool:
    try:
        split_material(mat)
        return True
    except (KeyError, ValueError):
        return False


def rebind(mesh: Mesh, colours: dict, ramps: dict):
    """Rewrite every face's material as a palette token."""
    table, warns = {}, []
    for name, rgb in colours.items():
        mat, de = bind_colour(rgb, ramps)
        table[name] = (mat, de)
        if de > MAX_BIND_DE:
            warns.append(f"{name} {tuple(rgb)} -> {mat} at dE {de:.3f} "
                         f"(limit {MAX_BIND_DE:.2f}) -- the palette does not "
                         f"contain this colour, so this is replacement rather "
                         f"than representation")
    out = Mesh()
    out.verts = list(mesh.verts)
    out.normals = list(mesh.normals)
    unknown = set()
    for tri, nrm, mat in mesh.faces:
        if mat in table:
            out.faces.append((tri, nrm, table[mat][0]))
        elif _is_palette(mat):
            out.faces.append((tri, nrm, mat))          # already one of ours
        else:
            unknown.add(mat)
            out.faces.append((tri, nrm, "neutral"))
    for u in sorted(unknown):
        warns.append(f"{u!r} has no colour in the MTL and is not a palette "
                     f"material; bound to neutral")
    return out, sorted((k, v[0], round(v[1], 3)) for k, v in table.items()), warns


def palette_rgb(mat: str, ramps: dict) -> tuple:
    """The RGB a palette material resolves to at its own ramp position.

    Only used to build the round-trip fixture, but it has to agree with what
    the shader does or the fixture proves nothing.
    """
    ramp, off = split_material(mat)
    steps = ramps[ramp]
    return steps[max(0, min(len(steps) - 1, len(steps) // 2 + off))]


def check_roundtrip(assets=None, ramps=None) -> list[str]:
    """Ingesting a colour the palette already contains must return that colour.

    This is the strongest thing that can be said about the binder without a
    generated mesh to feed it, and it is exhaustive rather than sampled: every
    step of every bindable ramp is a colour the palette definitely contains, so
    each one has exactly one correct answer. A binder that mis-assigns a ramp
    fails here immediately -- pointed at a stub that answers `neutral` for
    everything it reports 36 of 37.

    An earlier version of this walked ten library assets instead, which covered
    22 of the 37 steps. That is the wrong instrument for the same reason the
    generator sheet was: it tests what the library happens to use rather than
    what the binder is claimed to handle, so the fifteen steps nothing currently
    paints with would have gone unchecked until something did.

    The library walk is kept as a second, different assertion: every material
    named anywhere in `assetlib` has to be a legal palette token. That is not
    about the binder at all -- it catches a typo in a material name, which
    otherwise surfaces as a `KeyError` deep inside a render.

    Offsets are compared after clamping, because `wood-3` and `wood-4` both
    resolve to the darkest step of a 7-step ramp: the round trip cannot recover
    which was written and does not need to.
    """
    ramps = ramps or load_palette()
    out = []
    for name in BINDABLE:
        steps = ramps[name]
        for i, rgb in enumerate(steps):
            got, de = bind_colour(rgb, ramps)
            want = name if i == len(steps) // 2 else f"{name}{i - len(steps) // 2:+d}"
            if palette_rgb(got, ramps) != tuple(rgb):
                out.append(f"palette {want} {tuple(rgb)} binds to {got} = "
                           f"{palette_rgb(got, ramps)} (dE {de:.3f})")

    if assets is None:
        import assetlib as A
        assets = {"floor": A.floor(2, 2), "counter": A.counter(seed=1),
                  "chair": A.chair(seed=3, cushion="rose"),
                  "table": A.table_4top(seed=2), "plant": A.plant_large(seed=1),
                  "bookshelf": A.bookshelf(seed=4), "crate": A.crate(),
                  "menu": A.menu_board(), "espresso": A.espresso_machine(),
                  "pastry": A.pastry_case()}
    for name, mesh in assets.items():
        for mat in sorted({m for _t, _n, m in mesh.faces}):
            if not _is_palette(mat):
                out.append(f"{name}: {mat!r} is not a palette material")
    return out


def signed_volume(mesh: Mesh) -> float:
    """Six times the sum of tetrahedron volumes over the origin.

    The only cheap way to detect a mirrored mesh. Bounds, height, footprint and
    materials are all identical between a mesh and its reflection, so every
    other assertion in `check_transform` passes on one -- and a mirrored asset
    renders perfectly right up until it is a character with a bag on the wrong
    shoulder in half of its directions, or a counter whose service side faces
    the wall. Reflection flips the sign of every tetrahedron, so it flips this.
    """
    tot = 0.0
    for tri, _n, _m in mesh.faces:
        a, b, c = (mesh.verts[i] for i in tri)
        tot += (a[0] * (b[1] * c[2] - b[2] * c[1])
                - a[1] * (b[0] * c[2] - b[2] * c[0])
                + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6.0
    return tot


def check_transform(ramps=None) -> list[str]:
    """A full pass over a mesh that looks like something a generator emitted.

    The binder can be right while the adapter is still useless, because a mesh
    arriving from stage 3 is wrong in three independent ways at once and each
    correction can break the next. So this builds the adversarial case -- a
    library chair written out Y-up, scaled 37x, shifted off the origin, and
    with every palette material renamed to `Material_007` and pushed out to an
    MTL as raw RGB -- and asserts the four properties the rest of the pipeline
    depends on:

      it comes back Z-up and sitting on z=0, because `grounded` says so;
      centred on the tile, because `Layout` places by footprint;
      at the height asked for, because scale is what tells a chair from a table;
      carrying the materials it started with, because the binder is exact on
      colours the palette contains;
      and NOT mirrored, which none of the other four can see, since a
      reflection has the same bounds, the same height and the same materials.

    Round-tripping through a real file rather than calling the pieces directly
    is the point: `load_obj`, `read_mtl` and the OBJ's 1-based indices are all
    part of the seam, and a fixture that skipped them would be testing the easy
    half.
    """
    import tempfile
    import assetlib as A
    ramps = ramps or load_palette()
    src = A.chair(seed=3, cushion="rose")
    mats = sorted({m for _t, _n, m in src.faces})
    names = {m: f"Material_{i:03d}" for i, m in enumerate(mats)}
    scale, want_h = 37.0, 0.98

    out = []
    with tempfile.TemporaryDirectory() as td:
        obj, mtl = Path(td) / "gen.obj", Path(td) / "gen.mtl"
        lines = ["mtllib gen.mtl"]
        # z-up -> y-up, scaled, and shifted somewhere arbitrary.
        lines += [f"v {v[0] * scale + 120:.6f} {v[2] * scale - 8:.6f} "
                  f"{-v[1] * scale + 55:.6f}" for v in src.verts]
        cur = None
        for tri, _n, m in src.faces:
            if m != cur:
                lines.append(f"usemtl {names[m]}")
                cur = m
            lines.append(f"f {tri[0] + 1} {tri[1] + 1} {tri[2] + 1}")
        obj.write_text("\n".join(lines) + "\n", encoding="utf-8")
        mtl.write_text("\n".join(
            f"newmtl {names[m]}\nKd " + " ".join(
                f"{c / 255:.6f}" for c in palette_rgb(m, ramps))
            for m in mats) + "\n", encoding="utf-8")

        mesh, rep = ingest(obj, up="y", height=want_h)

    zs = [v[2] for v in mesh.verts]
    xs = [v[0] for v in mesh.verts]
    ys = [v[1] for v in mesh.verts]
    if abs(min(zs)) > 1e-6:
        out.append(f"ingested mesh does not sit on the floor: z0 = {min(zs):.4f}")
    for axis, lo, hi in (("x", min(xs), max(xs)), ("y", min(ys), max(ys))):
        if abs((lo + hi) / 2 - 0.5) > 1e-6:
            out.append(f"ingested mesh is not centred on its tile in {axis}: "
                       f"{lo:.3f}..{hi:.3f}")
    if abs((max(zs) - min(zs)) - want_h) > 1e-6:
        out.append(f"ingested mesh height {max(zs) - min(zs):.4f}, asked {want_h}")
    got = {m for _t, _n, m in mesh.faces}
    if got != set(mats):
        out.append(f"materials did not survive the round trip: {sorted(got)} "
                   f"from {mats}")
    if signed_volume(mesh) <= 0.0:
        out.append(f"ingested mesh is inside out or mirrored: signed volume "
                   f"{signed_volume(mesh):+.5f}, expected positive")
    out += [f"unexpected warning: {w}" for w in rep["warnings"]]
    return out


# How coarsely vertex colours are grouped before binding. A generated mesh has
# one colour per vertex and no two are alike, so binding each face's average
# independently is a hundred thousand ramp searches. Rounding to a 5-bit cube
# collapses that to a few thousand distinct keys with a quantization error of
# about 0.004 in sRGB -- an order of magnitude below `MAX_BIND_DE`, and the
# result is going onto a 37-colour palette regardless.
COLOUR_BUCKET = 8

# Every one of the thirty meshes in `assetlib` has an albedo median lightness
# between 0.596 and 0.845 in OKLab L. Not most of them -- all of them, and
# seventeen of the thirty sit on 0.600 exactly, because the library is authored
# out of ramp middles. That is not a coincidence to be preserved for its own
# sake; it is what "the renderer supplies the shading" means in numbers.
ALBEDO_L_FLOOR = 0.596
ALBEDO_L_CEIL = 0.845
# The modal authored value, and the middle step of both `wood` and `neutral`.
ALBEDO_L_TARGET = 0.600


def delight(vcolors, target: float = ALBEDO_L_TARGET):
    """Shift a reconstructed colour field back to albedo. Returns (colours, before).

    A photograph is albedo times lighting and a reconstructor cannot separate
    them, so TripoSR's vertex colours arrive with the concept image's key light
    already multiplied in. Binding those to the palette and then rendering runs
    the lighting twice: `bind_colour` picks the ramp step nearest the source's
    lightness, so a lit ceramic pot is bound at the pot's *lit* value and then
    lambert-shaded again on top. The first teapot through this seam came out a
    near-black blob with the right silhouette.

    What is corrected is the median and nothing else, because measurement says
    only the median is wrong:

        teapot field   L p50 0.408   p05-p95 band 0.481
        authored props L p50 0.596-0.845  band 0.000-0.585

    The band is comfortably inside the range thirty authored props occupy -- an
    espresso machine is busier -- so compressing it would be destroying real
    two-tone structure to fix a problem it does not have. The median is 0.188
    below a floor that no authored prop goes near. So this is a shift, not a
    normalisation, and the internal contrast the reconstructor recovered
    survives it intact.

    Clamping at the ends is the one nonlinearity, and it costs something: a
    field whose top already sits near white loses separation up there. Measured
    on the teapot the shift is +0.192 and p95 lands at 0.911, under the
    palette's own 0.969 ceiling, so nothing clips. A field that does clip will
    say so through `check_albedo_centre`, which reads the result rather than
    the intent.
    """
    labs = [srgb_to_oklab(c) for c in vcolors]
    Ls = sorted(l[0] for l in labs)
    before = Ls[len(Ls) // 2]
    shift = target - before
    out = [oklab_to_srgb255(min(1.0, max(0.0, L + shift)), a, b)
           for L, a, b in labs]
    return out, before


def check_albedo_centre(mesh: Mesh, ramps: dict) -> list[str]:
    """Is the bound albedo where authored albedo lives?

    Reads the materials a mesh actually ended up with, so it catches a bad
    `delight` and a bad MTL by the same route, and it is the reading that turns
    "the sprite looks wrong" into a number. The bracket is wide and measured:
    a defect at 0.408 against a weakest known-good at 0.596.
    """
    Ls = []
    for _, _, mat in mesh.faces:
        if _is_palette(mat):
            Ls.append(srgb_to_oklab(palette_rgb(mat, ramps))[0])
    if not Ls:
        return []
    Ls.sort()
    p50 = Ls[len(Ls) // 2]
    if ALBEDO_L_FLOOR <= p50 <= ALBEDO_L_CEIL:
        return []
    side = "dark" if p50 < ALBEDO_L_FLOOR else "light"
    return [f"bound albedo median L {p50:.3f} is too {side}; every authored "
            f"prop lands in {ALBEDO_L_FLOOR:.3f}-{ALBEDO_L_CEIL:.3f}. A "
            f"reconstructed colour field carries the concept image's lighting "
            f"and has to be de-lit before binding, or the renderer shades it "
            f"twice."]


def bind_vertex_colours(mesh: Mesh, ramps: dict):
    """Per-vertex colour -> a palette material per face.

    This is the half of the seam that had never met a real generator. `ingest`
    was written against an MTL full of arbitrary RGB, because that is what the
    docstring predicted TRELLIS would emit. TripoSR emits neither MTL nor
    `usemtl`: it writes colour on the vertices, and a reader that takes only
    the first three floats of a `v` line turns a two-tone teapot into one
    uniform material without failing anything.

    A face gets the mean of its three vertices, which is what the rasteriser
    would show at this scale anyway -- the pipeline flattens each triangle to
    one ramp step, so per-vertex interpolation has nowhere to go.
    """
    cache, worst, table = {}, 0.0, {}
    vcolors, before = delight(mesh.vcolors)
    if abs(before - ALBEDO_L_TARGET) >= 0.02:
        print(f"  de-lit: albedo median L {before:.3f} -> "
              f"{ALBEDO_L_TARGET:.3f}")
    out = Mesh()
    out.verts = list(mesh.verts)
    out.normals = list(mesh.normals)
    out.vcolors = list(vcolors)
    for tri, nrm, _ in mesh.faces:
        rgb = tuple(sum(vcolors[i][k] for i in tri) // 3
                    for k in range(3))
        key = tuple(c // COLOUR_BUCKET for c in rgb)
        if key not in cache:
            cache[key] = bind_colour(rgb, ramps)
        mat, de = cache[key]
        worst = max(worst, de)
        n, d = table.get(mat, (0, 0.0))
        table[mat] = (n + 1, max(d, de))
        out.faces.append((tri, nrm, mat))
    return out, table, worst


def mesh_geometry(mesh: Mesh) -> dict:
    """Read footprint, height and anchor off an already-fit mesh's own bounds.

    `fit()` returns this dict for the mesh it just built, in the same process.
    A render happening later -- `render_batch --mesh out/mesh/teapot_bound.obj`
    is a separate invocation loading a file off disk -- has no way to see that
    dict, and re-deriving it from the mesh's bounds is exact rather than
    approximate: `fit` centres a mesh on (0.5, 0.5) and rests it on z=0 by
    construction, so those numbers are recoverable from any mesh that went
    through it, not just the one still in memory.
    """
    xs = [v[0] for v in mesh.verts]
    ys = [v[1] for v in mesh.verts]
    zs = [v[2] for v in mesh.verts]
    if not xs:
        return {"height": 0.0, "footprint": 0.0, "footprint_xy": [0.0, 0.0],
                "anchor": [0.5, 0.5, 0.0], "walkable": False}
    fx, fy = max(xs) - min(xs), max(ys) - min(ys)
    return {
        "height": max(zs) - min(zs),
        "footprint": max(fx, fy),
        "footprint_xy": [fx, fy],
        # Fixed by `fit()`'s own construction, not measured -- every ingested
        # mesh is centred on its tile and rests on z=0, so this is the same
        # tuple for anything that came through the seam.
        "anchor": [0.5, 0.5, 0.0],
        # Not a measurable geometric fact. Every subject this factory has
        # produced is a physical object a customer would walk around, and
        # `assets.yaml`'s own convention reserves `walkable` for the `floor`
        # category (h: 0) exclusively -- so `False` is the correct default for
        # every prop this seam has ever seen, not a placeholder standing in
        # for a computation that belongs here later.
        "walkable": False,
    }


def ingest(obj: Path | str, mtl: Path | str | None = None, up: str = "z",
           height: float | None = None, footprint: float | None = None):
    ramps = load_palette()
    mesh = load_obj(obj, default_material="__unbound__")
    colours = read_mtl(mtl) if mtl else {}
    if not colours:
        beside = Path(obj).with_suffix(".mtl")
        if beside.exists():
            colours = read_mtl(beside)
    mesh = orient(mesh, up)
    mesh, geom = fit(mesh, height, footprint)
    geom["anchor"] = [0.5, 0.5, 0.0]
    geom["walkable"] = False

    # Vertex colours only when there is nothing better. An MTL names materials,
    # and a name survives a rebind in a way an averaged triangle colour does
    # not, so it wins wherever both exist.
    if not colours and mesh.vcolors and len(mesh.vcolors) == len(mesh.verts):
        mesh, hist, worst = bind_vertex_colours(mesh, ramps)
        warns = []
        if worst > MAX_BIND_DE:
            warns.append(f"worst vertex-colour bind is dE {worst:.3f} "
                         f"(limit {MAX_BIND_DE:.2f}) -- the palette does not "
                         f"contain some of this mesh's colour, so that part "
                         f"is replacement rather than representation")
        table = sorted((m, f"{n} faces", d) for m, (n, d) in hist.items())
        warns += check_albedo_centre(mesh, ramps)
        return mesh, {"geometry": geom, "bindings": table, "warnings": warns}

    mesh, table, warns = rebind(mesh, colours, ramps)
    warns += check_albedo_centre(mesh, ramps)
    return mesh, {"geometry": geom, "bindings": table, "warnings": warns}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("obj")
    ap.add_argument("--mtl")
    ap.add_argument("--up", default="z", choices=("y", "z"))
    ap.add_argument("--height", type=float)
    ap.add_argument("--footprint", type=float)
    ap.add_argument("-o", "--out")
    args = ap.parse_args()

    mesh, report = ingest(args.obj, args.mtl, args.up, args.height,
                          args.footprint)
    g = report["geometry"]
    print(f"{len(mesh.verts)} verts, {len(mesh.faces)} tris")
    print(f"  scaled x{g['scale']:.4f} -> height {g['height']:.3f}, "
          f"footprint {g['footprint']:.3f}")
    for name, mat, de in report["bindings"]:
        print(f"  {name:20s} -> {mat:12s} dE {de:.3f}")
    for w in report["warnings"]:
        print(f"  warning {w}")
    if args.out:
        save_obj(mesh, args.out)
        print(f"wrote {args.out}")
    return 1 if report["warnings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
