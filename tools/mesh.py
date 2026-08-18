"""Mesh loading and orthographic rasterization.

This is the seam the generation stages plug into. Stages 1-4 (concept -> mesh ->
rig -> motion) all terminate in geometry, and until something here could consume
a triangle the factory had nowhere to put their output.

Rasterization rather than raytracing: under an orthographic camera, projection is
affine, so a scanline z-buffer is both exact and roughly two orders of magnitude
faster than tracing rays against the same triangles. It is also what Blender will
do at this stage, so the stand-in and the production path agree by construction.

Emits the same (material, lambert, normal) buffers `isorender.render` does, so
everything downstream is unchanged.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

from isorender import DimetricCamera, add, camera_light, cross, dot, mul, norm, sub

Vec = tuple[float, float, float]


@dataclass
class Mesh:
    verts: list[Vec] = field(default_factory=list)
    normals: list[Vec] = field(default_factory=list)
    # (vertex indices, normal indices or None, material)
    faces: list[tuple[tuple[int, int, int], tuple[int, int, int] | None, str]] = \
        field(default_factory=list)

    def bounds(self) -> tuple[Vec, Vec]:
        xs = [v[0] for v in self.verts]
        ys = [v[1] for v in self.verts]
        zs = [v[2] for v in self.verts]
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))

    # --- construction helpers -------------------------------------------------

    def add_quad(self, a: Vec, b: Vec, c: Vec, d: Vec, material: str) -> None:
        i = len(self.verts)
        self.verts += [a, b, c, d]
        self.faces.append(((i, i + 1, i + 2), None, material))
        self.faces.append(((i, i + 2, i + 3), None, material))

    def add_box(self, lo: Vec, hi: Vec, material: str) -> None:
        (x0, y0, z0), (x1, y1, z1) = lo, hi
        p = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        for quad in ((4, 5, 6, 7), (1, 0, 3, 2), (0, 1, 5, 4),
                     (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            self.add_quad(*(p[i] for i in quad), material=material)

    def add_cylinder(self, centre: Vec, radius: float, height: float,
                     material: str, segments: int = 24) -> None:
        cx, cy, cz = centre
        top, bot = cz + height, cz
        ring = [(cx + radius * math.cos(2 * math.pi * i / segments),
                 cy + radius * math.sin(2 * math.pi * i / segments))
                for i in range(segments)]
        for i in range(segments):
            x0, y0 = ring[i]
            x1, y1 = ring[(i + 1) % segments]
            self.add_quad((x0, y0, bot), (x1, y1, bot),
                          (x1, y1, top), (x0, y0, top), material)
            # caps as a triangle fan
            ci = len(self.verts)
            self.verts += [(cx, cy, top), (x0, y0, top), (x1, y1, top)]
            self.faces.append(((ci, ci + 1, ci + 2), None, material))
            ci = len(self.verts)
            self.verts += [(cx, cy, bot), (x1, y1, bot), (x0, y0, bot)]
            self.faces.append(((ci, ci + 1, ci + 2), None, material))

    def add_sphere(self, centre: Vec, radius: float, material: str,
                   segments: int = 16, rings: int = 12) -> None:
        cx, cy, cz = centre
        def pt(i, j):
            theta = math.pi * j / rings
            phi = 2 * math.pi * i / segments
            return (cx + radius * math.sin(theta) * math.cos(phi),
                    cy + radius * math.sin(theta) * math.sin(phi),
                    cz + radius * math.cos(theta))
        for j in range(rings):
            for i in range(segments):
                self.add_quad(pt(i, j), pt(i + 1, j), pt(i + 1, j + 1), pt(i, j + 1),
                              material)


# --- OBJ ---------------------------------------------------------------------

def load_obj(path: Path | str, default_material: str = "wood") -> Mesh:
    """Minimal OBJ reader: v, vn, f, usemtl. Triangulates n-gons as a fan."""
    m = Mesh()
    material = default_material
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if not parts or parts[0].startswith("#"):
            continue
        tag = parts[0]
        if tag == "v":
            m.verts.append(tuple(float(x) for x in parts[1:4]))
        elif tag == "vn":
            m.normals.append(norm(tuple(float(x) for x in parts[1:4])))
        elif tag in ("usemtl", "o", "g") and len(parts) > 1:
            if tag == "usemtl":
                material = parts[1]
        elif tag == "f":
            vi, ni = [], []
            for tok in parts[1:]:
                bits = tok.split("/")
                vi.append(int(bits[0]) - 1 if int(bits[0]) > 0 else len(m.verts) + int(bits[0]))
                if len(bits) > 2 and bits[2]:
                    ni.append(int(bits[2]) - 1)
            for k in range(1, len(vi) - 1):
                tri = (vi[0], vi[k], vi[k + 1])
                nrm = (ni[0], ni[k], ni[k + 1]) if len(ni) == len(vi) else None
                m.faces.append((tri, nrm, material))
    return m


def save_obj(mesh: Mesh, path: Path | str) -> None:
    lines = ["# generated by cozy-coffee-iso"]
    lines += [f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}" for v in mesh.verts]
    current = None
    for tri, _, material in mesh.faces:
        if material != current:
            lines.append(f"usemtl {material}")
            current = material
        lines.append(f"f {tri[0]+1} {tri[1]+1} {tri[2]+1}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


# --- rasterizer --------------------------------------------------------------

class ShadowMap:
    """Orthographic depth buffer rendered from the key light.

    Cast shadows are not decoration here. Every isometric reference names them as
    the primary device that grounds an object to the floor, and without them
    props read as floating. They also fix a measured defect: with only
    axis-aligned faces the lambert term is bimodal, so a 7-step ramp collapses to
    about 3 used steps. Shadow gives the mid and dark steps something to describe.
    """

    def __init__(self, mesh: Mesh, light: Vec, res: int = 512):
        self.dir = light
        up = (0.0, 0.0, 1.0) if abs(light[2]) < 0.99 else (0.0, 1.0, 0.0)
        self.right = norm(cross(up, light))
        self.up = norm(cross(light, self.right))
        us = [dot(v, self.right) for v in mesh.verts]
        vs = [dot(v, self.up) for v in mesh.verts]
        self.u0, self.v0 = min(us), min(vs)
        pad = 1e-3
        self.su = (max(us) - self.u0) + pad
        self.sv = (max(vs) - self.v0) + pad
        self.res = res
        self.depth = [-1e30] * (res * res)

        for tri, _, _ in mesh.faces:
            a, b, c = (mesh.verts[i] for i in tri)
            pa, pb, pc = (self._project(p) for p in (a, b, c))
            area = ((pb[0] - pa[0]) * (pc[1] - pa[1]) -
                    (pb[1] - pa[1]) * (pc[0] - pa[0]))
            if abs(area) < 1e-12:
                continue
            x0 = max(0, int(min(pa[0], pb[0], pc[0])))
            x1 = min(res - 1, int(max(pa[0], pb[0], pc[0])) + 1)
            y0 = max(0, int(min(pa[1], pb[1], pc[1])))
            y1 = min(res - 1, int(max(pa[1], pb[1], pc[1])) + 1)
            for py in range(y0, y1 + 1):
                fy = py + 0.5
                for px in range(x0, x1 + 1):
                    fx = px + 0.5
                    w0 = ((pb[0]-pa[0])*(fy-pa[1]) - (pb[1]-pa[1])*(fx-pa[0])) / area
                    w1 = ((pc[0]-pb[0])*(fy-pb[1]) - (pc[1]-pb[1])*(fx-pb[0])) / area
                    w2 = 1.0 - w0 - w1
                    if w0 < -1e-9 or w1 < -1e-9 or w2 < -1e-9:
                        continue
                    z = pa[2] * w1 + pb[2] * w2 + pc[2] * w0
                    i = py * res + px
                    if z > self.depth[i]:
                        self.depth[i] = z

    def _project(self, p: Vec):
        return ((dot(p, self.right) - self.u0) / self.su * self.res,
                (dot(p, self.up) - self.v0) / self.sv * self.res,
                dot(p, self.dir))

    def lit(self, p: Vec, bias: float = 0.012) -> bool:
        x, y, z = self._project(p)
        ix, iy = int(x), int(y)
        if not (0 <= ix < self.res and 0 <= iy < self.res):
            return True
        return z + bias >= self.depth[iy * self.res + ix]


def rasterize(mesh: Mesh, cam: DimetricCamera, size: int,
              target: Vec = (0.0, 0.0, 0.62), smooth: bool = False,
              shadows: "ShadowMap | None" = None, fill: float = 0.0):
    """Orthographic scanline z-buffer. Returns (material, lambert, normal)."""
    light = camera_light(cam)
    fill_dir = norm((-light[0], -light[1], abs(light[2]) * 0.5 + 0.3))
    inv = size / (2.0 * cam.span)

    mat: list[str | None] = [None] * (size * size)
    lam: list[float] = [0.0] * (size * size)
    nrm: list[Vec] = [(0.0, 0.0, 0.0)] * (size * size)
    zbuf: list[float] = [-1e30] * (size * size)

    def project(v: Vec):
        r = sub(v, target)
        u, vv = dot(r, cam.right), dot(r, cam.up)
        # Depth increases toward the camera, so a larger value wins the z-test.
        return ((u * inv) + size * 0.5 - 0.5,
                size * 0.5 - 0.5 - (vv * inv),
                dot(r, cam.dir))

    for tri, nidx, material in mesh.faces:
        a, b, c = (mesh.verts[i] for i in tri)
        face_n = norm(cross(sub(b, a), sub(c, a)))
        pa, pb, pc = project(a), project(b), project(c)

        area = ((pb[0] - pa[0]) * (pc[1] - pa[1]) -
                (pb[1] - pa[1]) * (pc[0] - pa[0]))
        if abs(area) < 1e-12:
            continue

        x0 = max(0, int(math.floor(min(pa[0], pb[0], pc[0]))))
        x1 = min(size - 1, int(math.ceil(max(pa[0], pb[0], pc[0]))))
        y0 = max(0, int(math.floor(min(pa[1], pb[1], pc[1]))))
        y1 = min(size - 1, int(math.ceil(max(pa[1], pb[1], pc[1]))))
        if x1 < x0 or y1 < y0:
            continue

        vns = None
        if smooth and nidx and mesh.normals:
            try:
                vns = [mesh.normals[i] for i in nidx]
            except IndexError:
                vns = None

        for py in range(y0, y1 + 1):
            fy = py + 0.5
            for px in range(x0, x1 + 1):
                fx = px + 0.5
                w0 = ((pb[0] - pa[0]) * (fy - pa[1]) - (pb[1] - pa[1]) * (fx - pa[0])) / area
                w1 = ((pc[0] - pb[0]) * (fy - pb[1]) - (pc[1] - pb[1]) * (fx - pb[0])) / area
                w2 = 1.0 - w0 - w1
                # w1 is the weight of a, w0 of c, w2 of b under this formulation.
                if w0 < -1e-9 or w1 < -1e-9 or w2 < -1e-9:
                    continue
                z = pa[2] * w1 + pb[2] * w2 + pc[2] * w0
                i = py * size + px
                if z <= zbuf[i]:
                    continue
                zbuf[i] = z
                n = face_n
                if vns:
                    n = norm(add(add(mul(vns[0], w1), mul(vns[1], w2)), mul(vns[2], w0)))
                if dot(n, cam.dir) < 0:      # keep normals facing the camera
                    n = mul(n, -1.0)
                mat[i] = material
                nrm[i] = n

                key = max(0.0, dot(n, light))
                if shadows is not None and key > 0.0:
                    world = add(add(mul(a, w1), mul(b, w2)), mul(c, w0))
                    if not shadows.lit(world):
                        key *= 0.18          # in shadow: keep a little bounce
                # A weak opposing fill lifts the fully-turned-away face off the
                # bottom of the ramp, so mid steps get used instead of clamping.
                amb = fill * max(0.0, dot(n, fill_dir))
                lam[i] = min(1.0, 0.10 + 0.80 * key + amb)
    return mat, lam, nrm


def coffee_mesh() -> Mesh:
    """Tessellation of isorender.coffee_scene, for cross-checking the rasterizer."""
    m = Mesh()
    m.add_box((-0.62, -0.62, 0.0), (0.62, 0.62, 0.72), "wood")
    m.add_cylinder((0.0, 0.0, 0.72), 0.46, 0.06, "cream")
    m.add_cylinder((0.0, 0.0, 0.78), 0.30, 0.40, "cream")
    m.add_sphere((0.40, -0.42, 0.86), 0.18, "foliage")
    return m
