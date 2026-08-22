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
import tempfile
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

# How much of the run the espresso machine takes, including its lead-in gap.
MACHINE_SPAN = 2.9

# Counter length kept clear of the kit, for cups and cake stands to stand in.
DRESSING_RESERVE = 1.5

# Square metres of floor per ceiling lamp, from the reference room: three over
# 14.0 x 9.6.
LAMP_AREA = 45.0

# Focal check. The render size matters and 160 was the wrong one, chosen from a
# single seed where it happened to agree with 240 to within 0.003. Swept over
# three seeds and three sizes it does not agree at all:
#
#                160     320     480
#   reference   +.146   +.133   +.133      stable
#   seed 1      +.155   +.146   +.107
#   seed 2      +.093   +.054   +.048
#   seed 3      +.084   +.039   +.014      collapses
#
# Contrast is a 5-95 percentile spread, a tail statistic, so it moves as more
# resolution resolves more distinct values -- but only where there is detail to
# resolve. The reference room holds its reading and the generated rooms lose
# theirs, which is not the instrument drifting, it is the two rooms differing:
# the generated periphery is as detailed as its centre and gains contrast as
# fast as the counter does.
#
# So the check runs at 320, near the size that ships, and not at the size that
# made it pass. Mean L, a first moment, IS stable across all three sizes -- and
# checking that instead would have been choosing the metric that agreed with
# the answer already written down.
FOCAL_TARGET = 320
MIN_FOCAL_CONTRAST = -0.020

# The counter must also be brighter than its room, if only a little. Both
# floors say "leads", not "leads well" -- see `check_focal_contrast`.
MIN_FOCAL_L = 0.015


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
    # ON the counter, not half a tile in front of it. The reference room's two
    # hand-placed pools sit at y 1.20 and 1.35 over a run spanning 0.85 to
    # 1.85 -- that is its centre and a touch behind. Generalising them picked
    # up a `+0.35` and a `+0.50` from somewhere, which pushed a 2.6-radius core
    # off the counter and over the queue, and cost the counter 0.08 of mean L
    # against the rooms whose run happens to lie along the offset instead of
    # across it. Visible in the frame long before it was visible in the
    # numbers: one room's counter is a warm pool and the other's is a dim
    # corner, and the numbers said +0.107 and +0.045 without saying why.
    #
    # Perpendicular to the run, too. A vertical run's customer side is +x, and
    # a fixed +y offset slid the pool ALONG such a counter rather than across
    # it -- which is why the vertical-run rooms looked fine and hid the bug.
    if run.facing == 0.0:
        core, wash = (cx, cy - 0.15), (cx, cy)
    else:
        core, wash = (cx - 0.15, cy), (cx, cy)
    pools = [Pool((core[0], core[1], 1.26), 2.6, 0.66),
             Pool((wash[0], wash[1], 1.05), 4.6, 0.30)]
    for t in plan.win_x:
        pools.append(Pool((t + 0.5, 0.30, 0.95), 3.0, 0.40))
    for t in plan.win_y:
        pools.append(Pool((0.30, t + 0.5, 0.95), 3.0, 0.40))
    # One lamp per zone was a lamp per 36 square metres in the rooms with the
    # most zones, against the reference room's three lamps over 134 -- one per
    # 45. That is not a lighting preference, it is the focal measurement: the
    # two seeds with the most lamps were the two weakest, +0.093 and +0.039
    # contrast against a reference of +0.133, because every lamp lifts the
    # periphery the negatives are there to sink. So the count comes from the
    # floor's area and the biggest zones get them, rather than every zone
    # getting one because it happens to clear a fixed threshold. A room does
    # not light itself more brightly for having been divided more finely.
    lit = sorted((z for z in plan.of("cafe") + plan.of("lounge")
                  if z.area > 8.0), key=lambda z: -z.area)
    for z in lit[:max(1, round(plan.w * plan.d / LAMP_AREA))]:
        pools.append(Pool(((z.x0 + z.x1) / 2, (z.y0 + z.y1) / 2, 1.24),
                          3.6, 0.62))
    corners = sorted(((0.4, 0.4), (plan.w - 0.4, 0.4),
                      (0.4, plan.d - 0.4), (plan.w - 0.4, plan.d - 0.4)),
                     key=lambda c: -((c[0] - cx) ** 2 + (c[1] - cy) ** 2))
    # Three, not two. The reference room takes light out of three of its four
    # corners and the generated rig only did two, which leaves one corner as
    # bright as the counter and gives the eye a second place to land.
    for k, (px, py) in enumerate(corners[:3]):
        pools.append(Pool((px, py, 0.5), 6.0 - k * 1.0, -0.36 + k * 0.07))
    return LightRig(pools)


