#!/usr/bin/env python3
"""Style packs: the swappable art-direction layer.

The rest of this pipeline was written against one art direction --
`style_bible.yaml`'s Ghibli-through-pixel-constraints look -- with palette
already computed from data (`palette_forge.py`) but character proportions,
material-role names and check thresholds either hardcoded in `character.py`/
`assetlib.py`/`art_review.py` or simply absent as a concept. This is the
loader for a second kind of style pack, so a wholly different art direction
(the first target: SNES-JRPG-flavoured) can be declared as data instead of a
fork of the code.

A style pack is one `bible.yaml`, either the existing root `style_bible.yaml`
(name `cozy_ghibli`, kept exactly where every current script already expects
it -- no path migration, no regression risk for the default case) or
`styles/<name>/bible.yaml` for anything else. Every pack extends the same
schema `style_bible.yaml` already used (`art_direction` / `palette` /
`rendering` / `decisions`) with three more top-level keys:

    materials:  semantic role -> material token. Replaces `assetlib.py`'s
                WOOD/CERAMIC/GLASS/... constants, which today hardcode this
                palette's literal ramp names. NOT YET WIRED into assetlib.py
                -- see the module docstring there for why (function default
                arguments bind at *def* time, before any `--style` flag has
                been parsed, so switching them needs either an early args-peek
                or converting every default to a lazy lookup; that is real,
                separate work, not done here).
    rig:        character proportions + primitive vocabulary + target
                resolution. Recorded for `cozy_ghibli` with values identical
                to `character.py`'s own module constants, kept in sync by
                hand until the promotion described in NEXT.md lands. Also not
                yet consumed by `character.py`.
    checks:     per-style overrides for the numeric floors `character.py` and
                `art_review.py` hardcode (contrast gaps, silhouette pixel
                floor, ...). Empty for `cozy_ghibli` -- those floors were each
                set from a real measurement run against this rig and this
                palette, and a new style earns its own the same way, once it
                has real renders to measure rather than a guess.

    python tools/style.py --list          # every style pack found
    python tools/style.py --check NAME    # bible loads, required keys present
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
STYLES_DIR = ROOT / "styles"
DEFAULT_STYLE = "cozy_ghibli"

# assetlib.py's material-role constants, unchanged in meaning -- see that
# module's WOOD/CERAMIC/PLANT/FABRIC/METAL/GLASS/GLASS_EDGE/WALL_FIELD/
# FLOOR_FIELD. Every style pack must declare all nine so a missing role fails
# loudly at load time rather than silently rendering through whatever a stale
# default happens to point at.
REQUIRED_MATERIAL_ROLES = (
    "wood", "ceramic", "plant", "fabric", "metal",
    "glass", "glass_edge", "wall_field", "floor_field",
)


@dataclass
class Style:
    name: str
    bible_path: Path
    palette_dir: Path
    bible: dict
    materials: dict[str, str] = field(default_factory=dict)
    rig: dict = field(default_factory=dict)
    checks: dict = field(default_factory=dict)

    @property
    def palette_path(self) -> Path:
        return self.palette_dir / "palette.json"


def _resolve_paths(name: str) -> tuple[Path, Path]:
    """(bible_path, palette_dir) for a style name.

    `cozy_ghibli` resolves to the existing root files -- the ones every
    script's own default already points at -- rather than a `styles/`
    subdirectory, so adding this loader changes nothing about where the
    current game's palette lives or what path every unflagged script call
    already resolves to.
    """
    if name == DEFAULT_STYLE:
        return ROOT / "style_bible.yaml", ROOT / "palette"
    return STYLES_DIR / name / "bible.yaml", STYLES_DIR / name / "palette"


def available_styles() -> list[str]:
    names = [DEFAULT_STYLE]
    if STYLES_DIR.exists():
        names += sorted(p.name for p in STYLES_DIR.iterdir()
                        if p.is_dir() and (p / "bible.yaml").exists())
    return names


def load_style(name: str = DEFAULT_STYLE) -> Style:
    bible_path, palette_dir = _resolve_paths(name)
    if not bible_path.exists():
        raise SystemExit(f"no style pack {name!r} (looked for {bible_path}); "
                         f"available: {available_styles()}")
    bible = yaml.safe_load(bible_path.read_text(encoding="utf-8"))

    materials = bible.get("materials", {})
    missing = [r for r in REQUIRED_MATERIAL_ROLES if r not in materials]
    if missing:
        raise SystemExit(f"style {name!r}: bible.yaml materials: is missing "
                         f"{missing}")

    return Style(name=name, bible_path=bible_path, palette_dir=palette_dir,
                bible=bible, materials=materials,
                rig=bible.get("rig", {}), checks=bible.get("checks", {}))


def add_style_arg(ap: argparse.ArgumentParser) -> None:
    """Shared `--style` flag for entry-point scripts. Default preserves
    today's exact behaviour -- the root `style_bible.yaml` and `palette/`."""
    ap.add_argument("--style", default=DEFAULT_STYLE,
                    help=f"style pack name (default: {DEFAULT_STYLE}); "
                         f"see styles/<name>/bible.yaml")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--check", metavar="NAME")
    args = ap.parse_args()

    if args.list:
        for name in available_styles():
            print(name)
        return 0

    if args.check:
        style = load_style(args.check)
        print(f"{style.name}: bible ok, {len(style.materials)} material roles, "
              f"{len(style.rig)} rig keys, {len(style.checks)} check overrides")
        return 0

    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
