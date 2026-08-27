#!/usr/bin/env python3
"""Full factory-output -> Godot pipeline: stage, import, build.

    python tools/export_godot.py [--godot-bin PATH]

Three steps, each a real dependency of the next (see ART_CRITIQUE.md /
NEXT.md "Godot export" notes for why the order matters -- Godot's resource
loader refuses an un-imported PNG, and the workaround of loading pixels
directly serializes a bloated inline blob instead of a lightweight resource
reference):

  1. package_godot.py   copies out/sprites/*.png, the packed animation
                         sheets and out/ui/ into godot_export/project/,
                         gitignored (regenerated from factory output every
                         run)
  2. `godot --import`   headless import pass, produces .import sidecars so
                         the PNGs become real, file-backed Texture2D
                         resources
  3. build_all.gd        builds SpriteFrames for props (8 direction frames +
                         world facts) and for characters/FX (one animation
                         per clip and facing), and StyleBoxTexture for
                         nine-slice UI chrome, into
                         godot_export/project/resources/
  4. a round-trip check  re-reads the written .tres files and compares the
                         nine-slice margins against build_manifest.json

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


def check_nine_slice_roundtrip(build: dict) -> list[str]:
    """Do the margins in the written .tres match the insets that were drawn?

    Godot names its four texture margins left/top/right/bottom and
    `ui_chrome` names its insets in that same order, which is exactly the
    kind of agreement that is true until someone reorders one of them. The
    failure would be silent -- a frame that stretches with the wrong corner
    fixed still loads, still renders, and only looks subtly wrong in a
    running game.

    What this does NOT verify is the engine's own stretch. Godot's headless
    mode has no renderer, so the nine-slice can be checked as data here and
    is checked as pixels only on the Python side, through
    `ui_chrome.expand()` and `preview_ui.py`. Stated rather than glossed:
    the two implementations agree by construction and by margin, not by
    a compared render.
    """
    out = []
    icons = build.get("ui", {}).get("icons", {})
    keys = ("texture_margin_left", "texture_margin_top",
            "texture_margin_right", "texture_margin_bottom")
    for name, info in sorted(icons.items()):
        if "nine_slice" not in info:
            continue
        tres = PROJECT_DIR / "resources" / "ui" / f"{name}.tres"
        if not tres.exists():
            out.append(f"{name}: declares nine-slice insets but no "
                       f"StyleBoxTexture was written to {tres}")
            continue
        text = tres.read_text(encoding="utf-8")
        got = []
        for k in keys:
            for line in text.splitlines():
                if line.startswith(k + " ="):
                    got.append(int(float(line.split("=", 1)[1])))
                    break
            else:
                got.append(None)
        if got != list(info["nine_slice"]):
            out.append(f"{name}: drawn insets {info['nine_slice']} but "
                       f"{tres.name} carries {got} -- left/top/right/bottom "
                       f"ordering disagrees somewhere")
    if icons and not out:
        n = sum(1 for i in icons.values() if "nine_slice" in i)
        print(f"  {n} nine-slice margins match the drawn insets")
    return out


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
    print(package_godot.summarise(build))

    print("\n-- import pass --")
    run_godot(godot_bin, ["--import"])

    print("\n-- build pass --")
    run_godot(godot_bin, ["--script", "build_all.gd"])

    print("\n-- round-trip check --")
    problems = check_nine_slice_roundtrip(build)
    for p in problems:
        print(f"  BLOCKER  {p}", file=sys.stderr)

    resources = sorted((PROJECT_DIR / "resources").rglob("*.tres"))
    print(f"\n{len(resources)} resources written to "
          f"{PROJECT_DIR / 'resources'}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
