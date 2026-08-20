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

TUCK_OK = {
    frozenset({"chair", "table"}), frozenset({"chair", "counter"}),
    frozenset({"stool", "counter"}), frozenset({"stool", "bar"}),
    frozenset({"clutter", "table"}), frozenset({"prop", "counter"}),
    frozenset({"char", "chair"}), frozenset({"char", "table"}),
    frozenset({"char", "counter"}), frozenset({"clutter", "counter"}),
    frozenset({"prop", "wall"}), frozenset({"decor", "wall"}),
    frozenset({"chair", "clutter"}), frozenset({"char", "clutter"}),
}


@dataclass
class Layout:
    items: list[Placed] = field(default_factory=list)
    rots: dict = field(default_factory=dict)

    def add(self, mesh: Mesh, at=(0.0, 0.0, 0.0), rot: float = 0.0,
            name: str = "prop", track: bool = True, centre: bool = False) -> None:
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
        if not m.verts:
            return
        xs = [v[0] for v in m.verts]
        ys = [v[1] for v in m.verts]
        zs = [v[2] for v in m.verts]
        self.rots[name] = rot
        self.items.append(Placed(name, m, min(xs), min(ys), max(xs), max(ys),
                                 min(zs), max(zs)) if track else
                          Placed("_untracked", m, 0, 0, 0, 0, 0, 0))

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

    def grounded(self, tol: float = 0.03) -> list[str]:
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
                # Objects at different heights cannot collide (a cup on a counter).
                if a.z1 <= b.z0 + 1e-6 or b.z1 <= a.z0 + 1e-6:
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
