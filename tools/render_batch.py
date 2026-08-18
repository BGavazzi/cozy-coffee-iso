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
from isorender import AZIMUTH_STEP, DimetricCamera, coffee_scene, render  # noqa: E402
from mesh import load_obj, rasterize  # noqa: E402
from pixelize import (  # noqa: E402
    apply_outline, downsample_modal, load_palette, shade_toon,
)

ROOT = Path(__file__).resolve().parent.parent


def render_sprite(source, azimuth, target, factor, ramps, smooth=False):
    """`source` is either an analytic Scene or a Mesh. Everything downstream of
    the buffers is identical, which is the point: generation stages are pluggable."""
    size = target * factor
    cam = DimetricCamera(azimuth)
    if hasattr(source, "faces"):
        mat, lam, _ = rasterize(source, cam, size, smooth=smooth)
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

    manifest = []
    for k in range(8):
        az = 45.0 + k * AZIMUTH_STEP
        img, px = render_sprite(source, az, args.target, args.factor, ramps,
                                smooth=args.smooth)
        name = f"{asset}_dir{k}.png"
        img.save(out / name)
        manifest.append({"asset": asset, "direction": k, "azimuth": az,
                         "file": name, **(footprint(px, args.target) or {})})
        print(f"  dir{k}  az={az:5.1f}  {name}")

    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\n{len(manifest)} sprites -> {out}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
