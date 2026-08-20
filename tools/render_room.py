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
from mesh import LightRig, Pool, ShadowMap, rasterize  # noqa: E402
from pixelize import (  # noqa: E402
    apply_outline, downsample_modal, load_palette, shade_toon,
)

ROOT = Path(__file__).resolve().parent.parent
ROOM_W, ROOM_D = 14, 10

# Window apertures, shared by the geometry and the light rig so the two cannot
# drift apart. Sill and head match wall_run's a/b.
WIN_X = (4, 5, 10, 11)
WIN_Y = (6, 7)
SILL, HEAD = 0.38, 1.22
LAMPS = ((3.3, 5.3), (6.6, 7.6), (9.9, 4.5))


def light_rig():
    """Lamp pools, a wash over the service counter, and glow inside each window.

    Pools sit just under each shade rather than at it, so the brightest ring
    lands on the table below instead of on the lamp itself.
    """
    pools = [Pool((lx, ly, 1.24), 3.6, 0.62) for lx, ly in LAMPS]
    pools.append(Pool((4.9, 1.20, 1.26), 4.4, 0.58))       # service counter
    for i in WIN_X:                                        # daylight at the glass
        pools.append(Pool((i + 0.5, 0.30, 0.95), 3.0, 0.40))
    for i in WIN_Y:
        pools.append(Pool((0.30, i + 0.5, 0.95), 3.0, 0.40))
    return LightRig(pools)


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
                               (10.4, 6.9, 2.8, 2.6, "foliage")):
        add(A.rug(rw, rd, rm), at=(rx, ry, 0), name="floor#rug", track=False)
    add(A.wall_run((0, 0), "x", ROOM_W, openings=WIN_X), name="wall", track=False)
    add(A.wall_run((0, 0), "y", ROOM_D, openings=WIN_Y), name="wall", track=False)

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
    # Painted seating, cycling through the ramps that were starved of frame.
    # Painted frames sit BELOW the wood in lightness, not beside it. At -1 the
    # sky ramp measures L=0.70, identical to wood step 4, so the chairs differed
    # only in hue and read as equal-weight pastel blocks that pulled focus off
    # the counter. At -3 they are deep painted wood: they separate by hue but
    # recede by value, which is the whole point. One in three, not one in two.
    #
    # And no `sky` on furniture. The cool ramp is reserved for glass, windows
    # and daylight; spending it on chairs put six blue masses through a warm
    # room and made the coldest thing in frame a piece of seating. Reserving a
    # ramp for one job is what lets it mean something.
    FRAMES = ("wood", "wood", "rose-2", "wood", "wood", "foliage-3")
    tables = [(3.3, 5.3, "cafe", "cream"), (6.6, 7.7, "books", "wood"),
              (11.9, 8.2, "cafe", "cream")]
    for n, (tx, ty, clutter, ttop) in enumerate(tables):
        add(A.table_round(ttop), at=(tx, ty, 0), name=f"table#{n}")
        add(A.table_clutter(clutter), at=(tx, ty, 0.69), name=f"clutter#{n}")
        for k, (dx, dy, rot) in enumerate((
                (0.0, 1.15, 180), (0.0, -1.15, 0), (1.15, 0.0, 90), (-1.15, 0.0, 270))):
            add(A.chair(cushion="rose" if (n + k) % 3 == 0 else None,
                        frame=FRAMES[(n * 4 + k) % len(FRAMES)]),
                at=(tx + dx, ty + dy, 0), rot=rot, name=f"chair#{n}_{k}")

    # --- 4-top with four chairs
    add(A.table_4top(), at=(9.5, 4.5, 0), name="table#4top")
    add(A.table_clutter("work"), at=(9.9, 4.5, 0.71), name="clutter#4top")
    for cx in (9.8, 11.0):
        add(A.chair(),                  at=(cx, 3.35, 0), rot=0,   name=f"chair#4t_{cx}a")
        add(A.chair(),                  at=(cx, 5.65, 0), rot=180, name=f"chair#4t_{cx}b")

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

    # --- dressing the measured dead zones
    #
    # Occupancy mapped at 58% with an 8-tile bare rectangle at x12-13, y3-6 and
    # smaller voids at x3-4/y7-9 and x8-9/y7-9. Each cluster below targets one
    # of them; a room reads as under-dressed long before it reads as under-lit.
    add(A.rug(3.0, 2.3, "wood"), at=(2.9, 7.1, 0), name="floor#rug3", track=False)
    add(A.armchair(),   at=(3.6, 7.6, 0), rot=205, name="seat#arm1", centre=True)
    add(A.armchair(),   at=(3.9, 9.0, 0), rot=25,  name="seat#arm2", centre=True)
    add(A.side_table(), at=(3.0, 8.5, 0),          name="table#side1", centre=True)
    add(A.flower_vase(), at=(3.0, 8.5, 0.53),      name="clutter#vase1", centre=True)

    add(A.bench(2.0),   at=(12.6, 3.6, 0), rot=0,  name="seat#bench1", centre=True)
    add(A.side_table(), at=(12.5, 4.8, 0),         name="table#side2", centre=True)
    add(A.armchair(),   at=(12.5, 5.9, 0), rot=180, name="seat#arm3", centre=True)
    add(A.basket("foliage"), at=(13.4, 4.7, 0),    name="decor#basket1", centre=True)

    add(A.coat_rack("sky"), at=(8.5, 8.4, 0),      name="decor#coats", centre=True)
    add(A.sandwich_board(), at=(6.4, 9.1, 0), rot=25, name="decor#aframe", centre=True)

    # --- focal hierarchy at the service counter
    #
    # The interaction zone carried the same detail density and contrast as bare
    # floor, so the composition had no centre. A lit sign above it and the
    # densest cluster of small props under it is how the genre solves this.
    add(A.wall_sign(), at=(5.55, 0.0, 0), name="decor#sign", track=False)
    add(A.wall_shelf(1.8), at=(2.1, 0.10, 0.66), name="decor#shelf1", track=False)
    add(A.wall_shelf(1.8), at=(6.9, 0.10, 0.66), name="decor#shelf2", track=False)
    add(A.cake_stand(), at=(5.55, 0.95, 0.92), name="clutter#cake", centre=True)
    add(A.cup_and_saucer(), at=(5.9, 0.75, 0.92), name="clutter#cup1")
    add(A.cup_and_saucer(), at=(6.9, 1.10, 0.92), name="clutter#cup2")
    add(A.flower_vase(),    at=(7.6, 0.95, 0.92), name="clutter#vase2", centre=True)

    # --- characters
    add(C.build(C.BARISTA), at=(4.9, 1.95, 0), rot=0, name="char#barista")
    seated = [(3.3, 5.3 - 0.95, 0, 0), (3.3, 5.3 + 0.95, 180, 2),
              (6.6, 7.6 - 0.95, 0, 4), (9.8, 3.55, 0, 1), (11.0, 5.45, 180, 6)]
    for i, (cx, cy, rot, who) in enumerate(seated):
        add(C.build(C.CUSTOMERS[who], seated=True), at=(cx, cy, 0.0), rot=rot,
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
    floating = L.grounded()
    if floating:
        print(f"  FLOATING ({len(floating)}):")
        for f in floating:
            print(f"    {f}")
    else:
        print("  everything rests on a surface")
    facing = L.seating_faces_tables()
    if facing:
        print(f"  SEATING FACING ({len(facing)}):")
        for f in facing:
            print(f"    {f}")
    else:
        print("  all seating faces its table")
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
                            fill=0.0 if args.no_shadows else 0.20,
                            bounce=0.26, rig=light_rig(),
                            ambient=0.05, key_gain=0.60)

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
