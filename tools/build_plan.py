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

# Positive for the first time. It was -0.020 because generated rooms genuinely
# read negative -- but they read negative because the focal REGION was the
# axis-aligned bounding box of a projected parallelogram, which is 51-64%
# counter and the rest floor and wall. Clipping the region to the projected
# hull moved the worst room from -0.054 to +0.047 without touching a single
# room. Bracketed between the broken rig at -0.001 and the weakest good room
# at +0.047.
#
# It catches only 1 of 7 broken-rig rooms now, where it used to catch most of
# them -- and that is the honest reading of what it was doing before. The
# broken rig lights the PERIPHERY, so a focal box stuffed with periphery
# pixels moved when the rig broke. It was detecting the regression by
# measuring the very pixels it existed to exclude. Brightness carries the
# detection; contrast states the floor.
MIN_FOCAL_CONTRAST = 0.030

# The counter must also be brighter than its room, if only a little. Both
# floors say "leads", not "leads well" -- see `check_focal_contrast`.
MIN_FOCAL_L = 0.015

# A third floor inside check 22, not a twenty-fifth check: it is read off
# the same four renders, so the suite costs nothing extra for it.
#
# The counter must not be LESS detailed than the room around it,
# where detail means material transitions per pixel rather than brightness or
# spread. Zero is not a tuned constant, it is the sign change: below it the
# busiest thing in frame is not the thing the composition is pointing at.
#
# Bracketed, and the bracket is tight on purpose. Measured on live code before
# the back wall was dressed, three of five generated wall runs read NEGATIVE
# -- -0.005, -0.008, -0.009 -- while every peninsula, island and L run read
# positive. Afterwards the weakest room is +0.005. Ten thousandths between the
# defect and the floor and five between the floor and the weakest good room,
# which is thin, and thin is the honest report: a wall run that loses its
# shelf will fail this, and should.
#
# It exists because neither of the two floors above could see the defect. The
# same wall runs read +0.032 and +0.026 on brightness -- comfortably passing --
# because the wall behind a counter is lit vertical mass. It is also one flat
# ramp step, which is the same fact seen from the other side, and only this
# metric reports it.
#
# The "tight on purpose" bracket above did not survive being re-measured at
# scale (ART_CRITIQUE.md, "The detail floor's bracket, closed"). At n=50, two
# rooms sharing the identical back-wall dressing state landed 0.072 apart
# (-0.011 and +0.061), and the per-dressing-state spread (0.075-0.145) runs
# 3-6x a shelf's own mean effect (~0.02-0.03). No threshold between -0.017 and
# +0.061 separates the two populations cleanly, so 0.0 stays -- moving it only
# trades which rooms get miscategorized. Read this as a POPULATION check
# (roughly 1 in 8-9 wall/L runs reads under-detailed, stable across three
# sample sizes), not a per-room one: a lone room failing by a few thousandths
# is not proof that room specifically is under-dressed.
MIN_FOCAL_DETAIL = 0.0

# The resolution the check's failures get CONFIRMED at before being reported,
# matching `render_room.py`'s and this file's own `main()` delivery default
# (480). If that default ever moves, this should move with it -- it names the
# thing that ships, not an independent number.
#
# "The focal reading falls with render resolution" was long-open (see
# ART_CRITIQUE.md, "Still open") for the CONTRAST reading. Re-swept on current
# code -- after the hull clip, the wall shelf/sign dressing and the
# back-counter height/lamp tuning that landed since -- contrast no longer
# comes close to its floor at any resolution tested (160-480, four topologies
# plus the reference room): weakest reading 0.047 against a floor of 0.030,
# most rooms 0.09-0.18. That old escape has closed, as a side effect of
# unrelated composition fixes, never re-verified until now.
#
# It re-appeared on DETAIL -- added after that bullet was written, so never
# checked against it. Every room's detail LEAD shrinks with resolution,
# including the reference room's (+0.116 at 160 down to +0.071 at 480, a
# generated L run's +0.107 down to +0.044) -- the same "periphery resolves as
# much new detail as the centre" mechanism the original bullet named for
# contrast, just measured on the metric that replaced it. Confirmed on the
# live 12-plan scan with zero content changes: plan 1 reads -0.002 at 320
# (FAILS) and +0.001 at 480 (passes) -- the exact resolution-dependent flip
# this file has been tracking, just relocated.
#
# A ratio reformulation -- (di-do)/(di+do) instead of the raw difference --
# was measured and rejected. It shrinks the DRIFT for healthy rooms (the
# reference's relative range across 160-480 goes from 39% to 9%), but it
# cannot change a single VERDICT: at a floor fixed at exactly 0, sign(a-b) ==
# sign((a-b)/(a+b)) whenever a+b > 0, algebraically. Confirmed numerically --
# plan 1 flips sign at the same targets under the normalized form too. Not a
# fix, just a smaller number telling the same story.
#
# The root cause is the renderer, not the statistic. `shade_toon`'s ordered
# dither and `mesh.py`'s world-space surface grain are both amplitude-capped
# perturbations with a FIXED real-world footprint; `downsample_modal`'s
# majority vote only resolves a band that wide once a block's real-world
# footprint (span / target) shrinks below it -- which happens at a different
# target for a large flat counter than for the many small objects a busy
# periphery is made of. More resolution genuinely shows more real,
# palette-quantized detail, unevenly between zones. No reformulation of a
# screen-space pixel statistic removes that; it would take grading off
# world-space material samples instead of raster pixels, which is a
# rearchitecture, not a tuning pass -- scoped and left for a future pass,
# the same way the fifth topology and the style LoRA were.
#
# So stability comes from the decision rule, not the number: a room already
# failing at `target` gets ONE confirming render at `FOCAL_CONFIRM_TARGET`,
# and only the sub-checks that fail at BOTH resolutions get reported. Rooms
# that pass at `target` never pay for the second render. Verified: plan 1 (the
# resolution-dependent false positive) drops out, plan 10 (the accepted real
# defect -- negative at every one of 240/320/400/480) still fires.
FOCAL_CONFIRM_TARGET = 480


