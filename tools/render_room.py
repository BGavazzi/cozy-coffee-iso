#!/usr/bin/env python3
"""Compose and render the whole shop as one screen.

Everything runs through the same path a single sprite does -- same camera, same
ramp quantization, same palette -- so this doubles as an integration test. If the
projection, key light or palette are wrong, a room-scale composition shows it far
more brutally than one prop on transparency.

    python tools/render_room.py [--target 480] [--factor 3]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import assetlib as A  # noqa: E402
from isorender import DimetricCamera, camera_light, dot  # noqa: E402
from mesh import ShadowMap, rasterize  # noqa: E402
from pixelize import (  # noqa: E402
    apply_outline, downsample_modal, load_palette, shade_toon,
)

ROOT = Path(__file__).resolve().parent.parent
ROOM_W, ROOM_D = 14, 10


def build_room():
    """Layout.

    The camera looks from +x/+y, so the *far* walls -- the only two that may be
    drawn -- are at x=0 and y=0. Walling the near sides would occlude the room,
    which is why isometric games only ever build the back two.
    """
    put = A.transformed
    parts = [
        A.floor(ROOM_W, ROOM_D, checker=False),
        A.wall_run((0, 0), "x", ROOM_W, openings=(4, 5, 10, 11)),   # far-right wall
        A.wall_run((0, 0), "y", ROOM_D, openings=(6, 7)),           # far-left wall
    ]

    # --- service counter run against the far-right wall
    for i in range(6):
        parts.append(put(A.counter(), at=(2.0 + i, 0.9, 0)))
    parts.append(put(A.espresso_machine(), at=(2.3, 1.0, 0.90)))
    parts.append(put(A.grinder(),          at=(4.4, 1.0, 0.90)))
    parts.append(put(A.register(),         at=(6.3, 1.0, 0.90)))
    parts.append(put(A.plant_small(),      at=(7.2, 1.0, 0.90)))
    parts.append(put(A.pastry_case(),      at=(2.2, 2.15, 0.0)))
    for mx in (3.0, 4.5):
        parts.append(put(A.menu_board(), at=(mx, 0.06, 0)))

    # --- seating in the open floor
    for tx, ty in ((3.2, 5.2), (6.4, 7.4), (3.4, 8.4), (12.2, 6.9)):
        parts.append(put(A.table_round(), at=(tx, ty, 0)))
        parts.append(put(A.chair(), rot_z=180, at=(tx, ty + 1.05, 0)))
        parts.append(put(A.chair(), rot_z=0,   at=(tx, ty - 1.05, 0)))
        parts.append(put(A.cup_and_saucer(), at=(tx + 0.10, ty + 0.05, 0.68)))

    parts.append(put(A.table_4top(), at=(9.4, 4.6, 0)))
    for cx in (9.7, 10.9):
        parts.append(put(A.chair(), rot_z=0,   at=(cx, 3.55, 0)))
        parts.append(put(A.chair(), rot_z=180, at=(cx, 5.65, 0)))
    parts.append(put(A.cup_and_saucer(), at=(10.2, 5.0, 0.68)))

    # --- window bar with stools along the far-left wall
    for i in range(3):
        parts.append(put(A.counter(), at=(0.55, 5.4 + i * 1.4, 0)))
        parts.append(put(A.stool(),   at=(1.75, 5.4 + i * 1.4, 0)))

    # --- dressing
    parts.append(put(A.plant_large(), at=(0.5, 3.4, 0)))
    parts.append(put(A.plant_large(), at=(12.4, 1.1, 0)))
    parts.append(put(A.plant_large(), at=(6.9, 4.4, 0)))
    parts.append(put(A.plant_small(), at=(9.4, 8.6, 0)))
    parts.append(put(A.crate(),       at=(12.6, 8.9, 0)))
    parts.append(put(A.bookshelf(),   at=(9.9, 0.35, 0)))
    parts.append(put(A.crate(),       at=(0.6, 1.2, 0)))
    parts.append(put(A.crate(),       at=(0.6, 1.2, 0.52)))
    for lx, ly in ((3.2, 5.4), (6.6, 7.6), (9.9, 4.6)):
        parts.append(put(A.pendant_lamp(), at=(lx - 0.5, ly - 0.5, 0.60)))

    return A.merge(*parts)


def frame(mesh, cam, target_px, margin=0.04):
    """Fit the camera span and target to the mesh's projected bounds."""
    us = [dot(v, cam.right) for v in mesh.verts]
    vs = [dot(v, cam.up) for v in mesh.verts]
    cu, cv = (max(us) + min(us)) / 2, (max(vs) + min(vs)) / 2
    span = max(max(us) - min(us), max(vs) - min(vs)) / 2 * (1 + margin)
    centre = tuple(cam.right[i] * cu + cam.up[i] * cv for i in range(3))
    return span, centre


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=480)
    ap.add_argument("--factor", type=int, default=3)
    ap.add_argument("--azimuth", type=float, default=45.0)
    ap.add_argument("--out", default=str(ROOT / "proof" / "shop.png"))
    ap.add_argument("--no-shadows", action="store_true")
    args = ap.parse_args()

    mesh = build_room()
    print(f"room mesh: {len(mesh.verts)} verts, {len(mesh.faces)} tris")

    cam = DimetricCamera(args.azimuth)
    cam.span, centre = frame(mesh, cam, args.target)
    print(f"camera span {cam.span:.2f}, azimuth {args.azimuth}")

    size = args.target * args.factor
    ramps = load_palette()
    print(f"rasterizing {size}x{size} -> {args.target}x{args.target} ...")
    sm = None
    if not args.no_shadows:
        print("building shadow map ...")
        sm = ShadowMap(mesh, camera_light(cam), res=768)
    mat, lam, _ = rasterize(mesh, cam, size, target=centre, shadows=sm,
                            fill=0.0 if args.no_shadows else 0.16)

    px = downsample_modal(shade_toon(mat, lam, size, ramps, dither=True),
                          size, args.factor)
    ids = {m: (hash(m) % 251, 0, 0) for m in set(mat) if m is not None}
    back = {v: k for k, v in ids.items()}
    small = downsample_modal([ids[m] if m is not None else None for m in mat],
                             size, args.factor)
    px = apply_outline(px, [back.get(c) if c is not None else None for c in small],
                       args.target, ramps)

    bg = (26, 23, 31)
    img = Image.new("RGB", (args.target, args.target), bg)
    img.putdata([c if c is not None else bg for c in px])

    # crop to content, then scale for viewing
    solid = [(i % args.target, i // args.target) for i, c in enumerate(px) if c]
    x0 = min(p[0] for p in solid); x1 = max(p[0] for p in solid)
    y0 = min(p[1] for p in solid); y1 = max(p[1] for p in solid)
    img = img.crop((x0, y0, x1 + 1, y1 + 1))
    out = Path(args.out)
    out.parent.mkdir(exist_ok=True)
    img.resize((img.width * 2, img.height * 2), Image.NEAREST).save(out)
    print(f"wrote {out}  ({img.width}x{img.height} native)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
