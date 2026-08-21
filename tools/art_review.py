#!/usr/bin/env python3
"""Review a sprite against the style bible and report actionable feedback.

This is a critic, not a gate and not a generator. It does not care who or what
made the art -- hand-pixelled, AI-generated, or rendered. It reads an image and
says what is inconsistent with the spec, where, and what to do about it.

Deliberately *not* pass/fail. A blocker is worth fixing; a note may well be the
right artistic call and the tool simply cannot tell. Severity is a claim about
confidence, not about authority.

    python tools/art_review.py sprite.png [more.png ...] [--json]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from oklab import delta_e, srgb_to_oklab  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

BLOCKER, WARNING, NOTE = "blocker", "warning", "note"
ORDER = {BLOCKER: 0, WARNING: 1, NOTE: 2}


class Finding(dict):
    def __init__(self, severity, check, message, fix, where=None):
        super().__init__(severity=severity, check=check, message=message,
                         fix=fix, where=where)


def load_palette(path: Path | None = None):
    entries = json.loads((path or ROOT / "palette" / "palette.json")
                         .read_text(encoding="utf-8"))
    by_rgb = {tuple(e["rgb"]): e for e in entries}
    ramps: dict[str, list] = {}
    for e in sorted(entries, key=lambda e: (e["ramp"], e["index"])):
        ramps.setdefault(e["ramp"], []).append(tuple(e["rgb"]))
    return by_rgb, ramps, entries


# --- checks -----------------------------------------------------------------

def check_alpha(px, w, h) -> list[Finding]:
    partial = [(i % w, i // w) for i, p in enumerate(px) if 0 < p[3] < 255]
    if not partial:
        return []
    return [Finding(
        BLOCKER, "alpha",
        f"{len(partial)} pixels are semi-transparent; spec requires 1-bit alpha",
        "Threshold alpha at 50%. Usually caused by exporting with antialiasing "
        "on, or by scaling the sprite with a filter other than nearest-neighbour.",
        partial[:8])]


def check_palette(px, w, by_rgb, entries) -> list[Finding]:
    solid = [p[:3] for p in px if p[3] == 255]
    if not solid:
        return []
    off = Counter(c for c in solid if c not in by_rgb)
    if not off:
        return []

    labs = [(tuple(e["rgb"]), srgb_to_oklab(tuple(e["rgb"])), e["name"]) for e in entries]
    suggestions = []
    for colour, n in off.most_common(6):
        lab = srgb_to_oklab(colour)
        rgb, _, name = min(labs, key=lambda t: delta_e(lab, t[1]))
        d = delta_e(lab, srgb_to_oklab(rgb))
        suggestions.append(f"#{colour[0]:02x}{colour[1]:02x}{colour[2]:02x} "
                           f"({n}px) -> {name} #{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x} "
                           f"[dE {d:.3f}]")

    total = sum(off.values())
    pct = 100.0 * total / len(solid)
    sev = BLOCKER if pct > 2.0 else WARNING
    return [Finding(
        sev, "palette",
        f"{len(off)} off-palette colours across {total}px ({pct:.1f}% of the sprite)",
        "Remap to the nearest legal entry: " + "; ".join(suggestions),
    )]


def check_ramp_coherence(px, w, ramps) -> list[Finding]:
    """Look for shading that wanders between ramps.

    A surface shaded along its own ramp keeps neighbouring pixels within that
    ramp; steps change, the family does not. Shading that was matched to the
    nearest palette colour instead wanders across families as the gradient
    moves, which raises the rate at which adjacent pixels belong to different
    ramps.

    Important limit: from pixels alone this cannot *prove* contamination. A
    deliberately grey cup and a contaminated cream one are identical bytes. The
    check reports suspicion and names the evidence; the artist decides.
    """
    member = {c: name for name, ramp in ramps.items() for c in ramp}
    grid = {(i % w, i // w): member[p[:3]]
            for i, p in enumerate(px) if p[3] == 255 and p[:3] in member}
    if len(grid) < 40:
        return []

    per_ramp = Counter(grid.values())
    cross = total = 0
    for (x, y), r in grid.items():
        for dx, dy in ((1, 0), (0, 1)):
            n = grid.get((x + dx, y + dy))
            if n is None:
                continue
            total += 1
            cross += n != r
    rate = cross / max(1, total)

    out = []
    if rate > 0.045:
        out.append(Finding(
            WARNING, "ramp-coherence",
            f"cross-ramp adjacency is {rate:.1%} "
            f"(clean toon shading measures ~2.5%); ramps present: {dict(per_ramp)}",
            "Shading appears to wander between colour families rather than "
            "staying on one ramp. Typical cause is matching shaded pixels to the "
            "nearest palette colour instead of picking a step of the surface's "
            "own ramp. Ignore if the surface is genuinely multi-material.",
        ))

    minor = {r: n for r, n in per_ramp.items() if n / len(grid) < 0.02}
    if minor:
        out.append(Finding(
            NOTE, "ramp-coherence",
            "ramps used by under 2% of pixels: " +
            ", ".join(f"{r} ({n}px)" for r, n in sorted(minor.items())),
            "Often stray pixels rather than a choice. Harmless if intentional.",
        ))
    if len(per_ramp) > 4:
        out.append(Finding(
            NOTE, "ramp-coherence",
            f"sprite spans {len(per_ramp)} ramps: {dict(per_ramp)}",
            "Props usually read better on 2-3 ramps; more tends to muddy the "
            "silhouette at 64px.",
        ))
    return out


def check_grid(px, w, h) -> list[Finding]:
    """Detect art that was upscaled and is no longer on its native pixel grid."""
    best_b, best_score = 1, 0.0
    for b in (2, 3, 4, 6, 8):
        if w % b or h % b:
            continue
        uniform = total = 0
        for by in range(0, h, b):
            for bx in range(0, w, b):
                block = {px[(by + dy) * w + bx + dx]
                         for dy in range(b) for dx in range(b)}
                total += 1
                uniform += len(block) == 1
        score = uniform / max(1, total)
        # Prefer the *largest* block that still reads as uniform: 6x upscaled art
        # is also perfectly uniform at 2x, and reporting 2x understates the problem.
        if score > 0.92 and (score > best_score or b > best_b):
            best_b, best_score = b, score
    if best_b > 1 and best_score > 0.92:
        return [Finding(
            BLOCKER, "grid",
            f"art appears to be {best_b}x upscaled "
            f"({best_score:.0%} of {best_b}x{best_b} blocks are uniform)",
            f"True resolution is {w // best_b}x{h // best_b}. Author and export at "
            f"native size; upscale only for display.",
        )]
    return []


def check_extremes(px) -> list[Finding]:
    solid = [p[:3] for p in px if p[3] == 255]
    out = []
    if (0, 0, 0) in solid:
        out.append(Finding(
            WARNING, "extremes",
            f"pure black present ({solid.count((0, 0, 0))}px)",
            "The bible forbids #000: it reads harsh and kills the cozy register. "
            "Use neutral_0 for outlines instead.",
        ))
    if (255, 255, 255) in solid:
        out.append(Finding(
            WARNING, "extremes",
            f"pure white present ({solid.count((255, 255, 255))}px)",
            "Use cream_4 rather than #fff.",
        ))
    return out


def check_light_direction(px, w, h) -> list[Finding]:
    """Highlights should sit upper-left. A rough check, hence only a note."""
    lit = [(i % w, i // w, srgb_to_oklab(p[:3])[0])
           for i, p in enumerate(px) if p[3] == 255]
    if len(lit) < 40:
        return []
    lit.sort(key=lambda t: -t[2])
    top = lit[:max(8, len(lit) // 5)]
    cx = sum(t[0] for t in top) / len(top)
    cy = sum(t[1] for t in top) / len(top)
    ax = sum(t[0] for t in lit) / len(lit)
    ay = sum(t[1] for t in lit) / len(lit)
    dx, dy = cx - ax, cy - ay
    if dx > w * 0.04 or dy > h * 0.04:
        d = ("right" if dx > w * 0.04 else "") + (" lower" if dy > h * 0.04 else "")
        return [Finding(
            NOTE, "light-direction",
            f"highlight centroid sits {d.strip()} of centre "
            f"(offset {dx:+.1f}, {dy:+.1f}px)",
            "The bible fixes a single key from upper-left (NW). Verify against "
            "neighbouring assets; inconsistent light across a set is the second "
            "most visible defect after projection drift.",
        )]
    return []


def check_silhouette(px, w, h) -> list[Finding]:
    solid = [(i % w, i // w) for i, p in enumerate(px) if p[3] == 255]
    if not solid:
        return [Finding(BLOCKER, "silhouette", "sprite is fully transparent", "-")]
    xs, ys = [s[0] for s in solid], [s[1] for s in solid]
    bw, bh = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
    out = []
    cover = len(solid) / (bw * bh)
    if cover < 0.25:
        out.append(Finding(
            NOTE, "silhouette",
            f"bounding box is only {cover:.0%} filled ({bw}x{bh})",
            "Sparse silhouettes read poorly at this size and complicate pivots. "
            "Check the shape is chunky enough to survive 64px.",
        ))
    if bw > w * 0.98 or bh > h * 0.98:
        out.append(Finding(
            WARNING, "silhouette",
            f"art touches the canvas edge ({bw}x{bh} in {w}x{h})",
            "Leave at least 1px bleed, or outlines clip and neighbouring tiles "
            "bleed into each other.",
        ))
    return out


CHECKS_NEEDING_PALETTE = True


def review(path: Path, by_rgb, ramps, entries) -> list[Finding]:
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    px = list(getattr(img, "get_flattened_data", img.getdata)())
    findings: list[Finding] = []
    findings += check_alpha(px, w, h)
    findings += check_grid(px, w, h)
    findings += check_palette(px, w, by_rgb, entries)
    findings += check_ramp_coherence(px, w, ramps)
    findings += check_extremes(px)
    findings += check_light_direction(px, w, h)
    findings += check_silhouette(px, w, h)
    findings.sort(key=lambda f: ORDER[f["severity"]])
    return findings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="+")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    by_rgb, ramps, entries = load_palette()
    report = {}
    for spec in args.images:
        for path in sorted(Path().glob(spec)) or [Path(spec)]:
            report[str(path)] = review(path, by_rgb, ramps, entries)

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    for path, findings in report.items():
        print(f"\n{path}")
        if not findings:
            print("  nothing to flag")
            continue
        for f in findings:
            print(f"  [{f['severity']:7s}] {f['check']}: {f['message']}")
            print(f"            -> {f['fix']}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# --- mesh-level checks -------------------------------------------------------
#
# These run on geometry rather than on a finished sprite, so they catch a defect
# before it is rendered 3023 times.

ROOM_PX_PER_UNIT = 27.2       # the room framing; see render_room.frame()
MIN_MEMBER_PX = 4             # below this a member reads as a stray line
MAX_THIN_SHARE = 0.20         # how much of an asset may be thin before it wires


def check_member_thickness(mesh, name="asset", ppu=ROOM_PX_PER_UNIT,
                           floor_px=MIN_MEMBER_PX):
    """Thinnest drawn member, measured rather than modelled.

    Pixel-art convention is to exaggerate small members precisely because
    realistic proportions vanish at low resolution. Rather than audit box
    dimensions -- which says nothing about what the projection actually
    produces -- this rasterizes the asset at the scale it is really seen and
    takes the 10th-percentile horizontal run of solid pixels.

    The metric is the SHARE of the asset that is thin, not its thinnest point.
    A first version flagged the minimum and fired on a pendant lamp's cord, a
    cup's handle and a sign's brackets -- all of which are meant to be thin, and
    all of which are a rounding error of their asset's area. What actually reads
    as wire is an object most of whose mass is thin. So: the fraction of solid
    pixels lying in runs below the floor.

    Two findings this produced: chair stiles measured 1 px, and a sandwich board
    built from zero-thickness quads measured 3 px because a standing plane seen
    near edge-on collapses to a line. Quads are right for floor overlays and
    wrong for anything vertical.
    """
    from isorender import DimetricCamera
    from mesh import rasterize
    cam = DimetricCamera(45.0)
    cam.span = 1.15
    res = max(16, int(2 * cam.span * ppu))
    mat, _, _ = rasterize(mesh, cam, res, target=(0.5, 0.5, 0.5))
    runs = []
    for y in range(res):
        cur = 0
        for x in range(res):
            if mat[y * res + x] is not None:
                cur += 1
            elif cur:
                runs.append(cur)
                cur = 0
        if cur:
            runs.append(cur)
    if not runs:
        return [f"{name}: renders empty at room scale"]
    total = sum(runs)
    thin = sum(r for r in runs if r < floor_px)
    share = thin / total
    if share > MAX_THIN_SHARE:
        return [f"{name}: {share:.0%} of its mass is in runs under {floor_px} px "
                f"at room scale (limit {MAX_THIN_SHARE:.0%}) -- reads as wire"]
    return []


# What each seeded generator is, and the world span to judge it across. The
# span is SHARED between a generator's seeds on purpose: normalising each mesh
# to fill the frame would hide size variation, which is a real part of a
# generator's range and the cheapest part to get wrong.
GENERATORS = (
    ("table_round", lambda A, s: A.table_round(seed=s), 1.7),
    ("table_4top", lambda A, s: A.table_4top(seed=s), 2.6),
    ("chair", lambda A, s: A.chair(seed=s), 1.4),
    ("plant_large", lambda A, s: A.plant_large(seed=s), 1.7),
    ("plant_small", lambda A, s: A.plant_small(seed=s), 1.1),
)

# Below this a row of seeds reads as one object. It is set under the furniture
# generators' measured 17% rather than at it, because the number this check
# exists to catch is a generator that has quietly become a fixed mesh -- a
# seed argument that is accepted and ignored, or a style table that stopped
# being reached. Tightening it toward the plants' 41% would be asserting that
# cafe chairs ought to vary as much as houseplants, which is a taste call
# nobody has made.
MIN_SILHOUETTE_SPREAD = 0.12


def silhouette(mesh, azimuth: float, span: float, res: int = 64) -> frozenset:
    """The set of pixels a mesh covers, in a framing shared with its siblings."""
    from isorender import DimetricCamera, dot
    import math
    cam = DimetricCamera(azimuth)
    vs = mesh.verts
    cu = (max(dot(v, cam.right) for v in vs)
          + min(dot(v, cam.right) for v in vs)) * 0.5
    cv = (max(dot(v, cam.up) for v in vs)
          + min(dot(v, cam.up) for v in vs)) * 0.5
    inv = res / (2.0 * (span * 0.5))
    hit = set()
    for tri, _n, _m in mesh.faces:
        pts = [((dot(vs[i], cam.right) - cu) * inv + res * 0.5,
                res * 0.5 - (dot(vs[i], cam.up) - cv) * inv) for i in tri]
        (ax, ay), (bx, by), (cx, cy) = pts
        area = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
        if abs(area) < 1e-12:
            continue
        for py in range(max(0, int(min(ay, by, cy))),
                        min(res - 1, int(math.ceil(max(ay, by, cy)))) + 1):
            fy = py + 0.5
            for px in range(max(0, int(min(ax, bx, cx))),
                            min(res - 1, int(math.ceil(max(ax, bx, cx)))) + 1):
                fx = px + 0.5
                w0 = ((bx - ax) * (fy - ay) - (by - ay) * (fx - ax)) / area
                w1 = ((cx - bx) * (fy - by) - (cy - by) * (fx - bx)) / area
                if w0 >= -1e-9 and w1 >= -1e-9 and 1.0 - w0 - w1 >= -1e-9:
                    hit.add(py * res + px)
    return frozenset(hit)


def check_generator_range(seeds: int = 8, azimuth: float = 45.0,
                          floor: float = MIN_SILHOUETTE_SPREAD) -> list[str]:
    """Do the seeded generators actually generate different shapes?

    A generator can rot in a way nothing else here notices. Add a base style
    and forget to put it in the style table; take a seed and drop it on a code
    path that ignores it; weaken the random stream so one branch of four is
    reached a third as often as the rest. Every one of those still renders a
    room full of furniture, and the room render looks fine, because four
    chairs of the wrong four are still four chairs.

    The measure is mean pairwise Jaccard distance between the silhouettes of
    consecutive seeds. It has to be a distance and not a count: counting
    *distinct* silhouettes is a threshold at one pixel, which reported 8 of 8
    for every generator in the library including the ones the eye read as a
    single object. That was `check_buried_detail`'s first metric exactly --
    a measure of whether anything moved, standing in for how much.
    """
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    import assetlib as A

    out = []
    for name, factory, span in GENERATORS:
        shapes = [silhouette(factory(A, s + 1), azimuth, span)
                  for s in range(seeds)]
        pairs = [(a, b) for i, a in enumerate(shapes) for b in shapes[i + 1:]]
        spread = sum(1.0 - len(a & b) / (len(a | b) or 1)
                     for a, b in pairs) / (len(pairs) or 1)
        if spread < floor:
            out.append(f"{name}: silhouette spread {spread:.0%} over {seeds} "
                       f"seeds (floor {floor:.0%}) -- the seed is barely "
                       f"changing the shape")
    return out


def review_library(floor_px=MIN_MEMBER_PX):
    """Run the mesh checks across every asset the blockout library exposes."""
    import inspect
    import assetlib
    out, assets = [], {}
    for fn_name, fn in sorted(vars(assetlib).items()):
        if not callable(fn) or fn_name.startswith("_"):
            continue
        if fn_name in ("merge", "transformed", "floor", "wall_run", "rug", "Mesh"):
            continue
        try:
            sig = inspect.signature(fn)
            if any(p.default is p.empty for p in sig.parameters.values()):
                continue
            mesh = fn()
        except Exception:
            continue
        if not hasattr(mesh, "verts"):
            continue
        assets[fn_name] = mesh
        out += check_member_thickness(mesh, fn_name, floor_px=floor_px)
    out += check_buried_detail(assets)
    return out


SYMMETRY_FOR = {1: "radial", 2: "4fold", 4: "2fold", 8: "none"}


def measured_symmetry(mesh, res=48, factor=3, tol=0.005, ramps=None):
    """How many of the 8 azimuths actually produce different SPRITES.

    Symmetry is declared by hand in assets.yaml and drives the whole render
    budget -- `radial` costs 1 render where `none` costs 8. A wrong claim is
    expensive in one direction and broken in the other, and nothing was checking
    it. Rendering the thing settles it.

    Compare the quantized sprite, not the lambert buffer. A first version
    compared raw lambert and declared steam eight-way asymmetric; the material
    buffer was pixel-identical and only the shading differed, because coincident
    facets on a symmetric mesh resolve to different triangles depending on
    z-buffer tie-breaks. After quantization those sprites matched to 1 pixel in
    2304. The question a budget cares about is whether a player would see a
    difference, so `tol` is a share of pixels rather than zero.
    """
    from isorender import DimetricCamera
    from mesh import rasterize
    from pixelize import downsample_modal, load_palette, shade_toon
    ramps = ramps or load_palette()
    # Target the mesh's OWN centre. Assuming (0.5, 0.5) silently broke this for
    # every asset bigger than one tile: a 2x2 ceiling fan centred at (1, 1) was
    # rendered off-axis, so its four-fold symmetry vanished and the check
    # reported eight distinct directions for a perfectly symmetric object.
    xs = [v[0] for v in mesh.verts] or [0.0]
    ys = [v[1] for v in mesh.verts] or [0.0]
    zs = [v[2] for v in mesh.verts] or [0.0]
    ctr = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2,
           (min(zs) + max(zs)) / 2)
    span = max(max(xs) - min(xs), max(ys) - min(ys),
               max(zs) - min(zs)) * 0.75 or 1.0
    size = res * factor
    sprites = []
    for d in range(8):
        cam = DimetricCamera(45.0 + d * 45.0)
        cam.span = span
        mat, lam, _ = rasterize(mesh, cam, size, target=ctr)
        # Dither OFF. Ordered dithering is screen-space, so identical geometry
        # at a different azimuth lands on different Bayer cells: a four-blade
        # fan measured 1-2% pixel difference across a 90 degree rotation it is
        # exactly symmetric under. That is dither phase, not asymmetry, and
        # including it would force the tolerance so wide that real defects slip
        # through.
        sprites.append(tuple(downsample_modal(
            shade_toon(mat, lam, size, ramps, dither=False), size, factor)))

    n = len(sprites[0]) or 1

    def same(a, b):
        return sum(1 for p, q in zip(a, b) if p != q) / n <= tol

    for period in (1, 2, 4, 8):
        if all(same(sprites[i], sprites[i % period]) for i in range(8)):
            return period
    return 8


def check_symmetry_claims(declared: dict, meshes: dict):
    """Cross-check every declared symmetry class against measured geometry."""
    from manifest import DISTINCT_AZIMUTHS
    out = []
    for aid, mesh in meshes.items():
        if aid not in declared:
            continue
        claim = declared[aid]
        want = DISTINCT_AZIMUTHS.get(claim)
        got = measured_symmetry(mesh)
        if want is None:
            continue
        if got > want:
            out.append(f"{aid}: declared {claim!r} ({want} azimuths) but "
                       f"{got} are visually distinct -- directions will be WRONG")
        elif got < want:
            saved = want - got
            out.append(f"{aid}: declared {claim!r} ({want} azimuths) but only "
                       f"{got} differ -- {saved} wasted renders per frame; "
                       f"should be {SYMMETRY_FOR[got]!r}")
    return out


# --- buried detail ------------------------------------------------------------
#
# A fixed dimetric camera sees exactly two faces of any axis-aligned box, and a
# sprite pipeline sees at most eight orientations of one. Anything modelled on
# the other faces -- or inside the volume -- costs vertices, costs render time,
# and contributes no pixels in any frame that ships. This is not a style note.
# It is dead weight, and it hides as *effort*: the espresso machine carried two
# group heads and two portafilters buried inside its own carcass, which read on
# the counter as a blank grey slab while the mesh insisted it was detailed.

def visible_faces(mesh, azimuth: float, res: int = 96) -> set:
    """Indices of triangles that win at least one pixel at this azimuth."""
    from isorender import DimetricCamera, cross, dot, norm, sub
    cam = DimetricCamera(azimuth)
    vs = mesh.verts
    lo_u = min(dot(v, cam.right) for v in vs)
    hi_u = max(dot(v, cam.right) for v in vs)
    lo_v = min(dot(v, cam.up) for v in vs)
    hi_v = max(dot(v, cam.up) for v in vs)
    span = max(hi_u - lo_u, hi_v - lo_v) * 0.5 * 1.04 or 1e-6
    cu, cv = (hi_u + lo_u) * 0.5, (hi_v + lo_v) * 0.5
    inv = res / (2.0 * span)

    def project(v):
        return ((dot(v, cam.right) - cu) * inv + res * 0.5 - 0.5,
                res * 0.5 - 0.5 - (dot(v, cam.up) - cv) * inv,
                dot(v, cam.dir))

    zbuf = [-1e30] * (res * res)
    owner = [-1] * (res * res)
    for fi, (tri, _n, _m) in enumerate(mesh.faces):
        a, b, c = (vs[i] for i in tri)
        # Backfaces cannot be seen and must not claim pixels, or a box's far
        # side would count as visible whenever it happened to project first.
        if dot(norm(cross(sub(b, a), sub(c, a))), cam.dir) <= 0.0:
            continue
        pa, pb, pc = project(a), project(b), project(c)
        area = ((pb[0] - pa[0]) * (pc[1] - pa[1]) -
                (pb[1] - pa[1]) * (pc[0] - pa[0]))
        if abs(area) < 1e-12:
            continue
        import math
        x0 = max(0, int(math.floor(min(pa[0], pb[0], pc[0]))))
        x1 = min(res - 1, int(math.ceil(max(pa[0], pb[0], pc[0]))))
        y0 = max(0, int(math.floor(min(pa[1], pb[1], pc[1]))))
        y1 = min(res - 1, int(math.ceil(max(pa[1], pb[1], pc[1]))))
        for py in range(y0, y1 + 1):
            fy = py + 0.5
            for px in range(x0, x1 + 1):
                fx = px + 0.5
                w0 = ((pb[0] - pa[0]) * (fy - pa[1])
                      - (pb[1] - pa[1]) * (fx - pa[0])) / area
                w1 = ((pc[0] - pb[0]) * (fy - pb[1])
                      - (pc[1] - pb[1]) * (fx - pb[0])) / area
                w2 = 1.0 - w0 - w1
                if w0 < -1e-9 or w1 < -1e-9 or w2 < -1e-9:
                    continue
                z = w1 * pa[2] + w2 * pb[2] + w0 * pc[2]
                i = py * res + px
                if z > zbuf[i]:
                    zbuf[i] = z
                    owner[i] = fi
    return {o for o in owner if o >= 0}


def front_facing(mesh, azimuth: float, res: int = 160):
    """(camera-facing triangles big enough to matter, of those the visible ones).

    A triangle is a candidate only if it faces the camera AND projects to at
    least a pixel of area. Both halves are load-bearing: without the first the
    far side of every box counts as buried, and without the second every
    hairline trim in the library does.
    """
    import math

    from isorender import DimetricCamera, cross, dot, norm, sub
    cam = DimetricCamera(azimuth)
    vs = mesh.verts
    lo_u = min(dot(v, cam.right) for v in vs)
    hi_u = max(dot(v, cam.right) for v in vs)
    lo_v = min(dot(v, cam.up) for v in vs)
    hi_v = max(dot(v, cam.up) for v in vs)
    span = max(hi_u - lo_u, hi_v - lo_v) * 0.5 * 1.04 or 1e-6
    cu, cv = (hi_u + lo_u) * 0.5, (hi_v + lo_v) * 0.5
    inv = res / (2.0 * span)

    front = set()
    for fi, (tri, _n, _m) in enumerate(mesh.faces):
        a, b, c = (vs[i] for i in tri)
        if dot(norm(cross(sub(b, a), sub(c, a))), cam.dir) <= 0.0:
            continue
        pts = [((dot(v, cam.right) - cu) * inv, (dot(v, cam.up) - cv) * inv)
               for v in (a, b, c)]
        area = abs((pts[1][0] - pts[0][0]) * (pts[2][1] - pts[0][1])
                   - (pts[1][1] - pts[0][1]) * (pts[2][0] - pts[0][0])) * 0.5
        if area >= 1.0:
            front.add(fi)
    return front, visible_faces(mesh, azimuth, res)


# Assets whose occlusion is a property of the object, not a modelling mistake.
# The same role TUCK_OK plays for collisions: an allowlist is what lets the
# threshold stay tight enough to catch the real thing. Each entry needs a reason
# that would still be true if the asset were re-modelled from scratch.
ACCEPTED_BURIAL = {
    "table_4top": "the far pair of legs sits behind the tabletop's own near edge",
    "pastry_case": "a lidded display case has an interior its top pane covers",
    "counter": "modules tile flush, so each one's end panels abut its neighbour",
    "leafy_plant": "foliage self-occludes; leaves overlap because that is what a "
                   "canopy is",
    "plant_large": "as leafy_plant, which generates it",
    "plant_small": "as leafy_plant, which generates it",
}

# The plants were exempted only after acting on what the check said. It reported
# 55% of a 420-triangle canopy hidden behind its own leaves, and the exemption
# answers the "hidden" half -- overlapping leaves are what foliage is -- while
# the leaf prisms dropped from 8 sides to 6 to answer the "420 triangles" half.
# An allowlist entry that suppresses a warning without first asking whether the
# warning had a point is how a ratchet quietly turns back into decoration.


def check_buried_detail(assets: dict, azimuths=(45.0,), res: int = 160,
                        max_share: float = 0.30) -> list[str]:
    """Front-facing geometry that is nonetheless completely hidden.

    The obvious metric -- share of all triangles that never win a pixel -- is
    useless, and measuring it proves why: a closed box shows at most three of
    its six faces, so *every* solid asset scores about 67% "buried" and the
    check fires on all eighteen props in the library. That is not a defect, it
    is what solid geometry costs.

    What actually matters is a triangle that faces the camera and still reaches
    no pixel, because something else is in front of it. That is either detail
    modelled inside a volume, or detail on a face another part covers. Faces too
    small to claim a pixel are excluded: sub-pixel members are a real defect but
    they are `check_member_thickness`'s to report, and double-counting them here
    would bury the signal this check exists for.

    `azimuths` defaults to the single view the room composite uses. Pass all
    eight for anything that ships as a rotating sprite.
    """
    out = []
    for name, mesh in sorted(assets.items()):
        cand, hidden = 0, 0
        for az in azimuths:
            front, seen = front_facing(mesh, az, res)
            cand += len(front)
            hidden += len(front - seen)
        if cand < 12 or name in ACCEPTED_BURIAL:
            continue
        share = hidden / cand
        if share > max_share:
            out.append(f"{name}: {share:.0%} of its camera-facing tris are "
                       f"fully occluded ({hidden}/{cand}) -- detail modelled "
                       f"where the camera cannot reach it")
    return out
