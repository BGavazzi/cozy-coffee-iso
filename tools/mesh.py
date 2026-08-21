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

    def add_prism(self, centre: Vec, rx: float, ry: float, height: float,
                  material: str, segments: int = 8, phase: float = math.pi / 8,
                  cap_material: str | None = None) -> None:
        """An n-gon prism with independent x/y radii.

        Boxes are the wrong primitive for anything that must look the same from
        every camera azimuth: a box's projected width swings by half between its
        face-on and corner-on views. An octagon's swings by about 8%, so a
        character built from prisms keeps a stable silhouette through all eight
        directions -- and reads as rounded rather than blocky, which is what the
        art direction wants anyway.
        """
        cx, cy, cz = centre
        top, bot = cz + height, cz
        ring = [(cx + rx * math.cos(2 * math.pi * i / segments + phase),
                 cy + ry * math.sin(2 * math.pi * i / segments + phase))
                for i in range(segments)]
        cap = cap_material or material
        for i in range(segments):
            x0, y0 = ring[i]
            x1, y1 = ring[(i + 1) % segments]
            self.add_quad((x0, y0, bot), (x1, y1, bot),
                          (x1, y1, top), (x0, y0, top), material)
            ci = len(self.verts)
            self.verts += [(cx, cy, top), (x0, y0, top), (x1, y1, top)]
            self.faces.append(((ci, ci + 1, ci + 2), None, cap))
            ci = len(self.verts)
            self.verts += [(cx, cy, bot), (x1, y1, bot), (x0, y0, bot)]
            self.faces.append(((ci, ci + 1, ci + 2), None, cap))

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
        """Hard in-or-out test. Kept for callers that only need a boolean."""
        return self.shadow(p, bias) >= 0.999

    def shadow(self, p: Vec, bias: float = 0.012, falloff: float = 1.15,
               floor: float = 0.20, taps: int = 5) -> float:
        """How lit a point is, 0.20 (full contact shadow) to 1.0 (unshadowed).

        A boolean shadow is a uniformly dark region with a hard edge, and at
        this light elevation that reads as a smear stretching away from every
        prop rather than as the object sitting on the ground. Two changes:

        **Fade with occluder distance.** A shadow is darkest where the caster
        meets the floor and weakens as it travels, because a real key light has
        area. Exponential in the depth gap, so contact shadows stay tight and
        crisp while the long tail falls off instead of dragging.

        **Sample a small cross.** One tap gives a stair-stepped edge at map
        resolution. Five taps cost little and put the edge between ramp steps,
        where the dither band can resolve it.
        """
        x, y, z = self._project(p)
        acc = 0.0
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1))[:taps]:
            ix, iy = int(x) + dx, int(y) + dy
            if not (0 <= ix < self.res and 0 <= iy < self.res):
                acc += 1.0
                continue
            gap = self.depth[iy * self.res + ix] - (z + bias)
            if gap <= 0.0:
                acc += 1.0
            else:
                acc += 1.0 - (1.0 - floor) * math.exp(-gap / falloff)
        return acc / taps


@dataclass
class Pool:
    """A local light. Negative intensity is allowed and is not a hack.

    Negative lights are standard practice in film and game lighting: the way to
    give a composition a centre is usually to take light OUT of the periphery
    rather than to pile more onto the subject, because adding light to a subject
    that is already near the top of its ramp just clips it. Here the palette
    makes that literal -- pushing a corner DOWN its ramp also pushes it cooler,
    which is the same warm-centre / cool-edge move the whole palette is built
    around.
    """
    pos: Vec
    radius: float
    intensity: float


