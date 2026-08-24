#!/usr/bin/env python3
"""Full factory-output -> Godot pipeline: stage, import, build.

    python tools/export_godot.py [--godot-bin PATH]

Three steps, each a real dependency of the next (see ART_CRITIQUE.md /
NEXT.md "Godot export" notes for why the order matters -- Godot's resource
loader refuses an un-imported PNG, and the workaround of loading pixels
directly serializes a bloated inline blob instead of a lightweight resource
reference):

  1. package_godot.py   copies out/sprites/*.png + manifest facts into
                         godot_export/project/, gitignored (regenerated from
                         the factory output every run)
  2. `godot --import`   headless import pass, produces .import sidecars so
                         the PNGs become real, file-backed Texture2D
                         resources
  3. build_all.gd        builds one SpriteFrames resource per asset
                         (8 direction frames + world-fact metadata) into
                         godot_export/project/resources/

Needs a Godot 4.3 binary. Resolved in this order: --godot-bin, $GODOT_BIN,
then D:/vibes/.godot-tool/Godot_v4.3-stable_win64_console.exe (the portable
build downloaded for this project, kept outside the repo).
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECT_DIR = ROOT / "godot_export" / "project"
DEFAULT_GODOT = Path("D:/vibes/.godot-tool/Godot_v4.3-stable_win64_console.exe")


def find_godot(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    env = os.environ.get("GODOT_BIN")
    if env:
        return Path(env)
    return DEFAULT_GODOT


def run_godot(godot_bin: Path, args: list[str]) -> None:
    cmd = [str(godot_bin), "--headless", "--path", str(PROJECT_DIR)] + args
    print("$", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise SystemExit(f"godot exited {result.returncode}: {' '.join(cmd)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--godot-bin", default=None, help="path to Godot 4.3 executable")
    args = ap.parse_args()

    godot_bin = find_godot(args.godot_bin)
    if not godot_bin.exists():
        raise SystemExit(
            f"Godot binary not found at {godot_bin}\n"
            "Pass --godot-bin, set $GODOT_BIN, or download Godot 4.3 stable to "
            f"{DEFAULT_GODOT}"
        )

    sys.path.insert(0, str(ROOT / "tools"))
    import package_godot
    build = package_godot.stage()
    n_assets = len(build["assets"])
    n_frames = sum(len(a["frames"]) for a in build["assets"].values())
    print(f"staged {n_assets} assets, {n_frames} frames")

    print("\n-- import pass --")
    run_godot(godot_bin, ["--import"])

    print("\n-- build pass --")
    run_godot(godot_bin, ["--script", "build_all.gd"])

    resources = sorted((PROJECT_DIR / "resources").glob("*.tres"))
    print(f"\n{len(resources)} SpriteFrames resources written to {PROJECT_DIR / 'resources'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
