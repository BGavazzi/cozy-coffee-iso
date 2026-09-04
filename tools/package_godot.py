#!/usr/bin/env python3
"""Stage every kind of factory output for Godot import.

Reads the four things this repo actually produces and stages them into
`godot_export/project/`:

  out/sprites/manifest.json   static props, 8 fixed direction frames each
  sprites/atlas.json          animated characters and FX, packed sheets
  out/ui/                     icons (generated) and chrome (drawn)
  out/tiles/                  ground tiles, one atlas per type

Note the first two directories: `out/sprites/` is the static prop factory's
output and plain `sprites/` is `animate.py`'s. They are two different places
with almost the same name, which cost a wrong path on the first run of this
file. Both are gitignored; neither is being renamed here, because the name
appears in `animate.py`'s `--out` default and in the docs, and a rename is
its own change rather than a rider on this one.

into

  assets/<asset>/<asset>_dir<N>.png     one file per prop direction
  assets/anim/<name>.png                one packed sheet per character/effect
  assets/ui/<id>.png                    one file per icon or chrome piece
  assets/tiles/<type>.png               one atlas per tile type
  build_manifest.json                   the facts `build_all.gd` needs

Copied rather than referenced in place, so Godot's import cache lives outside
the generated `out/` tree and survives a `factory.py --force` re-run without
re-importing everything.

Three of those four had no export path until now, and the gap was structural
rather than neglect: this file only ever read `manifest.json`, whose shape is
"8 direction frames per asset", and neither a packed animation sheet nor a
single-frame icon nor a tile atlas fits that. `NEXT.md` recorded the first
two as one gap for a reason -- forcing either into the 8-direction shape
would have been worse than leaving it visible, and they wanted the same fix,
which is for the manifest to have a section per producer instead of one for
all of them. Tiles then cost four lines, which is the test of whether the
shape was right.

Nine-slice chrome carries insets from `out/ui/nine_slice.json` through to a
Godot `StyleBoxTexture`, which is the whole reason `ui_chrome.py` draws those
pieces instead of generating them: a generated frame is one fixed size
forever, and a drawn one becomes every dialogue box in the game.

This only stages files -- it does not invoke Godot. See
`tools/export_godot.py` for the full three-step pipeline (stage, import,
build).
"""
import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPRITES_MANIFEST = ROOT / "out" / "sprites" / "manifest.json"
SPRITES_DIR = ROOT / "out" / "sprites"
ATLAS = ROOT / "sprites" / "atlas.json"   # animate.py, NOT out/sprites/
UI_DIR = ROOT / "out" / "ui"
TILES_DIR = ROOT / "out" / "tiles"
PROJECT_DIR = ROOT / "godot_export" / "project"
ASSETS_DIR = PROJECT_DIR / "assets"
BUILD_MANIFEST = PROJECT_DIR / "build_manifest.json"


def style_paths(style_name: str) -> dict:
    """Where a given style's staging inputs and Godot project tree live.

    Every producer upstream of this file picked its own per-style path
    convention independently, and none of them agree with each other:
    `furnish.py` nests a non-default style UNDER the default's own directory
    (`out/sprites/<style>/`), while `tileset.py`/`ui_chrome.py` use a
    sibling-with-suffix (`out/tiles_<style>/`, `out/ui_<style>/`). Both are
    matched here exactly rather than papered over with one "consistent"
    scheme this file invents, because these are the paths those producers'
    OWN `--style` runs actually write to on disk -- inventing a third
    convention here would mean staging from a path nothing ever populates.

    `godot_export/project_<style>/` (this file's own output) follows the
    suffix convention: see `export_godot.py`'s module docstring / NEXT.md for
    why a second style gets its own project directory rather than sharing
    `godot_export/project/` with the default.

    `sprites/atlas.json` (animate.py's output) has no per-style variant at
    all -- `animate.py` has no `--style` flag yet, unlike every other
    producer this pipeline stages from -- so it is NOT resolved per style
    here; a non-default style simply gets whatever the one atlas on disk
    contains, same as today, until that producer is generalised too.
    """
    sys.path.insert(0, str(Path(__file__).parent))
    from style import DEFAULT_STYLE
    if style_name == DEFAULT_STYLE:
        return dict(manifest_path=SPRITES_MANIFEST, sprites_dir=SPRITES_DIR,
                    project_dir=PROJECT_DIR, ui_dir=UI_DIR, tiles_dir=TILES_DIR)
    return dict(
        manifest_path=SPRITES_DIR / style_name / "manifest.json",
        sprites_dir=SPRITES_DIR / style_name,
        project_dir=PROJECT_DIR.parent / f"project_{style_name}",
        ui_dir=UI_DIR.parent / f"ui_{style_name}",
        tiles_dir=TILES_DIR.parent / f"tiles_{style_name}",
    )