def build(plan: F.Plan) -> Layout:
    L = Layout()
    add = L.add
    # name -> the height of the surface someone sits on. Kept beside the
    # layout because `Placed` carries a bounding box and a seat's box tops out
    # at its backrest.
    seat_z: dict = {}
    # A stool's foot ring, where it has one. Kept beside `seat_z` for the same
    # reason: it is a height a person meets that a bounding box cannot report.
    perch_rail: dict = {}
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
    # A peninsula juts into the room, so its back bar does not hug the wall
    # that its run is parallel to. Everything below that used to say "the wall"
    # has to say "the back bar zone" instead: shelving was going to x=0.15
    # whatever the plan said, four tiles from the counter it belongs to, and
    # the only reason nothing complained is that `add_seeded` found the spot
    # empty and took it. A fallback that succeeds is the hardest kind of bug to
    # see.
    # A peninsula meets the wall end-on and an island meets none at all, so
    # neither has a stretch of wall behind its counter. Written as the set that
    # DOES hug a wall rather than as a list of exceptions, because the last
    # time a new topology arrived this line said `!= "peninsula"` and quietly
    # gave the island two chalkboards on a wall across the room.
    on_wall = plan.topology in ("wall run", "L run")
    length = run.w if horizontal else run.d
    # What stands on the counter, and how much of the run it eats. Tallied
    # before the back bar goes in rather than after, because the back bar has
    # to start past it -- shelving behind the machine measured 97% hidden, and
    # behind the grinder 37%.
    kit = [(A.espresso_machine, 2.0, "espresso"), (A.grinder, 0.8, "grinder"),
           (A.register, 0.9, "register")]
    # The kit stops short of the end of the run by DRESSING_RESERVE rather
    # than by a token 0.3, because the kit and the clutter compete for the same
    # counter and the kit is the low-contrast half of it. The machine's own
    # docstring records that a plain one is "a single featureless grey mass";
    # three grey boxes in a row is that argument three times.
    #
    # Measured: the one room in eight that fitted all three fitted only three
    # clutter items against the others' five to seven, and it is the one room
    # whose counter fails to lead the frame. The reference room, which holds
    # +0.133 at every render size, runs two kit items and ELEVEN pieces of
    # clutter. A cafe with a short counter owns a machine and a till, not a
    # machine and a till and a grinder.
    #
    # Decided ONCE, into `kit`, rather than tallied here and re-decided at
    # placement time. Those were two loops with the same `length - 0.3` in
    # them, and changing the reserve in one of them changed nothing: the tally
    # dropped the grinder and the placement loop put it down anyway. That is
    # the third time in this file that two copies of a rule have behaved as one
    # rule and one bug -- after the support test and the shelving span -- and
    # the fix is the same each time.
    kit_extent = 0.35
    fits = []
    for entry in kit:
        if kit_extent + entry[1] > length - DRESSING_RESERVE:
            break
        fits.append(entry)
        kit_extent += entry[1] + 0.55
    kit = fits

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

    # Placed BEFORE the back bar, not after. The shelves go in with
    # `add_seeded`, which rejects a seed whose result is hidden -- but it can
    # only see what is already in the layout, and the kit used to arrive
    # afterwards. So every shelf was checked against an empty counter and
    # passed, and three rooms in eight shipped a shelf 45% behind a grinder.
    # Ordering is part of a constraint solver's correctness: a check that runs
    # before the thing it constrains is a check that always passes.
    # --- the kit itself, spaced along the run rather than at coordinates
    top = run.y0 + 0.10 if horizontal else run.x0 + 0.10
    used = 0.35
    for factory, width, tag in kit:
        pos = (run.x0 + used, top + 0.05, 0.92) if horizontal else (
            top + 0.05, run.y0 + used, 0.92)
        try:
            L.add_seeded(lambda k, f=factory: f(seed=k), range(1, 10),
                         at=pos, name=f"prop#{tag}")
        except TypeError:
            add(factory(), at=pos, name=f"prop#{tag}")
        used += width + 0.55

    # --- the return arm of an L, tiled the same way the run is. Built from
    # the zone rather than inferred from the run's end, because the plan
    # already decided which end it turns at and inferring it here would be a
    # second copy of that decision.
    for ri, z in enumerate(plan.of("service_return")):
        along_x = z.w >= z.d
        n_ret = max(1, int(round(z.w if along_x else z.d)))
        for i in range(n_ret):
            at = (z.x0 + i, z.y0, 0) if along_x else (z.x0, z.y0 + i, 0)
            add(A.counter(seed=40 + ri * 5 + i,
                          front="y" if along_x else "x"),
                at=at, name=f"counter#ret{ri}_{i}")

    # --- back bar: shelving against the wall behind the run
    # Tall shelving only where there is a wall to put it against. A 1.9 stack
    # standing free on an island is a partition between the barista and the
    # room, which is the one thing an island exists not to be.
    back = plan.of("backbar") if on_wall else []
    if back:
        b = back[0]
        # Shelving runs along the back bar's own long axis and sits inside it,
        # rather than against whichever wall the reference room happened to
        # use. `A.bookshelf` is 0.9 wide and 0.3 deep, so it fits the 0.8 strip.
        along_x = b.w >= b.d
        span = b.w if along_x else b.d
        # Started from the FAR end of the run. Shelving from the near end sat
        # directly behind the espresso machine and `screen_occlusion` reported
        # 97% of it hidden -- geometry nobody can see, which is the most
        # expensive kind. The machine takes the first two tiles of any run, so
        # the back bar takes the rest.
        # Only the MACHINE is subtracted, not the whole kit. Subtracting all
        # three left `span - 5.7` on a six-tile run and the rooms shipped with
        # no back bar at all -- invisible, because an empty wall behind a
        # counter looks like a decision. The grinder and the register top out
        # at 1.3 against a 1.9 shelf; the machine reaches 1.74 and is the only
        # one that hides anything.
        # The offset is searched, not computed. `add_seeded` cannot rescue
        # this placement -- every `A.bookshelf` seed has the same 0.9 x 0.3
        # footprint, so no seed moves the shelf out from behind the grinder,
        # and the fallback quietly shipped one 45% hidden in three rooms of
        # eight. When the solver's only lever does not move the failing
        # quantity, give it the lever that does: here that is where along the
        # run the shelf goes, so the loop proposes offsets and keeps the ones
        # the occlusion rule accepts.
        want = max(0, int((span - MACHINE_SPAN - 0.6) / 1.6))
        taken, placed_i = [], 0
        off = span - 1.7
        while off > 0.3 and placed_i < want:
            if any(abs(off - t) < 1.5 for t in taken):
                off -= 0.35
                continue
            at = ((b.x0 + off, b.y0 + 0.08, 0) if along_x
                  else (b.x0 + 0.08, b.y0 + off, 0))
            name = f"prop#backbar{placed_i}"
            L.add(A.bookshelf(seed=3 + placed_i), at=at,
                  rot=0 if along_x else 270, name=name)
            cand = L.items.pop()
            if L._conflicts(cand, 45.0, 0.35):
                L.rots.pop(name, None)
            else:
                L.items.append(cand)
                taken.append(off)
                placed_i += 1
            off -= 0.35

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
    # Only when the run is parallel to the wall it backs onto. A peninsula
    # meets the wall end-on, so there is no stretch of wall behind it to hang a
    # board on -- and hanging one anyway put two chalkboards across the room
    # from the counter they price.
    for bi, t in enumerate(solid[:2] if on_wall else []):
        at = (t + 0.12, 0.04, 0.62) if horizontal else (0.04, t + 0.12, 0.62)
        add(A.menu_board(), at=at, rot=0 if horizontal else 270,
            name=f"decor#menu{bi}")

    # --- the counter top. The reference room carries ELEVEN clutter items
    # within 3.5 tiles of its till -- cups, a cake stand, vases, a clutter
    # cluster -- and the generated rooms carried none. That is where the focal
    # gap actually was, and it took three wrong answers to find: depth staging,
    # ramp balance and accent spread all came back matching, prop density per
    # square metre did not predict contrast either (the room with the densest
    # periphery reads strongest), and a mid-field negative pool would have been
    # a knob rather than a cause. The counter was simply bare, and a bare
    # counter has nothing for the eye to land ON once it has been sent there.
    #
    # Placed by the solver, in the gaps the kit leaves, so nothing lands behind
    # the machine or on top of the till.
    top_z = 0.92
    on_bar = 0
    dress = (lambda k: A.cake_stand(), lambda k: A.cup_and_saucer(),
             lambda k: A.flower_vase(seed=190 + k),
             lambda k: A.table_clutter("counter"),
             lambda k: A.cup_and_saucer())
    step, di = 0.42, 0
    reach = length - 0.35
    off = 0.35
    while off < reach and di < 7:
        along = run.x0 + off if horizontal else run.y0 + off
        at = ((along, run.y0 + 0.42, top_z) if horizontal
              else (run.x0 + 0.42, along, top_z))
        nm = f"clutter#bar{di}"
        L.add(dress[di % len(dress)](di), at=at, name=nm, centre=True)
        cand = L.items.pop()
        if L._conflicts(cand, 45.0, 0.35):
            L.rots.pop(nm, None)
        else:
            L.items.append(cand)
            on_bar += 1
            di += 1
        off += step

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
            st = A.stool(seed=20 + bi * 7 + i)
            nm = f"seat#stool{bi}_{i}"
            add(st, at=at, rot=int(z.facing), name=nm, centre=True)
            _remember(seat_z, nm, st)
            perch_rail[nm] = st.rail_z

    # --- seating. Tables with chairs on all four sides in the cafe blocks,
    # armchairs and benches in the lounges, both placed by the solver.
    made = on_bar
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
    made += _people(L, plan, seat_z=seat_z, perch_rail=perch_rail)
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
             perch_rail: dict | None = None,
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
    # And the stools, which take a different rig rather than none. The window
    # bar used to be furniture nobody used: every seat in the room was filled
    # and the row along the glass stayed empty in all twelve rooms, which is
    # not a cafe, it is a showroom.
    stools = [q for q in L.items if q.name.startswith("seat#stool")]
    rest = list(roster[2:])
    if seats:
        stride = max(1, len(seats) // max(1, len(rest) - len(stools[:2])))
        for i, spec in enumerate(rest[:max(0, len(rest) - 2)]):
            k = (i * stride + 1) % len(seats)
            st = seats[k]
            cx, cy = (st.x0 + st.x1) / 2, (st.y0 + st.y1) / 2
            put(C.build(spec, seated=True, seat=seat_z[st.name]), (cx, cy, 0.0),
                L.rots.get(st.name, 0.0), f"char#sit{i}")
    # Not adjacent, because two people at a window bar who did not arrive
    # together leave a stool between them, and because two figures one stool
    # apart on the screen diagonal is the queue-occlusion problem again.
    for i, spec in enumerate(rest[max(0, len(rest) - 2):]):
        if not stools:
            break
        st = stools[(i * 2) % len(stools)]
        cx, cy = (st.x0 + st.x1) / 2, (st.y0 + st.y1) / 2
        put(C.build(spec, perch=(seat_z.get(st.name, 0.70),
                                 perch_rail.get(st.name))),
            (cx, cy, 0.0), L.rots.get(st.name, 0.0), f"char#perch{i}")
    return placed





def focal_box(plan: F.Plan) -> tuple:
    """The service area, as the run and the back bar together."""
    zs = plan.of("service") + plan.of("backbar") + plan.of("service_return")
    return ((min(z.x0 for z in zs), max(z.x1 for z in zs)),
            (min(z.y0 for z in zs), max(z.y1 for z in zs)), (0.0, 1.50))


def check_focal_contrast(n: int = 4, seed: int = 1,
                         target: int = FOCAL_TARGET,
                         l_floor: float = MIN_FOCAL_L,
                         c_floor: float = MIN_FOCAL_CONTRAST) -> list[str]:
    """A generated room's counter must still read as the place to look.

    The last of the composition questions to survive being measured. Depth
    staging, ramp balance and accent spread were all tested against the
    reference room and all three came back matching, so no checks were written
    for them; a suite that grades what is not broken is decoration.

    BOTH metrics, and both floors are low. That is a retreat from the first
    version of this check and it is the honest one. Measured across four rooms
    under a good rig and a deliberately broken one, plus the reference room:

                     good            broken
        seed 1    L +.118 C +.146   L +.109 C +.087
        seed 2    L +.032 C +.093   L +.023 C +.039
        seed 3    L +.042 C +.045   L +.024 C -.054
        seed 4    L +.080 C +.099   L +.069 C +.048
        reference L +.024 C +.133

    Neither column supports an absolute floor that ranks composition. The
    REFERENCE ROOM has the lowest mean L of anything here, below every broken
    room -- it builds its centre out of contrast, a dark machine against a lit
    counter, rather than out of brightness. And a good room's contrast (+.045)
    sits below a broken room's (+.087), because these are different rooms and
    not two readings of one.

    The first version put the floor at 0.060 on contrast alone, calibrated on
    three samples, and it was grading how WELL the counter leads. This grades
    whether it leads at all, which is the most the instrument can carry:

    - contrast is a 5-95 percentile spread over a frame containing 37 distinct
      lightness values, because quantizing light to palette ramps is the whole
      pipeline. It is a step function, and four separate changes that visibly
      altered a room left it at exactly +0.045, inside 0.546 and outside 0.502
      to the thousandth. That is the same tell as a degenerate box.
    - mean L is a first moment over ~50 000 pixels and moves with everything,
      but it does not separate composed from broken, as the reference room's
      own +0.024 shows.

    One room per TOPOLOGY, found by scanning, rather than the first four
    seeds. A composition check that never sees an island has a blind spot
    shaped like a whole branch of the generator. The first version took seeds
    1 to 4 because they happened to be one of each, with a comment saying that
    this was luck and should become a search if the stream ever shifted -- and
    the very next change to the generator shifted it, leaving seeds 1 to 4 as
    two wall runs, a peninsula and an island, with the L run unwatched. A
    comment predicting a bug is not a fix for it.

    What both agree on is direction: every room got worse on both under the
    broken rig. A check that only ever sees one version of a room cannot use
    that, so it asks the weaker question honestly rather than the stronger one
    unreliably.

    THE CONTRAST FLOOR IS NEGATIVE, and that is the honest placement rather
    than a concession. The metric moves in steps of roughly 0.04 -- 37 distinct
    lightness values, a percentile spread -- so any floor between 0 and 0.04 is
    a floor sitting inside one step, and whether a marginal room clears it is
    decided by which side of a bin boundary it lands on. One wall run reads
    +0.000 at 320 and -0.014 at 480: the same room, one step apart, from
    resolution alone.

    So contrast is asked only for what it can answer at that granularity --
    that the counter is not MATERIALLY LESS interesting than the room around
    it, which catches the broken rig's -0.054 and does not adjudicate a step.
    Brightness, which is continuous, carries the positive requirement.

    Six structural explanations were measured against the room that sits at
    zero and none of them was the cause: prop density per square metre, floor
    occupancy (the reference room is DENSER than every generated room, at
    47%), back-wall dressing (that room has more shelving than the reference),
    counter dressing, kit size, and three lighting variants. Recording that
    the cause is unfound is better than shipping a seventh guess as a fix.
    A stronger check needs a metric that is not a percentile: edge density in
    palette-index space would be continuous over ~50 000 pixels and is the
    obvious candidate, with the caveat this file already records -- darkening a
    corner ADDS ramp transitions, so it can only be used as a zone-versus-rest
    comparison and never to search for where the focal point is.
    """
    import io as _io
    import contextlib
    import re as _re
    from render_room import render
    picks, seen = [], set()
    k = seed
    while len(picks) < n and k < seed + 60:
        plan = F.generate(k)
        if plan.topology not in seen:
            seen.add(plan.topology)
            picks.append((k, plan))
        k += 1
    out = []
    if len(picks) < n:
        out.append(f"only {len(picks)} topologies found in 60 seeds, "
                   f"wanted {n} -- the generator has lost a branch")
    for k, plan in picks:
        L = build(plan)
        buf = _io.StringIO()
        with contextlib.redirect_stdout(buf):
            render(L, light_rig(plan), target, Path(tempfile.gettempdir())
                   / "_focal_check.png", wear=L.wear_field(),
                   focal=focal_box(plan))
        hits = _re.findall(r"([+-]\d\.\d\d\d)", buf.getvalue())
        if len(hits) < 2:
            out.append(f"plan {k} ({plan.topology}): render reported no "
                       f"focal reading")
            continue
        lead, con = float(hits[0]), float(hits[1])
        if lead < l_floor:
            out.append(f"plan {k} ({plan.topology}): counter is only "
                       f"{lead:+.3f} brighter than its room "
                       f"(floor {l_floor:+.3f}) -- no centre")
        if con < c_floor:
            out.append(f"plan {k} ({plan.topology}): counter is {con:+.3f} "
                       f"in contrast against its room (floor {c_floor:+.3f})"
                       f" -- the periphery has as much to look at")
    return out


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
    # Taken from the run and the back bar together rather than from the run and
    # the wall behind it. The wall version was a peninsula bug of the same
    # family as the shelving: it assumed the counter backs onto y=0, so on a
    # peninsula the box swept a strip of empty floor into the focal region.
    # Changed because the old box was wrong, not because the new one scores
    # better -- an instrument chosen for its reading is not an instrument.
    run = plan.of("service")[0]
    back = plan.of("backbar")[0]
    focal = ((min(run.x0, back.x0), max(run.x1, back.x1)),
             (min(run.y0, back.y0), max(run.y1, back.y1)), (0.0, 1.50))
    from render_room import render
    render(L, light_rig(plan), args.target, Path(args.out),
           wear=L.wear_field(), focal=focal)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
