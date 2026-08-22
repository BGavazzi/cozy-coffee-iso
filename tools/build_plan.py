#!/usr/bin/env python3
"""Turn a generated floor plan into a room the renderer can draw.

`floorplan.py` proposes zones and checks them; this fills them. It is the half
that stops the plan generator being an adapter with no consumer -- the position
`ingest.py` is still in, and the reason both needed checks before anything fed
them.

Nothing here is new machinery. The counter run is the same `A.counter` modules
the reference room uses, the seating comes from `Layout.scatter`, and the props
are picked with `Layout.add_seeded`. What is new is that no coordinate in this
file is a number about *this* room: everything is derived from a zone. That is
the whole difference between a room and a room generator, and it is why the
reference room stays hand-authored -- six passes of art direction live in its
48 coordinates, and this file cannot reproduce judgement, only rules.

    python tools/build_plan.py --seed 3 --out proof/plan_room.png
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import assetlib as A  # noqa: E402
import character as C  # noqa: E402
import floorplan as F  # noqa: E402
from layout import Layout  # noqa: E402
from mesh import LightRig, Pool  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

SILL, HEAD = 0.58, 1.82

# Painted frames, as the reference room settled them: below the wood in
# lightness so they separate by hue and recede by value, and never `sky`, which
# is reserved for glass and daylight.
# One in three painted, not one in two, and never `sky` -- the cool ramp is
# reserved for glass and daylight, and spending it on chairs makes the coldest
# thing in frame a piece of seating. `neutral-3` was in this table and rendered
# near-black: a single chair with more value range than the counter, which is
# the one thing in the room that is supposed to lead the eye.
PAINTS = ("wood", "foliage-3", "rose-3", "wood", "wood-2", "wood")


def light_rig(plan: F.Plan) -> LightRig:
    """Daylight at each window, a core over the till, and dark corners.

    The negative pools go in the corners furthest from the service run rather
    than at fixed coordinates. That is the rule the reference room's three
    hand-placed negatives encode -- taking light out of the periphery is what
    builds a centre, because the counter is already near the top of its ramp
    and cannot simply be brightened.
    """
    run = plan.of("service")[0]
    cx, cy = (run.x0 + run.x1) / 2, (run.y0 + run.y1) / 2
    pools = [Pool((cx, cy + 0.35, 1.26), 2.6, 0.66),
             Pool((cx, cy + 0.50, 1.05), 4.6, 0.30)]
    for t in plan.win_x:
        pools.append(Pool((t + 0.5, 0.30, 0.95), 3.0, 0.40))
    for t in plan.win_y:
        pools.append(Pool((0.30, t + 0.5, 0.95), 3.0, 0.40))
    for z in plan.of("cafe") + plan.of("lounge"):
        if z.area > 8.0:
            pools.append(Pool(((z.x0 + z.x1) / 2, (z.y0 + z.y1) / 2, 1.24),
                              3.6, 0.62))
    corners = sorted(((0.4, 0.4), (plan.w - 0.4, 0.4),
                      (0.4, plan.d - 0.4), (plan.w - 0.4, plan.d - 0.4)),
                     key=lambda c: -((c[0] - cx) ** 2 + (c[1] - cy) ** 2))
    for k, (px, py) in enumerate(corners[:2]):
        pools.append(Pool((px, py, 0.5), 6.0 - k * 1.2, -0.34 + k * 0.06))
    return LightRig(pools)


def build(plan: F.Plan) -> Layout:
    L = Layout()
    add = L.add
    # name -> the height of the surface someone sits on. Kept beside the
    # layout because `Placed` carries a bounding box and a seat's box tops out
    # at its backrest.
    seat_z: dict = {}
    add(A.floor(plan.w, plan.d), name="floor", track=False)
    # A rug under each substantial seating block. The reference room uses two
    # to say "this group of tables is one place to sit", and a zone is exactly
    # that statement already -- so here it is free, where there it was two
    # hand-typed rectangles.
    # Only the lounges, and only the big ones. Every zone over 7 tiles got one
    # at first, which put four green slabs across a floor whose whole job is to
    # be the quiet surface everything else sits on -- the reference room uses
    # two in a room of the same size. A rug says "this is one place to sit",
    # and saying it four times says nothing.
    for zi, z in enumerate(sorted(plan.of("lounge"), key=lambda q: -q.area)[:2]):
        if z.area < 9.0:
            continue
        add(A.rug(min(z.w, 2.8) - 0.4, min(z.d, 2.8) - 0.4, "foliage"),
            at=(z.x0 + 0.4, z.y0 + 0.4, 0), name=f"floor#rug{zi}", track=False)
    add(A.wall_run((0, 0), "x", plan.w, openings=plan.win_x),
        name="wall", track=False)
    add(A.wall_run((0, 0), "y", plan.d, openings=plan.win_y),
        name="wall", track=False)
    L.warp_default = 0.030

    run = plan.of("service")[0]
    horizontal = run.facing == 0.0
    length = run.w if horizontal else run.d
    # What stands on the counter, and how much of the run it eats. Tallied
    # before the back bar goes in rather than after, because the back bar has
    # to start past it -- shelving behind the machine measured 97% hidden, and
    # behind the grinder 37%.
    kit = [(A.espresso_machine, 2.0, "espresso"), (A.grinder, 0.8, "grinder"),
           (A.register, 0.9, "register")]
    kit = [k for k in kit if True]
    kit_extent, used = 0.35, 0.35
    for _, width, _ in kit:
        if kit_extent + width > length - 0.3:
            break
        kit_extent += width + 0.55

    # --- the service run, as one-tile modules tiled flush along the zone
    n = max(1, int(round(run.w if horizontal else run.d)))
    for i in range(n):
        if horizontal:
            at = (run.x0 + i, run.y0, 0)
            m = A.counter(seed=4 + i, front="y")
        else:
            at = (run.x0, run.y0 + i, 0)
            m = A.counter(seed=4 + i, front="x")
        add(m, at=at, name=f"counter#{i}")

    # --- back bar: shelving against the wall behind the run
    back = plan.of("backbar")
    if back:
        b = back[0]
        span = b.w if horizontal else b.d
        # Started from the FAR end of the run. Shelving from the near end sat
        # directly behind the espresso machine and `screen_occlusion` reported
        # 97% of it hidden -- geometry nobody can see, which is the most
        # expensive kind. The machine takes the first two tiles of any run, so
        # the back bar takes the rest.
        for i in range(max(0, int((span - kit_extent - 0.6) / 1.6))):
            off = span - 1.7 - i * 1.6
            at = (b.x0 + off, 0.15, 0) if horizontal else (0.15, b.y0 + off, 0)
            L.add_seeded(lambda k: A.bookshelf(seed=k), range(3 + i, 14 + i),
                         at=at, rot=0 if horizontal else 270,
                         name=f"prop#backbar{i}")

    # --- menu boards above the counter, on solid wall and never over glass.
    # The reference room learned both halves of that the hard way: at counter
    # height the espresso machine covered 82% of the board, and hung over a
    # window a board both hid the daylight and lost its own contrast against
    # it. Here the plan already knows where the glass is, so the rule is a
    # filter rather than a comment about which tiles happen to be solid.
    # Past the machine, not merely on solid wall. `add_seeded` could not fix
    # this one: it varies which machine, and every machine is the same 2.0
    # tiles wide, so no seed moves it off the board. When the solver has no
    # move to make, the constraint belongs in the proposal -- which is the same
    # conclusion the floor plan reached about windows and the back bar.
    lo = (run.x0 if horizontal else run.y0) + 2.5
    hi = run.x1 if horizontal else run.y1
    glass = plan.win_x if horizontal else plan.win_y
    solid = [t for t in range(int(lo), int(hi) + 1) if t not in glass]
    for bi, t in enumerate(solid[:2]):
        at = (t + 0.12, 0.04, 0.62) if horizontal else (0.04, t + 0.12, 0.62)
        add(A.menu_board(), at=at, rot=0 if horizontal else 270,
            name=f"decor#menu{bi}")

    # --- the kit itself, spaced along the run rather than at coordinates
    top = run.y0 + 0.10 if horizontal else run.x0 + 0.10
    for factory, width, tag in kit:
        if used + width > length - 0.3:
            break
        pos = (run.x0 + used, top + 0.05, 0.92) if horizontal else (
            top + 0.05, run.y0 + used, 0.92)
        try:
            L.add_seeded(lambda k, f=factory: f(seed=k), range(1, 10),
                         at=pos, name=f"prop#{tag}")
        except TypeError:
            add(factory(), at=pos, name=f"prop#{tag}")
        used += width + 0.55

    # --- window bar: a run of stools facing the glass
    for bi, z in enumerate(plan.of("window_bar")):
        along_x = z.w >= z.d
        span = z.w if along_x else z.d
        add(A.wall_shelf(span - 0.3, "x" if along_x else "y", rows=(0.98,)),
            at=(z.x0 + 0.15, z.y0 + 0.15, 0), name=f"prop#bartop{bi}",
            track=False)
        for i in range(max(1, int(span / 0.95))):
            if along_x:
                at = (z.x0 + 0.4 + i * 0.95, z.y1 - 0.45, 0)
            else:
                at = (z.x1 - 0.45, z.y0 + 0.4 + i * 0.95, 0)
            add(A.stool(seed=20 + bi * 7 + i), at=at, rot=int(z.facing),
                name=f"seat#stool{bi}_{i}", centre=True)

    # --- seating. Tables with chairs on all four sides in the cafe blocks,
    # armchairs and benches in the lounges, both placed by the solver.
    made = 0
    for zi, z in enumerate(plan.of("cafe")):
        made += L.scatter(
            lambda i, zi=zi: A.table_4top(seed=6 + zi * 5 + i)
            if (zi + i) % 3 == 2 else A.table_round(seed=17 + zi * 5 + i),
            (z.x0 + 0.6, z.y0 + 0.6, z.x1 - 0.6, z.y1 - 0.6),
            max(1, int(z.area / 4.6)), f"table#c{zi}", seed=30 + zi)
    # Chairs go in after the tables, around whichever ones landed: the same
    # ordering `add_seeded` needs, for the same reason.
    for p in [q for q in list(L.items) if q.name.startswith("table#")]:
        cx, cy = (p.x0 + p.x1) / 2, (p.y0 + p.y1) / 2
        reach = max(p.x1 - p.x0, p.y1 - p.y0) / 2 + 0.40
        # A chair's back is at -y, so rot must point it AWAY from the table.
        # The two side rotations were 90 and 270 the other way round, which
        # `seating_faces_tables` reported for every side chair in every room --
        # a check written three passes ago for hand-typed rotations, catching
        # the same mistake made by a loop.
        for k, (dx, dy, rot) in enumerate(((0, -reach, 0), (0, reach, 180),
                                           (-reach, 0, 270), (reach, 0, 90))):
            before = len(L.items)
            piece = A.chair(cushion=None if k % 2 else A.FABRIC,
                            frame=PAINTS[(k + len(L.items)) % len(PAINTS)],
                            seed=40 + k + int(cx * 3))
            nm = f"chair#{p.name[6:]}_{k}"
            add(piece, at=(cx + dx, cy + dy, 0), rot=rot, centre=True, name=nm)
            cand = L.items[-1]
            L.items.pop()
            # And it has to satisfy `seating_faces_tables`, asked here rather
            # than read off a report afterwards. That check judges a seat
            # against whichever table is NEAREST, so a chair squeezed between
            # two tables serves one and backs onto the other -- and it is right
            # to complain, because that is what it looks like. Denser scatter
            # made it common. Approximating the rule with "is my table the
            # closest one" left one chair in twelve rooms still failing; asking
            # the rule itself leaves none, which is the whole argument for
            # running a validator as a solver instead of reimplementing it.
            L.items.append(cand)
            faces_wrong = any(cand.name in m for m in L.seating_faces_tables())
            L.items.pop()
            if (faces_wrong or cand.x0 < 0.35 or cand.y0 < 0.35
                    or cand.x1 > plan.w - 0.35 or cand.y1 > plan.d - 0.35
                    or L._conflicts(cand, 45.0, 0.35)):
                L.rots.pop(cand.name, None)
                continue
            L.items.append(cand)
            seat_z[nm] = piece.seat_z
            made += 1

    for zi, z in enumerate(plan.of("lounge")):
        made += L.scatter(lambda i, zi=zi: _remember(seat_z, f"seat#arm{zi}#{i}",
                                                     A.armchair(seed=5 + zi * 7 + i)),
                          (z.x0 + 0.6, z.y0 + 0.6, z.x1 - 0.6, z.y1 - 0.6),
                          max(1, int(z.area / 5.0)), f"seat#arm{zi}",
                          seed=50 + zi, rot_choices=(0, 90, 180, 270))
        made += L.scatter(lambda i, zi=zi: A.side_table(),
                          (z.x0 + 0.5, z.y0 + 0.5, z.x1 - 0.5, z.y1 - 0.5),
                          max(1, int(z.area / 9.0)), f"prop#side{zi}",
                          seed=60 + zi)

    # --- dressing in whatever is left, against the far walls where clutter
    # belongs: the near sides are open to the camera.
    made += L.scatter(lambda i: A.plant_small(seed=40 + i),
                      (0.45, 0.45, plan.w - 0.5, 1.5), 5, "decor#gplantN",
                      seed=13)
    made += L.scatter(lambda i: A.plant_large(seed=3 + i * 5),
                      (0.45, 1.6, 1.6, plan.d - 0.6), 4, "decor#gplantW",
                      seed=18)
    made += L.scatter(lambda i: A.crate(seed=140 + i),
                      (0.5, 1.6, 1.5, plan.d - 0.6), 3, "decor#gcrate", seed=11)
    made += L.scatter(lambda i: A.basket("foliage", seed=150 + i),
                      (0.45, 0.45, plan.w - 0.5, 1.4), 4, "decor#gbasket",
                      seed=12)
    made += L.scatter(lambda i: A.plant_small(seed=70 + i),
                      (plan.w - 1.6, 1.6, plan.w - 0.5, plan.d - 0.6), 4,
                      "decor#gplantE", seed=19)
    made += L.scatter(lambda i: A.crate(seed=145 + i),
                      (1.6, plan.d - 1.5, plan.w - 0.6, plan.d - 0.5), 3,
                      "decor#gcrateS", seed=17)

    # Clutter on whatever tables landed, at each table's own top -- the reason
    # `table()` returns `top_z`. Scattering at a fixed height is what put two
    # vases 0.05 above a table and turned up the disagreement between the
    # solver's support tolerance and `grounded`'s.
    tops = [q for q in L.items if q.name.startswith("table#")]
    for k, q in enumerate(tops):
        if k % 2:
            continue
        cx, cy = (q.x0 + q.x1) / 2, (q.y0 + q.y1) / 2
        add(A.flower_vase(seed=170 + k) if k % 4 else A.cup_and_saucer(),
            at=(cx - 0.25, cy - 0.25, q.z1), name=f"clutter#t{k}", centre=True)
        made += 1

    # A pendant over each table cluster, at the height the rig lights from.
    for zi, z in enumerate(plan.of("cafe") + plan.of("lounge")):
        if z.area > 8.0:
            add(A.pendant_lamp(), at=((z.x0 + z.x1) / 2 - 0.5,
                                      (z.y0 + z.y1) / 2 - 0.5, 0.60),
                name=f"decor#lamp{zi}", track=False)
    made += _people(L, plan, seat_z=seat_z)
    L.generated = made
    return L


def _remember(table: dict, name: str, mesh):
    """Stash a generated seat's surface height under the name it will be given.

    `scatter` builds the mesh and names the placement itself, so there is no
    hook between the two; the factory records what it made and the name is
    reconstructed to match. Ugly, and better than reading a backrest.
    """
    table[name] = getattr(mesh, "seat_z", 0.45)
    return mesh


def _people(L: Layout, plan: F.Plan, n: int = 7, seed: int = 1,
            seat_z: dict | None = None) -> int:
    """A barista, a queue, and customers in whatever seats were placed.

    The cast is `C.generate_roster`, so the two generators meet here: the
    character solver makes people the room has never seen, and the room solver
    puts them where the plan says people go. Neither knows about the other --
    the plan supplies a service side, a queue band and a set of seats, and
    those are the three things a cafe's occupants are sorted into.

    A queue runs ACROSS the view, not into it. The reference room recorded this
    the expensive way: two customers 1.5 tiles apart in world space sat 0.1
    apart on screen and the near one hid 74% of the far one. The camera looks
    down +x/+y, so a line of people spread along x - y stays legible and a line
    along x + y is one person with extra depth.
    """
    seat_z = seat_z or {}
    roster = C.generate_roster(n, seed)
    run = plan.of("service")[0]
    horizontal = run.facing == 0.0
    placed = 0

    def put(mesh, at, rot, name):
        nonlocal placed
        before = len(L.items)
        L.add(mesh, at=at, rot=rot, name=name)
        if len(L.items) == before:
            return
        cand = L.items[-1]
        L.items.pop()
        if L._conflicts(cand, 45.0, 0.35):
            L.rots.pop(name, None)
            return
        L.items.append(cand)
        placed += 1

    # Barista, on the staff side of the run, facing the customers.
    if horizontal:
        put(C.build(C.BARISTA), ((run.x0 + run.x1) / 2, run.y0 - 0.42, 0.0),
            180, "char#barista")
    else:
        put(C.build(C.BARISTA), (run.x0 - 0.42, (run.y0 + run.y1) / 2, 0.0),
            90, "char#barista")

    # The queue, stepped along the screen-horizontal so nobody hides anybody.
    q = plan.of("queue")
    if q:
        band = q[0]
        for i, spec in enumerate(roster[:2]):
            t = 0.30 + 0.34 * i
            if horizontal:
                at = (band.x0 + band.w * t, band.y0 + 0.45 + i * 0.30, 0.0)
                rot = 180
            else:
                at = (band.x0 + 0.45 + i * 0.30, band.y0 + band.d * t, 0.0)
                rot = 90
            put(C.build(spec), at, rot, f"char#queue{i}")

    # Everyone else sits. Seats are taken in a strided order rather than the
    # first few, because scatter fills a zone at a time and the first few are
    # all in one corner -- a cafe with one full table and three empty ones.
    # Chairs and armchairs only. `C.build(seated=True)` authors the legs about
    # a hip at SEAT_Z=0.45, and a bar stool stands at 0.62 to 0.78 -- the
    # figure is ground-clamped, so it does not float and `grounded` never
    # complains, it just sits in mid-air beside the stool at dining height.
    # A check that measures the floor cannot see a seat height.
    seats = [q for q in L.items
             if q.name.startswith(("chair#", "seat#arm"))
             and seat_z.get(q.name, 9.0) <= C.MAX_SEAT_Z]
    if seats:
        stride = max(1, len(seats) // max(1, len(roster) - 2))
        for i, spec in enumerate(roster[2:]):
            k = (i * stride + 1) % len(seats)
            st = seats[k]
            cx, cy = (st.x0 + st.x1) / 2, (st.y0 + st.y1) / 2
            put(C.build(spec, seated=True, seat=seat_z[st.name]), (cx, cy, 0.0),
                L.rots.get(st.name, 0.0), f"char#sit{i}")
    return placed





def check_built_rooms(n: int = 6, seed: int = 1) -> list[str]:
    """Every room built from a generated plan must satisfy the room checks.

    The plan checks say the *plan* is a cafe. They say nothing about whether
    filling it produces a room where the chairs face their tables and nothing
    is buried, because a plan is rectangles and a room is meshes -- and the
    gap between those is exactly where this file lives.

    It earned its place immediately. The first run reported 8 to 14 failures
    per room: two of the four chair rotations around every table were the wrong
    way round, and `seating_faces_tables` -- written three passes ago for
    hand-typed rotations -- caught the same mistake made by a loop, in every
    room, on the first try.
    """
    out = []
    for i in range(n):
        plan = F.generate(seed + i)
        L = build(plan)
        for msg in (L.collisions() + L.grounded()
                    + L.seating_faces_tables() + L.screen_occlusion()):
            out.append(f"plan seed {seed + i}: {msg}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--target", type=int, default=480)
    ap.add_argument("--out", default=str(ROOT / "proof" / "plan_room.png"))
    args = ap.parse_args()

    plan = F.generate(args.seed)
    bad = F.check_plan(plan)
    print(f"plan seed {args.seed}: " + ("clean" if not bad else "; ".join(bad)))
    print(F.describe(plan))
    L = build(plan)
    print(f"  {L.generated} props placed by constraint, "
          f"{len(L.items)} tracked in all")
    for msg in L.collisions() + L.grounded():
        print(f"  ! {msg}")
    for msg in L.screen_occlusion():
        print(f"  warning {msg}")

    # The focal box, derived from the run the same way the reference room's is
    # written by hand: the length of the counter, and from the wall to just
    # past its back edge -- the strip holding the machine, the boards and the
    # back bar, not the customer side.
    #
    # Padded out to the customer side first, and both regions then measured a
    # contrast of exactly 0.546. `focal_report` already records this failure
    # from the other direction, where a mis-projected box gave exactly 0.000:
    # a box that covers most of the frame makes "inside" and "outside" the same
    # sample, and two identical readings are the tell, the same way a
    # too-perfect one is.
    run = plan.of("service")[0]
    if run.facing == 0.0:
        focal = ((run.x0, run.x1), (0.06, run.y0 + 0.50), (0.0, 1.50))
    else:
        focal = ((0.06, run.x0 + 0.50), (run.y0, run.y1), (0.0, 1.50))
    from render_room import render
    render(L, light_rig(plan), args.target, Path(args.out),
           wear=L.wear_field(), focal=focal)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
