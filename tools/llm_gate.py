#!/usr/bin/env python3
"""The structural home for `gates.py`'s `llm` kind: a rubric-driven judgment
call, applied by a vision-capable model rather than approximated by an
ever-more-specific numeric proxy.

No external API is wired here, and that is a real choice, not a placeholder
waiting on one. The agent operating this repo -- the one that found the
eye-occlusion bug in `portrait.py` by rendering an image and looking at it,
the one this whole pipeline has never shipped a feature without asking to
open a proof sheet -- IS a vision-capable LLM, already in the loop for every
judgment call this pipeline has ever needed. Routing that same judgment
through this file rather than a third-party API costs nothing extra, commits
to no vendor, and needs no credential to manage or secret to leak. A future
automated backend -- an actual API call, for judging at a volume no
interactive session could keep up with -- is a real next step and a real
cost/vendor decision, deliberately not made here. `RUBRICS` is the stable
contract either backend judges against, so that decision, whenever it's
made, doesn't touch anything upstream of it.

Workflow, today: a rubric names the question. Whoever -- or whatever -- judges
it records a `Verdict` through `record`, which folds into the SAME
`lock.json` a deterministic `--lock` call writes (`lockfile.py`), so
staleness tracking (`NEXT.md`, "Style packs") covers both kinds identically:
an LLM verdict goes stale exactly the way a deterministic gate's does, when
the style it was judged against changes underneath it.

    python tools/llm_gate.py --list
    python tools/llm_gate.py --record focal_hierarchy --pass \
        --reasoning "..." --judge claude-sonnet-5 \
        --producer build_plan.py --scope "proof/shop_big.png"
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from style import load_style  # noqa: E402


@dataclass(frozen=True)
class Rubric:
    name: str
    gate: str          # matches a gates.py Gate.name
    question: str       # the judgment actually being asked
    passes_when: str    # what a PASS concretely looks like, so two different
                        # judges (human, model, future API) apply the same bar


RUBRICS: dict[str, Rubric] = {
    "focal_hierarchy": Rubric(
        name="focal_hierarchy",
        gate="focal_hierarchy (planned)",
        question="Does this room's service counter read as the thing the "
                 "eye lands on first, before anything else in the frame?",
        passes_when="A viewer glancing at the image for under a second "
                    "would name the counter -- not the floor, a wall, or a "
                    "piece of furniture -- as the first thing they noticed.",
    ),
}


@dataclass(frozen=True)
class Verdict:
    rubric: str
    passed: bool
    reasoning: str
    judge: str   # who/what rendered this verdict, e.g. "claude-sonnet-5"


def record(style_name: str, producer: str, scope: str, verdict: Verdict,
          extra_gates: list[str] | None = None) -> dict:
    """Fold an LLM verdict into the same lock.json a deterministic --lock
    call writes. `scope` should identify what was actually judged (a file
    path is fine) so a later re-run of the same rubric on the same output is
    a distinct, comparable entry."""
    import lockfile
    style = load_style(style_name)
    gates = [f"llm:{verdict.rubric}"] + (extra_gates or [])
    entry = lockfile.record(style, producer, scope, gates,
                            approved=verdict.passed)
    entry["llm_verdict"] = {
        "rubric": verdict.rubric, "reasoning": verdict.reasoning,
        "judge": verdict.judge,
    }
    lock = lockfile.load_lock(style)
    lock[f"{producer}:{scope}"] = entry
    lockfile.lock_path(style).write_text(
        __import__("json").dumps(lock, indent=2, sort_keys=True),
        encoding="utf-8")
    return entry


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--record", metavar="RUBRIC")
    ap.add_argument("--pass", dest="passed", action="store_true")
    ap.add_argument("--fail", dest="passed", action="store_false")
    ap.set_defaults(passed=None)
    ap.add_argument("--reasoning", default="")
    ap.add_argument("--judge", default="")
    ap.add_argument("--producer", default="")
    ap.add_argument("--scope", default="")
    ap.add_argument("--style", default="cozy_ghibli")
    args = ap.parse_args()

    if args.list:
        for r in RUBRICS.values():
            print(f"{r.name}\n  gate:   {r.gate}\n  asks:   {r.question}\n"
                  f"  passes: {r.passes_when}\n")
        return 0

    if args.record:
        if args.record not in RUBRICS:
            print(f"unknown rubric {args.record!r}; --list to see them",
                  file=sys.stderr)
            return 1
        if args.passed is None or not args.reasoning or not args.judge \
                or not args.producer or not args.scope:
            print("--record needs --pass/--fail --reasoning --judge "
                  "--producer --scope", file=sys.stderr)
            return 1
        v = Verdict(rubric=args.record, passed=args.passed,
                    reasoning=args.reasoning, judge=args.judge)
        entry = record(args.style, args.producer, args.scope, v)
        print(f"recorded {args.producer}:{args.scope} -> "
              f"{'PASS' if entry['approved'] else 'FAIL'} ({args.judge})")
        return 0

    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
