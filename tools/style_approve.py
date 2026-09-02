#!/usr/bin/env python3
"""Is this style pack actually approved for use, or just declared?

This is the "one of each asset class, approved, placed in engine" gate,
made checkable rather than a step someone has to remember to do by eye.
`cozy_ghibli` already satisfies it today, but only because `render_room.py`'s
whole-shop composite and `export_godot.py`'s Godot export happen to cover
every class this game needs -- nothing before this file made that an
explicit, re-checkable requirement a NEW style pack (the SNES-flavoured one,
or any future one) has to clear before it is safe to generate a real asset
library against.

Approval is computed entirely from `lock.json` (`lockfile.py`) -- no new
state, no new ceremony. A style pack is approved when, at its bible's
CURRENT content hash:

    - at least one producer covering character geometry has an approved,
      current entry (today: `character.py` and/or `portrait.py`)
    - the palette itself has an approved, current entry (`palette_forge.py`)
    - at least one `llm`-judged composition verdict exists, approved, current
      -- the actual "does this read as one coherent world" question, which
      is exactly what `llm_gate.py`'s `focal_hierarchy` rubric asks

That is deliberately not "every gate in `gates.py` passes" -- most of those
are per-producer regression checks, not questions about whether a STYLE
holds together. It is the smallest real evidence that someone actually
looked at this style's characters, its palette, and a composed scene, and
signed off, recently enough that none of it has drifted since.

    python tools/style_approve.py --style cozy_ghibli
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lockfile import load_lock, style_hash  # noqa: E402
from style import load_style  # noqa: E402

# producer -> what evidence it's meant to stand for, for the printed report.
REQUIRED_PRODUCERS = {
    "character.py": "a character roster was built and checked",
    "palette_forge.py": "the palette was forged and validated",
}
# At least one of these producers must have an approved, current entry --
# any is real evidence a character reads correctly in this style.
# `organic_rig.py` added alongside its own first style (`snes_rpg`): for a
# style whose rig.primitive is cylinder_sphere, it is the ONLY one of the
# three that actually builds that style's declared geometry today --
# `character.py` still only knows box/prism (see NEXT.md, the import-order
# gap), so requiring it specifically would make a cylinder/sphere style
# permanently unapprovable on a technicality unrelated to whether its
# characters actually read correctly.
REQUIRED_PRODUCERS_ANY_OF = ("character.py", "portrait.py", "organic_rig.py")

# At least one approved, current llm verdict using this rubric, on any scope.
REQUIRED_LLM_RUBRICS = ("focal_hierarchy",)


def approval_report(style_name: str) -> tuple[bool, list[str]]:
    style = load_style(style_name)
    lock = load_lock(style)
    current = style_hash(style)

    def current_approved(pred) -> bool:
        return any(pred(e) and e.get("approved") and e.get("style_hash") == current
                  for e in lock.values())

    reasons: list[str] = []

    if not any(current_approved(lambda e, p=p: e.get("producer") == p)
              for p in REQUIRED_PRODUCERS_ANY_OF):
        reasons.append(f"no approved, current character-roster entry from "
                       f"any of {REQUIRED_PRODUCERS_ANY_OF}")

    if not current_approved(lambda e: e.get("producer") == "palette_forge.py"):
        reasons.append("no approved, current palette_forge.py entry")

    for rubric in REQUIRED_LLM_RUBRICS:
        gate = f"llm:{rubric}"
        if not current_approved(lambda e, g=gate: g in e.get("gates", [])):
            reasons.append(f"no approved, current llm:{rubric} verdict on "
                           f"any scope")

    return not reasons, reasons


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", default="cozy_ghibli")
    args = ap.parse_args()

    ok, reasons = approval_report(args.style)
    if ok:
        print(f"{args.style}: APPROVED for use")
        return 0
    print(f"{args.style}: NOT approved")
    for r in reasons:
        print(f"  - {r}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
