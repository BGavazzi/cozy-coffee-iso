#!/usr/bin/env python3
"""Stage factory sprite output for Godot import.

Reads out/sprites/manifest.json (the factory's per-direction render output)
and stages it into godot_export/project/ as:
  - assets/<asset>/<asset>_dir<N>.png   (copied, so Godot's import cache
    lives outside the generated out/ tree and survives a `factory.py --force`
    re-run without re-importing everything)
  - build_manifest.json   (per-asset world facts + per-direction frame data,
    consumed by build_all.gd to build SpriteFrames resources)

This only stages files -- it does not invoke Godot. See
tools/export_godot.py for the full three-step pipeline (stage, import,
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
PROJECT_DIR = ROOT / "godot_export" / "project"
ASSETS_DIR = PROJECT_DIR / "assets"
BUILD_MANIFEST = PROJECT_DIR / "build_manifest.json"


def stage(manifest_path: Path = SPRITES_MANIFEST, sprites_dir: Path = SPRITES_DIR,
          project_dir: Path = PROJECT_DIR) -> dict:
    manifest = json.loads(manifest_path.read_text())

    by_asset = defaultdict(list)
    for entry in manifest:
        by_asset[entry["asset"]].append(entry)

    assets_dir = project_dir / "assets"
    if assets_dir.exists():
        shutil.rmtree(assets_dir)
    assets_dir.mkdir(parents=True)

    build = {"assets": {}}
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
            src = sprites_dir / e["file"]
            dst = asset_dir / e["file"]
            shutil.copyfile(src, dst)
            frames.append({
                "direction": e["direction"],
                "azimuth": e["azimuth"],
                "file": e["file"],
                "bbox": e["bbox"],
                "pivot": e["pivot"],
                "coverage": e["coverage"],
            })

        build["assets"][asset] = {
            "world": entries[0]["world"],
            "frames": frames,
        }

    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "build_manifest.json").write_text(json.dumps(build, indent=2))
    return build


def main():
    if not SPRITES_MANIFEST.exists():
        print(f"no manifest at {SPRITES_MANIFEST} -- run the factory first", file=sys.stderr)
        return 1
    build = stage()
    n_assets = len(build["assets"])
    n_frames = sum(len(a["frames"]) for a in build["assets"].values())
    print(f"staged {n_assets} assets, {n_frames} frames -> {ASSETS_DIR}")
    print(f"wrote {BUILD_MANIFEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