def stage_sprites(manifest_path: Path, sprites_dir: Path,
                  assets_dir: Path) -> dict:
    """Static props: 8 direction frames each, copied one file per frame."""
    manifest = json.loads(manifest_path.read_text())

    by_asset = defaultdict(list)
    for entry in manifest:
        by_asset[entry["asset"]].append(entry)

    out = {}
    for asset, entries in sorted(by_asset.items()):
        entries.sort(key=lambda e: e["direction"])
        if len(entries) != 8:
            raise SystemExit(f"{asset}: expected 8 directions, found {len(entries)}")
        worlds = {json.dumps(e["world"], sort_keys=True) for e in entries}
        if len(worlds) != 1:
            raise SystemExit(f"{asset}: world facts differ across directions")

        asset_dir = assets_dir / asset
        asset_dir.mkdir(parents=True)
        frames = []
        for e in entries:
            shutil.copyfile(sprites_dir / e["file"], asset_dir / e["file"])
            frames.append({
                "direction": e["direction"],
                "azimuth": e["azimuth"],
                "file": e["file"],
                "bbox": e["bbox"],
                "pivot": e["pivot"],
                "coverage": e["coverage"],
            })
        out[asset] = {"world": entries[0]["world"], "frames": frames}
    return out


def stage_anim(atlas_path: Path, atlas_dir: Path, assets_dir: Path) -> dict:
    """Animated characters and FX: one packed sheet each, plus its geometry.

    The sheet stays whole. Godot's `AtlasTexture` addresses a region of a
    parent texture, which is exactly what a packed sheet is for, so slicing
    it back into files here would undo the packing and quadruple the import
    count for no gain.

    What has to cross the boundary is the row arithmetic. `animate.py` lays
    clips out in row-blocks -- row `clip.row + d` holds direction `d` of that
    clip, column `f` holds frame `f` -- and a consumer that recomputes that
    from scratch is a consumer that can get it one row off. It has been one
    row off before, on the direction names (see `animate.py`'s DIRECTIONS
    comment), and that failure is invisible in every frame and wrong in all
    of them. So the rects are resolved here, once, and shipped explicitly.
    """
    atlas = json.loads(atlas_path.read_text())
    fw, fh = atlas["frame_size"]
    dirs = atlas["directions"]

    dest = assets_dir / "anim"
    dest.mkdir(parents=True, exist_ok=True)

    def sheet_entry(name: str, entry: dict, n_dirs: int, kind: str) -> dict:
        shutil.copyfile(atlas_dir / entry["image"], dest / entry["image"])
        clips = {}
        for clip, meta in entry["clips"].items():
            per_dir = {}
            for d in range(n_dirs):
                label = dirs[d] if n_dirs == len(dirs) else str(d)
                per_dir[label] = [
                    [f * fw, (meta["row"] + d) * fh, fw, fh]
                    for f in range(meta["frames"])
                ]
            clips[clip] = {
                "fps": meta["fps"],
                "frames": meta["frames"],
                "regions": per_dir,
                # Characters carry a per-clip anchor; effects do not, and
                # defaulting one in would be inventing a fact.
                **({"anchor": meta["anchor"]} if "anchor" in meta else {}),
            }
        return {"kind": kind, "file": f"anim/{entry['image']}",
                "sheet_size": entry["sheet_size"], "clips": clips,
                **({"role": entry["role"]} if "role" in entry else {}),
                **({"symmetry": entry["symmetry"]} if "symmetry" in entry
                   else {})}

    out = {"frame_size": [fw, fh], "directions": dirs, "sheets": {}}
    for name, entry in sorted(atlas.get("characters", {}).items()):
        out["sheets"][name] = sheet_entry(name, entry, len(dirs), "character")
    for name, entry in sorted(atlas.get("fx", {}).items()):
        # An effect is rendered at the azimuth count its symmetry allows, so
        # its row block is `azimuths` tall, not always 8.
        n = next(iter(entry["clips"].values()))["azimuths"]
        out["sheets"][name] = sheet_entry(name, entry, n, "fx")

    problems = check_anim_layout(out)
    if problems:
        raise SystemExit("animation sheet layout is wrong:\n  "
                         + "\n  ".join(problems))
    return out


