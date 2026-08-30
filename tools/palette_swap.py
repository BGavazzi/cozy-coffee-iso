#!/usr/bin/env python3
"""Re-palette the whole library into a time-of-day variant. Exactly.

    python tools/palette_swap.py --list
    python tools/palette_swap.py night
    python tools/palette_swap.py --all --check

There is no re-quantization here, and that is the whole point.

Every image this factory produces is palette-exact -- that guarantee is
enforced at four separate stages and checked by `pixelize.audit`, `ui_forge`,
`ui_chrome` and `manifest.check_ui`. So every pixel in `out/` is already
exactly one of the base palette's 40 swatches, which means it already carries
an identity: a ramp and an index. Swapping palettes is therefore a LOOKUP,
40 entries wide, and not an image operation at all.

That distinction is not pedantry. A nearest-colour re-quantization would be
lossy, order-dependent and unable to tell `wood_6` from `cream_3` (they sit
0.0354 apart, the closest pair in the palette). The lookup cannot make that
mistake, because it never compares colours -- it reads an identity the
producer already wrote and re-renders it under different generator parameters.

What the exactness buys, stated as checks
-----------------------------------------
`check_total`     every colour present in the library is in the table. An
                  unmapped pixel means something bypassed the palette, which
                  is a defect in that producer, not in this swap.
`check_injective` no two base colours share a variant colour. Two surfaces the
                  base palette kept apart must not merge, and `palette_forge`
                  checks this on the palette; this checks it on the table that
                  is actually applied.
`check_roundtrip` real assets survive base -> variant -> base byte-identically.
                  Injectivity says the table CAN be inverted; this says the
                  pixel path actually is lossless, alpha included. An earlier
                  version of this file checked instead that a base-to-base
                  table was the identity, which is identity by construction and
                  would have passed however wrong `remap_image` was.
`check_exact`     every written file is palette-exact in the TARGET palette.
                  Exhaustive, not sampled -- see the function for why the
                  sampled version was not worth keeping.

Alpha is carried through untouched. Every sprite here is 1-bit alpha by
construction and a variant has no opinion about silhouette.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))

import palette_forge as PF  # noqa: E402

# The directories the factory writes art into. `sprites/` is `animate.py`'s
# packed sheets and `out/sprites/` is the static prop factory -- two
# similarly-named outputs, which has cost a wrong path before, so both are
# named explicitly rather than globbed for.
SOURCES = (
    ("props", ROOT / "out" / "sprites"),
    ("ui", ROOT / "out" / "ui"),
    ("tiles", ROOT / "out" / "tiles"),
    ("anim", ROOT / "sprites"),
)


def is_asset(p: Path) -> bool:
    """Is this an asset, or something the factory left beside one?

    Three kinds of non-asset share these directories, and the first run of
    `--check` found all three at once by reporting 481,879 distinct colours in
    a library that should contain 40: `_`-prefixed previews, the 1024px
    `*_concept*` SDXL sources, and contact sheets. `package_godot.stage_ui`
    already excludes the first two by exactly this rule; sheets are added
    because `teapot_sheet.png` does not carry either marker and still is not an
    asset.

    With them excluded the library measures 755 PNGs, 40 distinct colours, all
    40 of them used and none off-palette -- which is the fact this whole file
    rests on, now measured rather than assumed.
    """
    return not (p.name.startswith("_") or "_concept" in p.name
                or p.name.endswith("_sheet.png"))


def load_bible() -> dict:
    return yaml.safe_load((ROOT / "style_bible.yaml").read_text(encoding="utf-8"))


def swap_table(bible: dict, variant: str) -> dict[tuple, tuple]:
    """base rgb -> variant rgb, keyed on identity rather than on colour.

    Both palettes are forged from the same spec in the same order, so swatch
    `i` of one is swatch `i` of the other by construction -- same ramp, same
    index, different generator parameters. Zipping them is the entire mapping,
    and it is why this cannot drift: there is no matching step to get wrong.
    """
    base = PF.forge(bible)
    var = PF.forge(bible, variant)
    if len(base) != len(var):
        raise SystemExit(f"variant {variant!r} produced {len(var)} swatches, "
                         f"base has {len(base)}")
    table = {}
    for b, v in zip(base, var):
        if (b.ramp, b.index) != (v.ramp, v.index):
            raise SystemExit(f"variant {variant!r} reordered the palette: "
                             f"{b.name} aligned with {v.name}")
        table[b.rgb] = v.rgb
    return table


def library_colours() -> tuple[set, int]:
    """Every distinct RGB in the factory's output, and how many files it took."""
    from PIL import Image
    seen: set = set()
    n = 0
    for _, root in SOURCES:
        if not root.exists():
            continue
        for p in sorted(root.rglob("*.png")):
            if not is_asset(p):
                continue
            n += 1
            with Image.open(p) as im:
                for px in im.convert("RGBA").getdata():
                    if px[3]:
                        seen.add(px[:3])
    return seen, n


