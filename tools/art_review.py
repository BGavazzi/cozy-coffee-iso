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


def review_library(floor_px=MIN_MEMBER_PX):
    """Run the mesh checks across every asset the blockout library exposes."""
    import inspect
    import assetlib
    out = []
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
        out += check_member_thickness(mesh, fn_name, floor_px=floor_px)
    return out
