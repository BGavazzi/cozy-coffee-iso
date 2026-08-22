#!/usr/bin/env python3
"""Contact sheet for generated floor plans.

Top-down, not isometric, because that is how a plan is read. The isometric
render answers "does this look like a cafe"; a plan answers "could you work
in it", and those are different questions with different failure modes.

Each cell shows one plan: the walls with their glazing, the service run and
the strip of floor the queue stands on, the seating blocks, and -- shaded
underneath all of it -- the region a body-sized disc can actually reach from
the door. That last layer is the point of the sheet. Every other rule in
`floorplan.check_plan` compares rectangles and can be argued about by reading
the numbers; circulation is emergent, and the only honest way to review it is
to look at the floor that is left.

    python tools/preview_plans.py [--plans 6] [--seed 1]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import floorplan as F  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

BG = (18, 16, 22)
WALL = (196, 178, 158)
GLASS = (126, 190, 214)
WALK = (44, 48, 58)
DOOR = (232, 196, 120)
LABEL = (150, 145, 155)
TITLE = (226, 220, 214)

FILL = {
    "service": ((150, 104, 74), "counter"),
    "backbar": ((96, 72, 56), "back bar"),
    "queue": ((58, 62, 74), "queue"),
    "cafe": ((104, 138, 104), "cafe"),
    "lounge": ((166, 120, 138), "lounge"),
    "window_bar": ((92, 132, 156), "bar"),
}


def draw_plan(d: ImageDraw.ImageDraw, plan: F.Plan, ox: int, oy: int,
              px: float) -> None:
    """One plan at `px` pixels per tile, top-left at (ox, oy)."""
    def X(v):
        return ox + v * px

    def Y(v):
        return oy + v * px

    d.rectangle([X(0), Y(0), X(plan.w), Y(plan.d)], fill=(26, 24, 30))

    # Walkable floor first, so every zone drawn over it reads as an obstruction
    # or a destination against the space that is actually left.
    grid, nx, ny = F._walkable(plan)
    cells = F._reachable(grid, nx, ny,
                         (int(plan.door[0] / F.CELL), int(plan.door[1] / F.CELL)))
    for i, j in cells:
        d.rectangle([X(i * F.CELL), Y(j * F.CELL),
                     X((i + 1) * F.CELL), Y((j + 1) * F.CELL)], fill=WALK)

    for z in plan.zones:
        col, _ = FILL.get(z.kind, ((120, 120, 120), z.kind))
        if z.kind == "queue":
            # Outline only: the queue is empty floor that nothing may stand on,
            # and filling it would read as furniture.
            d.rectangle([X(z.x0), Y(z.y0), X(z.x1), Y(z.y1)], outline=col)
        else:
            d.rectangle([X(z.x0), Y(z.y0), X(z.x1), Y(z.y1)], fill=col)

    # Walls last, with the glazing drawn over them.
    t = max(2, int(px * 0.16))
    d.rectangle([X(0), Y(0), X(plan.w), Y(0) + t], fill=WALL)
    d.rectangle([X(0), Y(0), X(0) + t, Y(plan.d)], fill=WALL)
    for tile in plan.win_x:
        d.rectangle([X(tile), Y(0), X(tile + 1), Y(0) + t], fill=GLASS)
    for tile in plan.win_y:
        d.rectangle([X(0), Y(tile), X(0) + t, Y(tile + 1)], fill=GLASS)

    r = max(3, int(px * 0.22))
    d.ellipse([X(plan.door[0]) - r, Y(plan.door[1]) - r,
               X(plan.door[0]) + r, Y(plan.door[1]) + r], fill=DOOR)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plans", type=int, default=6)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--px", type=float, default=26.0)
    ap.add_argument("--cols", type=int, default=3)
    ap.add_argument("--out", default=str(ROOT / "proof" / "floorplans.png"))
    args = ap.parse_args()

    plans = [F.generate(args.seed + i) for i in range(args.plans)]
    cw = int(max(p.w for p in plans) * args.px) + 20
    ch = int(max(p.d for p in plans) * args.px) + 46
    cols = args.cols
    rows = (len(plans) + cols - 1) // cols
    legend = 26
    img = Image.new("RGB", (cols * cw + 12, rows * ch + 12 + legend), BG)
    d = ImageDraw.Draw(img)

    for k, plan in enumerate(plans):
        ox = 12 + (k % cols) * cw
        oy = 12 + (k // cols) * ch
        draw_plan(d, plan, ox, oy, args.px)
        bad = F.check_plan(plan)
        seat = sum(z.area for z in plan.zones
                   if z.kind in ("cafe", "lounge", "window_bar"))
        d.text((ox, oy + plan.d * args.px + 6),
               f"seed {args.seed + k}   {plan.w}x{plan.d}   "
               f"{seat:.0f} tiles seating in "
               f"{len([z for z in plan.zones if z.kind in ('cafe','lounge','window_bar')])}"
               f" blocks", fill=TITLE)
        d.text((ox, oy + plan.d * args.px + 18),
               "clean" if not bad else "FAILS: " + bad[0],
               fill=LABEL if not bad else (216, 120, 110))

    x = 14
    for kind, (col, name) in FILL.items():
        y = rows * ch + 14
        d.rectangle([x, y, x + 12, y + 10], fill=col)
        d.text((x + 16, y), name, fill=LABEL)
        x += 20 + 7 * len(name)
    d.rectangle([x, rows * ch + 14, x + 12, rows * ch + 24], fill=WALK)
    d.text((x + 16, rows * ch + 14), "reachable from the door", fill=LABEL)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    ok = sum(1 for p in plans if not F.check_plan(p))
    print(f"  {ok}/{len(plans)} plans clean")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
