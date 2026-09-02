#!/usr/bin/env python3
"""Provenance and staleness: which producer outputs were approved against
which style-pack version, and which of those approvals no longer apply.

This is the mechanism `NEXT.md`'s "Style packs" section calls approval
chaining and precedence flagging. The problem it solves: an approval is only
ever true of a specific (output, upstream version) pair. `portrait.py`'s
roster passing every gate in `gates.py` against `cozy_ghibli` today says
nothing about whether it still would once `cozy_ghibli`'s bible changes
tomorrow -- and today, nothing notices the difference. A silently-stale
approval is worse than no approval, because it reads as done.

The model is deliberately small: one JSON file per style pack (beside its
`bible.yaml`, so `cozy_ghibli`'s lives at the repo root next to
`style_bible.yaml`, matching where its `palette/` already lives), keyed by
`producer:scope`. Recording an entry captures the style bible's content hash
at that moment; checking staleness recomputes the hash and compares. No
version number to remember to bump, no separate changelog to keep in sync --
the bible IS the version, the same way `palette_swap.check_roundtrip` treats
image bytes as the ground truth rather than a change log.

This does not decide WHAT counts as approved -- that is still `gates.py`'s
deterministic checks plus, eventually, a human. It only remembers that a
decision was made, against what, and whether that "what" has since moved.

    python tools/lockfile.py --status [--style NAME]
    python tools/lockfile.py --record PRODUCER SCOPE --gates g1,g2 [--style NAME]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from style import Style, load_style  # noqa: E402


def style_hash(style: Style) -> str:
    """Short content hash of the bible this style pack was built from.

    Deliberately the bible file itself, not a version field inside it --
    a version field is one more thing an edit can forget to bump, and the
    forged palette + rig + materials are all derived from these exact bytes
    anyway, so hashing them is hashing everything downstream depends on.
    """
    return hashlib.sha256(style.bible_path.read_bytes()).hexdigest()[:16]


def lock_path(style: Style) -> Path:
    return style.bible_path.parent / "lock.json"


def load_lock(style: Style) -> dict:
    p = lock_path(style)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def record(style: Style, producer: str, scope: str, gates: list[str],
          approved: bool = True) -> dict:
    """Record that `producer`'s `scope` output was checked against `gates`
    and (dis)approved, at the style bible's current content hash."""
    lock = load_lock(style)
    key = f"{producer}:{scope}"
    entry = {
        "producer": producer,
        "scope": scope,
        "style": style.name,
        "style_hash": style_hash(style),
        "gates": gates,
        "approved": approved,
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    lock[key] = entry
    lock_path(style).write_text(
        json.dumps(lock, indent=2, sort_keys=True), encoding="utf-8")
    return entry


def staleness_report(style: Style) -> list[str]:
    """Every APPROVED entry whose style hash no longer matches the bible's
    current one. Not a failure -- a flag. Whether the drift actually matters
    for a given entry is a call for the gates that produced it to re-answer,
    or for a human, same as `layout.py`'s overlap check: proportional, not
    binary."""
    lock = load_lock(style)
    current = style_hash(style)
    out = []
    for key, entry in sorted(lock.items()):
        if entry.get("approved") and entry.get("style_hash") != current:
            out.append(f"{key}: approved against {entry['style_hash']}, "
                       f"{style.name} is now {current} -- needs re-review")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", default="cozy_ghibli")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--record", nargs=2, metavar=("PRODUCER", "SCOPE"))
    ap.add_argument("--gates", default="", help="comma-separated gate names")
    ap.add_argument("--reject", action="store_true",
                    help="with --record, store approved: false")
    args = ap.parse_args()

    style = load_style(args.style)

    if args.record:
        producer, scope = args.record
        gates = [g for g in args.gates.split(",") if g]
        entry = record(style, producer, scope, gates, approved=not args.reject)
        print(f"recorded {producer}:{scope} -> approved={entry['approved']} "
              f"at {entry['style_hash']}")
        return 0

    lock = load_lock(style)
    current = style_hash(style)
    print(f"{style.name}  bible hash {current}  {len(lock)} entrie(s) locked")
    for key, entry in sorted(lock.items()):
        stale = entry.get("approved") and entry.get("style_hash") != current
        state = "STALE" if stale else ("approved" if entry.get("approved") else "rejected")
        print(f"  {key:<30s} {state:<9s} {entry.get('style_hash', '?')}  "
              f"gates: {', '.join(entry.get('gates', [])) or '(none recorded)'}")

    stale = staleness_report(style)
    if stale:
        print(f"\n{len(stale)} stale approval(s):")
        for s in stale:
            print(f"  - {s}")
        return 1
    if not args.status and not lock:
        print("\nnothing locked yet")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
