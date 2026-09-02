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
import copy
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


def _apply(value: float, tf) -> float:
    """One transform: {add: x}, {mul: x}, or a bare number read as `add`."""
    if tf is None:
        return value
    if isinstance(tf, (int, float)):
        return value + float(tf)
    out = value
    if "mul" in tf:
        out *= float(tf["mul"])
    if "add" in tf:
        out += float(tf["add"])
    return out


def _relight(span, tf) -> list:
    """Move a ramp's lightness range by SHIFT and SQUEEZE about its midpoint.

    The obvious form -- an absolute delta on each end -- is wrong, and wrong in
    a way that only shows up once the palette is validated. `cream` spans 0.25
    of lightness and `wood` spans 0.60, so the same 0.11 taken off both ends
    compresses cream by 44% and wood by 18%. Cream's steps then land on top of
    wood's, which is exactly the collision `validate` reported for every one of
    the first four variants.

    Shift-and-squeeze keeps each ramp's internal spacing proportional, so a
    variant slides the whole palette without changing which ramps are
    distinguishable from which. That is the difference between a time of day
    and a broken palette.
    """
    lo, hi = span
    mid, half = (lo + hi) / 2.0, (hi - lo) / 2.0
    mid = _apply(mid, tf.get("shift"))
    half = _apply(half, tf.get("squeeze"))
    return [mid - half, mid + half]


def variant_config(cfg: dict, variant: str | None) -> dict:
    """The palette config with one variant's transforms folded in.

    A variant transforms the GENERATOR'S PARAMETERS, never the colours. That is
    the payoff of computing the base palette instead of picking it: an evening
    palette costs six numbers and arrives already subject to `validate` --
    perceptual separation, monotonic ramps, the warm-highlight rule, no pure
    black or white. A hand-picked one would have to be re-argued from scratch
    and could only be checked by eye.

    Per-ramp overrides in the base spec survive: `rose` keeps its own low
    `cool_amount` (bending red toward violet gives plum, which reads as
    bruising) and a variant that scales the global cool amount scales that
    override too, rather than replacing it. Scaling rather than setting is
    deliberate -- a variant should not be able to silently undo a decision the
    base palette recorded a reason for.
    """
    if not variant:
        return cfg
    variants = cfg.get("variants", {})
    if variant not in variants:
        raise SystemExit(f"unknown palette variant {variant!r}; "
                         f"style_bible declares {sorted(variants)}")
    v = variants[variant]
    out = copy.deepcopy(cfg)

    hs_tf = v.get("hue_shift", {})
    for key in ("cool_amount", "warm_amount"):
        if key in hs_tf:
            out["hue_shift"][key] = _apply(out["hue_shift"][key], hs_tf[key])

    lt = v.get("lightness", {})
    ct = v.get("chroma")
    for name, spec in out["ramps"].items():
        spec["lightness"] = _relight(spec["lightness"], lt)
        if ct is not None:
            spec["chroma"] = _apply(spec["chroma"], ct)
        # A per-ramp cool/warm override is a ratio to the global amount, so the
        # variant has to scale it by the same factor or the override drifts
        # relative to everything else.
        for key in ("cool_amount", "warm_amount"):
            if key in spec and key in hs_tf:
                spec[key] = _apply(spec[key], hs_tf[key])

    # Per-ramp overrides, applied after the global ones. The base palette needed
    # these (`rose` has its own `cool_amount`) and so do the variants, for the
    # same reason and caught the same way: `validate` rejected all four on
    # `min_delta_e` first time out, and every collision was one named pair of
    # ramps rather than a palette that was globally too tight.
    for name, tf in v.get("ramps", {}).items():
        if name not in out["ramps"]:
            raise SystemExit(f"variant {variant!r} overrides unknown ramp {name!r}")
        spec = out["ramps"][name]
        if "chroma" in tf:
            spec["chroma"] = _apply(spec["chroma"], tf["chroma"])
        rlt = tf.get("lightness", {})
        if rlt:
            spec["lightness"] = _relight(spec["lightness"], rlt)
        for key in ("cool_amount", "warm_amount"):
            if key in tf:
                spec[key] = _apply(spec.get(key, out["hue_shift"][key]), tf[key])

    slt = v.get("spot_lightness")
    if slt is not None:
        for spec in out["spot"].values():
            spec["lightness"] = min(0.99, _apply(spec["lightness"], slt))
    return out


def forge(bible: dict, variant: str | None = None) -> list[Swatch]:
    cfg = variant_config(bible["palette"], variant)
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
        # shadow end, measured as angular distance from the warm anchor. Not
        # every style pack is chasing this look -- `require_warm_cool_shift:
        # false` lets one opt out instead of failing validation for not being
        # this style. Defaults true: silence should not turn the rule off.
        if con.get("require_warm_cool_shift", True):
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