def check_total(table: dict, colours: set) -> list[str]:
    unmapped = sorted(colours - set(table))
    if not unmapped:
        return []
    show = ", ".join("#%02x%02x%02x" % c for c in unmapped[:8])
    return [f"{len(unmapped)} colour(s) in the library are not in the base "
            f"palette, so no identity exists to swap: {show}"
            + (" ..." if len(unmapped) > 8 else "")]


def check_injective(table: dict, variant: str) -> list[str]:
    back: dict = {}
    for src, dst in table.items():
        back.setdefault(dst, []).append(src)
    merged = {d: s for d, s in back.items() if len(s) > 1}
    return [f"{variant}: {len(merged)} variant colour(s) are the destination of "
            f"more than one base colour -- surfaces the base palette kept apart "
            f"merge here"] if merged else []


def remap_image(src: Path, dst: Path, table: dict) -> tuple[int, int]:
    """Returns (pixels rewritten, pixels with no mapping)."""
    from PIL import Image
    with Image.open(src) as im:
        data = list(im.convert("RGBA").getdata())
        size = im.size
    out = []
    hit = miss = 0
    for r, g, b, a in data:
        if not a:
            out.append((0, 0, 0, 0))
            continue
        m = table.get((r, g, b))
        if m is None:
            miss += 1
            out.append((r, g, b, a))
        else:
            hit += 1
            out.append((m[0], m[1], m[2], a))
    img = Image.new("RGBA", size)
    img.putdata(out)
    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst)
    return hit, miss


def check_exact(path: Path, allowed: set) -> list[str]:
    """Palette-exact in the TARGET palette, on every written file.

    This began as a 12-file spot check using `pixelize.audit`, which measured
    1.6% of a claim made about 755 files. Set membership against the variant's
    40 swatches is the same question asked more cheaply, so it is now asked of
    everything: the exhaustive audit costs about eight seconds per variant.

    It is worth asking at all even though the table's destinations are variant
    swatches by construction. "By construction" is how the base palette was
    trusted before `pixelize.audit` existed, and the audit found real leaks.
    """
    from PIL import Image
    with Image.open(path) as im:
        px = {q[:3] for q in im.convert("RGBA").getdata() if q[3]}
    stray = px - allowed
    if stray:
        show = ", ".join("#%02x%02x%02x" % c for c in sorted(stray)[:4])
        return [f"{path.name}: {len(stray)} colour(s) off the variant "
                f"palette after swapping: {show}"]
    return []


def variant_ramps(bible: dict, variant: str) -> dict:
    """`pixelize.load_palette`'s shape, built from a variant's swatches.

    Spot colours are promoted to one-step ramps, exactly as `load_palette`
    does, because a spot colour with no ramp of its own is unaddressable -- the
    critique that found `lamp_glow` used on zero pixels. Reproduced here rather
    than imported because `load_palette` reads the base palette off disk and
    this needs the variant that is being built in memory.
    """
    out: dict = {}
    for sw in PF.forge(bible, variant):
        if sw.ramp == "spot":
            out[sw.name] = [sw.rgb]
        else:
            out.setdefault(sw.ramp, []).append(sw.rgb)
    return out


def swap(variant: str, bible: dict, out_root: Path, verify: bool = True) -> dict:
    table = swap_table(bible, variant)
    allowed = {sw.rgb for sw in PF.forge(bible, variant)}
    problems = check_injective(table, variant)

    written = hit = miss = audited = 0
    for label, root in SOURCES:
        if not root.exists():
            continue
        for p in sorted(root.rglob("*.png")):
            if not is_asset(p):
                continue
            dst = out_root / variant / label / p.relative_to(root)
            h, m = remap_image(p, dst, table)
            hit += h
            miss += m
            written += 1
            if verify:
                problems += check_exact(dst, allowed)
                audited += 1

    # Non-image metadata travels unchanged: a manifest describes geometry and
    # layout, neither of which a palette has any opinion about.
    for label, root in SOURCES:
        for name in ("manifest.json", "atlas.json", "tileset.json",
                     "nine_slice.json"):
            src = root / name
            if src.exists():
                dst = out_root / variant / label / name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)

    return {"variant": variant, "files": written, "pixels": hit,
            "unmapped": miss, "problems": problems,
            "verified": audited}


