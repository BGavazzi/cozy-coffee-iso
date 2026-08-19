#!/usr/bin/env python3
"""Character preview: the roster, and one archetype through all 8 directions.

Demonstrates the payoff of modular assembly -- every figure below is the same
parts library with a different short spec, so adding a ninth archetype costs a
few lines rather than a mesh.

    python tools/preview_characters.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import character as C  # noqa: E402
from isorender import DimetricCamera, camera_light, dot  # noqa: E402
from mesh import ShadowMap, rasterize  # noqa: E402
from pixelize import (  # noqa: E402
    apply_outline, downsample_modal, load_palette, shade_toon,
)

ROOT = Path(__file__).resolve().parent.parent
TARGET, FACTOR = 64, 4
BG = (30, 27, 36)


def render_one(mesh, azimuth, ramps, seated=False):
    cam = DimetricCamera(azimuth)
    cam.span = 0.95
    size = TARGET * FACTOR
    centre = (0.0, 0.0, 0.70 if not seated else 0.42)
    sm = ShadowMap(mesh, camera_light(cam), res=256)
    mat, lam, _ = rasterize(mesh, cam, size, target=centre, shadows=sm, fill=0.16, bounce=0.28)
    px = downsample_modal(shade_toon(mat, lam, size, ramps, dither=True), size, FACTOR)
    ids = {m: (hash(m) % 251, 0, 0) for m in set(mat) if m is not None}
    back = {v: k for k, v in ids.items()}
    small = downsample_modal([ids[m] if m is not None else None for m in mat],
                             size, FACTOR)
    return apply_outline(px, [back.get(c) if c else None for c in small], TARGET, ramps)


def to_img(px, scale):
    img = Image.new("RGB", (TARGET, TARGET), BG)
    img.putdata([c if c is not None else BG for c in px])
    return img.resize((TARGET * scale, TARGET * scale), Image.NEAREST)


def main() -> int:
    ramps = load_palette()
    roster = [("barista", C.BARISTA)] + [(s.name, s) for s in C.CUSTOMERS]
    scale, pad, label = 3, 8, 20
    cell = TARGET * scale

    cols = len(roster)
    sheet = Image.new("RGB", (cols * (cell + pad) + pad,
                              2 * (cell + label + pad) + pad + 14), (18, 16, 22))
    d = ImageDraw.Draw(sheet)

    print("roster, facing camera:")
    for i, (name, spec) in enumerate(roster):
        px = render_one(C.build(spec), 45.0, ramps)
        x = pad + i * (cell + pad)
        sheet.paste(to_img(px, scale), (x, pad))
        d.text((x + 2, pad + cell + 4), name, fill=(214, 208, 218))
        print(f"  {name:9s} shirt={spec.shirt:8s} hair={spec.hair_style:6s} "
              f"acc={spec.accessory_kind or '-'}")

    y2 = pad + cell + label + pad + 14
    d.text((pad, y2 - 16), "one archetype, all 8 directions", fill=(150, 145, 158))
    print("\n'regular' through 8 azimuths:")
    for k in range(8):
        az = 45.0 + k * 45.0
        px = render_one(C.build(C.CUSTOMERS[2]), az, ramps)
        x = pad + k * (cell + pad)
        sheet.paste(to_img(px, scale), (x, y2))
        d.text((x + 2, y2 + cell + 4), f"dir{k}", fill=(214, 208, 218))
        print(f"  dir{k} az={az:5.1f}")

    out = ROOT / "proof" / "characters.png"
    out.parent.mkdir(exist_ok=True)
    sheet.save(out)
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
