"""Minimal orthographic dimetric raytracer.

Stands in for the Blender stage so the deterministic half of the pipeline can be
built and proven before any GPU or DCC dependency exists. It renders the same
projection Blender will, and emits the same buffers the pixelizer consumes:
material id, surface normal, and depth.

The camera is the specification, not an approximation of it. Elevation is 30
degrees, which makes a unit square in the ground plane project to exactly 2:1
(height/width = sin 30 = 0.5) - the property that gives clean pixel stair-steps.
`verify_projection()` asserts it rather than trusting the arithmetic.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

Vec = tuple[float, float, float]

ELEVATION_DEG = 30.0    # -> exactly 2:1 dimetric. Do not change casually.
AZIMUTH_STEP = 45.0     # 8 directions


# --- vector helpers ---------------------------------------------------------

def sub(a: Vec, b: Vec) -> Vec: return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def add(a: Vec, b: Vec) -> Vec: return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def mul(a: Vec, s: float) -> Vec: return (a[0] * s, a[1] * s, a[2] * s)
def dot(a: Vec, b: Vec) -> float: return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Vec, b: Vec) -> Vec:
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def norm(a: Vec) -> Vec:
    m = math.sqrt(dot(a, a)) or 1.0
    return (a[0] / m, a[1] / m, a[2] / m)


# --- primitives -------------------------------------------------------------

@dataclass
class Hit:
    t: float
    normal: Vec
    material: str


@dataclass
class Sphere:
    centre: Vec
    radius: float
    material: str

    def intersect(self, o: Vec, d: Vec) -> Hit | None:
        oc = sub(o, self.centre)
        b = 2.0 * dot(oc, d)
        c = dot(oc, oc) - self.radius ** 2
        disc = b * b - 4 * c
        if disc < 0:
            return None
        t = (-b - math.sqrt(disc)) / 2.0
        if t < 1e-4:
            return None
        p = add(o, mul(d, t))
        return Hit(t, norm(sub(p, self.centre)), self.material)


@dataclass
class Box:
    lo: Vec
    hi: Vec
    material: str

    def intersect(self, o: Vec, d: Vec) -> Hit | None:
        tmin, tmax, axis, sign = -1e30, 1e30, 0, 1.0
        for i in range(3):
            if abs(d[i]) < 1e-9:
                if o[i] < self.lo[i] or o[i] > self.hi[i]:
                    return None
                continue
            inv = 1.0 / d[i]
            t1, t2 = (self.lo[i] - o[i]) * inv, (self.hi[i] - o[i]) * inv
            s = -1.0
            if t1 > t2:
                t1, t2, s = t2, t1, 1.0
            if t1 > tmin:
                tmin, axis, sign = t1, i, s
            tmax = min(tmax, t2)
            if tmin > tmax:
                return None
        if tmin < 1e-4:
            return None
        n = [0.0, 0.0, 0.0]
        n[axis] = sign
        return Hit(tmin, (n[0], n[1], n[2]), self.material)


@dataclass
class Cylinder:
    """Z-aligned capped cylinder."""
    centre: Vec       # base centre
    radius: float
    height: float
    material: str

    def intersect(self, o: Vec, d: Vec) -> Hit | None:
        cx, cy, cz = self.centre
        ox, oy = o[0] - cx, o[1] - cy
        a = d[0] * d[0] + d[1] * d[1]
        best: Hit | None = None

        if a > 1e-9:
            b = 2 * (ox * d[0] + oy * d[1])
            c = ox * ox + oy * oy - self.radius ** 2
            disc = b * b - 4 * a * c
            if disc >= 0:
                sq = math.sqrt(disc)
                for t in ((-b - sq) / (2 * a), (-b + sq) / (2 * a)):
                    if t < 1e-4:
                        continue
                    z = o[2] + d[2] * t
                    if cz <= z <= cz + self.height:
                        n = norm((o[0] + d[0] * t - cx, o[1] + d[1] * t - cy, 0.0))
                        if best is None or t < best.t:
                            best = Hit(t, n, self.material)
                        break

        for z_plane, nz in ((cz + self.height, 1.0), (cz, -1.0)):
            if abs(d[2]) < 1e-9:
                continue
            t = (z_plane - o[2]) / d[2]
            if t < 1e-4:
                continue
            px, py = o[0] + d[0] * t - cx, o[1] + d[1] * t - cy
            if px * px + py * py <= self.radius ** 2:
                if best is None or t < best.t:
                    best = Hit(t, (0.0, 0.0, nz), self.material)
        return best


@dataclass
class Scene:
    objects: list = field(default_factory=list)

    def trace(self, o: Vec, d: Vec) -> Hit | None:
        best: Hit | None = None
        for obj in self.objects:
            h = obj.intersect(o, d)
            if h and (best is None or h.t < best.t):
                best = h
        return best


# --- camera -----------------------------------------------------------------

class DimetricCamera:
    def __init__(self, azimuth_deg: float, span: float = 1.25,
                 elevation_deg: float = ELEVATION_DEG):
        el, az = math.radians(elevation_deg), math.radians(azimuth_deg)
        # Direction from the scene toward the camera.
        self.dir = norm((math.cos(el) * math.cos(az),
                         math.cos(el) * math.sin(az),
                         math.sin(el)))
        self.right = norm(cross((0.0, 0.0, 1.0), self.dir))
        self.up = norm(cross(self.dir, self.right))
        self.span = span

    def ray(self, u: float, v: float, target: Vec = (0.0, 0.0, 0.62)):
        """u, v in [-1, 1]. Orthographic: direction is constant."""
        origin = add(add(target, mul(self.dir, 10.0)),
                     add(mul(self.right, u * self.span),
                         mul(self.up, v * self.span)))
        return origin, mul(self.dir, -1.0)


def verify_projection(tol: float = 1e-6) -> float:
    """A ground-plane unit square must project 2:1. Returns the measured ratio."""
    cam = DimetricCamera(45.0)
    corners = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0)]
    us = [dot(c, cam.right) for c in corners]
    vs = [dot(c, cam.up) for c in corners]
    ratio = (max(vs) - min(vs)) / (max(us) - min(us))
    assert abs(ratio - 0.5) < 1e-6, f"projection is {ratio:.9f}:1, expected 0.5"
    return ratio


# --- render -----------------------------------------------------------------

LIGHT = norm((-0.55, -0.35, 0.76))   # fixed key, screen-space upper-left (NW)


def render(scene: Scene, cam: DimetricCamera, size: int):
    """Returns (material_id, lambert, normal, mask) buffers, row-major."""
    mat: list[str | None] = [None] * (size * size)
    lam: list[float] = [0.0] * (size * size)
    nrm: list[Vec] = [(0.0, 0.0, 0.0)] * (size * size)

    for y in range(size):
        v = 1.0 - 2.0 * (y + 0.5) / size
        for x in range(size):
            u = 2.0 * (x + 0.5) / size - 1.0
            o, d = cam.ray(u, v)
            h = scene.trace(o, d)
            if h is None:
                continue
            i = y * size + x
            mat[i] = h.material
            nrm[i] = h.normal
            # Ambient floor only. A half-lambert wrap compresses everything into
            # the ramp's light end, which wastes most of the ramp -- and the
            # ramp is the entire shading budget once this is quantized.
            d_ = max(0.0, dot(h.normal, LIGHT))
            lam[i] = min(1.0, 0.10 + 0.92 * d_)
    return mat, lam, nrm


def coffee_scene() -> Scene:
    """A cup and saucer on a crate. No ground plane: sprites render on alpha,
    and a ground plane would both dominate the frame and defeat the point."""
    return Scene([
        Box((-0.62, -0.62, 0.0), (0.62, 0.62, 0.72), "wood"),     # crate
        Cylinder((0.0, 0.0, 0.72), 0.46, 0.06, "cream"),          # saucer
        Cylinder((0.0, 0.0, 0.78), 0.30, 0.40, "cream"),          # cup
        Sphere((0.40, -0.42, 0.86), 0.18, "foliage"),             # bean pot
    ])
