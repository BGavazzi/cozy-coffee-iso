#!/usr/bin/env python3
"""Contact sheet for `out/ui/` -- generated icons and drawn chrome together.

The UI category is the only one in this repo whose assets come from two
different producers (`ui_forge.py` generates, `ui_chrome.py` draws), and the
whole reason the split exists is a difference the checks cannot see. So the
preview has to show them side by side and labelled by producer, because
"which of these came out right" is a question only an eye answers.

    python tools/preview_ui.py                 # -> out/ui/_preview.png
    python tools/preview_ui.py --scale 4

The second panel is the part worth looking at hardest: every nine-slice
piece rendered at its authored size and again expanded, so the insets are
*shown working* rather than asserted in a JSON file. A frame that smears
when stretched fails here visibly, which is the only kind of failure this
particular defect has.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

ROOT = Path(__file__).resolve().parent.parent
UI_DIR = ROOT / "out" / "ui"

BG = (28, 26, 32)
LABEL = (196, 190, 200)
DIM = (120, 116, 128)


def _load(path: Path):
    from PIL import Image
    return Image.open(path).convert("RGBA")


def _nearest(img, scale: int):
    from PIL import Image
    return img.resize((img.width * scale, img.height * scale),
                      Image.Resampling.NEAREST)


def _expanded(name: str, insets, out_w: int, out_h: int):
    """Run the real expander over the real PNG, not a mock of either."""
    from PIL import Image
    from ui_chrome import expand
    img = _load(UI_DIR / f"{name}.png")
    px = [None if p[3] < 128 else (p[0], p[1], p[2]) for p in img.getdata()]
    big = expand(px, img.width, img.height, insets, out_w, out_h)
    out = Image.new("RGBA", (out_w, out_h), (0, 0, 0, 0))
    out.putdata([(p[0], p[1], p[2], 255) if p else (0, 0, 0, 0) for p in big])
    return out


def build(scale: int) -> Path:
    from PIL import Image, ImageDraw

    chrome: set[str] = set()
    nine_path = UI_DIR / "nine_slice.json"
    nine = json.loads(nine_path.read_text()) if nine_path.exists() else {}
    rep = UI_DIR / "chrome_report.json"
    if rep.exists():
        chrome = {r["name"] for r in json.loads(rep.read_text())}

    icons = sorted(p for p in UI_DIR.glob("*.png")
                   if not p.name.startswith("_")
                   # `_concept` catches both the matted 1024px source and
                   # its `_raw` sibling; matching only the former let a
                   # 1024px image set the cell size and produced a 12404px
                   # sheet on the first run.
                   and "_concept" not in p.name)
    if not icons:
        raise SystemExit(f"no icons in {UI_DIR} -- run ui_forge.py / "
                         f"ui_chrome.py first")

    pad, gap, label_h = 16, 14, 14
    cell_w = max(_load(p).width for p in icons) * scale
    cell_h = max(_load(p).height for p in icons) * scale
    cols = 6
    rows = (len(icons) + cols - 1) // cols
    grid_h = rows * (cell_h + label_h + gap)

    demos = [(n, nine[n]) for n in sorted(nine)]
    demo_imgs = []
    for name, ins in demos:
        src = _load(UI_DIR / f"{name}.png")
        # Half again as wide and tall, which is enough to make a smear
        # obvious and small enough that every piece fits on one row.
        big = _expanded(name, ins, int(src.width * 1.7), int(src.height * 1.6))
        demo_imgs.append((name, _nearest(src, scale), _nearest(big, scale)))
    demo_h = (max((b.height for _, _, b in demo_imgs), default=0)
              + label_h + gap) if demo_imgs else 0
    demo_w = sum(a.width + b.width + gap * 2 for _, a, b in demo_imgs) + pad

    W = max(pad * 2 + cols * (cell_w + gap), demo_w + pad, 720)
    H = pad + label_h + grid_h + (pad + label_h + demo_h if demo_imgs else 0) + pad
    sheet = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(sheet)

    d.text((pad, pad - 4), "out/ui/  --  generated icons and drawn chrome",
           fill=LABEL)
    y = pad + label_h + 4
    for i, p in enumerate(icons):
        col, row = i % cols, i // cols
        x = pad + col * (cell_w + gap)
        yy = y + row * (cell_h + label_h + gap)
        img = _nearest(_load(p), scale)
        sheet.alpha_composite(img, (x + (cell_w - img.width) // 2,
                                    yy + (cell_h - img.height) // 2))
        # Two-tone label: the name in white, the producer dimmed after it.
        # Offsetting by a run of spaces does not work -- the default PIL font
        # is proportional, so the tags landed on top of the names.
        name = p.stem[3:]
        d.text((x, yy + cell_h + 2), name, fill=LABEL)
        d.text((x + d.textlength(name) + 5, yy + cell_h + 2),
               "drawn" if p.stem in chrome else "gen", fill=DIM)

    if demo_imgs:
        y2 = y + grid_h + pad
        d.text((pad, y2 - 4),
               "nine-slice: authored size, then expanded through "
               "expand() -- a smear here means the insets are wrong",
               fill=LABEL)
        x = pad
        y2 += label_h + 4
        for name, small, big in demo_imgs:
            sheet.alpha_composite(small, (x, y2))
            x += small.width + gap
            sheet.alpha_composite(big, (x, y2))
            d.text((x, y2 + big.height + 2), name[3:], fill=DIM)
            x += big.width + gap * 2

    out = UI_DIR / "_preview.png"
    sheet.convert("RGB").save(out)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=int, default=3,
                    help="nearest-neighbour zoom (default 3)")
    args = ap.parse_args()
    print(build(args.scale))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
