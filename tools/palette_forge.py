#!/usr/bin/env python3
"""Generate and validate the locked palette from style_bible.yaml.

The palette is *computed*, not hand-picked. That matters for two reasons:

1. Perceptual spacing becomes provable. "No two entries collapse under
   quantization" is a checked property, not a hope.
2. The Ghibli warm-light/cool-shadow rule becomes a parameter rather than a
   thing an artist remembers to do. Shadows bend toward a cool anchor hue and
   highlights toward a warm one; that single rule carries most of the look.

Outputs GPL (Aseprite/GIMP), JSON, and a swatch sheet. Exits non-zero if any
constraint fails, so it can gate CI.

Usage:  python tools/palette_forge.py [--out palette] [--quiet]
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from oklab import (  # noqa: E402
    delta_e, gamut_clip, hue_delta, lch_to_lab, oklab_to_srgb255, srgb_to_oklab,
)

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Swatch:
    name: str
    ramp: str
    index: int
    hex: str
    rgb: tuple[int, int, int]
    L: float
    C: float
    h: float


def build_ramp(name: str, spec: dict, cfg: dict) -> list[Swatch]:
    """Expand one ramp spec into swatches, shadow -> highlight."""
    steps = spec["steps"]
    l_lo, l_hi = spec["lightness"]
    c_peak = spec["chroma"]
    base_h = spec["hue"]

    hs = cfg["hue_shift"]
    cool_anchor, warm_anchor = hs["cool_anchor"], hs["warm_anchor"]
    # Per-ramp overrides. Red-family ramps need a much weaker cool shift: bending
    # a red shadow toward violet produces plum, which reads as bruising on skin.
    cool_amt = spec.get("cool_amount", hs["cool_amount"])
    warm_amt = spec.get("warm_amount", hs["warm_amount"])
    falloff = spec.get("chroma_falloff", cfg["chroma_falloff"])

    out = []
    for i in range(steps):
        t = i / (steps - 1) if steps > 1 else 0.5

        L = l_lo + (l_hi - l_lo) * t

        # Chroma peaks mid-ramp and falls toward both ends: highlights wash out
        # toward the light, shadows desaturate into the shadow hue.
        C = c_peak * (1.0 - falloff * (2.0 * t - 1.0) ** 2)

        # The painterly rule. Below mid, bend toward cool; above, toward warm.
        # Anchored so that t=0.5 sits exactly on the base hue.
        if t < 0.5:
            h = base_h + hue_delta(base_h, cool_anchor) * cool_amt * (1 - 2 * t)
        else:
            h = base_h + hue_delta(base_h, warm_anchor) * warm_amt * (2 * t - 1)
        h %= 360.0

        L, C, h = gamut_clip(L, C, h)
        rgb = oklab_to_srgb255(*lch_to_lab(L, C, h))
        out.append(Swatch(
            name=f"{name}_{i}", ramp=name, index=i,
            hex="#%02x%02x%02x" % rgb, rgb=rgb,
            L=round(L, 4), C=round(C, 4), h=round(h, 2),
        ))
    return out


def build_spot(name: str, spec: dict) -> Swatch:
    L, C, h = gamut_clip(spec["lightness"], spec["chroma"], spec["hue"])
    rgb = oklab_to_srgb255(*lch_to_lab(L, C, h))
    return Swatch(name=name, ramp="spot", index=0, hex="#%02x%02x%02x" % rgb,
                  rgb=rgb, L=round(L, 4), C=round(C, 4), h=round(h, 2))


def forge(bible: dict) -> list[Swatch]:
    cfg = bible["palette"]
    swatches: list[Swatch] = []
    for name, spec in cfg["ramps"].items():
        swatches += build_ramp(name, spec, cfg)
    for name, spec in cfg["spot"].items():
        swatches.append(build_spot(name, spec))
    return swatches


# --- validation -------------------------------------------------------------

def validate(swatches: list[Swatch], bible: dict) -> list[str]:
    cfg = bible["palette"]
    con = cfg["constraints"]
    errs: list[str] = []

    if len(swatches) != cfg["total_colours"]:
        errs.append(f"count: {len(swatches)} != {cfg['total_colours']}")

    # Perceptual separation. The whole point of working in OKLab.
    labs = {s.name: srgb_to_oklab(s.rgb) for s in swatches}
    worst, worst_pair = 1e9, None
    names = [s.name for s in swatches]
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            d = delta_e(labs[a], labs[b])
            if d < worst:
                worst, worst_pair = d, (a, b)
    if worst < cfg["min_delta_e"]:
        errs.append(f"min deltaE {worst:.4f} < {cfg['min_delta_e']} "
                    f"({worst_pair[0]} vs {worst_pair[1]})")

    # Ramps must be monotonic in lightness, or shading reads as noise.
    by_ramp: dict[str, list[Swatch]] = {}
    for s in swatches:
        if s.ramp != "spot":
            by_ramp.setdefault(s.ramp, []).append(s)

    warm = cfg["hue_shift"]["warm_anchor"]
    for ramp, items in by_ramp.items():
        items.sort(key=lambda s: s.index)
        Ls = [s.L for s in items]
        if any(b <= a for a, b in zip(Ls, Ls[1:])):
            errs.append(f"ramp {ramp}: lightness not strictly increasing: {Ls}")

        # The Ghibli rule, checked: the highlight end must sit warmer than the
        # shadow end, measured as angular distance from the warm anchor.
        shadow_gap = abs(hue_delta(items[0].h, warm))
        light_gap = abs(hue_delta(items[-1].h, warm))
        if light_gap >= shadow_gap:
            errs.append(
                f"ramp {ramp}: highlight not warmer than shadow (shadow "
                f"{shadow_gap:.1f}deg from warm anchor, highlight {light_gap:.1f}deg)")

    lo = min(s.L for s in swatches)
    hi = max(s.L for s in swatches)
    if con["no_pure_black"] and lo < con["min_lightness"]:
        errs.append(f"darkest L {lo:.3f} below min_lightness {con['min_lightness']}")
    if con["no_pure_white"] and hi > con["max_lightness"]:
        errs.append(f"lightest L {hi:.3f} above max_lightness {con['max_lightness']}")

    if any(s.rgb == (0, 0, 0) for s in swatches):
        errs.append("pure black present")
    if any(s.rgb == (255, 255, 255) for s in swatches):
        errs.append("pure white present")

    return errs


# --- output -----------------------------------------------------------------

def write_gpl(swatches: list[Swatch], path: Path) -> None:
    lines = ["GIMP Palette", "Name: Cozy Coffee Iso - Ghibli 16bit", "Columns: 5", "#"]
    for s in swatches:
        r, g, b = s.rgb
        lines.append(f"{r:3d} {g:3d} {b:3d}\t{s.name}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_swatch_sheet(swatches: list[Swatch], bible: dict, path: Path,
                       cell: int = 72) -> None:
    from PIL import Image, ImageDraw

    ramps = list(bible["palette"]["ramps"]) + ["spot"]
    grouped = {r: [s for s in swatches if s.ramp == r] for r in ramps}
    for r in grouped:
        grouped[r].sort(key=lambda s: s.index)

    rows, cols = len(ramps), max(len(v) for v in grouped.values())
    img = Image.new("RGB", (cols * cell, rows * cell), (24, 22, 28))
    d = ImageDraw.Draw(img)

    for y, ramp in enumerate(ramps):
        for x, s in enumerate(grouped[ramp]):
            d.rectangle([x * cell, y * cell, (x + 1) * cell - 1, (y + 1) * cell - 1],
                        fill=s.rgb)
            label = s.name if ramp == "spot" else str(s.index)
            ink = (255, 255, 255) if s.L < 0.6 else (20, 18, 24)
            d.text((x * cell + 5, y * cell + 5), ramp, fill=ink)
            d.text((x * cell + 5, y * cell + 17), label, fill=ink)
            d.text((x * cell + 5, y * cell + cell - 14), s.hex, fill=ink)
    img.save(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bible", default=str(ROOT / "style_bible.yaml"))
    ap.add_argument("--out", default=str(ROOT / "palette"))
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    bible = yaml.safe_load(Path(args.bible).read_text(encoding="utf-8"))
    swatches = forge(bible)
    errs = validate(swatches, bible)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "palette.json").write_text(
        json.dumps([asdict(s) for s in swatches], indent=2), encoding="utf-8")
    write_gpl(swatches, out / "palette.gpl")
    write_swatch_sheet(swatches, bible, out / "palette.png")

    if not args.quiet:
        for ramp in list(bible["palette"]["ramps"]) + ["spot"]:
            items = [s for s in swatches if s.ramp == ramp]
            print(f"{ramp:12s} " + " ".join(s.hex for s in items))
        print(f"\n{len(swatches)} colours -> {out}/")

    if errs:
        print("\nFAIL:", file=sys.stderr)
        for e in errs:
            print("  -", e, file=sys.stderr)
        return 1
    if not args.quiet:
        print("all constraints pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
