#!/usr/bin/env python3
"""Contact sheet and GIFs for animation review.

Stage 9 for motion. A sprite sheet is the machine's format and is close to
useless for judging animation: timing, weight and foot-slide are invisible in a
grid of stills. So this emits both -- a strip per clip for reading poses side by
side, and a looping GIF per clip for reading motion.

    python tools/preview_clips.py [--who barista] [--dir 0]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import character as C  # noqa: E402
import fx as FXM  # noqa: E402
from animate import fit, render_frame  # noqa: E402
from pixelize import load_palette  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BG = (30, 27, 36)
LABEL = (214, 208, 218)


def to_img(px, target, scale, bg=BG):
    img = Image.new("RGB", (target, target), bg)
    img.putdata([c if c is not None else bg for c in px])
    return img.resize((target * scale, target * scale), Image.NEAREST)


def foot_slide(spec, clip, frames):
    """How far the planted foot drifts across the cycle, in world units.

    The classic locomotion defect: a walk whose feet skate because the stride
    does not match the distance travelled. In a sprite pipeline the character is
    moved by the game, not by the clip, so what matters is that the two contact
    feet trade off symmetrically -- an asymmetric cycle limps.
    """
    lows = []
    for f in range(frames):
        ph = f / frames
        pose = C.CLIPS[clip](ph)
        lows.append((pose.leg_l, pose.leg_r))
    fwd = [a for a, _ in lows]
    back = [b for _, b in lows]
    # A symmetric gait has leg_r equal to leg_l shifted by half a cycle.
    half = frames // 2
    if half == 0:
        return 0.0
    err = max(abs(fwd[i] + back[i]) for i in range(frames))
    shift = max(abs(fwd[i] - back[(i + half) % frames]) for i in range(frames))
    return max(err, shift)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--who", default="barista")
    ap.add_argument("--dir", type=int, default=0, help="azimuth index 0-7")
    ap.add_argument("--target", type=int, default=48)
    ap.add_argument("--factor", type=int, default=3)
    ap.add_argument("--scale", type=int, default=2)
    args = ap.parse_args()

    ramps = load_palette()
    roster = {s.name: s for s in C.ROSTER}
    if args.who not in roster:
        print(f"unknown character {args.who!r}; have {', '.join(roster)}")
        return 1
    spec = roster[args.who]

    clip_specs = [("idle", 4), ("walk", 8), ("carry_walk", 8), ("sit", 4),
                  ("sit_idle", 4), ("sip", 4), ("wave", 4), ("serve", 4),
                  ("wipe", 6), ("brew", 6), ("pour", 6), ("talk", 4),
                  ("wait_impatient", 4), ("leave", 8)]
    span, centre, anchors = fit(spec, clip_specs)
    az = 45.0 + args.dir * 45.0

    t, sc = args.target, args.scale
    cell = t * sc
    cols = max(f for _, f in clip_specs)
    pad, label_h = 6, 14
    sheet = Image.new("RGB", (110 + cols * (cell + pad) + pad,
                              len(clip_specs) * (cell + pad) + pad), (18, 16, 22))
    d = ImageDraw.Draw(sheet)

    gifdir = ROOT / "proof" / "clips"
    gifdir.mkdir(parents=True, exist_ok=True)

    print(f"{args.who}, direction {args.dir} (azimuth {az:.0f})")
    for r, (name, frames) in enumerate(clip_specs):
        y = pad + r * (cell + pad)
        d.text((6, y + cell // 2 - 4), f"{name}", fill=LABEL)
        d.text((6, y + cell // 2 + 6), f"{frames}f", fill=(140, 136, 148))
        imgs = []
        for f in range(frames):
            ph = f / frames
            mesh = C.build(spec, pose=C.CLIPS[name](ph),
                           seated=C.is_seated(name, ph))
            px = render_frame(mesh, az, ramps, t, args.factor,
                              centre=centre, span=span)
            img = to_img(px, t, sc)
            sheet.paste(img, (110 + f * (cell + pad), y))
            imgs.append(img.convert("P", palette=Image.ADAPTIVE))
        imgs[0].save(gifdir / f"{args.who}_{name}.gif", save_all=True,
                     append_images=imgs[1:], duration=int(1000 / 12), loop=0)
        slide = foot_slide(spec, name, frames)
        flag = "  <-- asymmetric gait" if name in ("walk", "leave") and slide > 1e-6 else ""
        print(f"  {name:15s} {frames}f  gait asymmetry {slide:6.2f} deg{flag}")

    out = ROOT / "proof" / f"clips_{args.who}.png"
    sheet.save(out)
    print(f"\nwrote {out}")
    print(f"wrote {len(clip_specs)} GIFs to {gifdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
