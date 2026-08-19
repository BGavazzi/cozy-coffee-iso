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
import character as C  # noqa: E402
from layout import Layout  # noqa: E402
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

    Seating is placed on all four sides of each table rather than two, and every
    placement is tracked so `Layout.collisions()` can catch interpenetration.
    """
    L = Layout()
    add = L.add

    add(A.floor(ROOM_W, ROOM_D), name="floor", track=False)
    for rx, ry, rw, rd, rm in ((2.2, 4.1, 2.6, 2.6, "foliage"),
                               (10.5, 6.9, 3.0, 2.8, "rose")):
        add(A.rug(rw, rd, rm), at=(rx, ry, 0), name="floor#rug", track=False)
    add(A.wall_run((0, 0), "x", ROOM_W, openings=(4, 5, 10, 11)), name="wall", track=False)
    add(A.wall_run((0, 0), "y", ROOM_D, openings=(6, 7)), name="wall", track=False)

    # --- service counter run against the far-right wall (modules tile flush)
    for i in range(6):
        add(A.counter(), at=(2.0 + i, 0.85, 0), name=f"counter#{i}")
    add(A.espresso_machine(), at=(2.3, 0.95, 0.92), name="prop#espresso")
    add(A.grinder(),          at=(4.4, 0.95, 0.92), name="prop#grinder")
    add(A.register(),         at=(6.3, 0.95, 0.92), name="prop#register")
    add(A.plant_small(),      at=(7.15, 0.95, 0.92), name="prop#plant")
    add(A.table_clutter("counter"), at=(5.35, 0.95, 0.92), name="clutter#counter")
    add(A.pastry_case(), at=(2.2, 2.05, 0), name="prop#pastry")
    for mx in (3.1, 4.6):
        add(A.menu_board(), at=(mx, 0.04, 0), name=f"decor#menu{mx}")

    # --- cafe tables, chairs on all four sides
    tables = [(3.3, 5.3, "cafe"), (6.6, 7.7, "books"), (11.9, 8.2, "cafe")]
    for n, (tx, ty, clutter) in enumerate(tables):
        add(A.table_round(), at=(tx, ty, 0), name=f"table#{n}")
        add(A.table_clutter(clutter), at=(tx, ty, 0.69), name=f"clutter#{n}")
        for k, (dx, dy, rot) in enumerate((
                (0.0, 1.15, 180), (0.0, -1.15, 0), (1.15, 0.0, 270), (-1.15, 0.0, 90))):
            add(A.chair(cushion="rose" if (n + k) % 3 == 0 else None),
                at=(tx + dx, ty + dy, 0), rot=rot, name=f"chair#{n}_{k}")

    # --- 4-top with four chairs
    add(A.table_4top(), at=(9.5, 4.5, 0), name="table#4top")
    add(A.table_clutter("work"), at=(9.9, 4.5, 0.71), name="clutter#4top")
    for cx in (9.8, 11.0):
        add(A.chair(), at=(cx, 3.35, 0), rot=0,   name=f"chair#4t_{cx}a")
        add(A.chair(), at=(cx, 5.65, 0), rot=180, name=f"chair#4t_{cx}b")

    # --- window bar with stools along the far-left wall
    for i in range(3):
        add(A.counter(kick=False), at=(0.45, 5.3 + i * 1.5, 0), name=f"bar#{i}")
        add(A.stool(), at=(1.70, 5.3 + i * 1.5, 0), name=f"stool#{i}")

    # --- dressing
    add(A.plant_large(), at=(0.5, 3.2, 0),  name="decor#plant1")
    add(A.plant_large(), at=(12.5, 1.0, 0), name="decor#plant2")
    add(A.plant_large(), at=(7.1, 4.2, 0),  name="decor#plant3")
    add(A.bookshelf(),   at=(9.9, 0.25, 0), name="decor#shelf")
    add(A.crate(), at=(0.55, 1.15, 0),      name="decor#crate1")
    add(A.crate(), at=(0.55, 1.15, 0.52),   name="decor#crate2")
    add(A.crate(), at=(13.15, 1.9, 0),      name="decor#crate3")
    for lx, ly in ((3.3, 5.3), (6.6, 7.6), (9.9, 4.5)):
        add(A.pendant_lamp(), at=(lx - 0.5, ly - 0.5, 0.60), name=f"decor#lamp{lx}",
            track=False)

    # --- characters
    add(C.build(C.BARISTA), at=(4.9, 1.95, 0), rot=0, name="char#barista")
    seated = [(3.3, 5.3 - 0.95, 0, 0), (3.3, 5.3 + 0.95, 180, 2),
              (6.6, 7.6 - 0.95, 0, 4), (9.8, 3.55, 0, 1), (11.0, 5.45, 180, 6)]
    for i, (cx, cy, rot, who) in enumerate(seated):
        add(C.build(C.CUSTOMERS[who], seated=True), at=(cx, cy, 0.45), rot=rot,
            name=f"char#seat{i}")
    add(C.build(C.CUSTOMERS[3]), at=(6.0, 2.6, 0), rot=200, name="char#queue0")
    add(C.build(C.CUSTOMERS[7]), at=(6.8, 3.3, 0), rot=200, name="char#queue1")

    return L


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

    L = build_room()
    hits = L.collisions()
    print(f"placements: {len(L.items)}")
    if hits:
        print(f"  COLLISIONS ({len(hits)}):")
        for h in hits:
            print(f"    {h}")
    else:
        print("  no collisions")
    mesh = L.mesh()
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
                            fill=0.0 if args.no_shadows else 0.16,
                            bounce=0.22)

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