class LightRig:
    """Staged light on top of the global key/fill/bounce.

    This is the piece that turns the palette into art direction rather than a
    document. Every ramp was built warm-shifted at the top and cool-shifted at
    the bottom -- that hue rotation is the defining Ghibli move -- but with a
    single flat key the scene only ever occupied the middle of every ramp, so
    the shift was present in the JSON and invisible on screen.

    Local light supplies the range to spend. A pool pushes nearby surfaces UP
    their own ramp, which is automatically warmer as well as brighter; the
    corners the pools do not reach fall to the bottom, which is automatically
    cooler. Warm pools against cool shadow, and not one extra palette entry, as
    it is the same ramp read at different depths.

    Pools only, no projected window shafts. That was tried and abandoned for a
    structural reason worth recording: the key light is anchored to the camera
    basis, so at azimuth 45 its world direction runs essentially along +x. The
    only two walls an isometric room may draw are the far ones, and a shaft cast
    through those lands either as a 0.15-tile sliver against the skirting or
    outside the floor altogether -- both measured. Making shafts reach would
    mean a sun direction that disagrees with the cast shadows. A window is
    therefore lit as a bright pane plus a soft pool inside it, which is what a
    backlit window actually looks like from indoors, and which stays correct
    from every azimuth instead of only one.
    """

    def __init__(self, pools=()):
        self.pools = list(pools)

    def boost(self, p: Vec, n: Vec) -> float:
        out = 0.0
        for L in self.pools:
            d = sub(L.pos, p)
            dist = math.sqrt(d[0] * d[0] + d[1] * d[1] + d[2] * d[2]) or 1e-9
            if dist >= L.radius:
                continue
            t = 1.0 - dist / L.radius
            # Falloff exponent 1.5, not 2. Inverse-square is correct physics and
            # the wrong art: measured, a squared pool put 0.062 of boost on the
            # floor under a lamp -- a fifth of a ramp step, invisible after
            # quantization. A pool has to cross a step boundary to exist at all.
            facing = 0.34 + 0.66 * max(0.0, dot(n, mul(d, 1.0 / dist)))
            out += L.intensity * (t ** 1.5) * facing
        return out



# --- surface grain -----------------------------------------------------------

def _lattice(ix: int, iy: int, iz: int) -> float:
    """Deterministic value in [0,1) for an integer lattice cell."""
    h = (ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791)
    h = (h * 1103515245 + 12345) & 0x7FFFFFFF
    h ^= h >> 13
    return (h & 0xFFFFFF) / 0xFFFFFF


def surface_grain(p: Vec, axis: Vec = (1.0, 1.0, 1.0),
                  coarse: float = 1.7, fine: float = 5.3) -> float:
    """Two octaves of blocky value noise in world space, returned in [-1, 1].

    Deliberately *not* interpolated. Smooth noise resolves to a soft gradient
    that the ramp quantizer then re-hardens into contour bands -- the exact
    banding artefact `pixelize` exists to avoid. Blocky cells quantize cleanly
    because they are already flat, and cell edges land on ramp-step boundaries
    only where the two happen to disagree, which is what produces mottle rather
    than contours.

    World space, not screen space, so the pattern is fixed to the surface. In
    screen space it would crawl across a rotating sprite between the eight
    azimuths, which is the same class of mistake as screen-space dithering.
    """
    import math
    n = 0.0
    for scale, weight in ((coarse, 0.52), (fine, 0.48)):
        n += weight * _lattice(math.floor(p[0] * scale * axis[0]),
                               math.floor(p[1] * scale * axis[1]),
                               math.floor(p[2] * scale * axis[2]))
    return n * 2.0 - 1.0


# Per ramp: (amplitude as a fraction of one ramp step, lattice axis scaling).
#
# Amplitude never exceeds one step. Grain is meant to break a flat field, not to
# add a second value structure competing with the lighting. Glass, metal and
# painted surfaces stay clean because they read as manufactured; wood, plaster
# and foliage are where a viewer expects texture and are also the ramps holding
# the largest unbroken areas.
#
# The axis scaling is what separates grain from dirt. Isotropic noise on wood
# produces round blotches that read as stains, because wood does not have round
# features -- it has long ones. Squashing the lattice on x stretches each cell
# into a streak that runs along the board, and the floor's own courses already
# run that way. Plaster is genuinely isotropic and keeps a round cell. Foliage
# gets a fine, near-isotropic cell so it breaks into leaf-sized dapple rather
# than into patches larger than the plant.
# Checked before GRAIN_BY_RAMP, so a material can opt out of its ramp's texture.
GRAIN_BY_MATERIAL = {
    "skin": (0.0, (1.0, 1.0, 1.0)),
}

