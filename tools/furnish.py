#!/usr/bin/env python3
"""Build declared props from `assetlib` builders, in bulk.

    python tools/furnish.py                 # build everything mapped
    python tools/furnish.py --list          # what maps to what, and what doesn't
    python tools/furnish.py --only chair_wood table_4top

The gap this closes
-------------------
`assets.yaml` declares 64 props. Before this tool, two of them had sprites --
`teapot` and `wall_clock` -- and both arrived by accident, because the 32 built
sprites are named after `subjects_c1.yaml` (the SDXL concept path) and only two
of those names happen to collide with a declared id.

Meanwhile `assetlib.py` has been building most of that furniture procedurally
since the room renderer existed. `render_room.py` and `build_plan.py` both call
those builders, and both parameterise them inline at the call site, so there has
never been an id -> builder mapping anywhere in the repo. The furniture existed;
nothing connected it to the manifest that declares it.

That mapping is the whole of this file. Everything downstream -- fit, framing,
shading, outline, footprint, manifest merge -- is `ingest.fit` and
`render_batch`, called directly rather than reimplemented.

Why this path and not the generative one
----------------------------------------
The session's recurring finding is that SDXL makes *things* well and fails on
geometry that carries a semantic role. Furniture is the latter: a chair is legs
that must not fuse, a bookshelf is a carcass that must stay open on one side.
Rendering it from meshes is not a fallback, it is the correct producer -- no
GPU, deterministic across runs, and palette-exact by construction rather than
by quantizing a photograph and hoping.

Honesty about the mapping
-------------------------
A recipe is only written where a builder genuinely makes the declared object.
Where it does not, the id is REPORTED AS UNMAPPED rather than pointed at the
nearest-looking builder: a `sink_double` rendered from `counter()` would pass
every automated check in this repo and be wrong in the only way that matters.
Recipes that reuse a builder for a related-but-not-identical id carry a `note`,
which `--list` prints, so the approximation is visible rather than implied.

Scale comes from the manifest, not the builder
----------------------------------------------
Every mesh goes through `ingest.fit(mesh, height=declared_h)`. The builders
were written to look right in the room renderer's composition, which is not the
same thing as agreeing with `assets.yaml`'s declared heights -- and the declared
height is what the camera framing, the layout and the Godot metadata all read.
Fitting makes the manifest authoritative.

The declared FOOTPRINT is then a cap, not a target. `fp` is a layout
reservation -- what `manifest.check` sums against the room's tile count and what
`Layout` reserves for collision -- so a chair measuring 0.65 tiles inside its
1-tile reservation is correct, and only OVERFLOW is a defect. Where fitting to
the declared height overflows, the mesh is refit to the reservation instead and
the achieved height is printed: two declared numbers and a builder's proportions
cannot all three be satisfied, and the one with a downstream consumer wins.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))

import assetlib as A  # noqa: E402
from ingest import fit, mesh_geometry  # noqa: E402
from isorender import AZIMUTH_STEP  # noqa: E402
from mesh import Mesh  # noqa: E402
from pixelize import load_palette  # noqa: E402
from render_batch import footprint, frame_all, render_sprite  # noqa: E402


@dataclass
class Recipe:
    """One declared id, one callable that returns its mesh.

    `build` takes the seed and nothing else. Seeds are fixed per id rather than
    drawn per run, because a sprite set that changes silhouette between two
    invocations is not an asset -- it is a lottery, and every check in this repo
    that compares runs would start failing for the wrong reason.
    """
    build: Callable[[int], Mesh]
    seed: int
    note: str | None = None


def _counter_run(n: int, seed: int) -> Mesh:
    """`n` counter modules end to end.

    `counter()` deliberately spans the FULL tile so a run tiles seamlessly --
    that is recorded in its docstring as the fix for a seam between every
    adjacent module -- which makes a multi-tile bar exactly a translation of
    the single module, not a new mesh. Each module gets its own seed so the
    front treatments differ along the run; a three-tile bar with one repeated
    front reads as a single wide cabinet.
    """
    parts = [A.transformed(A.counter(kick=False, seed=seed + i), at=(float(i), 0.0, 0.0))
             for i in range(n)]
    return A.merge(*parts)


# --- the registry ------------------------------------------------------------
#
# Ordered as `assets.yaml` orders its props, so the two files can be read side
# by side and a gap is visible as a gap.

RECIPES: dict[str, Recipe] = {
    # service equipment
    "espresso_machine_2group": Recipe(lambda s: A.espresso_machine(seed=s), 11),
    "grinder_burr":            Recipe(lambda s: A.grinder(), 0),
    "pastry_case":             Recipe(lambda s: A.pastry_case(seed=s), 5),
    "register_till":           Recipe(lambda s: A.register(), 0),

    # counters
    "counter_straight":        Recipe(lambda s: A.counter(seed=s), 3),
    "bar_top_window":          Recipe(lambda s: _counter_run(3, s), 21,
                                      "three `counter` modules end to end; the "
                                      "module is authored to tile, so the run "
                                      "is a translation rather than a new mesh"),

    # shelving
    "shelf_wall":              Recipe(lambda s: A.wall_shelf(length=2.0), 0),
    "shelf_tall":              Recipe(lambda s: A.bookshelf(seed=s), 31,
                                      "`bookshelf` fit to the taller declared "
                                      "height; same carcass, different seed to "
                                      "keep it from twinning `bookshelf`"),

    # tables
    "table_2top_round":        Recipe(lambda s: A.table_round(seed=s), 7),
    "table_2top_square":       Recipe(lambda s: A.table(1.0, 1.0, 0.58,
                                                        round_top=False, seed=s), 9),
    "table_4top":              Recipe(lambda s: A.table_4top(seed=s), 13),
    "table_communal":          Recipe(lambda s: A.table(4.0, 2.0, 0.58,
                                                        round_top=False, seed=s), 17),

    # seating
    "chair_wood":              Recipe(lambda s: A.chair(seed=s), 3),
    "chair_metal":             Recipe(lambda s: A.chair(frame=A.METAL, seed=s), 19),
    "chair_cushioned":         Recipe(lambda s: A.chair(cushion=A.FABRIC, seed=s), 23),
    "stool_bar":               Recipe(lambda s: A.stool(seed=s), 5),
    "stool_low":               Recipe(lambda s: A.stool(seed=s), 29,
                                      "`stool` fit to the low declared height; "
                                      "the builder's own note says height is "
                                      "the only thing that reads at this size"),
    "sofa_2seat":              Recipe(lambda s: A.bench(length=2.0, seed=s), 37,
                                      "`bench` is the banquette mass; a 2-seat "
                                      "sofa is the same silhouette at a "
                                      "different back style, which the seed picks"),
    "armchair":                Recipe(lambda s: A.armchair(seed=s), 41),
    "booth_bench":             Recipe(lambda s: A.bench(length=2.0, seed=s), 43,
                                      "same builder as `sofa_2seat`, different "
                                      "seed -- the two differ by back style and "
                                      "seat mass, which is what separates them "
                                      "in a room"),

    # greenery
    "plant_monstera":          Recipe(lambda s: A.plant_large(seed=s), 3),
    "plant_fern":              Recipe(lambda s: A.leafy_plant(height=0.70, seed=s,
                                                              stems=7), 11),
    "plant_succulent":         Recipe(lambda s: A.succulent(seed=s), 13),

    # storage and fittings
    "bookshelf":               Recipe(lambda s: A.bookshelf(seed=s), 2),
    "crate_stack":             Recipe(lambda s: A.crate(seed=s), 8),
    "coat_rack":               Recipe(lambda s: A.coat_rack(), 0),
    "bin_waste":               Recipe(lambda s: A.trash_bin(), 0),

    # signage
    "menu_chalkboard":         Recipe(lambda s: A.menu_board(), 0),
    "menu_wall_board":         Recipe(lambda s: A.wall_sign(), 0,
                                      "`wall_sign` is the wall-mounted board "
                                      "with a bright face; that is what a wall "
                                      "menu board is, under a different name"),
    "chalkboard_easel":        Recipe(lambda s: A.sandwich_board(), 0),

    # lighting
    "lamp_pendant":            Recipe(lambda s: A.pendant_lamp(), 0),

    # back-of-house fixtures
    "fridge_under":            Recipe(lambda s: A.fridge_under(), 0),
    "ice_machine":             Recipe(lambda s: A.ice_machine(), 0),
    "sink_double":             Recipe(lambda s: A.sink_double(), 0),
    "cup_warmer":              Recipe(lambda s: A.cup_warmer(), 0),
    "bean_hopper":             Recipe(lambda s: A.bean_hopper(), 0),
    "drip_brewer":             Recipe(lambda s: A.drip_brewer(), 0),
    "pourover_stand":          Recipe(lambda s: A.pourover_stand(), 0),
    "grinder_hand":            Recipe(lambda s: A.grinder_hand(), 0),
    "kettle_gooseneck":        Recipe(lambda s: A.kettle_gooseneck(), 0),

    # wall and light
    "wall_art_framed":         Recipe(lambda s: A.wall_art_framed(seed=s), 47),
    "lamp_floor":              Recipe(lambda s: A.lamp_floor(), 0),
    "lamp_table":              Recipe(lambda s: A.lamp_table(), 0),
    "plant_hanging":           Recipe(lambda s: A.plant_hanging(seed=s), 5),

    # tableware
    "cup_espresso":            Recipe(lambda s: A.cup_espresso(), 0),
    "cup_latte":               Recipe(lambda s: A.cup_and_saucer(), 0),
    "cup_togo":                Recipe(lambda s: A.cup_togo(), 0),
    "mug_ceramic":             Recipe(lambda s: A.mug_ceramic(), 0),
    "milk_jug":                Recipe(lambda s: A.milk_jug(), 0),
    "sugar_caddy":             Recipe(lambda s: A.sugar_caddy(), 0),
    "napkin_holder":           Recipe(lambda s: A.napkin_holder(), 0),
    "tip_jar":                 Recipe(lambda s: A.tip_jar(seed=s), 53),
    "laptop_open":             Recipe(lambda s: A.laptop_open(), 0),
    "book_stack":              Recipe(lambda s: A.book_stack(seed=s), 59),
    "pastry_plate":            Recipe(lambda s: A.pastry_plate(seed=s), 61),
    "bean_sack":               Recipe(lambda s: A.bean_sack(seed=s), 67),
}

# Ids with no honest recipe, and why. Printed by --list so the gap stays a
# stated gap rather than a silence. These are decisions, not TODO noise: each
# one needs either new `assetlib` geometry or the SDXL concept path, and which
# of those is right is a per-id call.
UNMAPPED_REASON = {
    "espresso_machine_1group": "`espresso_machine` is authored 2 tiles wide and "
                               "takes no width; `fit` scales uniformly, so it "
                               "would stay 2 wide at a 1-tile reservation and "
                               "be capped into a squat 2-group instead",
    "counter_corner_l":        "`counter` is one straight module; an L worktop "
                               "is new geometry, not a rotation",
    "counter_corner_r":        "as counter_corner_l, mirrored",
    "counter_end":             "`counter` has no finished end panel",
    "counter_pass":            "no builder; the pass-through is a void",
    "wall_clock":              "no builder; already built on the SDXL path",
    "teapot":                  "already built on the SDXL path",
    "saucer":                  "`cup_and_saucer` is one mesh and `fit` scales it "
                               "UNIFORMLY -- fitting to the saucer's 0.03 height "
                               "shrinks the cup too rather than flattening to "
                               "the disc, and reframing then made the sprites "
                               "byte-identical to cup_latte (caught by "
                               "check_distinct)",
}


def load_declared() -> dict[str, dict]:
    data = yaml.safe_load((ROOT / "assets.yaml").read_text(encoding="utf-8"))
    return {p["id"]: p for p in data["props"]}


def build_one(asset_id: str, spec: dict, recipe: Recipe, out: Path,
              target: int, factor: int, ramps) -> dict:
    """Mesh -> fit -> 8 sprites -> manifest rows. Returns a report dict."""
    raw = recipe.build(recipe.seed)
    mesh, _ = fit(raw, height=float(spec["h"]))
    world = mesh_geometry(mesh)

    # The reserved cells are a hard cap; the declared height is a target.
    #
    # `fp` is what `manifest.check` sums against the room's tile count and what
    # `Layout` reserves for collision -- an object wider than its reservation
    # overlaps a neighbour that layout believes is clear, which is a placement
    # bug rather than a cosmetic one. Height has no such consumer: it drives
    # camera framing and rides along as Godot metadata, both of which read
    # whatever the sprite actually is.
    #
    # So when height-fitting overflows the reservation, refit by the wider
    # declared axis and record the height that produced. Capping by max(fp)
    # rather than per-axis is deliberate: these sprites are rendered at all 8
    # azimuths, so the reservation has to hold with the object turned.
    fit_note = None
    declared_fp = [float(v) for v in spec["fp"]]
    if all(d > 0 for d in declared_fp):
        cap = max(declared_fp)
        if max(world["footprint_xy"]) > cap + 1e-6:
            mesh, _ = fit(raw, footprint=cap)
            world = mesh_geometry(mesh)
            fit_note = (f"capped to fp {cap:g}; height {spec['h']} -> "
                        f"{world['height']:.2f}")

    span, centre = frame_all(mesh)

    entries = []
    for k in range(8):
        az = 45.0 + k * AZIMUTH_STEP
        img, px = render_sprite(mesh, az, target, factor, ramps,
                                span=span, centre=centre)
        name = f"{asset_id}_dir{k}.png"
        img.save(out / name)
        entries.append({"asset": asset_id, "direction": k, "azimuth": az,
                        "file": name, **(footprint(px, target) or {}),
                        "world": world})

    return {"id": asset_id, "entries": entries, "dir": out,
            "verts": len(mesh.verts),
            "tris": len(mesh.faces), "height": world["height"],
            "coverage": max(e["coverage"] for e in entries),
            "fit_note": fit_note}


def merge_manifest(path: Path, per_asset: list[dict]) -> int:
    """Replace each rebuilt asset's rows, keep everyone else's.

    Same merge rule `render_batch` uses, and for the same reason it learned it:
    overwriting left `manifest.json` describing only the last asset rendered.
    Here it matters more, because this tool writes into the same directory the
    SDXL path already filled with 32 assets.
    """
    manifest = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    rebuilt = {r["id"] for r in per_asset}
    manifest = [m for m in manifest if m.get("asset") not in rebuilt]
    for r in per_asset:
        manifest.extend(r["entries"])

    # Rows whose PNG is gone describe an asset that no longer exists. Retiring
    # a recipe leaves exactly that: deleting `saucer` from RECIPES stopped the
    # tool rebuilding it, and its eight rows sat in the manifest pointing at
    # eight deleted files -- which `package_godot` would happily stage and Godot
    # would fail to load. A merge that only ever adds cannot represent a
    # removal, so the removal is read off the filesystem.
    dropped = sorted({m["asset"] for m in manifest
                      if not (path.parent / m["file"]).exists()})
    if dropped:
        manifest = [m for m in manifest if (path.parent / m["file"]).exists()]
        print(f"  pruned rows for {len(dropped)} asset(s) with no PNG on disk: "
              f"{', '.join(dropped)}")

    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return len({m["asset"] for m in manifest})


def check_distinct(reports: list[dict]) -> list[str]:
    """Do any two ids render the same eight images?

    Not a theoretical worry -- it shipped. `saucer` and `cup_latte` were both
    `cup_and_saucer`, on the reasoning that fitting to the saucer's declared
    0.03 height would flatten the mesh to its disc. `fit` scales UNIFORMLY, so
    it shrank the cup along with everything else, and `frame_all` then reframed
    the result to fill the sprite box. Two declared ids, two manifest entries,
    two sets of eight PNGs, and one asset.

    This is specifically the failure that per-asset framing hides: every prop
    is framed to fill 64px, so scale is carried in metadata and is invisible in
    the image. Any pair of recipes differing only in declared height therefore
    produces identical pixels, and nothing else in the pipeline would notice --
    every downstream check is per-asset, and each of the two assets is
    individually fine.

    Hashing all eight directions rather than one: two props can share a
    silhouette from one azimuth and diverge from another, and only agreement
    across the whole set means one asset wearing two names.
    """
    seen: dict[str, list[str]] = {}
    for r in reports:
        digest = hashlib.sha256()
        for e in sorted(r["entries"], key=lambda e: e["direction"]):
            digest.update((r["dir"] / e["file"]).read_bytes())
        seen.setdefault(digest.hexdigest(), []).append(r["id"])
    return [f"identical sprite sets for {sorted(ids)} -- these are one asset "
            f"under two declared ids, not two assets"
            for ids in seen.values() if len(ids) > 1]


def cmd_list(declared: dict[str, dict]) -> int:
    print(f"{len(declared)} props declared in assets.yaml\n")
    print(f"-- {len(RECIPES)} mapped to assetlib builders --")
    for asset_id in declared:
        r = RECIPES.get(asset_id)
        if r is None:
            continue
        spec = declared[asset_id]
        print(f"  {asset_id:<24} h={spec['h']:<5} seed={r.seed}")
        if r.note:
            print(f"  {'':<24} note: {r.note}")

    missing = [a for a in declared if a not in RECIPES]
    print(f"\n-- {len(missing)} unmapped --")
    for asset_id in missing:
        why = UNMAPPED_REASON.get(asset_id, "NO REASON RECORDED")
        print(f"  {asset_id:<24} {why}")

    # A reason with no id, or an id with neither recipe nor reason, means the
    # two lists have drifted apart -- which is exactly the state this file
    # exists to prevent, so it is an error rather than a note.
    stale = sorted(set(UNMAPPED_REASON) - set(declared))
    silent = sorted(a for a in missing if a not in UNMAPPED_REASON)
    both = sorted(set(UNMAPPED_REASON) & set(RECIPES))
    problems = []
    if stale:
        problems.append(f"UNMAPPED_REASON names ids not in assets.yaml: {stale}")
    if silent:
        problems.append(f"unmapped with no recorded reason: {silent}")
    if both:
        problems.append(f"both mapped and listed unmapped: {both}")
    for p in problems:
        print(f"\n  BLOCKER  {p}", file=sys.stderr)
    return 1 if problems else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "out" / "sprites"))
    ap.add_argument("--target", type=int, default=64)
    ap.add_argument("--factor", type=int, default=4)
    ap.add_argument("--only", nargs="+", default=None,
                    help="build just these ids")
    ap.add_argument("--list", action="store_true",
                    help="print the registry and the unmapped ids, build nothing")
    args = ap.parse_args()

    declared = load_declared()
    unknown = sorted(set(RECIPES) - set(declared))
    if unknown:
        raise SystemExit(f"recipes for ids not declared in assets.yaml: {unknown}")

    if args.list:
        return cmd_list(declared)

    todo = list(RECIPES)
    if args.only:
        bad = [a for a in args.only if a not in RECIPES]
        if bad:
            raise SystemExit(f"no recipe for: {bad}")
        todo = args.only

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    ramps = load_palette()

    reports = []
    for i, asset_id in enumerate(todo, 1):
        rep = build_one(asset_id, declared[asset_id], RECIPES[asset_id],
                        out, args.target, args.factor, ramps)
        reports.append(rep)
        print(f"[{i:>2}/{len(todo)}] {asset_id:<24} {rep['verts']:>5} verts  "
              f"h={rep['height']:.2f}  cover={rep['coverage']:.3f}")
        if rep["fit_note"]:
            print(f"          {rep['fit_note']}")

    total = merge_manifest(out / "manifest.json", reports)
    print(f"\n{len(reports) * 8} sprites -> {out}  "
          f"({total} assets in manifest.json)")

    notes = [r for r in reports if r["fit_note"]]
    if notes:
        print(f"\n{len(notes)} prop(s) hit the footprint cap -- the builder's "
              f"proportions and the declared fp/h pair cannot both hold:")
        for r in notes:
            print(f"  {r['id']:<24} {r['fit_note']}")

    # Only meaningful over a full run: --only builds a subset, and two ids can
    # look distinct within it while colliding with something outside it.
    if not args.only:
        problems = check_distinct(reports)
        for p in problems:
            print(f"  BLOCKER  {p}", file=sys.stderr)
        if problems:
            return 1
        print(f"\n{len(reports)} distinct sprite sets -- no two ids render "
              f"the same eight images")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
