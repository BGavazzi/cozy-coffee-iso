#!/usr/bin/env python3
"""Stage 1-6 for flat UI art, skipping the 3D middle entirely.

`assets.yaml` declares fourteen `cat: ui` entries -- order tickets, drink
icons, a coin, a dialogue frame, a star rating -- and until now not one of
them had a sprite. They were the largest declared-but-unbuilt category in
the manifest, and the reason is structural rather than neglect: the main
pipeline is concept -> mesh -> 8 azimuths, and a UI icon has no mesh and
exactly one azimuth. Pushing an icon through `lift.py` would ask TripoSR to
reconstruct the depth of something that is deliberately flat, which is the
same class of mistake as asking it for a frog knight (see `ART_CRITIQUE.md`,
"The character ceiling is stage 2") -- except here the 3D step is not merely
unhelpful, it is contrary to the art direction.

So UI art takes the short path: generate, matte, quantize, outline. Stages
2 through 5 are skipped because they have nothing to contribute, not because
they were too slow.

    python tools/ui_forge.py                    # every ui entry in assets.yaml
    python tools/ui_forge.py --only ui_coin,ui_ticket
    python tools/ui_forge.py --target 32        # icons are small by nature

Nothing here is a new generation path. Every image comes from
`concept.concept()` via its `positive_override`/`negative_override` fields --
the same "custom" escape hatch the UI exposes -- and every quantization step
is `pixelize`'s, the same one `render_batch.py` uses. What differs is only
which stages are called, which is the honest difference between the two
kinds of asset.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from oklab import srgb_to_oklab  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
UI_DIR = ROOT / "out" / "ui"

# The 2D counterpart to `concept.STYLE`. Every clause is doing work:
#
#   "flat 2d game icon"  -- the single most load-bearing phrase; without it
#                           SDXL renders a photographed object every time.
#   "bold simple shapes,
#    thick clean outline" -- what makes an icon readable at 32px, and what
#                           the style bible asks of every sprite anyway.
#   "no shading, no
#    gradient"            -- the renderer supplies shading everywhere else in
#                           this repo; here nothing does, so flat is correct
#                           rather than lazy. It also keeps the palette snap
#                           honest: a gradient quantizes to banding.
#   "plain white
#    background"          -- gives `matte()` an easy separation, the same
#                           reason `STYLE` asks for a flat neutral one.
#
# Token budget checked, not assumed: 43 tokens with a short subject, well
# inside CLIP's 77-token truncation cliff. See `concept.NEGATIVE`'s comment
# for what happens when that ceiling is crossed silently.
UI_STYLE = ("flat 2d game icon of {subject}, vector illustration, centred, "
            "bold simple shapes, thick clean outline, plain white background, "
            "no shading, no gradient, front view, full icon in frame")

UI_NEGATIVE = ("photograph, 3d render, realistic, shading, gradient, "
               "drop shadow, perspective, multiple icons, grid, collage, "
               "text, watermark, signature, blurry, busy background, "
               "cropped, cut off, out of frame")

# What each declared `cat: ui` id should actually depict. `assets.yaml` names
# them but does not describe them, and "ui_icon_cold_brew" is not a prompt.
UI_PROMPTS = {
    "ui_ticket": "a paper order ticket with a torn edge",
    "ui_icon_espresso": "a small espresso cup on a saucer",
    "ui_icon_latte": "a tall latte glass with foam",
    "ui_icon_cappuccino": "a cappuccino cup with foam heart",
    "ui_icon_tea": "a teacup with a tea bag tag",
    "ui_icon_pastry": "a croissant",
    "ui_icon_cold_brew": "a cold brew cup with a straw",
    "ui_coin": "a round gold coin",
    "ui_clock_day": "a round clock face",
    "ui_dialogue_frame": "a rounded rectangular speech bubble",
    "ui_nameplate": "a horizontal rounded nameplate banner",
    "ui_upgrade_frame": "a square badge frame with a notched border",
    "ui_star_rating": "a five pointed star",
    "ui_heart_mood": "a heart symbol",
}

# An icon that fills too little of its own frame has been drawn small inside
# a lot of whitespace, and downsampling will hand back a few dozen pixels of
# mush. Deliberately looser than `concept.py`'s 12% floor for props: an icon
# is allowed to be a thin shape (a star, a ticket) in a way a reconstructable
# solid is not, and there is no mesh downstream whose resolution it would
# starve. Bracketed on what the first fourteen actually measured rather than
# picked in advance -- see `ART_CRITIQUE.md`.
MIN_ICON_COVERAGE = 0.06


def _snap(c, ramps, _cache={}):
    """Nearest palette colour in OKLab. Cached: a 1024x1024 image has far
    more pixels than the palette has distinct answers."""
    if not _cache:
        flat = [x for r in ramps.values() for x in r]
        _cache["_flat"] = flat
        _cache["_labs"] = [srgb_to_oklab(x) for x in flat]
    if c not in _cache:
        lab = srgb_to_oklab(c)
        _cache[c] = min(zip(_cache["_flat"], _cache["_labs"]),
                        key=lambda p: math.dist(lab, p[1]))[0]
    return _cache[c]


def flat_pixelize(png: Path | str, target: int, ramps: dict):
    """Matted RGBA -> palette-exact pixels at `target`, with an outline.

    Snap first, then take the modal colour per block -- NOT the other way
    round, which is what this did first and which produced visibly speckled
    icons. Measured on the first three generated, isolated-pixel ratio
    (`art_review`'s blocker, floor 6.2%):

        mean-then-snap   snap-then-modal
        18.8%            15.5%    ui_coin
        13.2%             1.5%    ui_icon_espresso
        39.1%             5.8%    ui_star_rating

    The reason is in `downsample_modal`'s own docstring -- "invents nothing,
    so stays palette-exact". It was written for the 3D path, where pixels
    arrive already palette-exact from `shade_toon`, and it is speckle-proof
    precisely because it only ever picks a colour that already dominates a
    block. Averaging first breaks that: adjacent blocks average to slightly
    different RGB, snap to different ramp steps, and salt-and-pepper the
    result. Snapping first puts the 2D path in the condition the 3D path was
    already in, and the fix is to reuse the existing function correctly
    rather than to write a de-speckler.

    Material ids come back by reverse-lookup after the snap, so
    `apply_outline` works unchanged and still tints each outline with its own
    surface's darkest step rather than black -- a style bible requirement,
    not something to reimplement differently here.
    """
    from PIL import Image
    from pixelize import apply_outline, downsample_modal

    img = Image.open(png).convert("RGBA")
    size = img.width
    if img.height != size:
        raise ValueError(f"{png} is {img.width}x{img.height}, expected square")
    if size % target:
        raise ValueError(f"target {target} does not divide source {size}")

    # 128 rather than >0: `matte()` leaves a soft edge, and treating a
    # half-transparent pixel as solid drags the icon's outline outward into
    # fringe. The same threshold the fitness gate reasons about.
    px = [_snap((p[0], p[1], p[2]), ramps) if p[3] >= 128 else None
          for p in img.getdata()]

    small = downsample_modal(px, size, size // target)
    member = {c: name for name, ramp in ramps.items() for c in ramp}
    mats = [member.get(c) if c is not None else None for c in small]
    return apply_outline(small, mats, target, ramps, selective=True)


# An icon whose pixels mostly have no matching neighbour is speckle, not
# art, whatever the coverage says. Same number `art_review` blocks sprites
# on, and deliberately the same: an icon and a sprite are the same kind of
# object once they are palette-quantized pixels, so they get held to one
# standard rather than to a softer one written to make this tool pass.
MAX_ISOLATED = 0.062


def check_icon(px, target: int, ramps: dict) -> list[str]:
    """Is this a usable icon? Same shape of answer as `check_concept_fitness`.

    The first version of this checked coverage and palette-exactness only,
    passed all three of the first icons generated, and was wrong about every
    one of them -- `art_review` blocked all three on isolated pixels (13.4%,
    19.1%, 33.5%) and the eye agreed. A check that cannot fail the thing it
    is meant to catch is the `MIN_FILL` mistake again, one file over, so the
    speckle reading is now the check rather than an afterthought.
    """
    from pixelize import audit
    out = []
    rep = audit(px, ramps)
    cover = rep["pixels"] / float(target * target)
    if cover < MIN_ICON_COVERAGE:
        out.append(f"icon fills {cover * 100:.1f}% of frame (floor "
                   f"{MIN_ICON_COVERAGE * 100:.0f}%) -- drawn small inside "
                   f"whitespace, so it will not read at this size")

    solid = [i for i, c in enumerate(px) if c is not None]
    iso = 0
    for i in solid:
        x, y = i % target, i // target
        if not any(0 <= x + dx < target and 0 <= y + dy < target
                   and px[(y + dy) * target + (x + dx)] == px[i]
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            iso += 1
    ratio = iso / max(1, len(solid))
    if ratio > MAX_ISOLATED:
        out.append(f"{ratio:.1%} of pixels match none of their four "
                   f"neighbours (cap {MAX_ISOLATED:.1%}) -- speckle rather "
                   f"than the flat shapes an icon needs to read at this size")

    if rep["off_palette"]:
        # Should be impossible: the snap picks from the palette by
        # construction. Reported rather than asserted because "impossible"
        # is exactly the claim worth having a check behind.
        out.append(f"{rep['off_palette_pct']}% of pixels are off-palette, "
                   f"which the snap should have made impossible")
    return out


def forge(name: str, prompt: str, target: int, ramps, pipe, seed: int = 1,
          retries: int = 2) -> dict:
    """One icon, generate through pixels. Returns a result dict, never raises."""
    import concept as C
    from PIL import Image

    result = {"name": name, "ok": False, "detail": "", "seed_used": seed}
    UI_DIR.mkdir(parents=True, exist_ok=True)
    raw_png = UI_DIR / f"{name}_concept.png"

    try:
        for attempt in range(retries + 1):
            s = seed + attempt
            C.concept(prompt, seed=s, out=raw_png, pipe=pipe,
                      positive_override=UI_STYLE.format(subject=prompt),
                      negative_override=UI_NEGATIVE)
            px = flat_pixelize(raw_png, target, ramps)
            bad = check_icon(px, target, ramps)
            if not bad:
                result["seed_used"] = s
                if attempt:
                    result["detail"] = f"passed on seed {s} after {attempt} reseed(s)"
                break
            if attempt == retries:
                result["detail"] = "; ".join(bad)
                return result
            print(f"  seed {s} gated, reseeding: {bad[0][:70]}")
    except Exception as e:
        result["detail"] = f"{type(e).__name__}: {e}"
        return result

    img = Image.new("RGBA", (target, target), (0, 0, 0, 0))
    img.putdata([(c[0], c[1], c[2], 255) if c else (0, 0, 0, 0) for c in px])
    img.save(UI_DIR / f"{name}.png")
    result["ok"] = True
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated ui ids to build")
    ap.add_argument("--target", type=int, default=64,
                    help="icon size in pixels (default 64, must divide 1024)")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--retry-seeds", type=int, default=2)
    args = ap.parse_args()

    wanted = dict(UI_PROMPTS)
    if args.only:
        keep = set(args.only.split(","))
        unknown = keep - set(wanted)
        if unknown:
            print(f"unknown ui ids: {sorted(unknown)}", file=sys.stderr)
            return 1
        wanted = {k: v for k, v in wanted.items() if k in keep}

    print(f"{len(wanted)} icons. Loading SDXL once...")
    import concept as C
    from pixelize import load_palette
    ramps = load_palette()
    pipe = C._pipe()

    results = []
    for name, prompt in sorted(wanted.items()):
        print(f"\n=== {name} ===")
        r = forge(name, prompt, args.target, ramps, pipe, seed=args.seed,
                  retries=args.retry_seeds)
        results.append(r)
        print(f"  {'OK' if r['ok'] else 'GATED'}"
              + (f": {r['detail']}" if r["detail"] else ""))

    ok = [r for r in results if r["ok"]]
    print(f"\n{len(ok)}/{len(results)} icons built -> {UI_DIR}")
    (UI_DIR / "ui_report.json").write_text(json.dumps(results, indent=2),
                                           encoding="utf-8")
    return 0 if len(ok) == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