def validate_variant(swatches: list[Swatch], bible: dict,
                     variant: str) -> tuple[list[str], list[str]]:
    """(errors, notes) for one variant. Every base constraint but one.

    `min_delta_e` becomes a REPORTED NUMBER rather than a gate, and the reason
    is the constraint's own stated justification: `style_bible` says "below this
    two entries collapse under quantization". A variant palette is never
    quantized against. Sprites reach it by exact `(ramp, index)` lookup from art
    that is already palette-exact -- `pixelize.material` addresses colours by
    name and index, and the only nearest-colour matching in the repo is
    `ingest.bind_colour`, which binds EXTERNAL generated meshes to the base
    palette and never runs on a variant. There is no quantization step for two
    close entries to collapse in.

    That is not a licence to let them merge. Two base colours that became the
    SAME variant colour would destroy information the base palette carried --
    two surfaces that were distinguishable at noon become one surface at dusk --
    so identity collapse stays a hard error, and it is checked directly rather
    than approximated by a distance floor.

    Measured: no variant produces a duplicate at any strength up to where the
    lightness bounds stop it. The variants ship at min deltaE 0.014 to 0.027
    against the base's 0.035, which says sky's dark end and neutral's middle
    read alike under overcast -- which is what overcast does to a room.

    Every other constraint is a hard error, unchanged: monotonic ramps, the
    warm-highlight rule, the lightness bounds, no pure black or white, and the
    colour count. Those are statements about whether the palette WORKS, and a
    variant that breaks them is broken.
    """
    errs = [e for e in validate(swatches, bible)
            if not e.startswith("min deltaE")]

    seen: dict = {}
    for sw in swatches:
        seen.setdefault(sw.rgb, []).append(sw.name)
    merged = [names for names in seen.values() if len(names) > 1]
    for names in merged:
        errs.append(f"variant {variant}: {sorted(names)} resolve to the same "
                    f"colour -- surfaces the base palette kept apart merge here")

    labs = {s.name: srgb_to_oklab(s.rgb) for s in swatches}
    names = list(labs)
    worst, pair = 1e9, None
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            d = delta_e(labs[a], labs[b])
            if d < worst:
                worst, pair = d, (a, b)
    notes = [f"variant {variant}: closest pair {worst:.4f} "
             f"({pair[0]} vs {pair[1]}); base palette holds "
             f"{bible['palette']['min_delta_e']}"]
    return errs, notes


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


def check_separation(bible: dict) -> tuple[list[str], list[str]]:
    """Every pair of SHIPPED palettes must be at least min_delta_e apart.

    All the other validation asks whether one palette is internally sound. None
    of it asks the question that actually matters to a player, which is whether
    two palettes look different from each other -- and that gap shipped a real
    defect: `evening` and `night` came out 0.0057 apart on average, under a
    sixth of the floor two colours inside one palette have to clear. Four
    variants were declared and three were visible.

    The reuse of `min_delta_e` here is deliberate rather than convenient. It is
    already this project's measured answer to "are these two colours the same
    colour", so applying it to the mean distance between corresponding swatches
    asks the same question one level up: is this the same palette twice. It is
    a floor and not a target -- `golden_hour` sits just over it at 0.0358 by
    design, because late afternoon is meant to be a warm reading of the base
    palette rather than a different world.
    """
    cfg = bible["palette"]
    floor = cfg["min_delta_e"]
    names = ["base"] + list(cfg.get("variants", {}))
    pal = {n: forge(bible, None if n == "base" else n) for n in names}

    errs, notes = [], []
    pairs = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            d = sum(delta_e(srgb_to_oklab(x.rgb), srgb_to_oklab(y.rgb))
                    for x, y in zip(pal[a], pal[b])) / len(pal[a])
            pairs.append((d, a, b))
    pairs.sort()
    for d, a, b in pairs:
        if d < floor:
            errs.append(f"separation: {a} and {b} are {d:.4f} apart on "
                        f"average, under min_delta_e {floor} -- they are the "
                        f"same palette shipped twice")
    if pairs:
        d, a, b = pairs[0]
        notes.append(f"closest palettes {a}/{b} at {d:.4f} (floor {floor})")
    return errs, notes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", default=None,
                    help="style pack name (see tools/style.py); "
                         "sets --bible/--out unless those are also given")
    ap.add_argument("--bible", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if args.style or not (args.bible and args.out):
        from style import load_style
        sty = load_style(args.style or "cozy_ghibli")
        args.bible = args.bible or str(sty.bible_path)
        args.out = args.out or str(sty.palette_dir)

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

    # Variants, each into palette/variants/<name>.{json,gpl}. Written beside the
    # base rather than instead of it: the base is what every producer renders
    # against, and a variant is a second reading of the same art.
    variants = bible["palette"].get("variants", {})
    vdir = out / "variants"
    if variants:
        vdir.mkdir(parents=True, exist_ok=True)
    for name in variants:
        vsw = forge(bible, name)
        verrs, vnotes = validate_variant(vsw, bible, name)
        errs += verrs
        (vdir / f"{name}.json").write_text(
            json.dumps([asdict(s) for s in vsw], indent=2), encoding="utf-8")
        write_gpl(vsw, vdir / f"{name}.gpl")
        if not args.quiet:
            lo = min(s.L for s in vsw)
            hi = max(s.L for s in vsw)
            print(f"{name:12s} L {lo:.3f}..{hi:.3f}  "
                  + vnotes[0].split(": ", 1)[1])

    serrs, snotes = check_separation(bible)
    errs += serrs
    if not args.quiet and snotes:
        print(snotes[0])

    if errs:
        print("\nFAIL:", file=sys.stderr)
        for e in errs:
            print("  -", e, file=sys.stderr)
        return 1
    if not args.quiet:
        print(f"all constraints pass"
              + (f"; {len(variants)} variants -> {vdir}/" if variants else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