# Full wear lifts a surface by about one ramp step. Less and the quantizer eats
# it; more and the tracks read as a second light source on the floor.
WEAR_LIFT = 1.15

GRAIN_BY_RAMP = {
    "wood":    (0.85, (0.42, 2.30, 2.30)),
    "cream":   (0.65, (1.00, 1.00, 1.00)),
    "foliage": (0.55, (1.70, 1.70, 1.70)),
    "rose":    (0.30, (1.00, 1.00, 1.00)),
    "neutral": (0.0,  (1.00, 1.00, 1.00)),
    "sky":     (0.0,  (1.00, 1.00, 1.00)),
}


_UNBAKED = object()


class WearField:
    """Where the floor has been walked on, as a function of world position.

    Grain gives every wooden surface the same texture everywhere, which is what
    a factory finish looks like and not what a floor looks like. Real wear is
    concentrated: pale, scuffed tracks in front of a counter and around every
    chair, and untouched boards under the furniture and in the corners.

    The point is that this is *derived*, not authored. `Layout.wear_field()`
    reads the placements and puts a patch wherever feet go -- in front of each
    seat, around the service counter, along the spine between them. Hand-placing
    wear would be the same mistake as hand-placing the dressing: the room already
    knows where people stand, because it knows where the chairs are.

    Same shape as `LightRig`, deliberately. A pool with a radius and a falloff is
    the right primitive for "influence that fades with distance", and having two
    unrelated implementations of it would be worse than reusing the idea.
    """

    def __init__(self, pools=(), height: float = 0.55):
        self.pools = list(pools)
        # Wear is a floor phenomenon. Without this the field would scuff the
        # walls and the tops of tables at whatever height happened to pass over
        # a pool, which reads as damp rather than as traffic.
        self.height = height
        self._grid = _UNBAKED

    # Cell size of the baked grid, in world units. At the shipping 27 px per
    # unit this is about three pixels, which is finer than the wear itself
    # varies -- the field is a sum of pools a tile across, so there is nothing
    # below this scale to lose.
    CELL = 0.12

    def _plan(self, x: float, y: float) -> float:
        best = 0.0
        for cx, cy, r, amount in self.pools:
            d = math.hypot(x - cx, y - cy)
            if d >= r:
                continue
            # Not linear: traffic wears a plateau with a quick edge, not a cone.
            t = 1.0 - (d / r)
            best = max(best, amount * (t ** 0.55))
        return best

    def _bake(self) -> None:
        """Grid the plan-view field once, because `at` is a per-pixel call.

        Routes overlap by construction, so the pool list runs to a few hundred
        and an exact query is a few hundred hypots. Multiplied by every lit
        pixel of floor that is a render's worth of work spent re-deriving a
        field that does not change during the render.
        """
        if not self.pools:
            self._grid = None
            return
        pad = max(r for _, _, r, _ in self.pools)
        self._x0 = min(c for c, _, _, _ in self.pools) - pad
        self._y0 = min(c for _, c, _, _ in self.pools) - pad
        self._nx = int((max(c for c, _, _, _ in self.pools) + pad
                        - self._x0) / self.CELL) + 2
        self._ny = int((max(c for _, c, _, _ in self.pools) + pad
                        - self._y0) / self.CELL) + 2
        self._grid = [self._plan(self._x0 + i * self.CELL,
                                 self._y0 + j * self.CELL)
                      for j in range(self._ny) for i in range(self._nx)]

    def at(self, p: Vec) -> float:
        if p[2] > self.height:
            return 0.0
        if self._grid is _UNBAKED:
            self._bake()
        if self._grid is None:
            return 0.0
        i = int((p[0] - self._x0) / self.CELL + 0.5)
        j = int((p[1] - self._y0) / self.CELL + 0.5)
        if not (0 <= i < self._nx and 0 <= j < self._ny):
            return 0.0
        return self._grid[j * self._nx + i] * (1.0 - (p[2] / self.height) ** 2)


