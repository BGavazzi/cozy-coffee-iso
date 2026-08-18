#!/usr/bin/env python3
"""Render the same asset both ways and measure the difference.

Settles empirically whether the 3D path can read as pixel art rather than as a
shrunk render. Emits a comparison sheet and a numeric audit.

    python tools/prove_shading.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from isorender import DimetricCamera, coffee_scene, render, verify_projection  # noqa: E402
from pixelize import (  # noqa: E402
    apply_outline, audit, downsample_mean_then_snap, downsample_modal,
    load_palette, shade_smooth, shade_toon,
)

ROOT = Path(__file__).resolve().parent.parent
TARGET = 64
FACTOR = 4
SIZE = TARGET * FACTOR


def to_image(px, size, scale=1, bg=(38, 34, 44)):
    img = Image.new("RGB", (size, size), bg)
    img.putdata([c if c is not None else bg for c in px])
    return img.resize((size * scale, size * scale), Image.NEAREST) if scale > 1 else img


def main() -> int:
    ratio = verify_projection()
    print(f"projection check: {ratio:.12f} (exactly 2:1)\n")

    ramps = load_palette()
    scene, cam = coffee_scene(), DimetricCamera(45.0)

    print(f"rendering {SIZE}x{SIZE} -> {TARGET}x{TARGET} ...")
    mat, lam, _ = render(scene, cam, SIZE)

    # --- naive: smooth shade, average down, snap to nearest palette entry
    naive_hi = shade_smooth(mat, lam, SIZE, ramps)
    naive = downsample_mean_then_snap(naive_hi, SIZE, FACTOR, ramps)

    # --- correct: quantize lighting to ramp indices, modal downsample, outline
    toon_hi = shade_toon(mat, lam, SIZE, ramps, dither=True)
    toon = downsample_modal(toon_hi, SIZE, FACTOR)
    mat_small = downsample_modal(
        [m if m is None else (hash(m) % 251, 0, 0) for m in mat], SIZE, FACTOR)
    id_to_mat = {(hash(m) % 251, 0, 0): m for m in set(mat) if m is not None}
    mat_small = [id_to_mat.get(c) if c is not None else None for c in mat_small]
    toon = apply_outline(toon, mat_small, TARGET, ramps)

    a_naive, a_toon = audit(naive, ramps), audit(toon, ramps)
    print(f"{'':22s}{'naive':>12s}{'ramp-quantized':>18s}")
    for k in ("pixels", "off_palette", "off_palette_pct", "distinct_colours"):
        print(f"  {k:20s}{str(a_naive[k]):>12s}{str(a_toon[k]):>18s}")
    print(f"\n  naive ramps touched: {a_naive['ramps_touched']}")
    print(f"  toon  ramps touched: {a_toon['ramps_touched']}")

    out = ROOT / "proof"
    out.mkdir(exist_ok=True)
    scale = 6
    sheet = Image.new("RGB", (TARGET * scale * 2 + 24, TARGET * scale + 8), (18, 16, 22))
    sheet.paste(to_image(naive, TARGET, scale), (8, 4))
    sheet.paste(to_image(toon, TARGET, scale), (TARGET * scale + 16, 4))
    sheet.save(out / "comparison.png")
    to_image(naive, TARGET, 6).save(out / "naive.png")
    to_image(toon, TARGET, 6).save(out / "ramp_quantized.png")
    print(f"\nwrote {out}/comparison.png  (left: naive, right: ramp-quantized)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
