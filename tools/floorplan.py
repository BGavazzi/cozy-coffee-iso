"""Cafe floor plans, proposed and tested rather than typed.

`render_room.build_room` is 249 lines of code holding 48 hand-written
coordinates. Six passes have been spent turning the things *in* the room into
generators, and the room itself is still the last authored asset in the
pipeline: `assetlib` can now make any number of chairs, and there is exactly
one place to put them.

This is the same move `Layout.scatter` made for dressing and `add_seeded` made
for fitted props, one level up. A plan is proposed -- room size, where the
daylight is, which wall the service run takes, where the seating goes -- and
then tested against rules a cafe has to satisfy. What comes out is zones, not
props: the plan says "a lounge belongs in this rectangle facing this way", and
the existing generators and the scatter solver fill it.

The rules are the interesting part, because they are what a floor plan *is*:

  * You must be able to walk from the door to the till, and from the till to
    every seating zone, through a corridor a person actually fits down. This is
    tested by erosion and flood fill on a grid, not by comparing rectangles --
    two zones can leave a legal-looking gap between them that is a dead end.
  * The service run goes against a wall, and not across a window: a counter
    under glass blocks the one light source the room has.
  * The queue stands in front of the till and nothing else may.
  * Seating gets daylight. A cafe whose seats are all in the dark corner is a
    floor plan that passes every geometric rule and that nobody would sit in.

The reference room stays hand-authored on purpose. It is the exemplar a person
critiques, and six passes of art direction live in its coordinates; the point
here is that it is no longer the *only* room the pipeline can make.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# A person, for the purpose of "does this corridor fit one". Shoulders measured
# off the actual rig: `character.arms` spans 0.75 tiles at bulk 1.0, and the
# generated cast reaches 0.80 at the top of its bulk range. 0.55 of clearance
# radius leaves a hand's width either side of the widest extra in the cast.
BODY_R = 0.55

# Grid step for the walkability test. Below 0.25 the flood fill starts costing
# more than the rest of the plan put together, and above it a real 1.2-wide
# corridor can fall between samples and read as blocked.
CELL = 0.25

SERVICE_DEPTH = 0.95        # counter carcass, wall to customer side
BACKBAR_DEPTH = 0.80        # the strip behind it the staff stand in
QUEUE_DEPTH = 1.45          # kept clear in front of the till

# The floor left between a galley's two queues once both stacks -- back bar +
# run + queue, BACKBAR_DEPTH + SERVICE_DEPTH + QUEUE_DEPTH = 3.20 deep each --
# are subtracted from the room. Bracketed between 1.10 (2 x BODY_R, below
# which the erosion grid in `_walkable` admits no cell at all: nothing narrower
# than a body-radius disc survives it) and 1.45 (QUEUE_DEPTH itself, this
# repo's own precedent for "enough clear floor to stand in"). Set above that
# precedent rather than at it, because this aisle carries traffic bound for
# BOTH counters at once, not one.
GALLEY_AISLE = 1.6


@dataclass
class Zone:
    """A tagged rectangle. `facing` is degrees, 0 meaning contents face +y."""
    kind: str
    x0: float
    y0: float
    x1: float
    y1: float
    facing: float = 0.0

    @property
    def w(self) -> float:
        return self.x1 - self.x0

    @property
    def d(self) -> float:
        return self.y1 - self.y0

    @property
    def area(self) -> float:
        return self.w * self.d

    def overlaps(self, o: "Zone", slack: float = 0.0) -> bool:
        return (min(self.x1, o.x1) - max(self.x0, o.x0) > slack
                and min(self.y1, o.y1) - max(self.y0, o.y0) > slack)


@dataclass
class Plan:
    w: int
    d: int
    win_x: tuple = ()        # window tiles on the y=0 wall
    win_y: tuple = ()        # window tiles on the x=0 wall
    door: tuple = (0.0, 0.0)
    zones: list = field(default_factory=list)
    # Which counter arrangement the generator chose. Recorded rather than
    # re-derived: `build_plan` was reading `backbar.y0 < 0.05` to decide
    # whether the run hugs a wall, the proof sheet had its own version, and a
    # sweep written to count the three topologies used a third that was simply
    # wrong -- it reported zero peninsulas out of sixty and the peninsulas were
    # there. Three readers reconstructing one decision from its consequences
    # will get three answers, and the one that is wrong looks exactly like a
    # regression in the generator.
    topology: str = "wall run"

    def of(self, kind: str) -> list:
        return [z for z in self.zones if z.kind == kind]

    def blocking(self) -> list:
        """Zones a person cannot walk through.

        Seating is NOT blocking. You walk between cafe tables -- that is what
        the gaps between them are -- and treating a table cluster as a solid
        block would reject every plan that has any seating in the middle of the
        floor, which is most of them.
        """
        return [z for z in self.zones
                if z.kind in ("service", "service_return", "backbar",
                              "window_bar")]


def _mix(seed: int) -> int:
    h = (seed * 2654435761 + 1013904223) & 0xFFFFFFFF
    h ^= h >> 16
    h = (h * 2246822519) & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 3266489917) & 0xFFFFFFFF
    return (h ^ (h >> 16)) & 0x7FFFFFFF


def _walkable(plan: Plan, clearance: float = BODY_R):
    """Grid of cells whose `clearance` disc is clear of walls and blockers.

    Erosion before flood fill, rather than a width check on the gaps between
    rectangles. A pair of zones can leave a 1.4-wide gap that goes nowhere, and
    a corridor can be wide at both ends and pinched in the middle; neither of
    those is visible in a comparison of rectangle edges, and both are obvious
    once you ask which cells a body-sized disc can occupy.
    """
    nx, ny = int(plan.w / CELL), int(plan.d / CELL)
    blockers = plan.blocking()
    grid = [[False] * ny for _ in range(nx)]
    for i in range(nx):
        cx = (i + 0.5) * CELL
        if cx < clearance or cx > plan.w - clearance:
            continue
        for j in range(ny):
            cy = (j + 0.5) * CELL
            if cy < clearance or cy > plan.d - clearance:
                continue
            for z in blockers:
                # Nearest point of the rectangle to the cell centre.
                dx = max(z.x0 - cx, 0.0, cx - z.x1)
                dy = max(z.y0 - cy, 0.0, cy - z.y1)
                if dx * dx + dy * dy < clearance * clearance:
                    break
            else:
                grid[i][j] = True
    return grid, nx, ny


def _reachable(grid, nx, ny, start) -> set:
    si, sj = start
    if not (0 <= si < nx and 0 <= sj < ny and grid[si][sj]):
        # Snap to the nearest walkable cell: a door sits in a wall, and the
        # wall is never walkable by construction.
        best = None
        for i in range(nx):
            for j in range(ny):
                if grid[i][j]:
                    d = (i - si) ** 2 + (j - sj) ** 2
                    if best is None or d < best[0]:
                        best = (d, i, j)
        if best is None:
            return set()
        si, sj = best[1], best[2]
    seen = {(si, sj)}
    stack = [(si, sj)]
    while stack:
        i, j = stack.pop()
        for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
            if 0 <= a < nx and 0 <= b < ny and grid[a][b] and (a, b) not in seen:
                seen.add((a, b))
                stack.append((a, b))
    return seen


def _touches(zone: Zone, cells: set, reach: float = 0.7) -> bool:
    """Is any reachable cell within `reach` of this zone?"""
    for i, j in cells:
        cx, cy = (i + 0.5) * CELL, (j + 0.5) * CELL
        dx = max(zone.x0 - cx, 0.0, cx - zone.x1)
        dy = max(zone.y0 - cy, 0.0, cy - zone.y1)
        if dx * dx + dy * dy < reach * reach:
            return True
    return False


# --- the rules ---------------------------------------------------------------

MIN_SEAT_AREA = 12.0        # tiles of seating zone; below this it is a kiosk

# One rectangle of tables is a canteen. The first version of this file said so
# in a comment above the splitting code and then did not enforce it, and the
# largest single seating block over sixty seeds came out at 93 tiles -- a third
# of the floor as one undivided block of covers. A comment is not a rule; the
# ratchet has said this about art direction for six passes and it is just as
# true about layout.
MAX_SEAT_BLOCK = 34.0
# Calibrated against the reference room, which is the only cafe in this
# repository that six passes of art direction have signed off on. It scores
# 30% of its seats within daylight reach, 27% by footprint area -- so a floor
# of 45%, which is where this started, rejects the exemplar. A threshold above
# the known-good case is as wrong as one below the defect, and it is the more
# dangerous of the two because it does not look blind: it looks strict, and it
# quietly chose the layout (horizontal counter runs went from 11% accepted to
# 5% and the whole cast of plans flipped walls).
MIN_DAYLIT_SHARE = 0.22     # of seating floor, by area, within reach of glass
DAYLIGHT_REACH = 4.2        # how far into the room a window is worth having
DAYLIGHT_SPILL = 1.1        # how far past its own tiles a window throws light

# How many `service` zones each topology is, EXACTLY -- a table rather than a
# floor, so the count stays an assertion about the generator and not a licence.
# An L run is still one: its arm is a `service_return`, for the reason the L
# branch records. A galley is two, and that is the whole topology.
#
# Read by topology rather than derived, the same argument `Plan.topology` itself
# was written down for: three readers reconstructing one decision from its
# consequences get three answers. A topology missing from this table defaults to
# one, so a new branch that forgets to declare itself is held to the old rule
# rather than to none.
SERVICE_RUNS = {"galley": 2}


def check_plan(plan: Plan) -> list[str]:
    """Everything a floor plan has to be true for. Errors, not warnings.

    Written as one function returning strings, matching every other check in
    this pipeline, so `manifest.py` can run it over generated plans the same
    way it runs the roster checks over generated extras.
    """
    out = []
    zones = plan.zones

    for a in range(len(zones)):
        for b in range(a + 1, len(zones)):
            za, zb = zones[a], zones[b]
            if za.kind == "queue" or zb.kind == "queue":
                continue      # the queue is empty floor; see its own rule
            if za.overlaps(zb, slack=0.05):
                out.append(f"{za.kind} and {zb.kind} zones overlap")

    for z in zones:
        if z.x0 < -0.01 or z.y0 < -0.01 or z.x1 > plan.w + 0.01 or z.y1 > plan.d + 0.01:
            out.append(f"{z.kind} zone runs outside the room")

    # How many service runs each topology is allowed. A CAP per topology, not a
    # relaxation of the rule: the rule's whole value is that it fires loudly on
    # a generator that appends its zone triple twice, which is exactly what the
    # peninsula branch shipped doing (see its comment below) -- every proposal
    # rejected, 0% acceptance, found only because this line said so. Deleting
    # it to admit the galley would have thrown that away and let the next
    # double-append pass silently, on the topology least able to survive it.
    want = SERVICE_RUNS.get(plan.topology, 1)
    svc = plan.of("service")
    if len(svc) != want:
        out.append(f"a {plan.topology} is {want} service run(s), "
                   f"this plan has {len(svc)}")
        return out

    # The counter must not sit under a window. A back bar is a solid 2.4-tall
    # wall of shelving and a counter run is 1.1 of carcass; either across glass
    # trades the room's only light source for storage.
    for z in plan.of("service") + plan.of("backbar"):
        if z.y1 < 1.2:                     # against the y=0 wall
            lo, hi = int(z.x0), int(z.x1 - 1e-6)
            for t in plan.win_x:
                if lo <= t <= hi:
                    out.append(f"{z.kind} runs across the window at x tile {t}")
        if z.x1 < 1.2:                     # against the x=0 wall
            lo, hi = int(z.y0), int(z.y1 - 1e-6)
            for t in plan.win_y:
                if lo <= t <= hi:
                    out.append(f"{z.kind} runs across the window at y tile {t}")

    # The queue stands in front of the till and nothing else may.
    q = plan.of("queue")
    if not q:
        out.append("no queue band in front of the service run")
    for band in q:
        for z in zones:
            if z.kind in ("queue", "service", "backbar"):
                continue
            if band.overlaps(z, slack=0.05):
                out.append(f"{z.kind} zone stands in the queue")

    grid, nx, ny = _walkable(plan)
    if not any(any(col) for col in grid):
        out.append("nowhere in this room is wide enough to stand")
        return out
    cells = _reachable(grid, nx, ny,
                       (int(plan.door[0] / CELL), int(plan.door[1] / CELL)))
    if not cells:
        out.append("the door opens onto nothing walkable")
        return out
    # EVERY run, not the first one. A galley's far counter is reached the long
    # way round the end of the near one, and a rule that only ever asked about
    # `svc[0]` would have accepted a plan whose second counter no customer can
    # get to -- the flood fill is already equipped to answer this, it was
    # simply only being asked once.
    for ri, r in enumerate(svc):
        if not _touches(r, cells):
            out.append("you cannot walk from the door to the counter"
                       + (f" at ({r.x0:.1f}, {r.y0:.1f})" if len(svc) > 1
                          else ""))
    seating = [z for z in zones if z.kind in ("cafe", "lounge", "window_bar")]
    for z in seating:
        if not _touches(z, cells):
            out.append(f"the {z.kind} zone at "
                       f"({z.x0:.1f}, {z.y0:.1f}) cannot be reached")

    for z in seating:
        if z.area > MAX_SEAT_BLOCK:
            out.append(f"the {z.kind} zone is {z.area:.0f} tiles in one block "
                       f"(cap {MAX_SEAT_BLOCK:.0f}) -- that is a canteen")
    area = sum(z.area for z in seating)
    if area < MIN_SEAT_AREA:
        out.append(f"only {area:.1f} tiles of seating (floor {MIN_SEAT_AREA})")

    # Daylight. Every geometric rule above can pass on a plan whose seats are
    # all against the back wall, which is a plan nobody would sit in.
    #
    # Measured as lit AREA, not as a flag per zone. The first version asked
    # whether a zone's near edge fell within reach of a window, which made a
    # block spanning y 3.6 to 8.0 exactly as dark as one spanning 6.0 to 8.0 --
    # a threshold standing in for a quantity, which is the same mistake the
    # silhouette metric made when it counted *distinct* outlines instead of
    # measuring how far apart they were. The cliff had a real consequence:
    # horizontal counter runs were rejected at 97% against 88% for vertical
    # ones, so the rule was quietly choosing the layout.
    lit = sum(_lit_area(z, plan) for z in seating)
    if area > 0 and lit / area < MIN_DAYLIT_SHARE:
        out.append(f"only {lit / area:.0%} of seating is near a window "
                   f"(floor {MIN_DAYLIT_SHARE:.0%})")
    return out


# --- the generator -----------------------------------------------------------

def generate(seed: int = 1, tries: int = 120) -> Plan:
    """Propose plans until one passes `check_plan`.

    Proposes rather than constructs, for the reason `Layout.scatter` does: the
    rules are already written and already run, so the cheapest correct
    generator is the one that asks them. A constructive version would have to
    encode "leave room for the queue" twice, once in the builder and once in
    the check, and the two would drift.

    Proposing blind, though, is not the same as proposing. The first version
    drew the service run and the windows independently and cut the seating out
    of a "free area" that did not know which wall the run was on. It passed 6
    proposals in 2157 -- 0.3% -- and the two failures it kept re-drawing were
    ones it had the information to avoid: the back bar crossed the glass 4754
    times, and the seating landed on the queue or the counter 5900 times.

    A rejection rate like that is not the solver being strict, it is the
    proposal being uninformed, and the difference matters. A search that
    rejects almost everything is one tightened rule away from returning its
    least-bad attempt every time -- silently, because the fallback looks like
    an answer. So the windows are now chosen around the back bar, and the
    seating is cut from the floor the service band actually leaves. What is
    left for the checker to reject is the genuinely awkward plan, which is what
    a checker is for.
    """
    st = _mix(seed)

    def rnd():
        nonlocal st
        st = _mix(st)
        return st / 0x7FFFFFFF

    best, best_n = None, 1 << 30
    for _ in range(tries):
        w = 12 + int(rnd() * 5)
        d = 9 + int(rnd() * 4)
        run_len = 4.0 + rnd() * 3.0
        ret = None
        # A peninsula juts into the room from the far wall instead of running
        # along it. It is the one counter arrangement here that changes the
        # circulation problem rather than the furniture arrangement: the floor
        # is cut in two and everything has to come round the end, which is a
        # question the flood fill is already equipped to ask and the rectangle
        # comparisons are not.
        peninsula = rnd() < 0.26
        # An island touches no wall at all. It is the last of the four and the
        # one that asks the most of the flood fill: the floor becomes a ring,
        # and every seat has to be reachable the long way round if the short
        # way is blocked. Nothing here tests that -- `blocking()` selects by
        # kind and the erosion grid does the rest, the same bargain the L run
        # made.
        #
        # It is also the only arrangement that frees every wall for glass. The
        # other three pin a counter or a back bar against one, and `_windows`
        # is handed a blocked span to route around; an island hands it None,
        # which is not a special case so much as the absence of the constraint
        # the other three impose. That is a real reason cafes build them.
        island = not peninsula and rnd() < 0.22
        # Two service runs facing each other across the main aisle, reusing
        # the run/back/queue triple a second time rather than a new kind of
        # zone. Scoped and named but deliberately not built two passes ago
        # (see ART_CRITIQUE.md, "A fifth topology") because the audit it
        # needed -- eight `plan.of("service")`/`plan.of("backbar")` reads in
        # `build_plan.py`, four hard-coded to `[0]` -- was a dedicated pass on
        # its own. That pass is `build_plan.py`'s `run_idx` loop; this branch
        # is what it unblocks.
        galley = not peninsula and not island and rnd() < 0.22
        horizontal = rnd() < 0.62
        zones = []

        if island:
            span = SERVICE_DEPTH + BACKBAR_DEPTH
            if horizontal:
                run_len = min(run_len, w - 2 * ISLAND_CLEAR - 0.4)
                if run_len < 3.0 or d < 2 * ISLAND_CLEAR + span + QUEUE_DEPTH:
                    continue
                # `iy` is bounded by the floor the island has to LEAVE, not
                # just by the walls it has to clear. Placed anywhere in the
                # legal band it pushed the main seating rectangle under the
                # 4.0 x 3.5 minimum and the proposal was thrown away further
                # down -- 7 island proposals reached the checker in sixty
                # seeds, and the rest died on a guard the branch could have
                # satisfied itself. Third time in this generator: the windows,
                # then the L run's queue, now this.
                lo = ISLAND_CLEAR + BACKBAR_DEPTH
                hi = d - 3.3 - MIN_SEAT_RECT_D
                if hi < lo:
                    continue        # an island needs floor on both sides
                ix = ISLAND_CLEAR + rnd() * max(0.1, w - run_len -
                                                2 * ISLAND_CLEAR)
                iy = lo + rnd() * (hi - lo)
                run = Zone("service", ix, iy, ix + run_len,
                           iy + SERVICE_DEPTH, 0.0)
                back = Zone("backbar", ix, iy - BACKBAR_DEPTH,
                            ix + run_len, iy, 0.0)
                queue = Zone("queue", ix - 0.4, run.y1, ix + run_len + 0.4,
                             run.y1 + QUEUE_DEPTH, 0.0)
                main = (0.5, queue.y1 + 0.4, w - 0.5, d - 0.5)
                side = (0.5, 0.5, w - 0.5, back.y0 - 0.6)
            else:
                run_len = min(run_len, d - 2 * ISLAND_CLEAR - 0.4)
                if run_len < 3.0 or w < 2 * ISLAND_CLEAR + span + QUEUE_DEPTH:
                    continue
                lo = ISLAND_CLEAR + BACKBAR_DEPTH
                hi = w - 3.3 - MIN_SEAT_RECT_W
                if hi < lo:
                    continue
                iy = ISLAND_CLEAR + rnd() * max(0.1, d - run_len -
                                                2 * ISLAND_CLEAR)
                ix = lo + rnd() * (hi - lo)
                run = Zone("service", ix, iy, ix + SERVICE_DEPTH,
                           iy + run_len, 90.0)
                back = Zone("backbar", ix - BACKBAR_DEPTH, iy, ix,
                            iy + run_len, 90.0)
                queue = Zone("queue", run.x1, iy - 0.4,
                             run.x1 + QUEUE_DEPTH, iy + run_len + 0.4, 90.0)
                main = (queue.x1 + 0.4, 0.5, w - 0.5, d - 0.5)
                side = (0.5, 0.5, back.x0 - 0.6, d - 0.5)
            # No wall is blocked, so the glass may go anywhere.
            blocked_x = blocked_y = None
            door = (w - 0.4, d - 0.4)
            # NO `zones += [run, back, queue]` here. The shared block below
            # does it, and the peninsula branch shipped with both -- every
            # proposal failing its own "a cafe has one service run" rule, 0%
            # acceptance. Writing the island from the peninsula as a template
            # reproduced it exactly, which is what a template is for and also
            # what it costs.
        elif peninsula:
            run_len = min(run_len, (d if horizontal else w) - 3.2)
            if run_len < 3.0:
                continue
            if horizontal:
                rx = 2.2 + rnd() * max(0.1, w - run_len - 6.0)
                run = Zone("service", rx, 0.8, rx + SERVICE_DEPTH,
                           0.8 + run_len, 90.0)
                back = Zone("backbar", rx - BACKBAR_DEPTH, 0.0,
                            rx, 0.8 + run_len + 0.3, 90.0)
                queue = Zone("queue", run.x1, 0.5, run.x1 + QUEUE_DEPTH,
                             run.y1 + 0.4, 90.0)
                blocked_x = (back.x0 - 0.2, queue.x1 + 0.2)
                blocked_y = None
                main = (queue.x1 + 0.5, 0.5, w - 0.5, d - 0.5)
                side = (0.5, 0.5, back.x0 - 0.5, d - 0.5)
                door = (w - 0.4, d - 0.4)
            else:
                ry = 2.2 + rnd() * max(0.1, d - run_len - 6.0)
                run = Zone("service", 0.8, ry, 0.8 + run_len,
                           ry + SERVICE_DEPTH, 0.0)
                back = Zone("backbar", 0.0, ry - BACKBAR_DEPTH,
                            0.8 + run_len + 0.3, ry, 0.0)
                queue = Zone("queue", 0.5, run.y1, run.x1 + 0.4,
                             run.y1 + QUEUE_DEPTH, 0.0)
                blocked_x = None
                blocked_y = (back.y0 - 0.2, queue.y1 + 0.2)
                main = (0.5, queue.y1 + 0.5, w - 0.5, d - 0.5)
                side = (0.5, 0.5, w - 0.5, back.y0 - 0.5)
                door = (w - 0.4, d - 0.4)
        elif galley:
            # `run`/`back`/`queue` is the near run -- identical in shape to a
            # plain wall run, backed against the real wall at y=0 (or x=0).
            # `run2`/`back2`/`queue2` is its mirror image across the aisle,
            # backed by nothing: `build_plan.py` only ever draws walls at
            # x=0 and y=0 (its two `A.wall_run` calls), so the far run gets
            # the free-standing back COUNTER an island uses instead of
            # shelving, not a second stretch of wall that doesn't exist.
            stack = BACKBAR_DEPTH + SERVICE_DEPTH + QUEUE_DEPTH
            if horizontal:
                run_len = min(run_len, w - 1.6)
                if run_len < 3.0 or d < 2 * stack + GALLEY_AISLE:
                    continue
                rx = 0.8 + rnd() * max(0.1, w - run_len - 1.6)
                run = Zone("service", rx, BACKBAR_DEPTH, rx + run_len,
                           BACKBAR_DEPTH + SERVICE_DEPTH, 0.0)
                back = Zone("backbar", rx - 0.3, 0.0, rx + run_len + 0.3,
                            BACKBAR_DEPTH, 0.0)
                queue = Zone("queue", rx - 0.4, run.y1, rx + run_len + 0.4,
                             run.y1 + QUEUE_DEPTH, 0.0)
                run2 = Zone("service", rx, d - BACKBAR_DEPTH - SERVICE_DEPTH,
                            rx + run_len, d - BACKBAR_DEPTH, 180.0)
                back2 = Zone("backbar", rx - 0.3, d - BACKBAR_DEPTH,
                             rx + run_len + 0.3, d, 180.0)
                queue2 = Zone("queue", rx - 0.4, run2.y0 - QUEUE_DEPTH,
                              rx + run_len + 0.4, run2.y0, 180.0)
                # Only the near wall (y=0) carries a window array in this
                # `Plan` -- there is no far-wall counterpart to `win_x` -- so
                # only the near back bar needs to steer `_windows`.
                blocked_x = (back.x0, back.x1)
                blocked_y = None
                door = (w - 0.4, d / 2)
                main = (rx + run_len + 0.5, 0.5, w - 0.5, d - 0.5)
                side = (0.5, 0.5, rx - 0.5, d - 0.5)
            else:
                run_len = min(run_len, d - 1.6)
                if run_len < 3.0 or w < 2 * stack + GALLEY_AISLE:
                    continue
                ry = 0.8 + rnd() * max(0.1, d - run_len - 1.6)
                run = Zone("service", BACKBAR_DEPTH, ry,
                           BACKBAR_DEPTH + SERVICE_DEPTH, ry + run_len, 90.0)
                back = Zone("backbar", 0.0, ry - 0.3, BACKBAR_DEPTH,
                            ry + run_len + 0.3, 90.0)
                queue = Zone("queue", run.x1, ry - 0.4, run.x1 + QUEUE_DEPTH,
                             ry + run_len + 0.4, 90.0)
                run2 = Zone("service", w - BACKBAR_DEPTH - SERVICE_DEPTH, ry,
                            w - BACKBAR_DEPTH, ry + run_len, 270.0)
                back2 = Zone("backbar", w - BACKBAR_DEPTH, ry - 0.3, w,
                             ry + run_len + 0.3, 270.0)
                queue2 = Zone("queue", run2.x0 - QUEUE_DEPTH, ry - 0.4,
                              run2.x0, ry + run_len + 0.4, 270.0)
                blocked_x = None
                blocked_y = (back.y0, back.y1)
                door = (w / 2, d - 0.4)
                main = (0.5, ry + run_len + 0.5, w - 0.5, d - 0.5)
                side = (0.5, 0.5, w - 0.5, ry - 0.5)
        elif horizontal:
            x0 = 0.8 + rnd() * max(0.1, w - run_len - 1.6)
            run = Zone("service", x0, BACKBAR_DEPTH, x0 + run_len,
                       BACKBAR_DEPTH + SERVICE_DEPTH, 0.0)
            back = Zone("backbar", x0 - 0.3, 0.0, x0 + run_len + 0.3,
                        BACKBAR_DEPTH, 0.0)
            queue = Zone("queue", x0 - 0.4, run.y1, x0 + run_len + 0.4,
                         run.y1 + QUEUE_DEPTH, 0.0)
            blocked_x, blocked_y = (back.x0, back.x1), None
        else:
            y0 = 0.8 + rnd() * max(0.1, d - run_len - 1.6)
            run = Zone("service", BACKBAR_DEPTH, y0,
                       BACKBAR_DEPTH + SERVICE_DEPTH, y0 + run_len, 90.0)  # noqa
            back = Zone("backbar", 0.0, y0 - 0.3, BACKBAR_DEPTH,
                        y0 + run_len + 0.3, 90.0)
            queue = Zone("queue", run.x1, y0 - 0.4, run.x1 + QUEUE_DEPTH,
                         y0 + run_len + 0.4, 90.0)
            blocked_x, blocked_y = None, (back.y0, back.y1)
        # A galley appends BOTH triples here, not just its near one -- the
        # far run has no separate append site of its own, so the shared line
        # below has to know about it. This is exactly the site the peninsula
        # branch's own comment (a few lines up) warns about getting wrong a
        # second way: not a double append of the SAME triple, but a triple
        # silently dropped for a topology that has two.
        zones += [run, back, queue, run2, back2, queue2] if galley else \
                 [run, back, queue]

        # An L: a short return at one end of the run, turning into the room.
        # It is modelled as its own kind rather than as a second `service`
        # zone, and that is not a dodge of the "a cafe has one service run"
        # rule -- it is what an L actually is. A cafe has one counter with a
        # short arm at the till end, not two counters. Modelling it as two
        # would also have been the expensive kind of wrong: seven places in
        # `build_plan` read `plan.of("service")[0]`, and every one of them
        # would have quietly served the first arm and ignored the second,
        # which is a fallback that succeeds.
        #
        # Nothing here checks that the return leaves room to walk round. It
        # does not need to: `blocking()` selects by kind, so adding the kind
        # puts the arm in the erosion grid and the flood fill judges it on the
        # same terms as everything else. A generator that has to be taught each
        # new obstacle separately is a generator with a list; this one has a
        # rule.
        if not peninsula and not island and not galley and rnd() < 0.30:
            arm = 1.4 + rnd() * 1.1
            # The arm turns at the end of the run FURTHEST from the camera,
            # always. Which end used to be a coin flip, and the flip is a
            # camera-space question with only one answer: an arm at the near
            # end crosses in front of the run it belongs to. Measured over
            # every L plan in twenty-four seeds -- every near-end arm hid
            # 53-55% of a counter module behind it and every far-end arm hid
            # nothing, six for six.
            #
            # So the draw is gone rather than constrained. A degree of freedom
            # whose every second value is wrong is not a degree of freedom, and
            # leaving the flip in and rejecting half its outcomes would have
            # been the plan generator's original 0.3% acceptance in miniature.
            if horizontal:
                ax = run.x0
                ret = Zone("service_return", ax, run.y1,
                           ax + SERVICE_DEPTH, run.y1 + arm, 0.0)
                q = Zone("queue", ret.x1 + 0.3, queue.y0, queue.x1,
                         queue.y1, 0.0)
            else:
                ay = run.y0
                ret = Zone("service_return", run.x1, ay,
                           run.x1 + arm, ay + SERVICE_DEPTH, 90.0)
                q = Zone("queue", queue.x0, ret.y1 + 0.3, queue.x1,
                         queue.y1, 90.0)
            # The queue steps aside for the arm rather than the checker
            # rejecting the pair. Left alone this was 9 of 20 L proposals
            # failing on "service_return zone stands in the queue" -- which is
            # true, and is also the proposal describing a cafe where the line
            # forms inside the counter. An L's queue runs along the long arm.
            if q.w < 1.2 or q.d < 1.2:
                ret = None              # no room left to queue in: not an L
            else:
                zones[zones.index(queue)] = q
                queue = q
                zones.append(ret)

        # Windows in runs of two, not scattered: a wall with single-tile
        # openings a tile apart is a colonnade, and the piers the wall
        # generator draws between them vanish at 27 px per tile.
        #
        # Chosen AROUND the back bar rather than independently of it. This is
        # the same argument as testing support at proposal time instead of
        # catching a floating vase afterwards -- a constraint the proposal can
        # satisfy for free should not be left to the checker.
        win_x = _windows(w, blocked_x, rnd)
        win_y = _windows(d, blocked_y, rnd)
        if not win_x and not win_y:
            continue

        # The floor the service band leaves, as TWO rectangles: the one below
        # the band, and the strip beside it that still reaches the wall.
        # A peninsula has already worked its own two out -- they are the floor
        # either side of it rather than below and beside.
        #
        # The second one is not a refinement, it is the difference between a
        # rule and a ban. With only the strip below, a horizontal counter puts
        # every seat at y > 3.6, past DAYLIGHT_REACH from the only wall on that
        # side with glass in it -- so the daylight rule rejected 97% of
        # horizontal proposals against 88% of vertical ones, and five plans in
        # six came out with the counter on the same wall. The rule was right
        # and the layout was wrong: a five-tile counter on a fourteen-tile wall
        # leaves nine tiles of window, and that is exactly where a cafe puts
        # its seats.
        if peninsula or island or galley:
            pass
        elif horizontal:
            # The seating floor starts past the deeper of the queue and the
            # arm. Cutting it from the queue alone put 8 of 20 L proposals
            # under a cafe block -- the service band had grown and the
            # rectangle that describes it had not.
            deep = max(queue.y1, ret.y1 if ret else 0.0)
            main = (0.5, deep + 0.4, w - 0.5, d - 0.5)
            side = (back.x1 + 0.6, 0.5, w - 0.5, queue.y1 - 0.1)
            door = (min(w - 0.5, back.x1 + 1.8), d - 0.4)
        else:
            deep = max(queue.x1, ret.x1 if ret else 0.0)
            main = (deep + 0.4, 0.5, w - 0.5, d - 0.5)
            side = (0.5, back.y1 + 0.6, queue.x1 - 0.1, d - 0.5)
            door = (w - 0.4, min(d - 0.5, back.y1 + 1.8))
        sx0, sy0, sx1, sy1 = main
        if sx1 - sx0 < MIN_SEAT_RECT_W or sy1 - sy0 < MIN_SEAT_RECT_D:
            continue

        # A window bar: stools along glass, on a stretch the run left free and
        # inside the seating floor, since a bar behind the counter is staff
        # shelving and not a place anyone sits.
        if win_x and sy0 < 1.6 and rnd() < 0.6:
            t0, t1 = min(win_x), max(win_x) + 1
            zones.append(Zone("window_bar", max(sx0, t0 + 0.1), 0.0,
                              min(sx1, t1 - 0.1), 1.5, 180.0))
            sy0 = max(sy0, 1.9)
        elif win_y and sx0 < 1.6 and rnd() < 0.6:
            t0, t1 = min(win_y), max(win_y) + 1
            zones.append(Zone("window_bar", 0.0, max(sy0, t0 + 0.1), 1.5,
                              min(sy1, t1 - 0.1), 270.0))
            sx0 = max(sx0, 1.9)
        if sx1 - sx0 < MIN_SEAT_RECT_W or sy1 - sy0 < MIN_SEAT_RECT_D:
            continue

        # Split into blocks small enough to clear MAX_SEAT_BLOCK, with an
        # aisle between each pair. The count comes from the area rather than
        # being fixed at two, because a fixed split puts a 12-tile block in a
        # small room and a 60-tile one in a large room, and only one of those
        # is a cafe.
        zones += _seating_blocks(sx0, sy0, sx1, sy1, rnd)
        if side[2] - side[0] > 3.0 and side[3] - side[1] > 2.4:
            zones += _seating_blocks(*side, rnd)

        plan = Plan(w, d, win_x, win_y, door, zones,
                    "galley" if galley else
                    "island" if island else
                    "peninsula" if peninsula else
                    ("L run" if ret is not None else "wall run"))
        bad = check_plan(plan)
        if not bad:
            return plan
        if len(bad) < best_n:
            best, best_n = plan, len(bad)
    return best if best is not None else Plan(14, 10)


def _lit_area(z: Zone, plan: Plan) -> float:
    """How much of a zone a window can actually see, by area.

    Windows are unioned onto a coarse grid rather than summed, because two
    window runs three tiles apart light overlapping floor and adding their
    footprints would report more lit area than the zone has.
    """
    step = 0.25
    nx = max(1, int(round(z.w / step)))
    ny = max(1, int(round(z.d / step)))
    cell = (z.w / nx) * (z.d / ny)
    total = 0.0
    for i in range(nx):
        cx = z.x0 + (i + 0.5) * z.w / nx
        for j in range(ny):
            cy = z.y0 + (j + 0.5) * z.d / ny
            for t in plan.win_x:
                if (t - DAYLIGHT_SPILL <= cx <= t + 1 + DAYLIGHT_SPILL
                        and cy <= DAYLIGHT_REACH):
                    total += cell
                    break
            else:
                for t in plan.win_y:
                    if (t - DAYLIGHT_SPILL <= cy <= t + 1 + DAYLIGHT_SPILL
                            and cx <= DAYLIGHT_REACH):
                        total += cell
                        break
    return total


def _seating_blocks(x0, y0, x1, y1, rnd) -> list:
    """Cut a seating floor into blocks under the cap, aisles between them.

    Two topologies, because one is not a range. `check_plan_range` measured the
    strip-only generator at 43% mean layout distance and said nothing, which is
    correct -- 43% is a real spread. What it cannot say is that the spread is
    all *within* one idea, and a sheet of six plans made that obvious in a way
    no scalar did. This is the same relationship the generator sheet has to
    `check_generator_range`: the number says whether a generator moved, and the
    contact sheet says whether it had anywhere interesting to move to.

    STRIPS run along the shorter axis, so the aisles run the long way. That is
    how a room this shape is usually laid out and it keeps every block touching
    the circulation the flood fill tests.

    PERIMETER hugs the walls and leaves the middle clear, which is what a cafe
    does when the floor is wide rather than long -- and it is a genuinely
    different room, not a reparameterised one: the circulation runs through the
    centre instead of down aisles between blocks.
    """
    if (x1 - x0) > 5.5 and (y1 - y0) > 4.6 and rnd() < 0.42:
        return _perimeter_blocks(x0, y0, x1, y1, rnd)
    out = []
    aisle = 0.9 + rnd() * 0.5
    horizontal = (x1 - x0) >= (y1 - y0)
    long_span = (x1 - x0) if horizontal else (y1 - y0)
    short_span = (y1 - y0) if horizontal else (x1 - x0)
    n = max(2, int((long_span * short_span) / (MAX_SEAT_BLOCK * 0.72)) + 1)
    n = min(n, max(2, int(long_span / 2.6)))
    step = (long_span - aisle * (n - 1)) / n
    if step < 1.8:
        return out
    for i in range(n):
        a = (x0 if horizontal else y0) + i * (step + aisle)
        b = a + step
        # The bite. Kept modest -- a block that loses half its depth stops
        # being able to hold a table and a chair on each side of it.
        keep = 0.62 + rnd() * 0.38
        kind = "lounge" if (i % 2) else "cafe"
        if horizontal:
            out.append(Zone(kind, a, y0, b, y0 + short_span * keep))
        else:
            out.append(Zone(kind, x0, a, x0 + short_span * keep, b))
    return out


def _perimeter_blocks(x0, y0, x1, y1, rnd) -> list:
    """Seating against the edges of the floor, circulation through the middle.

    The bands are deliberately shallow -- 1.5 to 2.1 tiles, a table and a chair
    each side -- because a deep perimeter band is just a strip layout with a
    hole in it, and the hole is the point.
    """
    out = []
    depth = 1.5 + rnd() * 0.6
    if (x1 - x0) - 2 * depth < 2.4 or (y1 - y0) - 2 * depth < 2.4:
        return out
    # Four bands, each cut short of the corners so the blocks do not overlap
    # and so a person can turn each one.
    gap = 0.5 + rnd() * 0.4
    bands = [
        ("cafe", x0, y0, x1, y0 + depth),
        ("lounge", x0, y1 - depth, x1, y1),
        ("cafe", x0, y0 + depth + gap, x0 + depth, y1 - depth - gap),
        ("lounge", x1 - depth, y0 + depth + gap, x1, y1 - depth - gap),
    ]
    for kind, a, b, c, d in bands:
        if c - a < 1.6 or d - b < 1.4:
            continue
        # Long bands get split, for the same reason a long strip does: the cap
        # is about how much undivided seating reads as a canteen, and a band is
        # no different from a block.
        run = c - a if (c - a) >= (d - b) else d - b
        n = max(1, int((c - a) * (d - b) / (MAX_SEAT_BLOCK * 0.7)) + 1)
        n = min(n, max(1, int(run / 2.4)))
        if (c - a) >= (d - b):
            step = (c - a - gap * (n - 1)) / n
            for i in range(n):
                sx = a + i * (step + gap)
                out.append(Zone(kind, sx, b, sx + step, d))
        else:
            step = (d - b - gap * (n - 1)) / n
            for i in range(n):
                sy = b + i * (step + gap)
                out.append(Zone(kind, a, sy, c, sy + step))
    return out


def _windows(span: int, blocked, rnd) -> tuple:
    """One or two runs of two window tiles, clear of `blocked`.

    Runs of two, not single tiles: a wall with openings a tile apart is a
    colonnade, and the piers the wall generator draws between them are gone at
    27 px per tile. Returns () when the wall has no room, which is legal -- a
    cafe with glass on one wall is a cafe, and `check_plan` is what insists the
    seating gets some of it.
    """
    free = [t for t in range(1, span - 2)
            if blocked is None or t + 2 <= blocked[0] or t >= blocked[1]]
    if not free:
        return ()
    out = set()
    for _ in range(1 if rnd() < 0.35 else 2):
        opts = [t for t in free if not (out & {t - 1, t, t + 1, t + 2})]
        if not opts:
            break
        t = opts[int(rnd() * len(opts)) % len(opts)]
        out |= {t, t + 1}
    return tuple(sorted(out))


# --- is the generator's range any good? --------------------------------------

# Mean pairwise layout distance over sixteen consecutive seeds. Measured at 49%
# before the floor was chosen, the same way every other range floor in this
# repository was set, and sat under rather than at.
#
# The MEAN here, where `check_roster_variety` insists on the minimum. That is a
# real difference and not an inconsistency: a cast of extras stands in one room
# together, so the two that collide are the two a player sees, and an average
# over the pairs that are already fine says nothing about them. Two floor plans
# are never in frame together -- each is a different shop -- so what matters is
# whether the generator covers ground, not whether some pair happens to be
# close. The closest pair over forty seeds is 6% and that is not a defect.
MIN_PLAN_SPREAD = 0.30

# Floor an island must keep clear of every wall, so a body can pass behind it.
ISLAND_CLEAR = 1.7

# The smallest seating rectangle the generator will cut blocks from. Named
# because three places used to spell it 4.0 and 3.5 inline, and the island has
# to solve for it rather than be rejected by it.
MIN_SEAT_RECT_W, MIN_SEAT_RECT_D = 4.0, 3.5


def plan_labels(plan: Plan, nx: int = 24, ny: int = 18) -> list:
    """Zone kind per cell on a grid normalised to the plan's own extent.

    Normalised, so this compares LAYOUT and not dimensions. Two rooms of
    different sizes with the counter on the same wall and the seating in the
    same relation to it are the same plan drawn at two scales, and a metric
    that scored them as different would be measuring `w` and `d`.
    """
    out = []
    for j in range(ny):
        cy = (j + 0.5) * plan.d / ny
        for i in range(nx):
            cx = (i + 0.5) * plan.w / nx
            kind = ""
            for z in plan.zones:
                if z.kind == "queue":
                    continue          # empty floor, not a thing in the room
                if z.x0 <= cx <= z.x1 and z.y0 <= cy <= z.y1:
                    kind = z.kind
                    break
            out.append(kind)
    return out


def plan_distance(a: Plan, b: Plan) -> float:
    """Share of cells where two normalised plans disagree."""
    la, lb = plan_labels(a), plan_labels(b)
    return sum(1 for x, y in zip(la, lb) if x != y) / len(la)


def check_plan_range(n: int = 16, seed: int = 1,
                     floor: float = MIN_PLAN_SPREAD) -> list[str]:
    """Do consecutive seeds actually produce different rooms?

    The floor plan version of `check_generator_range`, and it exists for the
    same reason: a generator can rot without breaking anything. A branch left
    out of the proposal, a rule tightened until only one topology survives, a
    random stream weak enough to favour one wall -- every one of those still
    returns a plan that passes every rule in `check_plan`, and the sheet is the
    only place it shows.

    That is not hypothetical here. A daylight floor set at 45% -- above what
    the reference room itself scores -- cut horizontal counter runs from 11%
    accepted to 5% and flipped the whole cast of plans onto one wall, while
    every individual plan stayed clean.
    """
    plans = [generate(seed + i) for i in range(n)]
    pairs = [plan_distance(plans[i], plans[j])
             for i in range(n) for j in range(i + 1, n)]
    if not pairs:
        return []
    mean = sum(pairs) / len(pairs)
    if mean < floor:
        return [f"floor plans are {mean:.0%} apart on average "
                f"(floor {floor:.0%}) -- the generator has one idea"]
    return []


def describe(plan: Plan) -> str:
    parts = [f"{plan.w}x{plan.d}, windows x{list(plan.win_x)} y{list(plan.win_y)}"]
    for z in plan.zones:
        parts.append(f"  {z.kind:11s} ({z.x0:5.2f},{z.y0:5.2f})-"
                     f"({z.x1:5.2f},{z.y1:5.2f})  {z.area:5.1f} tiles"
                     f"  facing {z.facing:.0f}")
    return "\n".join(parts)


def check_generated_plans(n: int = 24, seed: int = 1) -> list[str]:
    """Every plan the generator returns must pass the rules it solved against.

    Not a tautology: `generate` gives up after `tries` and returns its
    least-bad attempt rather than looping, the same bargain `scatter` makes
    when a region runs out of room. This is the check that says how often that
    happens, and a failure here means the proposal space and the rules have
    drifted apart -- which is exactly what happens when a rule is tightened.
    """
    out = []
    for i in range(n):
        bad = check_plan(generate(seed + i))
        if bad:
            out.append(f"plan seed {seed + i}: " + "; ".join(bad))
    return out


if __name__ == "__main__":
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    for k in range(1, n + 1):
        p = generate(k)
        bad = check_plan(p)
        print(f"--- seed {k} " + ("OK" if not bad else "FAILED: " + "; ".join(bad)))
        print(describe(p))
