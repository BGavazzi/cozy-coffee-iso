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
SILL, HEAD = 0.58, 1.82
LAMPS = ((3.3, 5.3), (6.6, 7.6), (9.9, 4.5))


def light_rig():
    """Lamp pools, a wash over the service counter, and glow inside each window.

    Pools sit just under each shade rather than at it, so the brightest ring
    lands on the table below instead of on the lamp itself.
    """
    pools = [Pool((lx, ly, 1.24), 3.6, 0.62) for lx, ly in LAMPS]
    # Service counter: a tight core inside a wide wash, not one broad pool.
    # At radius 4.4 the counter light spilled across half the room, which raised
    # the mean everywhere and left the zone leading by only +0.038 L. A small
    # bright core is what actually separates it from its surroundings.
    pools.append(Pool((4.9, 1.20, 1.26), 2.6, 0.66))
    pools.append(Pool((4.9, 1.35, 1.05), 4.6, 0.30))
    for i in WIN_X:                                        # daylight at the glass
        pools.append(Pool((i + 0.5, 0.30, 0.95), 3.0, 0.40))
    for i in WIN_Y:
        pools.append(Pool((0.30, i + 0.5, 0.95), 3.0, 0.40))
    # Negative pools in the two corners furthest from the counter. Edge density
    # measured a 1.42x spread across the frame -- near enough to flat that the
    # eye had nowhere to land -- and the counter cannot simply be brightened
    # because it is already near the top of its ramp. Taking light out of the
    # periphery is the move that actually builds a centre.
    pools.append(Pool((13.6, 9.6, 0.5), 6.5, -0.36))
    pools.append(Pool((0.4, 9.8, 0.5), 5.5, -0.30))
    pools.append(Pool((13.8, 0.8, 0.5), 4.6, -0.22))
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
    for rx, ry, rw, rd, rm in ((3.5, 3.8, 2.6, 2.6, "foliage"),
                               (10.4, 6.9, 2.8, 2.6, "foliage")):
        add(A.rug(rw, rd, rm), at=(rx, ry, 0), name="floor#rug", track=False)
    add(A.wall_run((0, 0), "x", ROOM_W, openings=WIN_X), name="wall", track=False)
    add(A.wall_run((0, 0), "y", ROOM_D, openings=WIN_Y), name="wall", track=False)

    # Everything from here on gets warped. The shell does not: a room whose
    # walls and floor wander reads as a bad render, while furniture that leans
    # and wears reads as furniture. The displacement is sampled in room
    # coordinates, so the six chairs around three tables come out as six
    # siblings rather than six copies, at no cost in authoring.
    L.warp_default = 0.030

    # --- service counter run against the far-right wall (modules tile flush)
    for i in range(6):
        # Seed base chosen for the RUN, not the module: at 4 the six
        # modules come out drawers/shelf/plain/plain/beaded/plain,
        # which is a fitted counter. Most bases give four plains in
        # six, and a couple give three distinct fronts in a row,
        # which reads as a showroom. The generator is right either
        # way; choosing where a run starts is the room's job.
        add(A.counter(seed=4 + i), at=(2.0 + i, 0.85, 0), name=f"counter#{i}")
    add(A.grinder(),          at=(4.4, 0.95, 0.92), name="prop#grinder")
    add(A.register(),         at=(6.3, 0.95, 0.92), name="prop#register")
    add(A.plant_small(seed=21), at=(7.15, 0.95, 0.92), name="prop#plant")
    add(A.table_clutter("counter"), at=(5.35, 0.95, 0.92), name="clutter#counter")
    # Menu boards hang ABOVE the counter-top props, not level with them. At
    # z=0 the board spans 0.55-1.30 and the espresso machine on the counter
    # spans 0.92-1.52 -- the same screen band, one tile apart in depth, so the
    # machine covered 82% of the board it sits in front of. Lifting them clears
    # the machines entirely and is also where a real shop hangs its menu.
    # On solid wall, not over glass. WIN_X opens tiles 4, 5, 10 and 11, and a
    # board at x=4.6 spans 4.7-5.5 -- dead centre of a window. Boards hung over
    # the daylight both hid the glass and lost their own contrast against it.
    # Tiles 2 and 3 are solid and sit directly above the counter run.
    for mx in (2.15, 3.05):
        add(A.menu_board(), at=(mx, 0.04, 0.62), name=f"decor#menu{mx}")
    # And the machine goes in after the boards it hangs beneath, for the same
    # reason the pastry case goes in after the crates: `add_seeded` can only
    # solve against what is already in the room. Seeding the machine gave it an
    # optional raised back panel, and the first seed with one covered 41% of a
    # menu board -- caught by the check, then avoided by the solver rather than
    # by a person reading the check's output and typing a different number.
    L.add_seeded(lambda k: A.espresso_machine(seed=k), range(1, 12),
                 at=(2.3, 0.95, 0.92), name="prop#espresso")

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
    tables = [(4.6, 5.0, "cafe", "cream"), (6.6, 7.7, "books", "wood"),
              (11.9, 8.2, "cafe", "cream")]
    for n, (tx, ty, clutter, ttop) in enumerate(tables):
        top = A.table_round(ttop, seed=17 + n * 5)
        add(top, at=(tx, ty, 0), name=f"table#{n}")
        add(A.table_clutter(clutter), at=(tx, ty, top.top_z), name=f"clutter#{n}")
        for k, (dx, dy, rot) in enumerate((
                (0.0, 1.15, 180), (0.0, -1.15, 0), (1.15, 0.0, 90), (-1.15, 0.0, 270))):
            add(A.chair(cushion="rose" if (n + k) % 3 == 0 else None,
                        frame=FRAMES[(n * 4 + k) % len(FRAMES)],
                        seed=51 + n * 4 + k),
                at=(tx + dx, ty + dy, 0), rot=rot, name=f"chair#{n}_{k}")

    # --- 4-top with four chairs
    big = A.table_4top(seed=6)
    add(big, at=(9.5, 4.5, 0), name="table#4top")
    add(A.table_clutter("work"), at=(9.9, 4.5, big.top_z), name="clutter#4top")
    for cx in (9.8, 11.0):
        add(A.chair(seed=int(cx * 10)),  at=(cx, 3.35, 0), rot=0,   name=f"chair#4t_{cx}a")
        add(A.chair(seed=int(cx * 10) + 7), at=(cx, 5.65, 0), rot=180, name=f"chair#4t_{cx}b")

    # --- window bar with stools along the far-left wall
    for i in range(3):
        add(A.counter(kick=False, seed=1 + i, front="x"),
            at=(0.45, 5.3 + i * 1.5, 0), name=f"bar#{i}")
        add(A.stool(seed=91 + i), at=(1.70, 5.3 + i * 1.5, 0), name=f"stool#{i}")

    # --- dressing
    add(A.plant_large(seed=3), at=(0.5, 3.2, 0),  name="decor#plant1")
    add(A.plant_large(seed=8), at=(12.5, 1.0, 0), name="decor#plant2")
    add(A.plant_large(seed=15), at=(7.1, 4.2, 0),  name="decor#plant3")
    add(A.bookshelf(seed=4), at=(9.9, 0.25, 0), name="decor#shelf")
    add(A.crate(seed=11), at=(0.55, 1.15, 0),   name="decor#crate1")
    add(A.crate(seed=12), at=(0.55, 1.15, A.crate(seed=11).top_z),
        name="decor#crate2")
    add(A.crate(seed=13), at=(13.15, 1.9, 0),   name="decor#crate3")
    # The case is placed HERE, after the crates, and not up with the counter
    # props it belongs to. `add_seeded` solves against what is already in the
    # room, so a prop that has to clear its neighbours has to be added after
    # them -- the same reason `scatter` runs last. Placed with the counter it
    # would have found an empty corner and taken the first seed.
    #
    # Nudged left by 0.3 when `reader`'s scarf grew: the scarf had been
    # measuring zero pixels of silhouette, so widening it to something a person
    # is actually wearing pushed the seated figure over the 35% occlusion floor
    # against the case two tiles behind it.
    L.add_seeded(lambda k: A.pastry_case(seed=k), range(1, 12),
                 at=(1.9, 2.05, 0), name="prop#pastry")
    for lx, ly in ((4.6, 5.0), (6.6, 7.6), (9.9, 4.5)):
        add(A.pendant_lamp(), at=(lx - 0.5, ly - 0.5, 0.60), name=f"decor#lamp{lx}",
            track=False)

    # The seating that used to sit at x 2.6-3.9 moved right by roughly a tile.
    # `screen_occlusion` reported a seated customer covering 43% of a bar stool
    # and an armchair covering 36% of another -- both because the window bar runs
    # along the left wall at x 0.45-1.70 and the lounge sat at the same screen
    # column, two tiles nearer the camera. Moving the bar made it worse; the
    # occluders were the thing in the wrong place. It also evens out a room whose
    # left third was crowded while the middle stayed empty.
    # --- dressing the measured dead zones
    #
    # Occupancy mapped at 58% with an 8-tile bare rectangle at x12-13, y3-6 and
    # smaller voids at x3-4/y7-9 and x8-9/y7-9. Each cluster below targets one
    # of them; a room reads as under-dressed long before it reads as under-lit.
    add(A.rug(3.0, 2.3, "wood"), at=(3.6, 7.1, 0), name="floor#rug3", track=False)
    L.add_seeded(lambda k: A.armchair(seed=k), range(5, 16), at=(4.4, 7.6, 0),
                 rot=205, name="seat#arm1", centre=True)
    L.add_seeded(lambda k: A.armchair(seed=k), range(9, 20), at=(4.7, 9.0, 0),
                 rot=25, name="seat#arm2", centre=True)
    add(A.side_table(), at=(3.4, 9.1, 0),          name="table#side1", centre=True)
    add(A.flower_vase(seed=21), at=(3.4, 9.1, 0.53), name="clutter#vase1", centre=True)

    L.add_seeded(lambda k: A.bench(2.0, seed=k), range(4, 15), at=(12.6, 3.6, 0),
                 rot=0, name="seat#bench1", centre=True)
    add(A.side_table(), at=(12.5, 4.8, 0),         name="table#side2", centre=True)
    L.add_seeded(lambda k: A.armchair(seed=k), range(2, 13), at=(12.5, 5.9, 0),
                 rot=180, name="seat#arm3", centre=True)
    add(A.basket("foliage", seed=31), at=(13.3, 5.6, 0), name="decor#basket1", centre=True)

    # Against the left wall, not mid-floor. A free-standing rack at (8.5, 8.4)
    # projected straight over a chair 1.9 tiles behind it and hid 67% of it --
    # a silhouette nobody modelled, and invisible to every world-space check
    # because in plan view the two are nowhere near each other. It also fills
    # the dead wedge at screen-left, which is where a coat rack belongs anyway.
    add(A.coat_rack("sky"), at=(11.4, 0.45, 0),   name="decor#coats", centre=True)
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
    add(A.cup_and_saucer(), at=(5.6, 0.72, 0.92), name="clutter#cup1")
    add(A.cup_and_saucer(), at=(5.05, 1.15, 0.92), name="clutter#cup2")
    add(A.flower_vase(seed=22), at=(7.6, 0.95, 0.92), name="clutter#vase2", centre=True)

    # --- generated dressing
    #
    # Everything above this line is 85 coordinates typed by hand. Everything
    # below is proposed and filtered by the same checks that used to only grade
    # hand placement: `scatter` offers a position, `collisions`, the z-stacking
    # rule and `screen_occlusion` reject it, and what survives is dressing
    # nobody had to place. A saturated region returning fewer than asked is the
    # solver working.
    #
    # Bands hug the walls and the corners because that is where a cafe actually
    # accumulates clutter, and because the middle has to stay walkable. The
    # counts are deliberately larger than the regions can hold.
    # Clutter hugs the FAR walls (x=0, y=0). The near edges are open to the
    # camera, and the first generated pass scattered crates along them, where
    # they stood in front of the whole room. A crate is 0.76 tiles square, which
    # is furniture rather than clutter: nine of them read as a stockroom, so the
    # count is small and the regions are tight. The small props carry the
    # density instead.
    made = 0
    made += L.scatter(lambda i: A.crate(seed=140 + i), (0.55, 1.7, 1.35, 4.4), 3,
                      "decor#gcrate", seed=11)
    made += L.scatter(lambda i: A.basket("foliage", seed=150 + i),
                      (8.7, 0.35, 11.2, 1.15), 4,
                      "decor#gbasket", seed=12)
    made += L.scatter(lambda i: A.plant_small(seed=40 + i), (0.5, 0.45, 13.4, 1.55), 6,
                      "decor#gplantN", seed=13)
    made += L.scatter(lambda i: A.plant_small(seed=70 + i), (0.45, 1.6, 1.55, 9.3), 5,
                      "decor#gplantW", seed=18)
    made += L.scatter(lambda i: A.basket("rose", seed=160 + i), (11.8, 1.6, 13.3, 3.6), 3,
                      "decor#gbasket2", seed=14)
    made += L.scatter(lambda i: A.cup_and_saucer(), (2.1, 0.6, 7.9, 1.3), 6,
                      "clutter#gcup", z=0.92, seed=16)
    made += L.scatter(lambda i: A.flower_vase(seed=170 + i), (0.5, 5.2, 1.4, 8.5), 3,
                      "clutter#gvase", z=0.82, seed=17)
    print(f"  generated dressing: {made} props placed by constraint")

    # --- characters
    add(C.build(C.BARISTA), at=(4.9, 1.95, 0), rot=0, name="char#barista")
    seated = [(4.6, 5.0 - 0.95, 0, 0), (4.6, 5.0 + 0.95, 180, 2),
              (6.6, 7.6 - 0.95, 0, 4), (9.8, 3.55, 0, 1), (11.0, 5.45, 180, 6)]
    for i, (cx, cy, rot, who) in enumerate(seated):
        add(C.build(C.CUSTOMERS[who], seated=True), at=(cx, cy, 0.0), rot=rot,
            name=f"char#seat{i}")
    # A queue must run ACROSS the view, not into it. At (6.0, 2.6) and
    # (6.8, 3.3) the two customers sat on the same screen column -- 1.5 tiles
    # apart in world, 0.1 apart on screen -- so the near one hid 74% of the far
    # one and the pair read as a single smeared figure. Offsetting mostly along
    # x separates them in screen u while keeping the line pointed at the till.
    add(C.build(C.CUSTOMERS[3]), at=(6.3, 2.5, 0), rot=200, name="char#queue0")
    add(C.build(C.CUSTOMERS[7]), at=(7.9, 2.9, 0), rot=200, name="char#queue1")

    return L