def check_anim_layout(anim: dict) -> list[str]:
    """Do the resolved rects fit the sheet, and does each one belong to one clip?

    Two failures are possible in the row arithmetic above and both are
    silent. A rect past the bottom of the sheet gives Godot an
    `AtlasTexture` reading outside its parent, which renders as empty rather
    than as an error. Two clips resolving to the same row gives two
    animations that play identical frames, which looks like a rig bug rather
    than a packing bug.

    Neither needs the image to be opened -- `sheet_size` comes from
    `animate.py`, which is the authority on how it packed. Checking against
    the packer's own declared size is the point: if the two ever disagree,
    that disagreement is the bug.
    """
    out = []
    for name, sheet in sorted(anim["sheets"].items()):
        sw, sh = sheet["sheet_size"]
        seen: dict[tuple, str] = {}
        for clip, meta in sheet["clips"].items():
            for label, rects in meta["regions"].items():
                for r in rects:
                    x, y, w, h = r
                    if x < 0 or y < 0 or x + w > sw or y + h > sh:
                        out.append(f"{name}.{clip}.{label}: frame at "
                                   f"({x},{y},{w},{h}) falls outside the "
                                   f"{sw}x{sh} sheet -- the row block for "
                                   f"this clip is wrong")
                        break
                    key = (x, y)
                    prev = seen.get(key)
                    if prev is not None and prev != f"{clip}.{label}":
                        out.append(f"{name}: {prev} and {clip}.{label} both "
                                   f"claim the cell at ({x},{y}) -- two "
                                   f"clips resolved to the same row")
                    seen[key] = f"{clip}.{label}"
    return out


def stage_ui(ui_dir: Path, assets_dir: Path) -> dict:
    """Icons and chrome. Flat, single-frame, and two producers deep.

    `_`-prefixed files are previews and `*_concept*` are the 1024px SDXL
    sources; neither is an asset. The producer is recorded per piece because
    it is the one fact about a UI asset that a later reader will want and
    cannot recover from the PNG -- which of these was drawn is the difference
    between "regenerate it with another seed" and "edit the function".
    """
    if not ui_dir.exists():
        return {}
    nine_path = ui_dir / "nine_slice.json"
    nine = json.loads(nine_path.read_text()) if nine_path.exists() else {}
    chrome_path = ui_dir / "chrome_report.json"
    drawn = ({r["name"] for r in json.loads(chrome_path.read_text())}
             if chrome_path.exists() else set())

    from PIL import Image
    dest = assets_dir / "ui"
    dest.mkdir(parents=True, exist_ok=True)

    icons = {}
    for p in sorted(ui_dir.glob("*.png")):
        if p.name.startswith("_") or "_concept" in p.name:
            continue
        shutil.copyfile(p, dest / p.name)
        with Image.open(p) as im:
            size = list(im.size)
        icons[p.stem] = {
            "file": f"ui/{p.name}",
            "size": size,
            "source": "drawn" if p.stem in drawn else "generated",
        }
        if p.stem in nine:
            icons[p.stem]["nine_slice"] = nine[p.stem]
    return {"icons": icons}


