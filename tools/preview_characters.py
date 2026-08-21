#!/usr/bin/env python3
"""Character preview: the roster, one archetype through 8 directions, and extras.

Demonstrates the payoff of modular assembly -- every figure below is the same
parts library with a different short spec, so adding a ninth archetype costs a
few lines rather than a mesh.

The third row costs nothing at all. Those specs are not written anywhere: they
are proposed and tested against `check_contrast` and `check_palette_spread`
until they pass, which is the same move `Layout.scatter` made with the
placement checks. Nine hand-written archetypes were the largest asset left in a
repo that is supposed to be a factory.

    python tools/preview_characters.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import character as C  # noqa: E402
from isorender import DimetricCamera, camera_light  # noqa: E402
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
    # Grain, matching `animate.render_frame`. A preview sheet whose render path
    # has drifted from the shipping one is worse than no sheet, because every
    # judgement made from it is about a picture the game will never show.
    mat, lam, _ = rasterize(mesh, cam, size, target=centre, shadows=sm, fill=0.20, bounce=0.26,
                            ambient=0.05, key_gain=0.60, grain=1.0, ramps=ramps)
    px = downsample_modal(shade_toon(mat, lam, size, ramps, dither=True), size, FACTOR)
    # Sorted index, not `hash(m) % 251`. Collisions are near-certain by the
    # birthday bound among thirty materials, and Python randomises string
    # hashing per process, so which materials collided -- and therefore which
    # outlines came out the wrong colour -- changed on every run. Fixed in
    # `render_room` and `animate` a pass ago; this file was missed, so the one
    # sheet a person actually looks at when judging characters was the one
    # still doing it.
    ids = {m: (i % 256, i // 256, 0)
           for i, m in enumerate(sorted(m for m in set(mat) if m is not None))}
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
                              3 * (cell + label + pad) + pad + 28), (18, 16, 22))
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

    y3 = y2 + cell + label + pad + 14
    d.text((pad, y3 - 16), "generated extras -- proposed and tested, not typed",
           fill=(150, 145, 158))
    print(chr(10) + "generated extras:")
    extras = C.generate_roster(cols, seed=1, ramps=ramps)
    for i, spec in enumerate(extras):
        px = render_one(C.build(spec), 45.0, ramps)
        x = pad + i * (cell + pad)
        sheet.paste(to_img(px, scale), (x, y3))
        d.text((x + 2, y3 + cell + 4), spec.name, fill=(214, 208, 218))
        print(f"  {spec.name:9s} shirt={spec.shirt:10s} trousers={spec.trousers:10s} "
              f"hair={spec.hair_style:6s}/{spec.hair_mat:10s} "
              f"acc={spec.accessory_kind or '-'}")
    bad = C.check_contrast(ramps, extras) + C.check_palette_spread(extras)
    print(f"  {len(bad)} check failures across {len(extras)} generated specs")

    out = ROOT / "proof" / "characters.png"
    out.parent.mkdir(exist_ok=True)
    sheet.save(out)
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