def check_roundtrip(bible: dict, variant: str, samples: list[Path]) -> list[str]:
    """base -> variant -> base recovers the original image, byte for byte.

    A table that is the identity when built from base to base proves nothing --
    it is identity by construction and would stay identity however wrong
    `remap_image` was. This runs real images through the real function and back
    through the inverted table, which is only lossless if the mapping is a
    bijection AND the pixel path preserves everything it is not supposed to
    touch, alpha included.

    Invertibility is not free: it holds exactly because no two base colours
    share a variant colour, which is what `check_injective` and
    `palette_forge.validate_variant` both assert on the palette. This is the
    same claim tested where it is actually used.
    """
    from PIL import Image
    table = swap_table(bible, variant)
    inverse = {v: k for k, v in table.items()}
    if len(inverse) != len(table):
        return [f"{variant}: table is not invertible, so no round trip exists"]

    out = []
    for src in samples:
        with Image.open(src) as im:
            original = list(im.convert("RGBA").getdata())
        there = [(0, 0, 0, 0) if not a else (*table.get((r, g, b), (r, g, b)), a)
                 for r, g, b, a in original]
        back = [(0, 0, 0, 0) if not a else (*inverse.get((r, g, b), (r, g, b)), a)
                for r, g, b, a in there]
        if back != original:
            differing = sum(1 for a, b in zip(back, original) if a != b)
            out.append(f"{variant}: {src.name} does not survive a base -> "
                       f"{variant} -> base round trip ({differing} px differ)")
    return out


def sample_assets(limit: int = 24) -> list[Path]:
    """A spread across producers, not the first N of one.

    A round trip that only ever sees prop sprites would miss a UI piece drawn
    from a spot colour, and the spot colours are precisely the entries a variant
    treats differently (`night` lifts them while everything else falls).
    """
    out: list[Path] = []
    per = max(1, limit // len(SOURCES))
    for _, root in SOURCES:
        if not root.exists():
            continue
        found = [p for p in sorted(root.rglob("*.png")) if is_asset(p)]
        out += found[:per]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("variant", nargs="?", default=None)
    ap.add_argument("--all", action="store_true", help="build every variant")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--check", action="store_true",
                    help="audit the library and the tables, build nothing")
    ap.add_argument("--out", default=str(ROOT / "out" / "variants"))
    args = ap.parse_args()

    bible = load_bible()
    variants = list(bible["palette"].get("variants", {}))

    if args.list:
        print(f"{len(variants)} variants declared in style_bible.yaml\n")
        for v in variants:
            spec = bible["palette"]["variants"][v]
            note = " ".join(str(spec.get("note", "")).split())
            print(f"  {v:<13} {note}")
        return 0

    if args.check:
        colours, files = library_colours()
        print(f"{files} PNG(s) across the library, {len(colours)} distinct "
              f"colours")
        problems = check_total(swap_table(bible, variants[0]), colours)
        samples = sample_assets()
        for v in variants:
            problems += check_injective(swap_table(bible, v), v)
            problems += check_roundtrip(bible, v, samples)
        if problems:
            for p in problems:
                print(f"  BLOCKER  {p}", file=sys.stderr)
            return 1
        print(f"  every library colour has an identity in the base palette, "
              f"and all {len(colours)} of them are palette entries")
        print(f"  all {len(variants)} tables injective")
        print(f"  {len(samples)} assets survive base -> variant -> base "
              f"byte-identically, for every variant")
        return 0

    todo = variants if args.all else ([args.variant] if args.variant else [])
    if not todo:
        raise SystemExit("name a variant, or pass --all / --list / --check")
    bad = [v for v in todo if v not in variants]
    if bad:
        raise SystemExit(f"unknown variant(s) {bad}; declared: {variants}")

    out_root = Path(args.out)
    reports = []
    for v in todo:
        rep = swap(v, bible, out_root, verify=True)
        reports.append(rep)
        print(f"{v:<13} {rep['files']:>4} files  {rep['pixels']:>9} px  "
              f"all {rep['verified']} palette-exact"
              + (f"  {rep['unmapped']} UNMAPPED" if rep["unmapped"] else ""))
        for p in rep["problems"]:
            print(f"  BLOCKER  {p}", file=sys.stderr)

    index = {r["variant"]: {"files": r["files"], "pixels": r["pixels"]}
             for r in reports}
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "variants.json").write_text(json.dumps(index, indent=2),
                                            encoding="utf-8")
    print(f"\n-> {out_root}")
    return 1 if any(r["problems"] or r["unmapped"] for r in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())