def rasterize(mesh: Mesh, cam: DimetricCamera, size: int,
              target: Vec = (0.0, 0.0, 0.62), smooth: bool = False,
              shadows: "ShadowMap | None" = None, fill: float = 0.0,
              bounce: float = 0.0, rig: "LightRig | None" = None,
              ambient: float = 0.10, key_gain: float = 0.80,
              haze: float = 0.0, haze_to: float = 0.82,
              grain: float = 0.0, ramps: dict | None = None,
              wear: "WearField | None" = None):
    """Orthographic scanline z-buffer. Returns (material, lambert, normal).

    Three light terms, and the third is not decoration:

    * **key** -- one directional light, upper-left, anchored to the camera basis.
    * **fill** -- a soft opposing wash so shadow sides do not go to a single flat
      value.
    * **bounce** -- a weak light along the view direction.
    * **rig** -- optional staged light: lamp pools and daylight shafts.

    `haze` is aerial perspective. `style_bible.yaml` specifies it -- the entry
    reads `atmosphere: value compression toward the ramp's light end, not blur`
    -- and nothing implemented it for four passes, because the substitution table
    was treated as prose rather than as a spec. Distant surfaces are pulled
    toward `haze_to` in proportion to their depth, which both *lifts* them and
    *compresses* their contrast, since everything converges on one value as the
    weight rises. Blur is not an option at this scale and would be the wrong
    look anyway; a limited palette does depth by flattening the far plane, which
    is what every SNES background this project cites does.

    `grain` breaks up flat fields. Every surface in the library is an
    axis-aligned primitive, so large areas land on exactly one ramp step and read
    as blockout no matter how good the palette is -- the single largest remaining
    gap against the SNES backgrounds this project cites, all of which broke every
    flat area with a step or two of tonal noise. It is applied to the *lambert*,
    not the colour, so the existing quantizer turns it into legal palette steps
    for free and it can never produce an off-ramp pixel. `ramps` is needed to
    know how large one step is for the material under each pixel.

    `ambient` and `key_gain` set how much of each ramp the global light claims.
    They drop when a rig is supplied, because staged light needs headroom: if
    the key alone already fills the ramp there is nothing left for a pool to
    brighten, and every pool washes out to the same top step.

    Bounce exists because a character's face is a vertical surface and the key
    comes from above, so without it every face sits permanently at the bottom of
    its ramp: measured, skin peaked at 0.56 lambert and never rose past step 3 of
    7, leaving heads as dark lumps. Cozy games all light faces this way. It is
    also what stops the fronts of props -- the sides turned toward the player --
    from being the darkest thing on screen.
    """
    light = camera_light(cam)
    # Interior bounce is horizontal: indoors, fill comes off the walls, not out
    # of a sky. Aiming it upward gave up-facing surfaces a second helping of
    # light on top of the key they already faced, which is the other half of why
    # floors outshone faces.
    fill_dir = norm((-light[0], -light[1], 0.15))
    view = cam.dir
    inv = size / (2.0 * cam.span)

    mat: list[str | None] = [None] * (size * size)
    lam: list[float] = [0.0] * (size * size)
    nrm: list[Vec] = [(0.0, 0.0, 0.0)] * (size * size)
    zbuf: list[float] = [-1e30] * (size * size)
    zdepth: list[float] = [-1e30] * (size * size)
    # One ramp-step size per material token, resolved once. Doing this per pixel
    # meant a string parse and a dict walk seven million times.
    _grain_amp: dict = {}

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
                world = None
                if shadows is not None:
                    world = add(add(mul(a, w1), mul(b, w2)), mul(c, w0))
                if shadows is not None and key > 0.0:
                    key *= shadows.shadow(world)
                # A weak opposing fill lifts the fully-turned-away face off the
                # bottom of the ramp, so mid steps get used instead of clamping.
                amb = fill * max(0.0, dot(n, fill_dir))
                bnc = bounce * max(0.0, dot(n, view))
                stage = 0.0
                if rig is not None:
                    if shadows is None:
                        world = add(add(mul(a, w1), mul(b, w2)), mul(c, w0))
                    stage = rig.boost(world, n)
                lam[i] = max(0.0, min(1.0, ambient + key_gain * key
                                          + amb + bnc + stage))
                if grain > 0.0:
                    if world is None:
                        world = add(add(mul(a, w1), mul(b, w2)), mul(c, w0))
                    g = _grain_amp.get(material)
                    if g is None:
                        from pixelize import material as _split
                        try:
                            ramp = _split(material)[0]
                        except (KeyError, ValueError):
                            ramp = None
                        steps = len(ramps[ramp]) if (ramps and ramp in ramps) else 0
                        base = material.split("+")[0].split("-")[0]
                        amp, axis = GRAIN_BY_MATERIAL.get(
                            base, GRAIN_BY_RAMP.get(ramp, (0.0, (1.0, 1.0, 1.0))))
                        # The step is the unit everything here is denominated
                        # in. Grain is deliberately under one step, so it breaks
                        # a flat field without competing with the lighting; wear
                        # is deliberately about one, so it actually shows.
                        step = (1.0 / steps) if steps > 1 else 0.0
                        g = (amp * step, axis, step)
                        _grain_amp[material] = g
                    if g[0]:
                        amp, lift = grain * g[0], 0.0
                        if wear is not None:
                            w = wear.at(world)
                            if w > 0.0:
                                # Worn boards are paler -- the finish is rubbed
                                # off -- and rougher. Both, or the tracks read as
                                # a lighting artefact rather than as wear.
                                #
                                # The lift is a share of a RAMP STEP, not of the
                                # grain amplitude. Denominating it in grain gave
                                # a maximum lift of 0.086 against a step of 0.20,
                                # so the quantizer rounded nearly all of it away
                                # and the whole field moved 2.5% of pixels.
                                amp *= 1.0 + 0.9 * w
                                lift = WEAR_LIFT * g[2] * w
                        lam[i] = max(0.0, min(1.0, lam[i] + lift + amp
                                              * surface_grain(world, g[1])))
                if haze > 0.0:
                    zdepth[i] = z

    if haze > 0.0:
        seen = [z for z in zdepth if z > -1e29]
        if seen:
            near, far = max(seen), min(seen)
            spread = (near - far) or 1e-9
            for i, z in enumerate(zdepth):
                if mat[i] is None:
                    continue
                # 1 at the furthest surface, 0 at the nearest. Squared, so the
                # near two-thirds of the room is left alone and the haze builds
                # only where depth actually reads.
                t = haze * ((near - z) / spread) ** 2
                lam[i] += t * (haze_to - lam[i])
    return mat, lam, nrm


def coffee_mesh() -> Mesh:
    """Tessellation of isorender.coffee_scene, for cross-checking the rasterizer."""
    m = Mesh()
    m.add_box((-0.62, -0.62, 0.0), (0.62, 0.62, 0.72), "wood")
    m.add_cylinder((0.0, 0.0, 0.72), 0.46, 0.06, "cream")
    m.add_cylinder((0.0, 0.0, 0.78), 0.30, 0.40, "cream")
    m.add_sphere((0.40, -0.42, 0.86), 0.18, "foliage")
    return m
