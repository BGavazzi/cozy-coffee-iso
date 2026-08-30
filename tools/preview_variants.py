#!/usr/bin/env python3
"""Proof sheet for the time-of-day palettes: the same room, five ways.

    python tools/preview_variants.py            # -> proof/variants.png
    python tools/preview_variants.py --scale 1

Two panels, because the interesting claim needs both halves to be believed.

The room panel is the result. Every frame is the SAME render -- one 924x580
composition from `render_room.py`, pixel for pixel -- passed through nothing
but a 40-entry lookup. Nothing was re-rendered, re-lit or re-quantized, so any
difference visible between two frames is entirely a difference between two
palettes. That is a stronger statement than a set of re-renders would make,
where a changed light rig could be doing the work.

The ramp panel is the cause, and it is the one that catches a bad variant.
A transform that looks plausible as numbers can still crush a ramp's interior
-- the reason `palette_forge._relight` shifts and squeezes about each ramp's
midpoint instead of pulling both ends by a fixed delta, which compressed
`cream` (range 0.25) by 44% while barely touching `wood` (0.60). Ramps drawn
as strips make that failure obvious: the steps bunch up.

The room render is deliberately NOT one of the 755 library assets. It is a
composition at a different size from a different producer, so it exercises the
table on input the swap has never seen, and it is checked for exactness here
like everything else.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import palette_forge as PF  # noqa: E402
import palette_swap as PS  # noqa: E402
from render_room import BACKDROP  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ROOM = ROOT / "proof" / "shop.png"

BG = (28, 26, 32)
LABEL = (196, 190, 200)
DIM = (120, 116, 128)

SWATCH = 22
STRIP_GAP = 3


def remap(img, table: dict):
    """The same lookup `palette_swap.remap_image` applies, in memory."""
    from PIL import Image
    out = []
    for r, g, b, a in img.getdata():
        if not a:
            out.append((0, 0, 0, 0))
            continue
        m = table.get((r, g, b))
        out.append((*(m if m else (r, g, b)), a))
    im = Image.new("RGBA", img.size)
    im.putdata(out)
    return im


def ramps_of(bible: dict, variant: str | None) -> dict:
    """Ordered ramp -> [rgb], spot colours kept together under one key."""
    out: dict = {}
    for sw in PF.forge(bible, variant):
        out.setdefault(sw.ramp, []).append(sw.rgb)
    return out


def build(scale: int = 1) -> Path:
    from PIL import Image, ImageDraw

    bible = PS.load_bible()
    variants = list(bible["palette"].get("variants", {}))
    if not ROOM.exists():
        raise SystemExit(f"{ROOM} not found -- run tools/render_room.py first")

    room = Image.open(ROOM).convert("RGBA")
    frames = [("base", room)]
    problems = []
    for v in variants:
        table = PS.swap_table(bible, v)
        swapped = remap(room, table)
        allowed = {sw.rgb for sw in PF.forge(bible, v)}
        # BACKDROP is the surround `render_room` flattens onto and is not a
        # palette entry, so the lookup correctly passes it through untouched --
        # it appears here as 41% of the frame and would otherwise read as a
        # leak. Excluding it is the whole exemption; anything else off-palette
        # is a real one.
        seen = {p[:3] for p in swapped.getdata() if p[3]} - {BACKDROP}
        if seen - allowed:
            problems.append(f"{v}: room render has {len(seen - allowed)} "
                            f"colour(s) off the variant palette")
        frames.append((v, swapped))

    if scale != 1:
        frames = [(n, im.resize((im.width * scale, im.height * scale),
                                Image.Resampling.NEAREST)) for n, im in frames]

    fw, fh = frames[0][1].size
    pad, gap, label_h = 16, 10, 16
    cols = 2
    rows = (len(frames) + cols - 1) // cols

    ramp_names = list(ramps_of(bible, None))
    strip_h = SWATCH + STRIP_GAP
    ramp_block = len(frames) * strip_h + label_h + 8
    ramp_panel_h = len(ramp_names) * ramp_block + label_h + pad

    sheet_w = pad * 2 + cols * fw + (cols - 1) * gap
    sheet_h = (pad + label_h + rows * (fh + label_h + gap) + pad
               + ramp_panel_h + pad)
    sheet = Image.new("RGBA", (sheet_w, sheet_h), (*BG, 255))
    d = ImageDraw.Draw(sheet)

    d.text((pad, pad - 4),
           "one render, five palettes -- nothing below was re-rendered, only "
           "looked up through a 40-entry table",
           fill=LABEL)

    y = pad + label_h
    for i, (name, im) in enumerate(frames):
        cx = pad + (i % cols) * (fw + gap)
        cy = y + (i // cols) * (fh + label_h + gap)
        sheet.alpha_composite(im, (cx, cy))
        spec = bible["palette"].get("variants", {}).get(name, {})
        note = " ".join(str(spec.get("note", "")).split())
        d.text((cx, cy + im.height + 2),
               name if not note else f"{name}  -  {note}", fill=DIM)

    y = y + rows * (fh + label_h + gap) + pad
    d.text((pad, y), "each ramp under each palette -- steps that bunch up "
                     "mean the transform crushed that ramp's interior",
           fill=LABEL)
    y += label_h + 4

    for rname in ramp_names:
        d.text((pad, y), rname, fill=LABEL)
        y += label_h
        for vname, _ in frames:
            cols_rgb = ramps_of(bible, None if vname == "base" else vname)[rname]
            x = pad + 90
            for rgb in cols_rgb:
                d.rectangle([x, y, x + SWATCH - 1, y + SWATCH - 1], fill=rgb)
                x += SWATCH
            d.text((pad + 4, y + 4), vname, fill=DIM)
            y += strip_h
        y += 8

    out = ROOT / "proof" / "variants.png"
    sheet.convert("RGB").save(out)
    for p in problems:
        print(f"  BLOCKER  {p}", file=sys.stderr)
    print(f"{len(frames)} palettes over one {fw}x{fh} render; "
          f"{len(ramp_names)} ramps compared")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=int, default=1,
                    help="nearest-neighbour zoom on the room frames")
    args = ap.parse_args()
    print(build(args.scale))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
