"""Placement with automatic footprint derivation and overlap detection.

Objects intersecting each other was caught by eye on a contact sheet. Per the
ratchet in PIPELINE.md that makes it a candidate for automation, and it is a
cheap one: footprints come free from the mesh XY bounds, so collision is a
rectangle test.

The nuance worth encoding is that not all overlap is a defect. A chair tucked
under a table is correct and desirable; two chairs in the same square is not. So
the check is *proportional* -- it fires when overlap exceeds a share of the
smaller object's footprint -- and specific pairs can be whitelisted as
deliberately interpenetrating.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from assetlib import merge, transformed
from mesh import Mesh


@dataclass
class Placed:
    name: str
    mesh: Mesh
    x0: float
    y0: float
    x1: float
    y1: float
    z0: float
    z1: float

    @property
    def area(self) -> float:
        return max(0.0, self.x1 - self.x0) * max(0.0, self.y1 - self.y0)


# Pairs allowed to interpenetrate: seating tucks under tables, props sit on
# counters, clutter sits on tables.
# Kinds that hang on a wall and legitimately have nothing beneath them.
WALL_MOUNTED = {"menu", "sign", "shelf", "decor#menu", "picture"}

# How much two stacked objects may share in z before it counts as overlap.
Z_TOUCH = 0.05

TUCK_OK = {
    frozenset({"chair", "table"}), frozenset({"chair", "counter"}),
    frozenset({"stool", "counter"}), frozenset({"stool", "bar"}),
    frozenset({"clutter", "table"}), frozenset({"prop", "counter"}),
    frozenset({"char", "chair"}), frozenset({"char", "table"}),
    frozenset({"char", "counter"}), frozenset({"clutter", "counter"}),
    frozenset({"prop", "wall"}), frozenset({"decor", "wall"}),
    frozenset({"chair", "clutter"}), frozenset({"char", "clutter"}),
    # An armchair is named `seat#arm...` and a bench `seat#bench...`, and a
    # character sitting in one interpenetrates it exactly as a character on a
    # `chair` does. The reference room never needed this because it seats
    # everyone on dining chairs.
    frozenset({"char", "seat"}),
}


# How far an object's underside may sit off the surface below it. One constant,
# used by `grounded` and by the support test inside `_conflicts`, because they
# were 0.03 and 0.06: the solver accepted a placement its own validator then
# rejected. `build_plan` hit it the first time it ran -- two vases scattered
# onto tables, accepted at proposal time and reported as floating afterwards. A
# solver whose predicate is looser than the check it exists to satisfy is not a
# solver, it is a source of warnings.
SUPPORT_TOL = 0.03


@dataclass
class Layout:
    items: list[Placed] = field(default_factory=list)
    rots: dict = field(default_factory=dict)
    # Applied to every placement that does not override it. Set after the floor
    # and walls go in, so the room's shell stays true and only its contents
    # acquire the wear.
    warp_default: float = 0.0

    def add(self, mesh: Mesh, at=(0.0, 0.0, 0.0), rot: float = 0.0,
            name: str = "prop", track: bool = True, centre: bool = False,
            warp: float | None = None) -> None:
        """Place a mesh. `centre=True` rotates about the mesh's own XY centre.

        Worth having because `transformed` rotates about the local origin, so a
        prop placed at 200 degrees lands nowhere near the coordinates that were
        written for it -- an armchair intended for (3.0, 7.5) actually occupied
        x 2.19-3.21, y 6.35-7.37 and collided with a stool a metre away. With
        the pivot at the centre, `at` means what it reads as, which is the only
        way hand-written placements stay maintainable.
        """
        if centre:
            xs = [v[0] for v in mesh.verts]
            ys = [v[1] for v in mesh.verts]
            if xs:
                cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
                mesh = transformed(mesh, at=(-cx, -cy, 0.0))
        m = transformed(mesh, rot_z=rot, at=at)
        warp = self.warp_default if warp is None else warp
        if warp > 0.0:
            # After placement, so the displacement field is sampled in room
            # coordinates and two copies of the same prop in different places
            # warp differently. Warping before placement would give every chair
            # the identical dent.
            from assetlib import warp as _warp
            m = _warp(m, amount=warp)
        if not m.verts:
            return
        xs = [v[0] for v in m.verts]
        ys = [v[1] for v in m.verts]
        zs = [v[2] for v in m.verts]
        self.rots[name] = rot
        self.items.append(Placed(name, m, min(xs), min(ys), max(xs), max(ys),
                                 min(zs), max(zs)) if track else
                          Placed("_untracked", m, 0, 0, 0, 0, 0, 0))

    def add_seeded(self, factory, seeds, at=(0.0, 0.0, 0.0), rot: float = 0.0,
                   name: str = "prop", azimuth: float = 45.0,
                   occlude: float = 0.35, **kw) -> int:
        """Place the first seed whose result breaks no rule already enforced.

        `scatter` solves for a *position* with the seed fixed; this solves for a
        seed with the position fixed, which is the case a fitted prop actually
        has -- an espresso machine goes where the counter is, and what is free
        to move is which machine it is.

        Written after the third time a hand-picked constant had to dodge a
        check. Seeding the pastry case made it taller, the taller case covered
        39% of a crate two tiles behind it, and the fix was to read a table of
        eight measurements and type the seed that passed. That is a person
        doing a search, and a search is the thing this file is for. Note that
        the two props involved were BOTH hand-placed: `scatter` has tested
        occlusion at proposal time for two passes, and neither of these went
        through it.

        Falls back to the first seed if none pass, for the reason `scatter`
        returns short rather than raising -- a room with one warning is worth
        more than no room.
        """
        seeds = list(seeds)
        for k in seeds:
            before = len(self.items)
            self.add(factory(k), at=at, rot=rot, name=name, **kw)
            if len(self.items) == before:
                return k                       # empty mesh, nothing placed
            cand = self.items[-1]
            self.items.pop()
            if not self._conflicts(cand, azimuth, occlude):
                self.items.append(cand)
                return k
            self.rots.pop(name, None)
        self.add(factory(seeds[0]), at=at, rot=rot, name=name, **kw)
        return seeds[0]

    def mesh(self) -> Mesh:
        return merge(*(p.mesh for p in self.items))

    def seating_faces_tables(self, back_local=(0.0, -1.0),
                             max_reach: float = 2.2) -> list[str]:
        """A chair's back must point AWAY from the table it serves.

        Promoted from review. Seat rotations are written by hand and two of the
        four around each round table were 180 degrees out, so those chairs had
        their backs to the table -- individually valid geometry, wrong only in
        relation to a neighbour, which is precisely the class of error a
        per-sprite check can never see.
        """
        import math
        tables = [p for p in self.items if p.name.split("#")[0] in ("table", "counter")]
        out = []
        for p in self.items:
            if p.name.split("#")[0] != "chair":
                continue     # stools are radially symmetric: no back to point
            cx, cy = (p.x0 + p.x1) / 2, (p.y0 + p.y1) / 2
            near, best = None, max_reach
            for t in tables:
                tx, ty = (t.x0 + t.x1) / 2, (t.y0 + t.y1) / 2
                d = math.hypot(tx - cx, ty - cy)
                if d < best:
                    near, best = (tx, ty), d
            if near is None:
                continue
            r = math.radians(self.rots.get(p.name, 0.0))
            bx = back_local[0] * math.cos(r) - back_local[1] * math.sin(r)
            by = back_local[0] * math.sin(r) + back_local[1] * math.cos(r)
            tvx, tvy = near[0] - cx, near[1] - cy
            n = math.hypot(tvx, tvy) or 1e-9
            if (bx * tvx + by * tvy) / n > 0.25:
                out.append(f"{p.name}: back points toward the table it serves")
        return out

    def grounded(self, tol: float = SUPPORT_TOL) -> list[str]:
        """Every object must rest on the floor or on something beneath it.

        Floating and sunk props have been the most repeated defect in this
        project -- seated characters standing on chairs, characters buried in
        the floor, shelves hovering above a wall, a lamp pool with nothing under
        it. Each was caught by eye, one at a time, after a full render. It is a
        pure geometry question: an object is well founded if its underside meets
        either the floor or the top of something whose footprint it overlaps.
        """
        out = []
        for p in self.items:
            if p.name == "_untracked":
                continue
            kind = p.name.split("#")[0]
            tag = p.name.split("#")[-1]
            if kind in WALL_MOUNTED or any(w in tag for w in WALL_MOUNTED):
                continue                              # hangs on a wall
            if abs(p.z0) <= tol:
                continue                              # on the floor
            best = None
            for q in self.items:
                if q is p or q.name == "_untracked":
                    continue
                ox = min(p.x1, q.x1) - max(p.x0, q.x0)
                oy = min(p.y1, q.y1) - max(p.y0, q.y0)
                if ox <= 0 or oy <= 0 or q.z1 > p.z0 + tol:
                    continue
                if best is None or q.z1 > best:
                    best = q.z1
            if best is None:
                out.append(f"{p.name}: underside at z={p.z0:.2f} with nothing "
                           f"beneath it - floats")
            elif p.z0 - best > tol:
                out.append(f"{p.name}: underside at z={p.z0:.2f} sits "
                           f"{p.z0 - best:.2f} above the surface below "
                           f"(z={best:.2f}) - floats")
        return out

    def collisions(self, share: float = 0.34) -> list[str]:
        """Overlaps exceeding `share` of the smaller footprint, at shared height."""
        out = []
        for i, a in enumerate(self.items):
            if a.name == "_untracked":
                continue
            for b in self.items[i + 1:]:
                if b.name == "_untracked":
                    continue
                kind_a, kind_b = a.name.split("#")[0], b.name.split("#")[0]
                if frozenset({kind_a, kind_b}) in TUCK_OK:
                    continue
                # Objects at different heights cannot collide (a cup on a
                # counter). The tolerance is not cosmetic: stacked props touch at
                # exactly one z, and an exact test fails the moment anything
                # perturbs a vertex. `warp` did exactly that -- a crate stack
                # that had been correct for four passes started reporting a 100%
                # collision because the lower crate's lid rose 0.015 into the
                # upper crate's floor. Real interpenetration is measured in
                # tenths of a tile, so a 5 cm skin costs nothing.
                if a.z1 <= b.z0 + Z_TOUCH or b.z1 <= a.z0 + Z_TOUCH:
                    continue
                ox = min(a.x1, b.x1) - max(a.x0, b.x0)
                oy = min(a.y1, b.y1) - max(a.y0, b.y0)
                if ox <= 0 or oy <= 0:
                    continue
                overlap = ox * oy
                smaller = min(a.area, b.area) or 1e-9
                frac = overlap / smaller
                if frac > share:
                    out.append(f"{a.name} <-> {b.name}: "
                               f"{frac:.0%} of the smaller footprint "
                               f"({ox:.2f} x {oy:.2f} tiles)")
        return out

    def screen_occlusion(self, azimuth: float = 45.0, share: float = 0.35,
                         depth: float = 0.8) -> list[str]:
        """Props that hide each other on screen despite not touching in world space.

        World-space collision is necessary and not sufficient. In a dimetric view
        two objects several tiles apart project to the same pixels, and the near
        one erases the far one: the composite shows a silhouette nobody modelled,
        which is what "that corner is mush" means when a human says it. Nothing in
        `collisions()` can see this, because in plan view those objects are nowhere
        near each other.

        Fires when a pair's screen boxes overlap by more than `share` of the
        smaller AND they are at least `depth` apart along the view axis -- the
        depth gate is what separates a genuine occlusion from a chair legibly
        tucked at a table, which overlaps on screen precisely because it is meant
        to. Depth is in camera units, not tiles: `cam.dir` is normalised and
        tilted, so 1.5 tiles of ground separation is only 0.92 of depth.

        Both thresholds are calibrated against measured cases rather than
        guessed:

            two customers queued along the view axis   56%   1.0 apart  BAD
            a coat rack standing in front of a chair   33%   2.4 apart  BAD
            the same queue at corrected spacing         9%   1.3 apart  ok
            a chair tucked at its own table            16%   0.6 apart  ok
            two chairs across a round table            30%   1.4 apart  ok

        `share` sits at 0.35, above the 30% that four correctly-placed chairs
        around one table produce and below the 43% and 65% cases in the live
        room. That leaves the 33% coat-rack case just under the line: bounding
        boxes cannot separate it from a correct four-top, so it is honestly out
        of reach here and was caught by eye instead. Do not tighten the
        threshold to capture it without new measurements -- it would fire on
        every round table in the room.

        This is a screen bounding-box test, and its limits are worth stating: a
        menu board hidden behind an espresso machine measures 11% here, no
        different from a correct tuck, because the two boxes overlap in a narrow
        vertical band. Boxes cannot see that. It catches gross occlusion, not
        every occlusion.
        """
        # Use the camera that ships. The first version re-derived the screen
        # basis by hand from sin/cos of the azimuth and got three things wrong:
        # u came out sign-flipped, v was off by up to a third of a tile on tall
        # objects, and depth ignored z entirely -- so the depth gate, the whole
        # point of the check, was measuring the wrong axis. A check that
        # disagrees with the renderer is not a check.
        from isorender import DimetricCamera, dot
        cam = DimetricCamera(azimuth)

        def box(p):
            us, vs, ds = [], [], []
            for x in (p.x0, p.x1):
                for y in (p.y0, p.y1):
                    for z in (p.z0, p.z1):
                        w = (x, y, z)
                        us.append(dot(w, cam.right))
                        vs.append(dot(w, cam.up))
                        ds.append(dot(w, cam.dir))
            return (min(us), max(us), min(vs), max(vs), sum(ds) / len(ds))

        boxes = {p.name: box(p) for p in self.items if p.name != "_untracked"}
        items = [p for p in self.items if p.name != "_untracked"]
        out = []
        for i, a in enumerate(items):
            au0, au1, av0, av1, ad = boxes[a.name]
            for b in items[i + 1:]:
                kind_a, kind_b = a.name.split("#")[0], b.name.split("#")[0]
                if frozenset({kind_a, kind_b}) in TUCK_OK:
                    continue
                # Members of one furniture group. Four chairs around a round
                # table are placed as a unit at fixed offsets, so how much they
                # overlap on screen is a property of the group's geometry, not
                # of anyone's placement -- give one of them a tall back and the
                # near chair covers 45% of the far one, which is what a tall
                # chair does. Two chairs from *different* tables landing on each
                # other is still a defect and still fires.
                if (a.name.rsplit("_", 1)[0] == b.name.rsplit("_", 1)[0]
                        and "_" in a.name and "_" in b.name):
                    continue
                bu0, bu1, bv0, bv1, bd = boxes[b.name]
                if abs(ad - bd) < depth:
                    continue
                ou = min(au1, bu1) - max(au0, bu0)
                ov = min(av1, bv1) - max(av0, bv0)
                if ou <= 0 or ov <= 0:
                    continue
                # Share of the FAR object that is lost, not of the smaller box.
                # Those differ exactly when the occluder is the smaller of the
                # two -- a thin coat rack in front of a wide chair -- which is
                # the case this check exists for, and the message said "hides
                # 33% of the chair" while reporting 33% of the coat rack.
                near, far = (a, b) if ad > bd else (b, a)
                fu0, fu1, fv0, fv1, _ = boxes[far.name]
                far_area = (fu1 - fu0) * (fv1 - fv0) or 1e-9
                frac = (ou * ov) / far_area
                if frac > share:
                    out.append(f"{near.name} hides {frac:.0%} of {far.name} "
                               f"({abs(ad - bd):.1f} apart in depth)")
        return out

    # --- generation ----------------------------------------------------------

    def _conflicts(self, cand: Placed, azimuth: float, occlude: float) -> bool:
        """Would placing `cand` break any rule already being enforced?"""
        kind_c = cand.name.split("#")[0]
        for a in self.items:
            if a.name == "_untracked":
                continue
            kind_a = a.name.split("#")[0]
            if frozenset({kind_a, kind_c}) in TUCK_OK:
                continue
            if a.z1 <= cand.z0 + Z_TOUCH or cand.z1 <= a.z0 + Z_TOUCH:
                continue
            ox = min(a.x1, cand.x1) - max(a.x0, cand.x0)
            oy = min(a.y1, cand.y1) - max(a.y0, cand.y0)
            if ox > 0 and oy > 0:
                if (ox * oy) / (min(a.area, cand.area) or 1e-9) > 0.10:
                    return True
        # Support. A proposal lifted onto a surface -- a cup at counter height,
        # a vase on the bar -- has to actually land on one. The first generated
        # pass put a vase 0.82 up in clear air just past the end of the bar run,
        # and `grounded` caught it after the fact; a solver that can check a rule
        # afterwards can check it before, and then the rule never has to fire.
        if cand.z0 > 0.03:
            for a in self.items:
                if abs(a.z1 - cand.z0) > SUPPORT_TOL:
                    continue
                if (min(a.x1, cand.x1) - max(a.x0, cand.x0) > 0.04
                        and min(a.y1, cand.y1) - max(a.y0, cand.y0) > 0.04):
                    break
            else:
                return True
        if occlude > 0.0:
            self.items.append(cand)
            try:
                for msg in self.screen_occlusion(azimuth, share=occlude):
                    if cand.name in msg:
                        return True
            finally:
                self.items.pop()
        return False

    def scatter(self, factory, region, count: int, name: str,
                z: float = 0.0, rot_choices=(0, 90, 180, 270), seed: int = 1,
                azimuth: float = 45.0, occlude: float = 0.35,
                tries_per: int = 40) -> int:
        """Place up to `count` props inside `region`, rejecting bad placements.

        This is the point of having written the checks. For four passes
        `collisions`, `grounded` and `screen_occlusion` were *validators* -- they
        graded 85 coordinates typed by hand and said which were wrong. The same
        predicates, run before a placement instead of after, are a constraint
        solver: propose, test, keep or discard. Density stops being authoring
        work and becomes a number.

        That matters because a room reads as under-dressed long before it reads
        as under-lit, and hand-placing the two hundred small objects a lived-in
        interior needs is not work anyone will do twice. It is also the honest
        answer to a library of 135 hand-written primitive calls: the fix is not
        to write more of them, it is to generate the placements.

        `factory` is called as `factory(i)` with the instance index, so
        generators can differ per copy.

        `region` is (x0, y0, x1, y1). Sampling is a fixed LCG, so a room built
        twice is identical -- the same requirement the floor's butt joints have,
        for the same reason.

        Returns the number actually placed, which is usually fewer than `count`.
        A saturated region rejecting proposals is the check working, not failing.
        """
        x0, y0, x1, y1 = region
        state = seed * 2654435761 + 12345

        def rnd():
            nonlocal state
            state = (state * 1103515245 + 12345) & 0x7FFFFFFF
            return (state >> 7) / (0x7FFFFFFF >> 7)

        placed = 0
        for i in range(count):
            for _ in range(tries_per):
                px = x0 + (x1 - x0) * rnd()
                py = y0 + (y1 - y0) * rnd()
                rot = rot_choices[int(rnd() * len(rot_choices)) % len(rot_choices)]
                # The factory is handed the instance index, so a generator can
                # vary each copy. Ten scattered plants calling a zero-argument
                # factory would be ten identical plants, which defeats the point
                # of having made the plant procedural at all.
                mesh = factory(i)
                xs = [v[0] for v in mesh.verts]
                ys = [v[1] for v in mesh.verts]
                cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
                m = transformed(transformed(mesh, at=(-cx, -cy, 0.0)),
                                rot_z=rot, at=(px, py, z))
                if self.warp_default > 0.0:
                    from assetlib import warp as _warp
                    m = _warp(m, amount=self.warp_default)
                vx = [v[0] for v in m.verts]
                vy = [v[1] for v in m.verts]
                vz = [v[2] for v in m.verts]
                cand = Placed(f"{name}#{i}", m, min(vx), min(vy), max(vx),
                              max(vy), min(vz), max(vz))
                if self._conflicts(cand, azimuth, occlude):
                    continue
                self.items.append(cand)
                self.rots[cand.name] = rot
                placed += 1
                break
        return placed

    def wear_field(self, seat_r: float = 0.62, seat_amt: float = 0.55,
                   counter_r: float = 1.15, counter_amt: float = 0.85,
                   spine_amt: float = 0.45):
        """Traffic patches derived from what is already placed.

        Nobody types these. A chair means someone stands in front of it to sit
        down; a counter means a queue; and the route between the door corner and
        the till is the busiest line in any cafe. All three are readable off the
        placements, which is the whole argument for tracking placements in the
        first place.

        Wear goes in FRONT of a seat, not under it -- the boards under a chair
        are the least-walked in the room, which is why an evenly-worn floor reads
        as dirty rather than as used. `rots` already records which way each seat
        faces, so "in front" is known exactly.

        Returns a `mesh.WearField`.
        """
        import math

        from mesh import WearField
        pools = []
        for p in self.items:
            kind = p.name.split("#")[0]
            cx, cy = (p.x0 + p.x1) / 2, (p.y0 + p.y1) / 2
            if kind in ("chair", "stool", "seat"):
                # A chair's back is at -y in local space, so a seat at rot=0 is
                # approached from +y. Step one radius that way.
                rot = math.radians(self.rots.get(p.name, 0.0))
                # Local +y, rotated into world.
                pools.append((cx - math.sin(rot) * 0.55,
                              cy + math.cos(rot) * 0.55, seat_r, seat_amt))
            elif kind in ("counter", "bar"):
                # The customer side, which for the service run is +y.
                pools.append((cx, cy + 0.95, counter_r, counter_amt))
        # The routes. Wherever there is a counter and a seat, there is a line
        # people walk between them, and that line is the busiest floor in the
        # room -- so lay a run of pools along each one. Spurs to nearby seats
        # share their first half, which makes the trunk in front of the counter
        # come out strongest without anyone deciding it should be; that is what
        # a worn floor looks like, and it falls out of the geometry.
        #
        # An earlier version picked a single "walkway" as the emptiest lane
        # across the room. The scores came out 4.6 against 6.9 over 23
        # candidates -- an argmin over what is essentially noise, which would
        # have moved the walkway to a different place on any change to the
        # dressing. Two real endpoints beat one shallow minimum.
        tills = [q for q in pools if q[3] >= counter_amt]
        seats = [q for q in pools if q[3] == seat_amt]
        # Origins are the service run thinned onto a coarse grid. Neither
        # extreme worked: the tills' centroid put the fan's apex a couple of
        # tiles clear of the counter and left a bare stripe across the one
        # stretch of floor that certainly is walked on, while one origin per
        # placement gave nine, because a six-module counter is six placements
        # and one counter -- 207 routes, and the room came out uniformly worn,
        # which is the failure this whole field exists to fix.
        origins: dict = {}
        for q in tills:
            origins.setdefault((round(q[0] / 1.8), round(q[1] / 1.8)), q)
        for tx, ty, _, _ in origins.values():
            for sx, sy, _, _ in seats:
                steps = max(2, int(math.hypot(sx - tx, sy - ty) / 0.55))
                for i in range(1, steps):
                    t = i / steps
                    # Fades toward the seat: the last stretch of any route is
                    # walked by one party, the first by everybody.
                    pools.append((tx + (sx - tx) * t, ty + (sy - ty) * t,
                                  0.72, spine_amt * (1.0 - 0.45 * t)))
        # Merge onto a grid. `at` is O(pools) per pixel, and the spurs overlap
        # heavily by construction, so without this the trunk would be re-tested
        # twenty times for every pixel it covers.
        merged: dict = {}
        for cx, cy, r, amt in pools:
            k = (round(cx / 0.45), round(cy / 0.45), round(r, 2))
            cur = merged.get(k)
            if cur is None:
                merged[k] = [cx, cy, r, amt, 1]
            else:
                cur[3], cur[4] = max(cur[3], amt), cur[4] + 1
        # Traffic count, not just presence. `at` takes the max over pools, so
        # without this a stretch of floor crossed by nine routes would wear
        # exactly as much as one crossed by a single route -- which is how the
        # first version came out uniformly faint across half the room. The
        # trunk is now darker than the fringe for the reason it should be:
        # more people walk down it.
        return WearField([(cx, cy, r, min(0.92, amt * (1.0 + 0.11 * (n - 1))))
                          for cx, cy, r, amt, n in merged.values()])
