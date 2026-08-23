#!/usr/bin/env python3
"""Batch review queue: the interface humans critique the factory through.

The factory generates at volume, so critique has to happen at volume too. This
builds a contact sheet of a whole batch with automated findings already
annotated, plus a verdicts file for human judgement.

The division is deliberate:

  automated tier  - spec violations. Cheap, deterministic, exhaustive.
                    Palette, alpha, grid, ramp coherence, silhouette.
  human tier      - does it look good. Not automatable, and the whole point.

And the loop is a **ratchet**. Every human rejection carries a reason. Reasons
that recur are candidates for promotion into the automated tier, which means
human review volume falls as the factory matures. `--stats` reports which
reasons are recurring hardest, so the next check to write is never a guess.

    python tools/review_queue.py build "sprites/*.png"   # -> review/sheet.png
    python tools/review_queue.py stats                   # -> automation candidates
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
from art_review import load_palette, review  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
REVIEW = ROOT / "review"

BADGE = {"blocker": (206, 92, 106), "warning": (216, 181, 1), "note": (95, 140, 171)}


def check_direction_set(records) -> list[str]:
    """Cross-sprite check: is the key light consistent across a direction set?

    Written *because* human critique caught it. The first batch rotated the
    camera with a world-fixed light, so the lit face drifted around the object
    between directions -- obvious to a person scanning a contact sheet, invisible
    to any per-sprite check, since each frame is individually valid.

    This is the ratchet working: a recurring human rejection becomes a cheap
    automated check, and never needs a human again -- except this one still
    needs one, and the reason is worth recording so nobody re-fixes the bug
    that isn't there.

    Run against the 22-object lifted library, this fires on 19 of 22 --
    `mesh.rasterize()` was re-read line by line to check: `light =
    camera_light(cam)` is called fresh inside `rasterize()`, and
    `render_batch.render_sprite()` builds a fresh `DimetricCamera(azimuth)`
    per direction, so the key genuinely is re-resolved into world space per
    azimuth. The world-fixed-light bug this check was built for is not back.

    The three objects that DO pass -- kettle, candle, french_press -- are the
    three closest to a body of revolution: round in plan, so their lit region
    barely moves in screen space as they turn. Every failure inspected by eye
    (wall_clock, picture_frame) has an off-axis bright material patch instead
    -- a clock face, a photo inset -- whose position on screen moves with
    azimuth for a completely different reason than the key light does. "top
    20% brightest pixels" cannot tell a specular highlight apart from a
    patch of pale albedo, and most objects in a café have one.

    Tried and discarded: restricting the brightest-pixel pool to each frame's
    dominant palette ramp before measuring, to filter out cross-material
    jumps. Measured before/after on all 22 -- it fixed 2 (teapot, roughly
    cutting_board) and broke a clean pass (candle, 3.4x16.2 vs the original
    5.1x3.9), because narrowing the pool made the centroid noisier than the
    cross-material signal it was removing. Not shipped. A real fix needs the
    raw per-pixel material id from `rasterize()`, not the quantized PNG this
    check only ever sees -- `review_queue.py` doesn't have that buffer today.

    Left firing as a regression guard on the three round objects it can
    actually speak to; treat a "drifts" verdict on anything else as an
    albedo-shape question first, a lighting-bug question only if a
    rotationally-symmetric object starts failing too.
    """
    from art_review import srgb_to_oklab

    groups: dict[str, list] = {}
    for r in records:
        stem = Path(r["file"]).stem
        asset = stem.rsplit("_dir", 1)[0] if "_dir" in stem else stem
        groups.setdefault(asset, []).append(r)

    out = []
    for asset, items in groups.items():
        if len(items) < 4:
            continue
        offsets = []
        for r in items:
            img = Image.open(r["file"]).convert("RGBA")
            w, h = img.size
            px = list(getattr(img, "get_flattened_data", img.getdata)())
            lit = [(i % w, i // w, srgb_to_oklab(p[:3])[0])
                   for i, p in enumerate(px) if p[3] == 255]
            if len(lit) < 40:
                continue
            lit.sort(key=lambda t: -t[2])
            top = lit[:max(8, len(lit) // 5)]
            offsets.append((sum(t[0] for t in top) / len(top) - sum(t[0] for t in lit) / len(lit),
                            sum(t[1] for t in top) / len(top) - sum(t[1] for t in lit) / len(lit)))
        if len(offsets) < 4:
            continue
        spread_x = max(o[0] for o in offsets) - min(o[0] for o in offsets)
        spread_y = max(o[1] for o in offsets) - min(o[1] for o in offsets)
        if spread_x > 6.0 or spread_y > 6.0:
            out.append(
                f"{asset}: brightest-region centroid drifts across the direction "
                f"set (spread {spread_x:.1f}x{spread_y:.1f}px). Re-verify "
                f"`camera_light()` is called fresh per azimuth before assuming a "
                f"lighting bug -- as of this check's last audit it was, and the "
                f"drift on most objects is an off-axis bright material patch "
                f"(a face, a photo, a lid) moving in screen space, not the key.")
        else:
            out.append(f"{asset}: key light consistent across {len(offsets)} "
                       f"directions (spread {spread_x:.1f}x{spread_y:.1f}px) [ok]")
    return out


def build(patterns: list[str], cols: int, scale: int) -> int:
    paths: list[Path] = []
    for pat in patterns:
        paths += sorted(Path().glob(pat)) or ([Path(pat)] if Path(pat).exists() else [])
    if not paths:
        print("no images matched", file=sys.stderr)
        return 1

    by_rgb, ramps, entries = load_palette()
    records = []
    for p in paths:
        findings = review(p, by_rgb, ramps, entries)
        worst = min((f["severity"] for f in findings),
                    key=lambda s: ("blocker", "warning", "note").index(s),
                    default=None)
        records.append({"file": str(p), "auto": findings, "worst": worst,
                        "verdict": None, "reason": None})

    # --- contact sheet
    thumbs = [Image.open(r["file"]).convert("RGBA") for r in records]
    tw = max(t.width for t in thumbs) * scale
    th = max(t.height for t in thumbs) * scale
    pad, label = 10, 34
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (tw + pad) + pad,
                              rows * (th + label + pad) + pad), (20, 18, 24))
    d = ImageDraw.Draw(sheet)

    for i, (rec, t) in enumerate(zip(records, thumbs)):
        cx = pad + (i % cols) * (tw + pad)
        cy = pad + (i // cols) * (th + label + pad)
        d.rectangle([cx, cy, cx + tw - 1, cy + th - 1], fill=(34, 30, 40))
        big = t.resize((tw, th), Image.NEAREST)
        sheet.paste(big, (cx, cy), big)
        d.text((cx + 3, cy + th + 3), Path(rec["file"]).stem[:24], fill=(210, 205, 215))
        if rec["worst"]:
            counts = Counter(f["severity"] for f in rec["auto"])
            txt = " ".join(f"{k[:1].upper()}{v}" for k, v in counts.items())
            d.text((cx + 3, cy + th + 17), txt, fill=BADGE[rec["worst"]])
            d.rectangle([cx, cy, cx + tw - 1, cy + th - 1],
                        outline=BADGE[rec["worst"]], width=2)
        else:
            d.text((cx + 3, cy + th + 17), "auto-clean", fill=(120, 170, 130))

    REVIEW.mkdir(exist_ok=True)
    sheet.save(REVIEW / "sheet.png")

    with (REVIEW / "verdicts.jsonl").open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")

    for line in check_direction_set(records):
        print(f"  set-check: {line}")
    print()

    clean = sum(1 for r in records if r["worst"] is None)
    blocked = sum(1 for r in records if r["worst"] == "blocker")
    print(f"{len(records)} sprites reviewed")
    print(f"  auto-clean          {clean:3d}  -> go to human critique")
    print(f"  auto-blocked        {blocked:3d}  -> fix before a human looks")
    print(f"  warnings/notes only {len(records) - clean - blocked:3d}")
    print(f"\nwrote {REVIEW}/sheet.png and {REVIEW}/verdicts.jsonl")
    print('Fill in "verdict" (accept|reject) and "reason" on each line, then run stats.')
    return 0


def stats() -> int:
    path = REVIEW / "verdicts.jsonl"
    if not path.exists():
        print("no verdicts yet; run build first", file=sys.stderr)
        return 1
    recs = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    judged = [r for r in recs if r.get("verdict")]
    if not judged:
        print(f"{len(recs)} sprites queued, none judged yet")
        return 0

    rejected = [r for r in judged if r["verdict"] == "reject"]
    reasons = Counter(r["reason"] for r in rejected if r.get("reason"))
    print(f"judged {len(judged)}/{len(recs)}   accepted {len(judged)-len(rejected)}   "
          f"rejected {len(rejected)}")

    if reasons:
        print("\nrecurring rejection reasons (automation candidates):")
        for reason, n in reasons.most_common(10):
            share = 100.0 * n / len(rejected)
            flag = "  <-- worth automating" if n >= 3 else ""
            print(f"  {n:3d}  ({share:4.1f}%)  {reason}{flag}")

    # A human rejecting sprites the automated tier called clean is the signal
    # that the tier is missing a check.
    missed = [r for r in rejected if r["worst"] is None]
    if missed:
        print(f"\n{len(missed)} rejected sprites passed every automated check.")
        print("  That gap is exactly what the next check should cover.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("patterns", nargs="+")
    b.add_argument("--cols", type=int, default=4)
    b.add_argument("--scale", type=int, default=3)
    sub.add_parser("stats")
    args = ap.parse_args()
    return build(args.patterns, args.cols, args.scale) if args.cmd == "build" else stats()


if __name__ == "__main__":
    raise SystemExit(main())
