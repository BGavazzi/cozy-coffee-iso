#!/usr/bin/env python3
"""Stage every kind of factory output for Godot import.

Reads the three things this repo actually produces and stages them into
`godot_export/project/`:

  out/sprites/manifest.json   static props, 8 fixed direction frames each
  out/sprites/atlas.json      animated characters and FX, packed sheets
  out/ui/                     icons (generated) and chrome (drawn)

into

  assets/<asset>/<asset>_dir<N>.png     one file per prop direction
  assets/anim/<name>.png                one packed sheet per character/effect
  assets/ui/<id>.png                    one file per icon or chrome piece
  build_manifest.json                   the facts `build_all.gd` needs

Copied rather than referenced in place, so Godot's import cache lives outside
the generated `out/` tree and survives a `factory.py --force` re-run without
re-importing everything.

Two of those three had no export path until now, and the gap was structural
rather than neglect: this file only ever read `manifest.json`, whose shape is
"8 direction frames per asset", and neither a packed animation sheet nor a
single-frame icon fits that. `NEXT.md` recorded them as one gap for a reason
-- forcing either into the 8-direction shape would have been worse than
leaving it visible, and they wanted the same fix, which is for the manifest
to have three sections instead of one.

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
ATLAS = ROOT / "out" / "sprites" / "atlas.json"
UI_DIR = ROOT / "out" / "ui"
PROJECT_DIR = ROOT / "godot_export" / "project"
ASSETS_DIR = PROJECT_DIR / "assets"
BUILD_MANIFEST = PROJECT_DIR / "build_manifest.json"


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


def stage(manifest_path: Path = SPRITES_MANIFEST,
          sprites_dir: Path = SPRITES_DIR,
          project_dir: Path = PROJECT_DIR,
          atlas_path: Path = ATLAS,
          ui_dir: Path = UI_DIR) -> dict:
    """Clear `assets/`, stage all three producers, write the build manifest.

    The clear happens once, here, rather than inside each stager -- three
    functions each rmtree-ing a shared directory is a bug waiting for the
    first person who reorders the calls.
    """
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
    ui = build.get("ui", {}).get("icons", {})
    if ui:
        nine = sum(1 for i in ui.values() if "nine_slice" in i)
        drawn = sum(1 for i in ui.values() if i["source"] == "drawn")
        lines.append(f"{len(ui)} UI pieces ({drawn} drawn, {len(ui) - drawn} "
                     f"generated), {nine} nine-slice")
    return "\n".join(lines)


def main():
    if not SPRITES_MANIFEST.exists():
        print(f"no manifest at {SPRITES_MANIFEST} -- run the factory first",
              file=sys.stderr)
        return 1
    build = stage()
    print(summarise(build))
    print(f"-> {ASSETS_DIR}")
    print(f"wrote {BUILD_MANIFEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