def light_rig(plan: F.Plan) -> LightRig:
    """Daylight at each window, a core over the till, and dark corners.

    The negative pools go in the corners furthest from the service run rather
    than at fixed coordinates. That is the rule the reference room's three
    hand-placed negatives encode -- taking light out of the periphery is what
    builds a centre, because the counter is already near the top of its ramp
    and cannot simply be brightened.
    """
    # ONE CORE AND ONE WASH PER RUN, not per plan. This is the site the last
    # pass named when it refused to build the double-run topology: a rig keyed
    # to `service[0]` renders one lit counter and one bare one, and the bare one
    # is exactly as dark as the corners the negatives are there to sink. The
    # pools are appended in the same order as before, so a one-run plan gets a
    # byte-identical rig -- the loop body below is exactly the single-run
    # computation the previous version did, just no longer discarded after
    # the last run.
    #
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
    #
    # `AWAY` is "away from the customer", by facing: 0 faces +y so its wall
    # side is -y, 90 faces +x so its wall side is -x, and 180/270 -- the
    # galley's far run, the first zone in this file ever built with them --
    # are exactly those two negated. One table instead of an `if run.facing
    # == 0.0` / `else` because that pair only ever had to distinguish two of
    # four directions; a third branch guessing at the other two is exactly
    # the kind of unexercised code this audit exists to not add.
    AWAY = {0.0: (0.0, -1.0), 90.0: (-1.0, 0.0),
            180.0: (0.0, 1.0), 270.0: (1.0, 0.0)}
    runs = plan.of("service")
    pools = []
    run_centres = []
    for run in runs:
        cx, cy = (run.x0 + run.x1) / 2, (run.y0 + run.y1) / 2
        run_centres.append((cx, cy))
        ax, ay = AWAY[run.facing % 360]
        core, wash = (cx + ax * 0.15, cy + ay * 0.15), (cx, cy)
        pools.append(Pool((core[0], core[1], 1.26), 2.6, 0.66))
        pools.append(Pool((wash[0], wash[1], 1.05), 4.6, 0.30))
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
    # Ranked by distance to the NEAREST run, not to a single (cx, cy). One run
    # reduces this to exactly the old formula (the min of one element is that
    # element), so a one-run plan's ranking is unchanged. A galley's four
    # corners are each near one of its two runs -- there is no corner "far
    # from the service run" the way a wall run has one -- so what the negatives
    # actually sink for it is whichever corner is least claimed by either run,
    # which is the honest generalisation of the same rule.
    corners = sorted(((0.4, 0.4), (plan.w - 0.4, 0.4),
                      (0.4, plan.d - 0.4), (plan.w - 0.4, plan.d - 0.4)),
                     key=lambda c: -min((c[0] - rcx) ** 2 + (c[1] - rcy) ** 2
                                        for rcx, rcy in run_centres))
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

    runs = plan.of("service")
    backs_all = plan.of("backbar")
    # Position, not kind, is what pairs a run with its own back bar --
    # `floorplan.generate()` appends each run's own [run, back, queue] triple
    # together, so `runs[i]` and `backs_all[i]` are one counter's two halves.
    # Every multi-run topology built so far (only `galley`) keeps that order;
    # a generator that ever emitted them out of step would need this comment
    # updated, not just the code.
    #
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
    #
    # A galley is neither exception nor member: its near run hugs the y=0 (or
    # x=0) wall exactly like a wall run, but its far run backs onto nothing --
    # `build()` only ever draws walls at x=0 and y=0 (the two `A.wall_run`
    # calls above), so there is no far wall for the second run's shelving to
    # hang on. It gets the free-standing back COUNTER an island uses instead,
    # for the same reason an island does: a run with nothing behind it still
    # needs the lit mass, and there is no wall to put it against.
    ON_WALL_TOPOLOGIES = ("wall run", "L run")

    def run_on_wall(run_idx: int) -> bool:
        if plan.topology in ON_WALL_TOPOLOGIES:
            return True
        if plan.topology == "galley":
            return run_idx == 0
        return False

    on_bar = 0
    for run_idx, run in enumerate(runs):
        # An AXIS (0 or 180 is horizontal), not just "facing exactly 0". The
        # single-run branches never needed the distinction -- they only ever
        # built facing 0 or 90 -- but a galley's far run is the first zone in
        # this file with facing 180 or 270, and `== 0.0` would silently treat
        # a 180 run as vertical, tiling its counter across the room instead
        # of along it.
        horizontal = run.facing in (0.0, 180.0)
        # MIRROR is the half of the four facings this file never built before
        # today: a run whose wall/back side is at the zone's HIGH coordinate
        # rather than its low one, because it backs onto the far run of a
        # galley rather than a real wall. Every placement below that used to
        # assume "low coordinate = back of counter" asks `mirror` first now.
        mirror = run.facing in (180.0, 270.0)
        # The rotation that makes a `front="y"`/`front="x"` mesh -- baked with
        # its detail on the local +y or +x face -- show that detail on the
        # correct side once `mirror` has put the wall on the other one.
        # `centre=True` is what makes this rotation safe: `Layout.add`'s own
        # docstring warns a rotation about the local origin lands nowhere near
        # the coordinates written for it, and every one of these meshes used
        # to be placed by its corner. `rot0` is 0 for the two facings this
        # file already shipped, so every centred call below reproduces the
        # old corner-anchored placement exactly when `mirror` is False --
        # verified by the focal scan matching pre-refactor, not just argued
        # here.
        rot0 = 180.0 if mirror else 0.0
        on_wall = run_on_wall(run_idx)
        length = run.w if horizontal else run.d
        back = backs_all[run_idx] if run_idx < len(backs_all) else None

        # The wall/back edge of THIS run, by facing rather than by axis.
        # Every placement that used to read `run.y0` (or `run.x0`) as "the
        # back of the counter" reads this instead -- for the two facings this
        # file already had, `wall_edge` IS `run.y0`/`run.x0`, so nothing
        # downstream changes; for a galley's mirrored run the wall is at
        # y1/x1 instead, and everything anchored to it flips with it.
        if horizontal:
            wall_edge = run.y1 if mirror else run.y0
        else:
            wall_edge = run.x1 if mirror else run.x0
        # +1 steps AWAY from the wall, toward the customer, in world space;
        # for a mirrored run that is the negative direction.
        away = -1.0 if mirror else 1.0

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

        # --- the service run, as one-tile modules tiled flush along the zone.
        # Anchored and rotated about its own centre rather than its corner, so
        # `rot0` can flip which local face carries the detail without also
        # sliding the footprint -- a corner-anchored rotation would move the
        # whole module half a tile, per `Layout.add`'s own warning.
        n = max(1, int(round(run.w if horizontal else run.d)))
        for i in range(n):
            if horizontal:
                at = (run.x0 + i + 0.5, run.y0 + 0.5, 0)
                m = A.counter(seed=4 + run_idx * 100 + i, front="y")
            else:
                at = (run.x0 + 0.5, run.y0 + i + 0.5, 0)
                m = A.counter(seed=4 + run_idx * 100 + i, front="x")
            # `bar_` because the run and the back bar it serves are ONE fitted
            # group, and `screen_occlusion` already knows what to do with those:
            # how much of each other two members of a group cover is a property of
            # the group's geometry, not of anyone's placement. See the back
            # counter below for why that matters here. `run_idx` sits INSIDE
            # that group tag (`bar{run_idx}_`), so a galley's two runs form two
            # separate groups instead of one group spanning both counters.
            add(m, at=at, rot=rot0, centre=True,
                name=f"counter#bar{run_idx}_{i}")

        # Placed BEFORE the back bar, not after. The shelves go in with
        # `add_seeded`, which rejects a seed whose result is hidden -- but it can
        # only see what is already in the layout, and the kit used to arrive
        # afterwards. So every shelf was checked against an empty counter and
        # passed, and three rooms in eight shipped a shelf 45% behind a grinder.
        # Ordering is part of a constraint solver's correctness: a check that runs
        # before the thing it constrains is a check that always passes.
        # --- the kit itself, spaced along the run rather than at coordinates
        #
        # The non-mirror placement below is corner-anchored (no `centre`),
        # matching every kit item's own local origin sitting near its front
        # edge and extending further along `away` from there -- true for
        # every kit factory, not just measured on one, since it is exactly
        # the geometry that kept an unrotated espresso machine off the floor
        # for every existing topology. `top + away*0.05` puts that origin
        # just off the wall, so the item's bulk lands mid-counter.
        #
        # For a mirrored run that same corner anchor is wrong in the other
        # direction: the item still extends along `away`, but `away` is now
        # NEGATIVE, so anchoring near the wall pushes the item's bulk PAST
        # the counter's own far edge into open floor. Measured directly on
        # seed 8's galley: an unrotated grinder at y 9.34-9.76 against a
        # run spanning 8.25-9.20, floating with nothing under it --
        # `check_built_rooms`' `grounded()` catches exactly this. Centring
        # the mesh and rotating it 180, the same fix the counter modules
        # above use, and anchoring to the run's own depth MIDPOINT rather
        # than a wall offset puts its bulk back over the counter regardless
        # of which kit item it is or how deep that item happens to be.
        top = wall_edge + away * 0.10
        used = 0.35
        mid = (run.y0 + run.y1) / 2 if horizontal else (run.x0 + run.x1) / 2
        for factory, width, tag in kit:
            along = run.x0 + used if horizontal else run.y0 + used
            depth = mid if mirror else top + away * 0.05
            pos = (along, depth, 0.92) if horizontal else (depth, along, 0.92)
            kw = {"rot": rot0, "centre": True} if mirror else {}
            try:
                L.add_seeded(lambda k, f=factory: f(seed=k),
                             range(1 + run_idx * 10, 10 + run_idx * 10),
                             at=pos, name=f"prop#{tag}{run_idx}", **kw)
            except TypeError:
                add(factory(), at=pos, name=f"prop#{tag}{run_idx}", **kw)
            used += width + 0.55

        # --- the return arm of an L, tiled the same way the run is. Built from
        # the zone rather than inferred from the run's end, because the plan
        # already decided which end it turns at and inferring it here would be a
        # second copy of that decision. An L run is always a single service run
        # (`SERVICE_RUNS` in `floorplan.py` defaults to 1), so this only ever
        # fires once regardless of the outer loop; it stays inside the loop
        # rather than after it so a one-run plan's placement order -- and so
        # its solver outcomes -- are untouched.
        for ri, z in enumerate(plan.of("service_return")):
            along_x = z.w >= z.d
            n_ret = max(1, int(round(z.w if along_x else z.d)))
            for i in range(n_ret):
                at = (z.x0 + i, z.y0, 0) if along_x else (z.x0, z.y0 + i, 0)
                add(A.counter(seed=40 + ri * 5 + i,
                              front="y" if along_x else "x"),
                    at=at, name=f"counter#ret{ri}_{i}")

        # --- back counter: what an island (or a galley's far run) has
        # instead of a wall
        # The exclusion below is right about TALL shelving and was wrong to leave
        # the zone empty. A back bar is a counter before it is a shelf, and a run
        # with nothing behind it loses the one surface a wall run gets for free:
        # roughly 1.5 m of lit vertical mass directly behind the till, inside the
        # focal region, holding the eye there. At 0.92 it is under eye level from
        # either side, so it is not the partition the tall stack would be.
        #
        # Anchored to the edge the back bar SHARES with the run, because the tile
        # is 1.0 deep against a 0.8 zone and the 0.2 has to overflow away from the
        # counter it serves. Flush the other way puts it 0.2 inside the service
        # run and every tile is a collision.
        #
        # Which edge is shared used to be READ from geometry (`abs(z.y1 -
        # run.y0) < 0.05`), because every not-on_wall run so far was an island
        # or a peninsula and both only ever built their back bar below/left of
        # the run. `mirror` says it directly instead: a galley's far run has
        # its back bar ABOVE it, the geometric mirror image, and the old
        # geometric read would have flushed the module to the wrong edge and
        # left it unrotated, showing the aisle a plain back instead of a front.
        if not on_wall and back is not None:
            z = back
            along_x = z.w >= z.d
            n_bc = max(1, int(round(z.w if along_x else z.d)))
            for i in range(n_bc):
                if along_x:
                    y0 = z.y0 if mirror else z.y1 - 1.0
                    at = (z.x0 + i + 0.5, y0 + 0.5, 0)
                else:
                    x0 = z.x0 if mirror else z.x1 - 1.0
                    at = (x0 + 0.5, z.y0 + i + 0.5, 0)
                add(A.counter(seed=70 + run_idx * 10 + i,
                              front="y" if along_x else "x", h=BACK_COUNTER_H),
                    at=at, rot=rot0, centre=True,
                    name=f"counter#bar{run_idx}_back{i}")

        # --- back bar: shelving against the wall behind the run
        # Tall shelving only where there is a wall to put it against. A 1.9 stack
        # standing free on an island is a partition between the barista and the
        # room, which is the one thing an island exists not to be.
        if on_wall and back is not None:
            b = back
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
                name = f"prop#backbar{run_idx}_{placed_i}"
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
        #
        # `on_wall` runs are never `mirror` -- the only wall this file ever
        # draws is at x=0/y=0, and both places that back a run against a real
        # wall (a wall/L run's single run, a galley's near run) reach it with
        # the unmirrored facing -- so `run.x0`/`run.y0` (not `wall_edge`) are
        # still the right anchor here, unchanged.
        lo = (run.x0 if horizontal else run.y0) + 2.5
        hi = run.x1 if horizontal else run.y1
        glass = plan.win_x if horizontal else plan.win_y
        solid = [t for t in range(int(lo), int(hi) + 1) if t not in glass]
        # Only when the run is parallel to the wall it backs onto. A peninsula
        # meets the wall end-on, so there is no stretch of wall behind it to hang a
        # board on -- and hanging one anyway put two chalkboards across the room
        # from the counter they price.

        # --- the rest of the back wall: open shelving, and the sign.
        #
        # Found by measuring edge density -- material transitions per pixel -- in
        # the focal region rather than by looking for missing assets. Every
        # generated WALL RUN reads at or below its own periphery on that metric
        # (three of five are negative) while the reference room, which is also a
        # wall run, reads +0.092. The wall is what makes the difference in both
        # directions: it hands a wall run 1.5 m of lit vertical mass, which is why
        # those rooms read brightest, and it is 1.5 m of one flat ramp step, which
        # is why they read flattest. A wall behind a counter is a surface that has
        # to be USED, and the generator was leaving the band between the counter
        # top and the menu boards empty.
        #
        # `A.wall_shelf` puts a row of alternating jars on it, which is transitions
        # rather than mass -- the metric and the fix agree about what is missing.
        # Proposed and tested rather than allocated. Handing out tiles by index --
        # menus 0 and 1, shelves 2 and 3, the sign in the middle -- put the sign
        # through a shelf in three rooms and through a menu board in three more,
        # because a 1.6 shelf is two tiles wide and an index is not a footprint.
        # The back bar shelving above already learned this; the rule is the same
        # rule, so it is the same loop.
        def try_wall(mesh, at, rot, name):
            L.add(mesh, at=at, rot=rot, name=name)
            cand = L.items.pop()
            if L._conflicts(cand, 45.0, 0.35):
                L.rots.pop(name, None)
                return False
            L.items.append(cand)
            return True

        # The sign goes first and takes the middle, because it is the one object
        # here that has a place it needs to be. `A.wall_sign` has sat in the
        # library since the second pass with a docstring calling it "the one
        # bright, high-contrast object over the interaction zone, which is how the
        # composition tells the player where to look" -- and no generated room has
        # ever had one. The reference has had one all along. A focal device the
        # focal check never saw.
        if on_wall and solid:
            mid = solid[len(solid) // 2]
            at = (mid + 0.05, 0.0, 0) if horizontal else (0.0, mid + 0.05, 0)
            try_wall(A.wall_sign(), at, 0 if horizontal else 270,
                    f"decor#sign{run_idx}")

        placed_m = 0
        for t in (solid if on_wall else []):
            if placed_m >= 2:
                break
            at = (t + 0.12, 0.04, 0.62) if horizontal else (0.04, t + 0.12, 0.62)
            if try_wall(A.menu_board(), at, 0 if horizontal else 270,
                        f"decor#menu{run_idx}_{placed_m}"):
                placed_m += 1

        placed_s = 0
        for t in (solid if on_wall else []):
            if placed_s >= 2:
                break
            at = (t + 0.10, 0.10, 0.66) if horizontal else (0.10, t + 0.10, 0.66)
            if try_wall(A.wall_shelf(1.6, "x" if horizontal else "y"), at, 0,
                        f"decor#wshelf{run_idx}_{placed_s}"):
                placed_s += 1

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
        dress = (lambda k: A.cake_stand(), lambda k: A.cup_and_saucer(),
                 lambda k: A.flower_vase(seed=190 + k),
                 lambda k: A.table_clutter("counter"),
                 lambda k: A.cup_and_saucer())
        step, di = 0.42, 0
        reach = length - 0.35
        off = 0.35
        while off < reach and di < 7:
            along = run.x0 + off if horizontal else run.y0 + off
            depth = wall_edge + away * 0.42
            at = ((along, depth, top_z) if horizontal
                  else (depth, along, top_z))
            nm = f"clutter#bar{run_idx}_{di}"
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

    # People BEFORE the dressing. `scatter` already rejects a placement that
    # conflicts, so whichever of the two goes down first wins the floor -- and
    # the dressing was winning it. A six-stool window bar came out empty
    # because plants had been scattered along the same strip and a perched
    # figure's legs landed inside one: a real collision, correctly rejected,
    # caused entirely by the order.
    #
    # This is the occlusion hierarchy again, one level up. There the rule was
    # that a person may stand in front of a plant; here it is that a person
    # gets the seat and the plant goes somewhere else. People are the subject
    # and dressing fills what is left, in both senses.
    made += _people(L, plan, seat_z=seat_z, perch_rail=perch_rail)

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
    runs = plan.of("service")
    queues = plan.of("queue")
    placed = 0
    consumed = 0

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

    # A barista and a queue PER RUN, paired the same way `build()` pairs a
    # run with its own back bar -- position in `plan.of(...)`, not a kind
    # lookup. A galley has two of each; every other topology has one, so the
    # loop below reduces to exactly the old single-barista, single-queue
    # behaviour when `runs` has one element.
    for ri, run in enumerate(runs):
        horizontal = run.facing in (0.0, 180.0)
        mirror = run.facing in (180.0, 270.0)
        # Barista, on the staff side of the run, facing the customers. The
        # base rotations (180 horizontal, 90 vertical) are this rig's own
        # zero-point, not `Zone.facing`'s -- flipping 180 degrees for a
        # mirrored run is correct regardless of which convention the base
        # values came from, because a half-turn is a half-turn either way.
        if horizontal:
            by = run.y1 + 0.42 if mirror else run.y0 - 0.42
            brot = 0.0 if mirror else 180.0
            put(C.build(C.BARISTA), ((run.x0 + run.x1) / 2, by, 0.0),
                brot, f"char#barista{ri}")
        else:
            bx = run.x1 + 0.42 if mirror else run.x0 - 0.42
            brot = 270.0 if mirror else 90.0
            put(C.build(C.BARISTA), (bx, (run.y0 + run.y1) / 2, 0.0),
                brot, f"char#barista{ri}")

        # The queue, stepped along the screen-horizontal so nobody hides
        # anybody. Each run gets its own two roster slots rather than every
        # queue drawing from the same `roster[:2]` -- a galley's two queues
        # would otherwise be the same two people, dressed identically, one
        # tile apart on two different counters.
        if ri < len(queues):
            band = queues[ri]
            for i, spec in enumerate(roster[consumed:consumed + 2]):
                t = 0.30 + 0.34 * i
                if horizontal:
                    at = (band.x0 + band.w * t, band.y0 + 0.45 + i * 0.30, 0.0)
                    rot = 180
                else:
                    at = (band.x0 + 0.45 + i * 0.30, band.y0 + band.d * t, 0.0)
                    rot = 90
                put(C.build(spec), at, rot, f"char#queue{ri}_{i}")
            consumed += 2

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
    # `consumed` is how many roster slots the queue loop above actually used
    # -- 2 per run for every topology so far, but read rather than assumed,
    # so a future run with no queue band (`ri >= len(queues)`) does not
    # starve seating of two people who were never drawn to begin with.
    rest = list(roster[consumed:])
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


# How tall the island's back bar stands, and the reasoning that got there is
# worth keeping because half of it was wrong.
#
# At the service counter's own 0.92 the back bar reads 52-55% hidden behind
# the run, which `screen_occlusion` calls an error. Raising it looked like the
# fix, and the projection says it cannot be: the run sits 1.1 nearer in depth,
# which lifts it 0.39 up the screen, so the back bar's top only clears the
# run's above h = 1.37 -- past chest height and into the partition an island
# exists not to be. Swept 1.10 to 1.32, the hidden share moved 49% to 44%.
# Height was never going to clear that rule; what the back bar actually shows
# is its END, because the same depth offset shifts it 0.78 sideways.
#
# So the occlusion is exempted as what it is -- a fitted pair, like the four
# chairs of a table set -- and the height is chosen on the focal reading
# instead, where it turns out to matter for a different reason than the one it
# was proposed for: the exposed end is taller. The worst island goes +0.017 to
# +0.037 against a floor of 0.015, and the best +0.123 to +0.136.
BACK_COUNTER_H = 1.24

MIN_STOOL_OCCUPANCY = 0.20


def check_stool_occupancy(n: int = 8, seed: int = 1,
                          floor: float = MIN_STOOL_OCCUPANCY) -> list[str]:
    """Somebody must actually be sitting at the window bars.

    Promoted because perching switched itself off and stayed off for several
    commits without failing anything. The stools were placed, the rig worked,
    the support model worked, and the rooms simply had nobody at the bar --
    which is indistinguishable from a room where nobody felt like sitting
    down. A FEATURE THAT SILENTLY SWITCHES OFF LOOKS IDENTICAL TO A FEATURE
    THAT HAD NOTHING TO DO, and the only defence is to assert that it did
    something.

    Two unrelated causes, both found only because the number was eventually
    counted:

    - `screen_occlusion` was symmetric, so of any two objects the one placed
      second lost, and characters are placed last. Every perched figure was
      rejected for hiding a plant. Occupancy 4%.
    - the perimeter dressing was scattered before the people, so plants took
      the window-bar strip and a perched figure's legs landed inside one --
      a real collision, correctly rejected, caused entirely by the order.
      Occupancy 28%.

    With both fixed, 39% over eight rooms. The floor is 0.20, bracketed by the
    4% of the broken state and that 39%. It is a RATE rather than a per-room
    rule on purpose: a room whose only stool is behind a pillar should be
    allowed to stay empty, and one that never seats anyone anywhere should not.

    On verification, honestly: the 4% was measured on the live code before
    either fix, so the bracket is real. It cannot be reproduced now by
    reverting only the occlusion asymmetry -- with people placed before the
    dressing there are no plants behind the stools yet for the symmetric rule
    to trip on, so the two fixes turn out to overlap and either one alone is
    enough. What was verified against the shipped code is that the check
    computes and reports: at a floor of 0.45 it says "7 of 18 stools occupied
    across 8 rooms (39%)". A check whose failure path has never executed is
    not a check, so that much had to be shown even where the original defect
    is no longer reachable.
    """
    stools = perched = 0
    for k in range(seed, seed + n):
        L = build(F.generate(k))
        stools += sum(1 for q in L.items if q.name.startswith("seat#stool"))
        perched += sum(1 for q in L.items if "perch" in q.name)
    if stools == 0:
        return [f"no window bars at all in {n} rooms -- the plan generator "
                f"has stopped proposing them"]
    got = perched / stools
    if got < floor:
        return [f"{perched} of {stools} stools occupied across {n} rooms "
                f"({got:.0%}, floor {floor:.0%}) -- the window bars are "
                f"furniture nobody uses"]
    return []


def check_focal_contrast(n: int = 5, seed: int = 1,
                         target: int = FOCAL_TARGET,
                         confirm_target: int = FOCAL_CONFIRM_TARGET,
                         l_floor: float = MIN_FOCAL_L,
                         c_floor: float = MIN_FOCAL_CONTRAST,
                         d_floor: float = MIN_FOCAL_DETAIL) -> list[str]:
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

    `n` moved from 4 to 5 the day `galley` shipped, for the reason just
    above: with 5 topologies and `n` still 4, the scan stops as soon as it
    has found any four of them, and which one gets left out depends on scan
    order rather than on anything about the topology. Concretely, at seed=1
    the galley now sorts ahead of wall run in that order -- adding a branch
    silently dropped an existing one from the one check built to guarantee
    every branch gets watched.

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

    RESOLUTION-CONFIRMED, not resolution-invariant. See `FOCAL_CONFIRM_TARGET`
    for the full measurement -- edge density (the third reading, `det`) turned
    out to inherit exactly the resolution sensitivity contrast was once
    dropped for, and a ratio reformulation cannot fix a verdict at a floor
    fixed at 0 (it is a sign-preserving transform, proven and confirmed). So a
    failure at `target` gets ONE confirming render at `confirm_target` --
    `render_room.py`'s own delivery resolution -- and is reported only if it
    fails at BOTH. A room that passes at `target` never pays for the second
    render, so the common case costs nothing extra; only the failures do.
    """
    import io as _io
    import contextlib
    import re as _re
    from render_room import render

    def read_room(plan, tgt):
        L = build(plan)
        buf = _io.StringIO()
        with contextlib.redirect_stdout(buf):
            render(L, light_rig(plan), tgt, Path(tempfile.gettempdir())
                   / "_focal_check.png", wear=L.wear_field(),
                   focal=focal_box(plan))
        hits = _re.findall(r"([+-]\d\.\d\d\d)", buf.getvalue())
        return (float(hits[0]), float(hits[1]), float(hits[2])) \
            if len(hits) >= 3 else None

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
        got = read_room(plan, target)
        if got is None:
            out.append(f"plan {k} ({plan.topology}): render reported no "
                       f"focal reading")
            continue
        lead, con, det = got
        fails = []
        if lead < l_floor:
            fails.append(("brightness", f"counter is only "
                          f"{lead:+.3f} brighter than its room "
                          f"(floor {l_floor:+.3f}) -- no centre"))
        if con < c_floor:
            fails.append(("contrast", f"counter is {con:+.3f} "
                          f"in contrast against its room (floor {c_floor:+.3f})"
                          f" -- the periphery has as much to look at"))
        if det < d_floor:
            fails.append(("detail", f"counter carries {det:+.3f} "
                          f"detail against its room (floor {d_floor:+.3f}) -- the "
                          f"busiest thing in frame is not the counter"))
        if fails and confirm_target and confirm_target != target:
            got2 = read_room(plan, confirm_target)
            if got2 is not None:
                lead2, con2, det2 = got2
                still_bad = {"brightness": lead2 < l_floor,
                            "contrast": con2 < c_floor,
                            "detail": det2 < d_floor}
                fails = [(kind, msg) for kind, msg in fails if still_bad[kind]]
        for _, msg in fails:
            out.append(f"plan {k} ({plan.topology}): {msg}")
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


def _focal_scan(n: int, target: int,
                confirm_target: int = FOCAL_CONFIRM_TARGET) -> int:
    """Every plan from 1 to n, graded against the focal floors.

    Exists because the suite check samples ONE ROOM PER TOPOLOGY -- four
    renders, about a minute -- and that sample was measured to be optimistic.
    Over twelve consecutive plans two failed, and neither of the two was one
    the suite check looked at. A 17% escape rate is worth knowing about and
    worth stating; hiding it behind a green check would be worse.

    It reads 0 of 12 now, and the two it caught had nothing in common. One was
    an INSTRUMENT error -- the focal region was the bounding box of a
    projected parallelogram, half of it floor and wall -- and no room changed
    to fix it. The other was a real defect, an island whose back bar zone was
    empty, and one room changed. Saying "the escape rate is closed" would hide
    which was which.

    Graded at FOCAL_TARGET, like the suite check. It used to default to 480
    while the check ran at 320, so the two gates disagreed by construction.

    A failure here is now CONFIRMED at `confirm_target` (the delivery
    resolution) before it counts -- see `FOCAL_CONFIRM_TARGET`. A room that
    fails at `target` but passes at `confirm_target` prints RESCUED rather
    than being silently dropped, so the resolution-dependent cases stay
    visible instead of just disappearing from the count.

    Not folded into the suite because twelve rooms is several minutes, and a
    check nobody runs protects nothing.
    """
    import io as _io
    import contextlib
    import re as _re
    from render_room import render

    def read_room(plan, tgt):
        L = build(plan)
        buf = _io.StringIO()
        with contextlib.redirect_stdout(buf):
            render(L, light_rig(plan), tgt, Path(tempfile.gettempdir())
                   / "_focal_scan.png", wear=L.wear_field(),
                   focal=focal_box(plan))
        hits = _re.findall(r"([+-]\d\.\d\d\d)", buf.getvalue())
        return float(hits[0]), float(hits[1]), float(hits[2])

    bad = rescued = 0
    for k in range(1, n + 1):
        plan = F.generate(k)
        lead, con, det = read_room(plan, target)
        fail = (lead < MIN_FOCAL_L or con < MIN_FOCAL_CONTRAST
                or det < MIN_FOCAL_DETAIL)
        note = ""
        if fail and confirm_target and confirm_target != target:
            lead2, con2, det2 = read_room(plan, confirm_target)
            still = (lead2 < MIN_FOCAL_L or con2 < MIN_FOCAL_CONTRAST
                     or det2 < MIN_FOCAL_DETAIL)
            if not still:
                fail = False
                rescued += 1
                note = (f"   RESCUED at {confirm_target} "
                        f"(L {lead2:+.3f} C {con2:+.3f} D {det2:+.3f})")
        bad += fail
        print(f"  plan {k:2d}  {plan.topology:10s} L {lead:+.3f}  C {con:+.3f}"
              f"  D {det:+.3f}   {'FAIL' if fail else 'ok'}{note}")
    print("")
    print(f"  {bad} of {n} rooms fail the focal floors "
          f"({bad / n:.0%})" + (f", {rescued} rescued by the "
          f"{confirm_target} confirmation" if rescued else ""))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=3)
    # 0 means "whatever this mode is calibrated at". A single default of 480
    # made `--focal-scan` grade twelve rooms at a resolution the suite check
    # does not use, so the two gates disagreed by construction and the scan's
    # own docstring cited a 17% escape rate measured against different floors
    # than the ones it was comparing to.
    ap.add_argument("--target", type=int, default=0)
    ap.add_argument("--style", default=None,
                    help="style pack to render against (default: cozy_ghibli)")
    ap.add_argument("--out", default=None,
                    help="default: proof/plan_room.png, or "
                         "proof/plan_room_<style>.png for a non-default --style")
    ap.add_argument("--focal-scan", type=int, default=0, metavar="N",
                    help="measure focal lead over N consecutive plans and "
                         "exit; the suite check only samples one room per "
                         "topology, and this is how that sample was shown to "
                         "be optimistic")
    ap.add_argument("--no-confirm", action="store_true",
                    help="skip the FOCAL_CONFIRM_TARGET re-render on a "
                         "failure -- for reproducing the single-resolution "
                         "reading directly, not for normal use")
    args = ap.parse_args()

    if args.focal_scan:
        return _focal_scan(args.focal_scan, args.target or FOCAL_TARGET,
                           confirm_target=0 if args.no_confirm
                           else FOCAL_CONFIRM_TARGET)

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
    # `focal_box(plan)`, not a second copy of it. This was a hand-inlined
    # duplicate hard-coded to `service[0]`/`backbar[0]` -- one lit counter and
    # one bare one for any topology with more than one run, and a second
    # place that would have had to be remembered and edited alongside
    # `focal_box` itself. `focal_box` already unions every service, backbar
    # and service_return zone, so calling it here is both the fix and a
    # simplification.
    focal = focal_box(plan)
    ramps = None
    if args.style:
        from pixelize import load_palette
        from style import load_style
        ramps = load_palette(load_style(args.style).palette_path)
    out_path = args.out or (str(ROOT / "proof" / "plan_room.png") if not args.style
                            else str(ROOT / "proof" / f"plan_room_{args.style}.png"))
    from render_room import render
    render(L, light_rig(plan), (args.target or 480), Path(out_path),
           wear=L.wear_field(), focal=focal, ramps=ramps)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