def stage_font(ui_dir: Path, assets_dir: Path) -> dict:
    """The bitmap font: one uniform-cell sheet per size, plus its metrics.

    A font is not an icon, which is why it lives in `out/ui/font/` rather than
    beside them -- `stage_ui` globs `out/ui/*.png` and would otherwise stage
    four glyph sheets and a demo render as game assets.

    Everything an engine needs to cut the sheet up is arithmetic on the cell
    size and the glyph's index, so only the per-glyph ADVANCE has to travel:
    the cells are uniform and the font is not, and that difference is the whole
    of what makes the setting proportional. Passed through unchanged from
    `font.json` rather than recomputed here, for the reason `stage_tiles`
    records -- one authority for the metrics, on the Python side.
    """
    src = ui_dir / "font"
    index = src / "font.json"
    if not index.exists():
        return {}
    meta = json.loads(index.read_text(encoding="utf-8"))
    dest = assets_dir / "font"
    dest.mkdir(parents=True, exist_ok=True)
    sizes = {}
    for cap, entry in meta["sizes"].items():
        png = src / entry["file"]
        if not png.exists():
            continue
        shutil.copyfile(png, dest / png.name)
        out = dict(entry)
        out["file"] = f"font/{png.name}"
        sizes[cap] = out
    return {"sizes": sizes, "ink": meta.get("ink")} if sizes else {}


def stage_tiles(tiles_dir: Path, assets_dir: Path) -> dict:
    """Ground tiles: one atlas per tile type, variants in a row.

    `tileset.json` already carries everything an engine needs -- tile size,
    the two lattice steps, and the region of each variant inside its atlas --
    because `tileset.py` computed all of it from the projection basis and
    proved the tiling. Passing it through unchanged rather than recomputing
    it here keeps one authority for the geometry.

    `_proof_*.png` and `_room_corner.png` are evidence rather than assets and
    stay out of the export.

    Walls ride in the same manifest but a separate section, because they are a
    different shape of claim: a floor tile tiles in two directions and a wall
    tile in one, and each wall carries the `origin_offset` that puts its base
    on the floor edge it stands on. That number is verified on the Python side
    by rebuilding the room from the manifest alone and requiring the result to
    be pixel-identical to the projected one.
    """
    meta_path = tiles_dir / "tileset.json"
    if not meta_path.exists():
        return {}
    meta = json.loads(meta_path.read_text())
    dest = assets_dir / "tiles"
    dest.mkdir(parents=True, exist_ok=True)
    for section in ("tiles", "walls"):
        for name, info in meta.get(section, {}).items():
            shutil.copyfile(tiles_dir / info["file"], dest / info["file"])
            info["file"] = f"tiles/{info['file']}"
    return meta


