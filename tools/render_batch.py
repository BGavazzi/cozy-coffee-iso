#!/usr/bin/env python3
"""Render a batch of sprites across all 8 azimuths.

Stand-in for the production generation stage (concept -> mesh -> rig -> motion ->
Blender). Same contract, same outputs, no GPU: enough to exercise and prove the
batch review loop before the heavy stages exist.

    python tools/render_batch.py [--out sprites] [--target 64]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from isorender import (  # noqa: E402
    AZIMUTH_STEP, DimetricCamera, coffee_scene, dot, render,
)
from mesh import load_obj, rasterize  # noqa: E402
from pixelize import (  # noqa: E402
    apply_outline, downsample_modal, load_palette, shade_toon,
)

ROOT = Path(__file__).resolve().parent.parent


def frame_all(mesh, margin: float = 0.06):
    """One camera span and one world centre for the whole direction set.

    The default span of 1.25 is sized for the analytic test scene, and an
    ingested prop is whatever size it really is -- a 0.26 m teapot came out as
    a nine-pixel smudge, which `review_queue` correctly called an 8x upscale
    because 97% of its 8x8 blocks were empty.

    Fitting per direction would fix the size and break something worse. The
    span is therefore the LARGEST the object needs across all eight azimuths,
    and the centre is fixed in world space, so the prop neither breathes nor
    drifts as it turns. That is the same guarantee `PIPELINE.md` claims for
    projection and frame coherence, and it has to hold for scale too or a
    sprite set animates by pulsing.
    """
    best = 0.0
    for k in range(8):
        cam = DimetricCamera(k * AZIMUTH_STEP)
        us = [dot(v, cam.right) for v in mesh.verts]
        vs = [dot(v, cam.up) for v in mesh.verts]
        best = max(best, (max(us) - min(us)) / 2, (max(vs) - min(vs)) / 2)
    lo, hi = mesh.bounds()
    centre = tuple((lo[i] + hi[i]) / 2 for i in range(3))
    return best * (1 + margin), centre


def render_sprite(source, azimuth, target, factor, ramps, smooth=False,
                  span=None, centre=None):
    """`source` is either an analytic Scene or a Mesh. Everything downstream of
    the buffers is identical, which is the point: generation stages are pluggable."""
    size = target * factor
    cam = DimetricCamera(azimuth)
    if span:
        cam.span = span
    if hasattr(source, "faces"):
        mat, lam, _ = rasterize(source, cam, size, smooth=smooth,
                                target=centre)
    else:
        mat, lam, _ = render(source, cam, size)

    px = downsample_modal(shade_toon(mat, lam, size, ramps, dither=True), size, factor)

    # Carry material ids through the same downsample so the outline pass knows
    # which ramp bounds each surface.
    ids = {m: (hash(m) % 251, 0, 0) for m in set(mat) if m is not None}
    back = {v: k for k, v in ids.items()}
    small = downsample_modal([ids[m] if m is not None else None for m in mat],
                             size, factor)
    mat_small = [back.get(c) if c is not None else None for c in small]

    px = apply_outline(px, mat_small, target, ramps)

    img = Image.new("RGBA", (target, target), (0, 0, 0, 0))
    img.putdata([(c[0], c[1], c[2], 255) if c else (0, 0, 0, 0) for c in px])
    return img, px


def footprint(px, target):
    """Pivot and footprint from the silhouette base, in pixels."""
    solid = [(i % target, i // target) for i, c in enumerate(px) if c is not None]
    if not solid:
        return None
    xs, ys = [p[0] for p in solid], [p[1] for p in solid]
    base_y = max(ys)
    base_xs = [x for x, y in solid if y >= base_y - 1]
    return {
        "bbox": [min(xs), min(ys), max(xs), max(ys)],
        "pivot": [round(sum(base_xs) / len(base_xs)), base_y],
        "coverage": round(len(solid) / (target * target), 4),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "sprites"))
    ap.add_argument("--target", type=int, default=64)
    ap.add_argument("--factor", type=int, default=4)
    ap.add_argument("--mesh", help="OBJ to render; omit to use the analytic test scene")
    ap.add_argument("--name", default=None, help="asset name for output files")
    ap.add_argument("--smooth", action="store_true", help="interpolate vertex normals")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    ramps = load_palette()
    if args.mesh:
        source = load_obj(args.mesh)
        asset = args.name or Path(args.mesh).stem
        print(f"mesh: {len(source.verts)} verts, {len(source.faces)} tris")
    else:
        source = coffee_scene()
        asset = args.name or "crate_cup"

    # Only for real meshes. The analytic scene is authored at the default span
    # on purpose and refitting it would change every committed sprite.
    span, centre = frame_all(source) if args.mesh else (None, None)
    if span:
        print(f"  framed at span {span:.3f}, centre "
              f"({centre[0]:.2f}, {centre[1]:.2f}, {centre[2]:.2f})")

    # Stage 7. `ingest.fit()` already computed these once, in the process that
    # wrote the OBJ this run loaded -- but that was a different invocation, so
    # they are re-derived here from the mesh's own bounds via `mesh_geometry`,
    # which is exact rather than approximate: `fit` centres every mesh on
    # (0.5, 0.5) and rests it on z=0 by construction, so the numbers are
    # recoverable from the file alone. The analytic scene has no single
    # footprint -- it is a whole room -- so it is left out rather than given a
    # placeholder that looks like a measurement.
    world = None
    if args.mesh:
        from ingest import mesh_geometry
        world = mesh_geometry(source)
        print(f"  world: height {world['height']:.3f}  footprint "
              f"{world['footprint_xy'][0]:.3f}x{world['footprint_xy'][1]:.3f} "
              f"tiles")

    entries = []
    for k in range(8):
        az = 45.0 + k * AZIMUTH_STEP
        img, px = render_sprite(source, az, args.target, args.factor, ramps,
                                smooth=args.smooth, span=span, centre=centre)
        name = f"{asset}_dir{k}.png"
        img.save(out / name)
        row = {"asset": asset, "direction": k, "azimuth": az, "file": name,
              **(footprint(px, args.target) or {})}
        if world:
            row["world"] = world
        entries.append(row)
        print(f"  dir{k}  az={az:5.1f}  {name}")

    # Merged by (asset, direction) rather than overwritten. A batch that
    # renders three assets one call at a time used to leave manifest.json
    # describing only the last one -- verified: three renders in a row left
    # 8 entries naming one asset, not 24 naming three.
    path = out / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    manifest = [m for m in manifest if m.get("asset") != asset]
    manifest.extend(entries)
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\n{len(entries)} sprites -> {out}/  ({len(manifest)} total across "
          f"{len({m['asset'] for m in manifest})} assets)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
