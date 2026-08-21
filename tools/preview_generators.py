#!/usr/bin/env python3
"""Contact sheet for the procedural asset generators.

The premise of this pipeline is that humans direct and critique what the
machine generates. That only works if the generated output is *reviewable*,
and a generator is not reviewable through one sample -- the whole question
about a generator is whether its range is any good, which needs a row.

So: one row per generator, one column per seed, all through the shipping
render path. What a row is meant to show is that the silhouettes differ.
Where a row comes out as the same shape eight times, that generator is a
fixed mesh wearing a seed argument, and the sheet says so directly rather
than leaving it to be noticed in a room render three passes later.

    python tools/preview_generators.py [--seeds 8] [--target 64]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import assetlib as A  # noqa: E402
from animate import render_frame  # noqa: E402
from art_review import (  # noqa: E402
    DEFAULT_SPREAD_FLOOR, GENERATORS, _screen_spread, screen_materials,
)
from pixelize import load_palette  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BG = (30, 27, 36)
LABEL = (214, 208, 218)
DIM = (140, 136, 148)

# The rows come from `art_review.GENERATORS`, which is also what the check
# gates on. Keeping a second list here is how a sheet and a check end up
# reporting different numbers for the same generator, and when that happens
# one of them is wrong and nobody can tell which.
#
# The span is per-generator because these differ in size by 3x, and a shared
# span would render the plants at eight pixels tall to leave room for a
# two-tile table. Framing is a property of the subject.
ROWS = tuple((name, (lambda f: lambda s: f(A, s))(factory), span, own)
             for name, factory, span, own, _why in GENERATORS)

# Extra rows the check does not gate on. A painted chair exercises the same
# generator through a different material path, which is worth looking at and
# not worth failing a build over.
ROWS += (("chair, cushioned",
          lambda s: A.chair(cushion="rose", frame="foliage-3", seed=s),
          1.4, None),)



def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--target", type=int, default=64)
    ap.add_argument("--factor", type=int, default=3)
    ap.add_argument("--scale", type=int, default=2)
    ap.add_argument("--azimuth", type=float, default=45.0)
    ap.add_argument("--out", default=str(ROOT / "proof" / "generators.png"))
    args = ap.parse_args()

    ramps = load_palette()
    t, sc, pad, gutter = args.target, args.scale, 6, 128
    cell = t * sc
    sheet = Image.new("RGB", (gutter + args.seeds * (cell + pad) + pad,
                              len(ROWS) * (cell + pad) + pad), (18, 16, 22))
    d = ImageDraw.Draw(sheet)

    for r, (name, factory, span, own) in enumerate(ROWS):
        y = pad + r * (cell + pad)
        d.text((6, y + cell // 2 - 10), name, fill=LABEL)
        frames = []
        for c in range(args.seeds):
            mesh = factory(c + 1)
            # Centre on the mesh's own bounds. Generators vary in height by
            # design, so a fixed centre would walk the subject out of frame
            # exactly where the generator is doing its job.
            xs = [v[0] for v in mesh.verts]
            ys = [v[1] for v in mesh.verts]
            zs = [v[2] for v in mesh.verts]
            centre = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2,
                      (min(zs) + max(zs)) / 2)
            px = render_frame(mesh, args.azimuth, ramps, t, args.factor,
                              centre=centre, span=span)
            img = Image.new("RGB", (t, t), BG)
            img.putdata([p if p is not None else BG for p in px])
            sheet.paste(img.resize((cell, cell), Image.NEAREST),
                        (gutter + c * (cell + pad), y))
            # The spread number comes from `art_review`, deliberately. The
            # sheet and the check must not be able to report different figures
            # for the same generator; if they diverge, one of them is wrong and
            # nobody can tell which.
            frames.append(screen_materials(mesh, args.azimuth, span))
        spread = _screen_spread(frames)
        bar = DEFAULT_SPREAD_FLOOR if own is None else own
        under = spread < bar
        d.text((6, y + cell // 2 + 4), f"spread {spread:.0%}",
               fill=(206, 122, 122) if under else LABEL)
        print(f"  {name:18s} screen spread {spread:5.1%}  (floor {bar:.0%})"
              f"{'   <-- barely varies' if under else ''}")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.out)
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