def stage_palettes(assets_dir: Path, style_name: str = "cozy_ghibli") -> dict:
    """Every palette as one lookup texture: 40 columns, one row per time of day.

    The art itself is NOT re-exported per variant. `palette_swap.py` can write
    all four pre-swapped copies to `out/variants/` (3.8 MB each) and a project
    that wants the no-shader path should copy those, but staging 3,020 extra
    PNGs into the engine to express 160 numbers is the wrong trade -- and it
    buys the weaker feature. Four folders of art give four discrete states.
    This texture gives a shader the endpoints to interpolate BETWEEN, which is
    what a day/night cycle actually is, and costs 200 pixels.

    Row 0 is always the base palette, so a shader that samples row 0 renders
    the art unchanged and `mix()` toward any other row is a dissolve from
    "now" to "then". Column order is the forge order -- ramp by ramp, index by
    index -- which is the same identity `palette_swap` keys its table on, so
    the two cannot disagree about what column 17 means.

    Nearest-neighbour and no mipmaps are not preferences here: a filtered
    sample of this texture is a colour that exists in no palette.
    """
    from PIL import Image
    sys.path.insert(0, str(Path(__file__).parent))
    import palette_forge as PF
    import palette_swap as PS

    bible = PS.load_bible(style_name)
    names = ["base"] + list(bible["palette"].get("variants", {}))
    rows = [PF.forge(bible, None if n == "base" else n) for n in names]
    width = len(rows[0])

    img = Image.new("RGBA", (width, len(rows)))
    img.putdata([(*sw.rgb, 255) for row in rows for sw in row])
    dest = assets_dir / "palette"
    dest.mkdir(parents=True, exist_ok=True)
    img.save(dest / "lut.png")

    return {
        "lut": "palette/lut.png",
        "size": [width, len(rows)],
        "rows": {n: i for i, n in enumerate(names)},
        "columns": [s.name for s in rows[0]],
        "notes": {n: " ".join(str(bible["palette"]["variants"][n]
                                  .get("note", "")).split())
                  for n in names[1:]},
    }


def check_palette_lut(build: dict, assets_dir: Path,
                      style_name: str = "cozy_ghibli") -> list[str]:
    """Read the written texture back and require it to BE the palettes.

    Writing a lookup table and trusting it is how a lookup table goes wrong:
    every failure mode here (a transposed row, an RGBA channel order, a save
    path that quantized) produces a file that loads fine and recolours the
    game incorrectly. Reading the pixels back and comparing them to a fresh
    forge is the only check that would catch a transpose.
    """
    pal = build.get("palettes")
    if not pal:
        return []
    from PIL import Image
    sys.path.insert(0, str(Path(__file__).parent))
    import palette_forge as PF
    import palette_swap as PS

    bible = PS.load_bible(style_name)
    with Image.open(assets_dir / "palette" / "lut.png") as im:
        px = list(im.convert("RGBA").getdata())
        w, h = im.size

    out = []
    for name, row in pal["rows"].items():
        want = PF.forge(bible, None if name == "base" else name)
        got = [p[:3] for p in px[row * w:(row + 1) * w]]
        if got != [s.rgb for s in want]:
            bad = sum(1 for a, b in zip(got, want) if a != b.rgb)
            out.append(f"palette lut row {row} ({name}) disagrees with the "
                       f"forged palette on {bad} of {w} columns")
    return out


def stage(style_name: str | None = None,
          manifest_path: Path | None = None,
          sprites_dir: Path | None = None,
          project_dir: Path | None = None,
          atlas_path: Path = ATLAS,
          ui_dir: Path | None = None,
          tiles_dir: Path | None = None) -> dict:
    """Clear `assets/`, stage all three producers, write the build manifest.

    The clear happens once, here, rather than inside each stager -- three
    functions each rmtree-ing a shared directory is a bug waiting for the
    first person who reorders the calls.

    `style_name` resolves every path default through `style_paths()` (see
    that function's docstring for the per-producer convention it mirrors).
    It defaults to `None` rather than `style.DEFAULT_STYLE` directly because
    the latter would bind the style module at `def` time, the exact
    import-order trap `style.py`'s own docstring warns every OTHER consumer
    of style data about -- resolving it inside the call, instead, costs one
    `or` and sidesteps the trap entirely.

    Any of the five path arguments can still be passed explicitly, same as
    before this gained style-awareness; an explicit value always wins over
    the style-derived default, so an unflagged call with no arguments at all
    resolves to the exact five constants it always did and stages into the
    exact `godot_export/project/` tree it always did -- the default style's
    export is unchanged, byte for byte, by any of this.
    """
    sys.path.insert(0, str(Path(__file__).parent))
    from style import DEFAULT_STYLE
    style_name = style_name or DEFAULT_STYLE
    defaults = style_paths(style_name)
    manifest_path = manifest_path or defaults["manifest_path"]
    sprites_dir = sprites_dir or defaults["sprites_dir"]
    project_dir = project_dir or defaults["project_dir"]
    ui_dir = ui_dir or defaults["ui_dir"]
    tiles_dir = tiles_dir or defaults["tiles_dir"]

    assets_dir = project_dir / "assets"
    if assets_dir.exists():
        shutil.rmtree(assets_dir)
    assets_dir.mkdir(parents=True)

    build = {"assets": stage_sprites(manifest_path, sprites_dir, assets_dir)}
    if atlas_path.exists():
        build["anim"] = stage_anim(atlas_path, atlas_path.parent, assets_dir)
    if ui_dir.exists():
        ui = stage_ui(ui_dir, assets_dir)
        if ui.get("icons"):
            build["ui"] = ui
        font = stage_font(ui_dir, assets_dir)
        if font.get("sizes"):
            build["font"] = font
    if tiles_dir.exists():
        tiles = stage_tiles(tiles_dir, assets_dir)
        if tiles.get("tiles"):
            build["tiles"] = tiles
    build["palettes"] = stage_palettes(assets_dir, style_name)
    for problem in check_palette_lut(build, assets_dir, style_name):
        raise SystemExit(f"BLOCKER  {problem}")

    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "build_manifest.json").write_text(json.dumps(build, indent=2))
    return build


