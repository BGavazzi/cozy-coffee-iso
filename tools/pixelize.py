"""The deterministic conformance stage: shaded buffers -> spec-exact sprite.

This module is where "does it read as pixel art or as a shrunk 3D render" is
decided, so the central claim is worth stating plainly:

    Quantize the LIGHTING, not the IMAGE.

The naive chain -- smooth-shade, downsample, then snap each pixel to its nearest
palette colour -- fails for two compounding reasons. Nearest-colour search is
unaware of material, so a wood surface picks up sky blues in its midtones
(cross-ramp contamination). And averaging during downsample manufactures
intermediate colours that were never in the palette, which the snap then
scatters across unrelated ramps. The result is continuous, noisy banding: the
visual signature of a shrunk render.

Here, each material declares a palette ramp up front. The toon shader maps the
lambert term to a discrete ramp *index*, and emits that exact colour. No pixel
can ever hold a colour that is not a step of its own material's ramp. Gradients
are recovered by ordered dithering between *adjacent steps of the same ramp*,
never across ramps. Downsampling takes the modal colour rather than the mean, so
no intermediate colour is ever invented.

Both paths are implemented so the difference can be measured rather than argued.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from oklab import delta_e, srgb_to_oklab  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# Ordered 4x4 Bayer matrix, normalised to [0, 1).
BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]

# Which palette ramp each material shades along. This binding is the whole
# mechanism -- it is what makes cross-ramp contamination impossible.
MATERIAL_RAMPS = {
    "ground": "wood",
    "wood": "wood",
    "cream": "cream",
    "foliage": "foliage",
    "rose": "rose",
    "sky": "sky",
}


def load_palette(path: Path | None = None) -> dict[str, list[tuple[int, int, int]]]:
    path = path or ROOT / "palette" / "palette.json"
    entries = json.loads(path.read_text(encoding="utf-8"))
    ramps: dict[str, list] = {}
    for e in sorted(entries, key=lambda e: (e["ramp"], e["index"])):
        ramps.setdefault(e["ramp"], []).append(tuple(e["rgb"]))
    return ramps


# --- the two competing quantization strategies ------------------------------

def shade_toon(mat, lam, size, ramps, dither=True):
    """Quantize lighting to ramp indices. Output is palette-exact by construction."""
    out: list[tuple[int, int, int] | None] = [None] * (size * size)
    for y in range(size):
        for x in range(size):
            i = y * size + x
            m = mat[i]
            if m is None:
                continue
            ramp = ramps[MATERIAL_RAMPS[m]]
            n = len(ramp)

            # Continuous position along the ramp, then split into index + fraction.
            pos = lam[i] * (n - 1)
            idx = int(pos)
            frac = pos - idx

            if dither and idx < n - 1:
                # Ordered dither between *adjacent steps of this ramp only*.
                if frac > BAYER4[y % 4][x % 4] / 16.0:
                    idx += 1
            elif frac > 0.5:
                idx = min(idx + 1, n - 1)

            out[i] = ramp[max(0, min(n - 1, idx))]
    return out


def shade_smooth(mat, lam, size, ramps):
    """Naive path: continuous shading off the ramp's mid colour."""
    out: list[tuple[int, int, int] | None] = [None] * (size * size)
    for i, m in enumerate(mat):
        if m is None:
            continue
        ramp = ramps[MATERIAL_RAMPS[m]]
        base = ramp[len(ramp) // 2]
        s = 0.35 + 0.95 * lam[i]
        out[i] = tuple(max(0, min(255, int(c * s))) for c in base)
    return out


# --- downsampling -----------------------------------------------------------

def downsample_modal(px, size, factor):
    """Most common colour per block. Invents nothing, so stays palette-exact."""
    t = size // factor
    out: list[tuple[int, int, int] | None] = [None] * (t * t)
    for y in range(t):
        for x in range(t):
            block = [px[(y * factor + dy) * size + (x * factor + dx)]
                     for dy in range(factor) for dx in range(factor)]
            solid = [c for c in block if c is not None]
            if len(solid) * 2 >= len(block):        # coverage >= 50% -> opaque
                out[y * t + x] = Counter(solid).most_common(1)[0][0]
    return out


def downsample_mean_then_snap(px, size, factor, ramps):
    """Naive path: average, then snap to nearest palette entry."""
    flat = [c for ramp in ramps.values() for c in ramp]
    labs = [srgb_to_oklab(c) for c in flat]
    t = size // factor
    out: list[tuple[int, int, int] | None] = [None] * (t * t)
    cache: dict[tuple[int, int, int], tuple[int, int, int]] = {}
    for y in range(t):
        for x in range(t):
            block = [px[(y * factor + dy) * size + (x * factor + dx)]
                     for dy in range(factor) for dx in range(factor)]
            solid = [c for c in block if c is not None]
            if len(solid) * 2 < len(block):
                continue
            n = len(solid)
            avg = (sum(c[0] for c in solid) // n,
                   sum(c[1] for c in solid) // n,
                   sum(c[2] for c in solid) // n)
            if avg not in cache:
                lab = srgb_to_oklab(avg)
                cache[avg] = min(zip(flat, labs), key=lambda p: delta_e(lab, p[1]))[0]
            out[y * t + x] = cache[avg]
    return out


# --- outline ----------------------------------------------------------------

def apply_outline(px, mat_small, size, ramps, selective=True):
    """Silhouette outline always; internal boundaries only where contrast is low.

    Outline colour is the bounding surface's own darkest ramp step, so it is
    tinted per-surface and never pure black -- both style bible requirements
    satisfied by construction rather than by a colour choice.
    """
    out = list(px)
    for y in range(size):
        for x in range(size):
            i = y * size + x
            if px[i] is None:
                continue
            m = mat_small[i]
            edge = False
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < size and 0 <= ny < size):
                    edge = True
                    break
                j = ny * size + nx
                if px[j] is None:
                    edge = True
                    break
                if selective and mat_small[j] != m:
                    a, b = srgb_to_oklab(px[i]), srgb_to_oklab(px[j])
                    if abs(a[0] - b[0]) < 0.14:   # low contrast -> needs a line
                        edge = True
                        break
            if edge and m is not None:
                out[i] = ramps[MATERIAL_RAMPS[m]][0]
    return out


# --- verification -----------------------------------------------------------

def audit(px, ramps) -> dict:
    """Report palette exactness and cross-ramp contamination."""
    member = {c: name for name, ramp in ramps.items() for c in ramp}
    solid = [c for c in px if c is not None]
    off = [c for c in solid if c not in member]
    used = Counter(member[c] for c in solid if c in member)
    return {
        "pixels": len(solid),
        "off_palette": len(off),
        "off_palette_pct": round(100.0 * len(off) / max(1, len(solid)), 2),
        "distinct_colours": len(set(solid)),
        "ramps_touched": dict(used),
    }
