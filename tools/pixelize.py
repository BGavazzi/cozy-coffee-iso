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
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from oklab import delta_e, srgb_to_oklab  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# Ordered 4x4 Bayer matrix, normalised to [0, 1).
BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]

# Dither only within this band around a step boundary; snap outside it.
DITHER_LO, DITHER_HI = 0.36, 0.64

# Which palette ramp each material shades along. This binding is the whole
# mechanism -- it is what makes cross-ramp contamination impossible.
MATERIAL_RAMPS = {
    "ground": "wood",
    "wood": "wood",
    # Skin reads off the wood ramp -- the warm mid-browns are exactly right for
    # it -- but it must be addressable separately from timber, because they want
    # opposite treatment everywhere except colour. Surface grain is the case
    # that forced this: at 0.85 of a step it reads as plank on a floor and as
    # stubble on a face.
    "skin": "wood",
    "cream": "cream",
    "foliage": "foliage",
    "rose": "rose",
    "sky": "sky",
    "neutral": "neutral",
    # Spot accents. Each is a 1-step ramp, so it renders as itself at any
    # lambert -- an emissive surface, not a shaded one.
    "lamp_glow": "lamp_glow",
    "accent_read": "accent_read",
    "gold_coin": "gold_coin",
}


def material(m: str) -> tuple[str, int]:
    """Split a material token into (ramp, tone offset).

    A trailing signed integer shifts the shaded result along the material's own
    ramp: `"wood-3"` is wood, three steps darker. This is the pixel-art idiom of
    drawing detail with value rather than with geometry -- eyes, panel seams and
    fabric folds are a darker step of the surface they sit on, not a new colour.
    Crucially it stays palette-exact, because the result is still a step of the
    same ramp, so cross-ramp contamination remains structurally impossible.

    Offsets compose by summing, so `"neutral-2+1"` is neutral one step down.
    That matters for modular assembly: a part may brighten whatever material it
    is handed (a hair bun is `mat + "+1"`) without needing to know that the spec
    already darkened it.
    """
    parts = _TONE_RE.findall(m)
    base = _TONE_RE.sub("", m)
    return MATERIAL_RAMPS[base], sum(int(p) for p in parts)


_TONE_RE = re.compile(r"[+-]\d+")



def load_palette(path: Path | None = None) -> dict[str, list[tuple[int, int, int]]]:
    """Ramps by name, with each spot colour promoted to its own 1-step ramp.

    Spot colours are not lightness ramps -- they are single accents, and the
    palette file groups all three under `ramp: "spot"`. Left that way they are
    unaddressable: no material can name `lamp_glow`, which is precisely why the
    critique found it used on 0 pixels while the scene had pendant lamps in it.

    A 1-step ramp is exactly the right shape for an accent. The toon shader
    indexes `lam * (n - 1)`, which is 0 for every lambert when n is 1, so a spot
    colour emits itself regardless of lighting -- which is what "this thing is a
    light source" should mean.
    """
    path = path or ROOT / "palette" / "palette.json"
    entries = json.loads(path.read_text(encoding="utf-8"))
    ramps: dict[str, list] = {}
    for e in sorted(entries, key=lambda e: (e["ramp"], e["index"])):
        if e["ramp"] == "spot":
            ramps[e["name"]] = [tuple(e["rgb"])]
        else:
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
            rname, tone = material(m)
            ramp = ramps[rname]
            n = len(ramp)

            # Continuous position along the ramp, then split into index + fraction.
            pos = lam[i] * (n - 1) + tone
            idx = int(pos // 1)
            frac = pos - idx

            if dither and idx < n - 1 and DITHER_LO < frac < DITHER_HI:
                # Ordered dither between *adjacent steps of this ramp only*, and
                # only inside a band around the step boundary. Dithering the
                # whole 0..1 range -- the obvious implementation -- puts a
                # checker on every shaded surface in the frame, which reads as
                # static rather than as pixel art. Hand artists lay a dither
                # band at the transition and leave the flats flat; this is that,
                # made mechanical.
                t = (frac - DITHER_LO) / (DITHER_HI - DITHER_LO)
                if t > BAYER4[y % 4][x % 4] / 16.0:
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
        rname, tone = material(m)
        ramp = ramps[rname]
        base = ramp[max(0, min(len(ramp) - 1, len(ramp) // 2 + tone))]
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
                out[i] = ramps[material(m)[0]][0]
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
