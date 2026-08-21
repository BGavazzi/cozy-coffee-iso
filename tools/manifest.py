#!/usr/bin/env python3
"""Load, validate and budget the asset manifest.

Turns assets.yaml into the factory's work queue, and answers the question that
actually decides schedule: how many renders is this, really?

The answer is dominated by rotational symmetry. Eight azimuths is the worst case,
not the default -- a round table is identical from every angle, a square crate
repeats every 90 degrees. Declaring symmetry per asset is the single largest
saving available, and it is free.

    python tools/manifest.py                # summary + render budget
    python tools/manifest.py --queue 1      # work queue for priority tier 1
    python tools/manifest.py --check        # validate against the style bible
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

# How many of the 8 azimuths are visually distinct, per symmetry class.
DISTINCT_AZIMUTHS = {"radial": 1, "4fold": 2, "2fold": 4, "none": 8}

SECTIONS = ("tiles", "props", "characters", "fx", "ui")


def load(path: Path | None = None) -> dict:
    return yaml.safe_load((path or ROOT / "assets.yaml").read_text(encoding="utf-8"))


def entries(man: dict):
    for section in SECTIONS:
        for a in man.get(section, []) or []:
            yield section, a


def renders_for(section: str, a: dict) -> int:
    """Distinct sprites this asset needs: azimuths x frames x variants."""
    if section == "ui":
        return 1
    az = DISTINCT_AZIMUTHS[a.get("sym", "none")]
    frames = sum((a.get("clips") or {}).values()) or 1
    return az * frames * a.get("variants", 1)


def summarise(man: dict) -> None:
    by_section = Counter()
    by_cat = Counter()
    by_prio = defaultdict(lambda: [0, 0])
    renders_by_section = Counter()
    total_assets = total_renders = 0
    naive_renders = 0

    for section, a in entries(man):
        r = renders_for(section, a)
        by_section[section] += 1
        by_cat[a.get("cat", section)] += 1
        by_prio[a.get("prio", 3)][0] += 1
        by_prio[a.get("prio", 3)][1] += r
        renders_by_section[section] += r
        total_assets += 1
        total_renders += r
        if section != "ui":
            frames = sum((a.get("clips") or {}).values()) or 1
            naive_renders += 8 * frames * a.get("variants", 1)
        else:
            naive_renders += 1

    print(f"ASSET MANIFEST  -  {total_assets} distinct assets\n")
    print(f"  {'section':12s}{'assets':>8s}{'renders':>10s}")
    for s in SECTIONS:
        if by_section[s]:
            print(f"  {s:12s}{by_section[s]:8d}{renders_by_section[s]:10d}")
    print(f"  {'':12s}{'':->8s}{'':->10s}")
    print(f"  {'TOTAL':12s}{total_assets:8d}{total_renders:10d}")

    print("\n  by category")
    for cat, n in sorted(by_cat.items(), key=lambda kv: -kv[1]):
        print(f"    {cat:12s}{n:4d}")

    print("\n  by priority")
    labels = {1: "vertical slice", 2: "fills the room", 3: "variety / polish"}
    for prio in sorted(by_prio):
        n, r = by_prio[prio]
        print(f"    tier {prio}  {n:3d} assets  {r:6d} renders   {labels.get(prio, '')}")

    # Symmetry saving, broken out by section. Reported in aggregate it looks
    # small, but that is characters diluting it -- they legitimately need all 8
    # azimuths and dominate the total. The saving on static geometry is large.
    print("\n  symmetry saving")
    print(f"    {'section':12s}{'if all 8':>10s}{'actual':>9s}{'avoided':>9s}")
    for s in SECTIONS:
        if s == "ui" or not by_section[s]:
            continue
        naive = sum(8 * (sum((a.get('clips') or {}).values()) or 1) * a.get("variants", 1)
                    for sec, a in entries(man) if sec == s)
        act = renders_by_section[s]
        pct = 100 * (naive - act) / naive if naive else 0
        print(f"    {s:12s}{naive:10d}{act:9d}{naive-act:8d} ({pct:.0f}%)")

    static = sum(renders_by_section[s] for s in ("tiles", "props", "fx"))
    static_naive = sum(
        8 * (sum((a.get('clips') or {}).values()) or 1) * a.get("variants", 1)
        for s, a in entries(man) if s in ("tiles", "props", "fx"))
    print(f"    {'static only':12s}{static_naive:10d}{static:9d}"
          f"{static_naive-static:8d} ({100*(static_naive-static)/static_naive:.0f}%)")

    sym = Counter(a.get("sym", "none") for s, a in entries(man) if s != "ui")
    print("    " + ", ".join(f"{k}: {v}" for k, v in sym.most_common()))
    print(f"\n  characters are {100*renders_by_section['characters']/total_renders:.0f}% "
          f"of the render budget ({renders_by_section['characters']} of {total_renders}).")
    print("  Cutting a customer archetype saves more than every prop optimisation combined.")


def check(man: dict) -> int:
    """Validate the manifest against itself and the style bible."""
    bible = yaml.safe_load((ROOT / "style_bible.yaml").read_text(encoding="utf-8"))
    legal_ramps = set(bible["palette"]["ramps"]) | set(bible["palette"]["spot"])
    errs, warns = [], []

    seen = set()
    for section, a in entries(man):
        aid = a.get("id")
        if not aid:
            errs.append(f"{section}: entry with no id")
            continue
        if aid in seen:
            errs.append(f"duplicate id: {aid}")
        seen.add(aid)
        if section == "ui":
            continue
        if a.get("sym") not in DISTINCT_AZIMUTHS:
            errs.append(f"{aid}: bad sym {a.get('sym')!r}")
        for m in a.get("mat", []):
            if m not in legal_ramps:
                errs.append(f"{aid}: unknown ramp {m!r} "
                            f"(legal: {', '.join(sorted(legal_ramps))})")

    # Does the priority-1 furniture actually fit the room?
    rw, rh = man["room"]["tiles"]
    area = rw * rh
    used = sum((a.get("fp") or [0, 0])[0] * (a.get("fp") or [0, 0])[1]
               for s, a in entries(man)
               if s == "props" and a.get("prio") == 1)
    if used > area * 0.6:
        warns.append(f"tier-1 props occupy {used} tiles of {area} "
                     f"({100*used/area:.0f}%) - little room left to walk")

    # Every palette ramp should be exercised by something, or it is dead weight.
    used_ramps = {m for s, a in entries(man) if s != "ui" for m in a.get("mat", [])}
    for r in sorted(legal_ramps - used_ramps):
        warns.append(f"palette ramp {r!r} is never used by any asset")

    # Every clip the manifest budgets renders for must actually be posable.
    # Without this the budget is fiction: assets.yaml can promise a `brew` clip
    # for years while nothing in the rig knows how to stand at a machine.
    try:
        import character as _c
        posable = set(_c.CLIPS)
        declared = set()
        fx_clips = 0
        for section, a in entries(man):
            clips = a.get("clips") or {}
            if section == "characters":
                declared |= set(clips)
            elif clips:
                fx_clips += sum(clips.values())
        for name in sorted(declared - posable):
            errs.append(f"character clip {name!r} is budgeted in assets.yaml "
                        f"but has no pose function in character.CLIPS")
        for name in sorted(posable - declared):
            warns.append(f"character clip {name!r} is implemented but never "
                         f"budgeted - no asset declares it")
        # Declared symmetry drives the entire render budget, so verify it
        # against the geometry rather than trusting the yaml. Every effect has a
        # generator, so this is cheap and exact.
        import fx as _fx
        from art_review import check_symmetry_claims
        fx_declared = {a["id"]: a.get("sym", "none")
                       for a in (man.get("fx") or [])}
        fx_meshes = {n: fn(0.25) for n, (fn, _) in _fx.FX.items()}
        for msg in check_symmetry_claims(fx_declared, fx_meshes):
            (errs if "WRONG" in msg else warns).append(msg)
        for msg in _fx.check_loops():
            errs.append(msg)
        # Characters must have internal contrast, and the reference room must be
        # legible from the camera that ships. Both are geometry-and-palette
        # facts the manifest cannot state, so they are measured here rather than
        # declared: a spec that passes every stated rule and still renders as a
        # brown smear has only proved the rules were incomplete.
        for msg in _c.check_palette_spread():
            errs.append(msg)
        # And a figure needs a waist. `check_palette_spread` counts ramps, not
        # values, so two different ramps landing on the same step slip past it:
        # `elder` shipped with a wood shirt 0.004 in value from neutral
        # trousers and rendered as one column.
        from pixelize import load_palette as _lp
        for msg in _c.check_waistline(_lp()):
            errs.append(msg)
        # The generated extras have to pass everything the hand-written roster
        # does. They are proposed against exactly these predicates, so a failure
        # here means the solver has stopped consulting one of them -- which is
        # invisible on the sheet, because the sheet only shows what was
        # accepted.
        _ramps = _lp()
        _extras = _c.generate_roster(12, seed=1, ramps=_ramps)
        for msg in (_c.check_contrast(_ramps, _extras)
                    + _c.check_palette_spread(_extras)
                    + _c.check_waistline(_ramps, _extras)):
            errs.append(f"generated: {msg}")
        # And no two members of a cast may be the same person. The three checks
        # above are predicates on ONE spec; a generator can satisfy all three
        # forty times and return forty variations of one person, each
        # individually legal and collectively a crowd with one extra in it.
        for msg in _c.check_roster_variety() + [
                f"generated: {m}" for m in _c.check_roster_variety(_extras)]:
            errs.append(msg)
        from animate import check_direction_labels
        for msg in check_direction_labels():
            errs.append(msg)
        from render_room import build_room
        room = build_room()
        for msg in room.screen_occlusion():
            warns.append(f"reference room: {msg}")
        from art_review import check_generator_range, review_library
        for msg in review_library():
            warns.append(msg)
        # A generator that has quietly become a fixed mesh renders a room that
        # looks entirely fine, which is why this needs to be a check and not an
        # eye on a contact sheet.
        for msg in check_generator_range():
            warns.append(msg)
        # The stage 1-3 seam. Nothing feeds it yet, which is exactly why it
        # needs a check: an adapter that is never exercised is an adapter that
        # is wrong by the time something arrives.
        from ingest import check_roundtrip, check_transform
        for msg in check_roundtrip():
            errs.append(f"ingest: {msg}")
        for msg in check_transform():
            errs.append(f"ingest: {msg}")
    except Exception as exc:                       # pragma: no cover
        warns.append(f"clip cross-check skipped: {exc}")

    for e in errs:
        print(f"  ERROR   {e}")
    for w in warns:
        print(f"  warning {w}")
    if not errs and not warns:
        print("  manifest clean")
    print(f"\n  {len(errs)} errors, {len(warns)} warnings")
    return 1 if errs else 0


def queue(man: dict, tier: int) -> None:
    rows = [(s, a) for s, a in entries(man) if a.get("prio", 3) <= tier]
    rows.sort(key=lambda t: (t[1].get("prio", 3), t[0], t[1]["id"]))
    total = 0
    print(f"WORK QUEUE  -  priority <= {tier}\n")
    print(f"  {'id':26s}{'sect':11s}{'sym':8s}{'az':>3s}{'frm':>5s}{'rend':>7s}")
    for s, a in rows:
        r = renders_for(s, a)
        total += r
        az = 1 if s == "ui" else DISTINCT_AZIMUTHS[a.get("sym", "none")]
        frames = sum((a.get("clips") or {}).values()) or 1
        print(f"  {a['id']:26s}{s:11s}{a.get('sym', '-'):8s}{az:3d}{frames:5d}{r:7d}")
    print(f"\n  {len(rows)} assets, {total} renders")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue", type=int, metavar="TIER")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    man = load()
    if args.check:
        return check(man)
    if args.queue:
        queue(man, args.queue)
        return 0
    summarise(man)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