def summarise(build: dict) -> str:
    lines = []
    props = build.get("assets", {})
    lines.append(f"{len(props)} props, "
                 f"{sum(len(a['frames']) for a in props.values())} frames")
    anim = build.get("anim", {}).get("sheets", {})
    if anim:
        clips = sum(len(s["clips"]) for s in anim.values())
        frames = sum(len(r) for s in anim.values()
                     for c in s["clips"].values()
                     for r in c["regions"].values())
        chars = sum(1 for s in anim.values() if s["kind"] == "character")
        lines.append(f"{chars} characters + {len(anim) - chars} effects, "
                     f"{clips} clips, {frames} frames")
    tiles = build.get("tiles", {}).get("tiles", {})
    walls = build.get("tiles", {}).get("walls", {})
    if tiles or walls:
        lines.append(f"{len(tiles)} floor types + {len(walls)} wall types, "
                     f"{sum(t['variants'] for t in tiles.values()) + sum(t['variants'] for t in walls.values())} "
                     f"variants")
    ui = build.get("ui", {}).get("icons", {})
    if ui:
        nine = sum(1 for i in ui.values() if "nine_slice" in i)
        drawn = sum(1 for i in ui.values() if i["source"] == "drawn")
        lines.append(f"{len(ui)} UI pieces ({drawn} drawn, {len(ui) - drawn} "
                     f"generated), {nine} nine-slice")
    pal = build.get("palettes")
    if pal:
        w, h = pal["size"]
        lines.append(f"{h} palettes x {w} colours as one {w}x{h} lookup "
                     f"texture ({', '.join(pal['rows'])})")
    font = build.get("font", {}).get("sizes", {})
    if font:
        caps = sorted(int(c) for c in font)
        glyphs = len(next(iter(font.values()))["glyphs"])
        lines.append(f"{glyphs} glyphs at cap heights {caps}")
    return "\n".join(lines)


def main():
    import argparse
    sys.path.insert(0, str(Path(__file__).parent))
    from style import DEFAULT_STYLE
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", default=None,
                    help="style pack to stage (default: cozy_ghibli); stages "
                         "into godot_export/project_<style>/ for a "
                         "non-default style")
    args = ap.parse_args()
    style_name = args.style or DEFAULT_STYLE

    paths = style_paths(style_name)
    if not paths["manifest_path"].exists():
        print(f"no manifest at {paths['manifest_path']} -- run the factory "
              f"first (furnish.py --style {style_name})", file=sys.stderr)
        return 1
    build = stage(style_name)
    print(summarise(build))
    print(f"-> {paths['project_dir'] / 'assets'}")
    print(f"wrote {paths['project_dir'] / 'build_manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