# World bounds of the service counter run -- the zone the player interacts with,
# and therefore the zone the composition is supposed to lead the eye to.
FOCAL_BOX = ((2.0, 8.0), (0.06, 1.30), (0.0, 1.50))


def focal_report(px, target, cam, centre, span):
    """Does the interaction zone actually read as the focal point?

    Measured against the frame, not in the abstract: a focal zone has to be
    brighter and higher-contrast than its surroundings or the eye has nowhere to
    land. An earlier attempt used edge density per ninth of the frame, which is
    the wrong instrument -- darkening a corner ADDS ramp transitions there, so a
    deliberate vignette scored as detail and the "focal peak" landed in an empty
    corner.
    """
    from oklab import srgb_to_oklab
    (ax, bx), (ay, by), (az, bz) = FOCAL_BOX
    us, vs = [], []
    for x in (ax, bx):
        for y in (ay, by):
            for z in (az, bz):
                p = (x, y, z)
                us.append(dot(p, cam.right) - dot(centre, cam.right))
                vs.append(dot(p, cam.up) - dot(centre, cam.up))
    def to_px(u, v):
        # `px` is the full target x target buffer, before the crop-to-content
        # step. Subtracting the crop origin here shifted the rect off the
        # counter entirely and produced a contrast of exactly 0.000 -- a number
        # a real region cannot have, and the tell that the box was degenerate.
        return ((u / span * 0.5 + 0.5) * target,
                (0.5 - v / span * 0.5) * target)
    pts = [to_px(u, v) for u, v in zip(us, vs)]
    fx0 = int(max(0, min(p[0] for p in pts)))
    fx1 = int(min(target, max(p[0] for p in pts)))
    fy0 = int(max(0, min(p[1] for p in pts)))
    fy1 = int(min(target, max(p[1] for p in pts)))

    w = target
    def stats(pred):
        Ls = [srgb_to_oklab(c)[0] for i, c in enumerate(px)
              if c is not None and pred(i % w, i // w)]
        if not Ls:
            return 0.0, 0.0
        Ls.sort()
        return (sum(Ls) / len(Ls),
                Ls[int(len(Ls) * 0.95)] - Ls[int(len(Ls) * 0.05)])

    inside = lambda x, y: fx0 <= x <= fx1 and fy0 <= y <= fy1   # noqa: E731
    n_in = sum(1 for i, c in enumerate(px)
               if c is not None and inside(i % w, i // w))
    if n_in < 200:
        print(f"  focal zone: only {n_in} px in the box "
              f"({fx0}..{fx1}, {fy0}..{fy1}) - projection is wrong")
        return
    cm, cc = stats(inside)
    om, oc = stats(lambda x, y: not inside(x, y))
    ok = cm > om and cc > oc
    print(f"  focal zone (service counter): mean L {cm:.3f} vs {om:.3f} elsewhere "
          f"({cm - om:+.3f})")
    print(f"                                contrast {cc:.3f} vs {oc:.3f} "
          f"({cc - oc:+.3f})   {'reads as the centre' if ok else 'DOES NOT lead the eye'}")


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
    hidden = L.screen_occlusion(args.azimuth)
    if hidden:
        print(f"  SCREEN OCCLUSION ({len(hidden)}):")
        for h in hidden:
            print(f"    {h}")
    else:
        print("  nothing is buried behind anything")
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
                            ambient=0.05, key_gain=0.60,
                            haze=0.30, grain=1.0, ramps=ramps,
                            wear=L.wear_field())

    px = downsample_modal(shade_toon(mat, lam, size, ramps, dither=True),
                          size, args.factor)
    # Material ids by SORTED INDEX, never by hash. `hash(m) % 251` collides
    # among ~30 materials by the birthday bound, and Python randomises string
    # hashing per process, so which materials collided changed every run: the
    # outline pass then read a colliding material's ramp and drew, for instance,
    # foliage-green edges around the wooden counter. It also meant this render
    # was not reproducible, which quietly invalidates every before/after
    # comparison in ART_CRITIQUE.md.
    ids = {m: (i % 256, i // 256, 0)
           for i, m in enumerate(sorted(m for m in set(mat) if m is not None))}
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
    focal_report(px, args.target, cam, centre, cam.span)

    out = Path(args.out)
    out.parent.mkdir(exist_ok=True)
    img.resize((img.width * 2, img.height * 2), Image.NEAREST).save(out)
    print(f"wrote {out}  ({img.width}x{img.height} native)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
