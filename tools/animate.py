#!/usr/bin/env python3
"""Render animation clips to packed sprite sheets with an atlas manifest.

This is the factory's actual output. Everything else -- palette, camera, review,
the room composite -- exists to make what lands here correct; a game engine
consumes this directory and nothing else.

One sheet per character. Rows are directions, columns are frames, clips stacked
in row-blocks, so a runtime can seek to (clip, direction, frame) with two
multiplies and no per-frame lookup. The JSON carries the same information
explicitly for tools that would rather read than compute.

    python tools/animate.py [--out sprites] [--target 64] [--gif]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import character as C  # noqa: E402
import fx as FX  # noqa: E402
from isorender import DimetricCamera, camera_light, dot  # noqa: E402
from mesh import ShadowMap, rasterize  # noqa: E402
from pixelize import (  # noqa: E402
    apply_outline, downsample_modal, load_palette, shade_toon,
)

ROOT = Path(__file__).resolve().parent.parent

# Eight facings, named by where the character looks ON SCREEN, for azimuths
# 45, 90, ... 360 in that order. The camera is fixed and the character rotates,
# so "direction" is a property of the sprite, not of the view.
#
# This tuple used to start at "s" and was wrong by exactly one step, which is
# the worst size of error to have: the sheet looked perfect, every frame was
# correctly rendered, and the manifest filed each one under the neighbouring
# facing. A game reading atlas.json would have drawn a character walking south
# using the south-east sprite -- eight sprites all subtly turned, in a way that
# reads as "the animation feels off" rather than as a bug with a location.
#
# The order is not a convention to be chosen. It is a consequence of the
# character's front being +y and the camera being 2:1 dimetric, so it is derived
# rather than declared: `check_direction_labels` recomputes it from the camera
# basis and fails if this tuple drifts.
DIRECTIONS = ("se", "s", "sw", "w", "nw", "n", "ne", "e")


def derived_directions() -> tuple:
    """The facing each azimuth actually produces, from the camera basis alone.

    `character.face()` puts the front at +y. Project that vector through each
    azimuth's screen basis and read off the compass point it lands on, where
    screen-down is south. No tuning constants, so this cannot agree with a
    mistake.
    """
    import math

    from isorender import DimetricCamera, dot
    fwd = (0.0, 1.0, 0.0)
    names = ("e", "se", "s", "sw", "w", "nw", "n", "ne")
    out = []
    for d in range(8):
        cam = DimetricCamera(45.0 + d * 45.0)
        u, v = dot(fwd, cam.right), dot(fwd, cam.up)
        out.append(names[int(round(math.degrees(math.atan2(-v, u)) / 45.0)) % 8])
    return tuple(out)


def check_direction_labels() -> list:
    want = derived_directions()
    if want == DIRECTIONS:
        return []
    bad = [f"{45 + i * 45:.0f}deg: labelled {DIRECTIONS[i]!r}, actually {want[i]!r}"
           for i in range(8) if want[i] != DIRECTIONS[i]]
    return [f"DIRECTIONS is wrong for {len(bad)}/8 azimuths -- every sprite in "
            f"the atlas is filed under the wrong facing: " + "; ".join(bad)]

FPS = 12


def fit(spec, clip_specs, margin=0.06):
    """One camera span and centre for a whole character, across every frame.

    Fitting per frame is the obvious thing and is wrong: the span would breathe
    with the pose and the sprite would swell and shrink on the spot. Fitting the
    union of all poses in all directions gives a fixed scale, which is what lets
    a runtime treat frames as interchangeable.

    Anchors are per clip, not per character, because a seated clip's contact
    point is the seat and a standing clip's is the floor. One anchor for both
    would plant every sitting customer either in the chair or above it.

    Returns (span, centre, {clip: anchor_v}).
    """
    lo_u = lo_v = 1e9
    hi_u = hi_v = -1e9
    contact = {}
    for name, frames in clip_specs:
        c = 1e9
        for f in range(frames):
            ph = f / frames
            mesh = C.build(spec, pose=C.CLIPS[name](ph),
                           seated=C.is_seated(name, ph))
            for d in range(8):
                cam = DimetricCamera(45.0 + d * 45.0)
                us = [dot(v, cam.right) for v in mesh.verts]
                vs = [dot(v, cam.up) for v in mesh.verts]
                lo_u, hi_u = min(lo_u, min(us)), max(hi_u, max(us))
                lo_v, hi_v = min(lo_v, min(vs)), max(hi_v, max(vs))
                c = min(c, min(vs))
        contact[name] = c
    cu, cv = (hi_u + lo_u) / 2, (hi_v + lo_v) / 2
    span = max(hi_u - lo_u, hi_v - lo_v) / 2 * (1 + margin)
    cam0 = DimetricCamera(45.0)
    centre = tuple(cam0.right[i] * cu + cam0.up[i] * cv for i in range(3))
    anchors = {k: round((cv + span - v) / (2 * span), 4) for k, v in contact.items()}
    return span, centre, anchors


def render_frame(mesh, azimuth, ramps, target, factor, centre=(0.0, 0.0, 0.70),
                 span=0.98):
    """One sprite, through exactly the path a static asset takes."""
    cam = DimetricCamera(azimuth)
    cam.span = span
    size = target * factor
    sm = ShadowMap(mesh, camera_light(cam), res=192)
    # Grain, but no haze. Aerial perspective is a property of where a thing
    # sits in a scene, and a sprite is composited at whatever depth the game
    # decides; baking it in would fix every copy at one distance. Grain is a
    # property of the surface itself and travels with it.
    mat, lam, _ = rasterize(mesh, cam, size, target=centre, shadows=sm,
                            fill=0.20, bounce=0.26, ambient=0.05, key_gain=0.60,
                            grain=1.0, ramps=ramps)
    px = downsample_modal(shade_toon(mat, lam, size, ramps, dither=True),
                          size, factor)
    # Rebuild a downsampled material buffer so outlining knows which ramp each
    # edge pixel belongs to; outlines are tinted, never black.
    # Sorted index, not hash: see the note in render_room. Randomised string
    # hashing made outline colour non-deterministic across processes, which on
    # a sprite sheet means the same frame outlines differently between runs.
    ids = {m: (i % 256, i // 256, 0)
           for i, m in enumerate(sorted(m for m in set(mat) if m is not None))}
    back = {v: k for k, v in ids.items()}
    small = downsample_modal([ids[m] if m is not None else None for m in mat],
                             size, factor)
    return apply_outline(px, [back.get(c) if c else None for c in small],
                         target, ramps)


def render_clip(spec, name, frames, ramps, target, factor, span, centre):
    """All 8 directions x N frames for one clip."""
    clip_fn = C.CLIPS[name]
    out = {}
    for f in range(frames):
        ph = f / frames
        mesh = C.build(spec, pose=clip_fn(ph), seated=C.is_seated(name, ph))
        for d in range(8):
            out[(d, f)] = render_frame(mesh, 45.0 + d * 45.0, ramps, target,
                                       factor, centre=centre, span=span)
    return out


def build_sheet(spec, clip_specs, ramps, target, factor):
    span, centre, anchors = fit(spec, clip_specs)
    grids, meta = {}, {}
    for name, frames in clip_specs:
        grids[name] = render_clip(spec, name, frames, ramps, target,
                                  factor, span, centre)
    cols = max(f for _, f in clip_specs)
    rows = 8 * len(clip_specs)
    sheet = Image.new("RGBA", (cols * target, rows * target), (0, 0, 0, 0))

    frame_index = []
    for ci, (name, frames) in enumerate(clip_specs):
        meta[name] = {"row": ci * 8, "frames": frames, "fps": FPS,
                      "anchor": [0.5, anchors[name]]}
        for d in range(8):
            for f in range(frames):
                px = grids[name][(d, f)]
                tile = Image.new("RGBA", (target, target), (0, 0, 0, 0))
                tile.putdata([(c + (255,)) if c is not None else (0, 0, 0, 0)
                              for c in px])
                x, y = f * target, (ci * 8 + d) * target
                sheet.paste(tile, (x, y))
                frame_index.append({"clip": name, "dir": DIRECTIONS[d],
                                    "index": f, "x": x, "y": y,
                                    "w": target, "h": target})
    return sheet, meta, frame_index, cols, rows


def fx_sheets(ramps, target, factor, outdir, atlas):
    """Effects, one sheet each, at the azimuth count their symmetry allows.

    Steam is radial: rendering it eight times produces eight near-identical
    sprites and eight times the storage. The manifest already records each
    effect's symmetry class, so the budget is read from there rather than
    assumed -- the same discipline the static asset queue uses.
    """
    import yaml
    from manifest import DISTINCT_AZIMUTHS
    man = yaml.safe_load((ROOT / "assets.yaml").read_text(encoding="utf-8"))
    sym = {a["id"]: a.get("sym", "none") for a in (man.get("fx") or [])}

    total = 0
    for name, (fn, clips) in sorted(FX.FX.items()):
        az_n = DISTINCT_AZIMUTHS[sym.get(name, "none")]
        cols = max(clips.values())
        rows = az_n * len(clips)
        sheet = Image.new("RGBA", (cols * target, rows * target), (0, 0, 0, 0))
        meta, ci = {}, 0
        for clip, frames in clips.items():
            meta[clip] = {"row": ci * az_n, "frames": frames, "fps": FPS,
                          "azimuths": az_n}
            for d in range(az_n):
                for f in range(frames):
                    mesh = fn(f / frames)
                    px = render_frame(mesh, 45.0 + d * (360.0 / max(1, az_n)),
                                      ramps, target, factor,
                                      centre=(0.5, 0.5, 0.35), span=0.62)
                    tile = Image.new("RGBA", (target, target), (0, 0, 0, 0))
                    tile.putdata([(c + (255,)) if c is not None else (0, 0, 0, 0)
                                  for c in px])
                    sheet.paste(tile, (f * target, (ci * az_n + d) * target))
                    total += 1
            ci += 1
        img = outdir / f"{name}.png"
        sheet.save(img)
        atlas.setdefault("fx", {})[name] = {
            "image": img.name, "clips": meta, "symmetry": sym.get(name, "none"),
            "sheet_size": [cols * target, rows * target],
        }
        print(f"  {name:18s} {cols}x{rows} tiles, {az_n} azimuth(s) -> {img.name}")
    return total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="sprites")
    ap.add_argument("--target", type=int, default=64)
    ap.add_argument("--factor", type=int, default=4)
    ap.add_argument("--gif", action="store_true", help="also write GIF previews")
    ap.add_argument("--only", default=None, help="one character by name")
    ap.add_argument("--fx", action="store_true", help="also render effects")
    ap.add_argument("--fx-only", action="store_true", help="effects only")
    # The point of the whole pipeline, expressed as an integer. Extras are not
    # written down anywhere: `generate_spec` proposes one and tests it against
    # the promoted character checks until it passes, so `--extras 40` costs
    # exactly as much thought as `--extras 0` and forty times the render.
    ap.add_argument("--extras", type=int, default=0,
                    help="also emit N generated extras")
    ap.add_argument("--extras-seed", type=int, default=1)
    args = ap.parse_args()

    ramps = load_palette()
    outdir = ROOT / args.out
    outdir.mkdir(exist_ok=True)

    # Clips per role, mirroring assets.yaml. Only clips with a pose function are
    # emitted; the rest are declared but unbuilt, and the summary says so rather
    # than silently shipping a short sheet.
    ROLE_CLIPS = {
        "barista": [("idle", 4), ("walk", 8), ("carry_walk", 8), ("brew", 6),
                    ("wipe", 6), ("serve", 4), ("pour", 6)],
        "customer": [("idle", 4), ("walk", 8), ("sit", 4), ("sit_idle", 4),
                     ("sip", 4), ("wait_impatient", 4), ("talk", 4),
                     ("leave", 8)],
    }
    roster = [(C.BARISTA, "barista")] + [(s, "customer") for s in C.CUSTOMERS]
    if args.extras:
        roster += [(s, "customer") for s in
                   C.generate_roster(args.extras, args.extras_seed, ramps)]
    if args.fx_only:
        roster = []
    if args.only:
        roster = [(s, r) for s, r in roster if s.name == args.only]
        if not roster:
            print(f"no character named {args.only!r}")
            return 1

    atlas = {"frame_size": [args.target, args.target], "fps": FPS,
             "directions": list(DIRECTIONS), "characters": {}}
    total = 0
    for spec, role in roster:
        clip_specs = ROLE_CLIPS[role]
        sheet, meta, index, cols, rows = build_sheet(
            spec, clip_specs, ramps, args.target, args.factor)
        img = outdir / f"{spec.name}.png"
        sheet.save(img)
        n = sum(8 * f for _, f in clip_specs)
        total += n
        atlas["characters"][spec.name] = {
            "image": img.name, "role": role, "clips": meta,
            "sheet_size": [cols * args.target, rows * args.target],
        }
        print(f"  {spec.name:9s} {cols}x{rows} tiles, {n:3d} frames -> {img.name}")

        if args.gif:
            frames = [f for f in index if f["clip"] == "walk" and f["dir"] == "s"]
            imgs = [sheet.crop((f["x"], f["y"], f["x"] + f["w"], f["y"] + f["h"]))
                    .resize((args.target * 3, args.target * 3), Image.NEAREST)
                    for f in sorted(frames, key=lambda f: f["index"])]
            if imgs:
                bg = Image.new("RGBA", imgs[0].size, (30, 27, 36, 255))
                flat = [Image.alpha_composite(bg, im).convert("P") for im in imgs]
                flat[0].save(outdir / f"{spec.name}_walk.gif", save_all=True,
                             append_images=flat[1:], duration=int(1000 / FPS),
                             loop=0)

    if args.fx or args.fx_only:
        problems = FX.check_loops()
        for p in problems:
            print(f"  BLOCKER  {p}")
        if problems:
            return 1
        total += fx_sheets(ramps, args.target, args.factor, outdir, atlas)

    (outdir / "atlas.json").write_text(json.dumps(atlas, indent=2), encoding="utf-8")
    declared = {"idle", "walk", "carry_walk", "brew", "wipe", "serve", "pour",
                "sit", "sit_idle", "sip", "wait_impatient", "talk", "leave"}
    built = set(C.CLIPS)
    print(f"\n{total} frames across {len(roster)} characters -> {outdir}")
    missing = sorted(declared - built)
    print(f"clips built: {len(built & declared)}/{len(declared)} declared"
          + (f" ({', '.join(missing)} still unposed)" if missing else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
