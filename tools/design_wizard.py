#!/usr/bin/env python3
"""Ground-up game design wizard.

Elicits a `tools/design_doc.py`-schema design document -- project identity,
core loop, win/lose conditions, camera, tone, art influences, asset
categories, and a seed list of subjects -- and writes a validated
`design_doc.json`. This is deliberately the FIRST stage of the two the user
chose between: a generalist any-2D-game content pipeline (turning a design
doc + art influences into rendered assets, the way `game_factory.py` already
does for one hand-written recipe) needs this document as its input and does
not exist yet.

Two ways to answer each field, freely mixed:

  1. Pre-filled in a `--answers` JSON file (any subset of top-level design-
     doc keys). Useful for scripting a design in one shot, and for tests.
  2. Prompted for interactively (plain `input()`) for whatever `--answers`
     left out.

`--non-interactive` turns a missing answer into a hard failure instead of a
prompt -- for unattended/CI use, so a script never blocks on stdin.

Nothing here calls an external model. Same posture as `local_designer.py`'s
own docstring: this repo treats the agent or human driving the tool as the
creative source already in the loop, not something to route through a
second API. A future batch/LLM-assisted front end can still produce the
`--answers` JSON this wizard consumes -- that is a separate, later concern,
same separation `local_designer.py` draws between proposal and validation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable

from design_doc import ASSET_CATEGORIES, CAMERAS, GENRES, DesignDocError, save, validate

ROOT = Path(__file__).resolve().parent.parent
PromptFn = Callable[[str], str]


def _split(raw: str) -> list[str]:
    return [v.strip() for v in raw.split(",") if v.strip()]


def elicit(answers: dict | None = None, prompt_fn: PromptFn = input) -> dict:
    """Build one design doc from `answers`, prompting via `prompt_fn` for
    anything missing. Same resulting document shape either way -- a fully
    pre-filled `answers` dict never calls `prompt_fn` at all, which is what
    lets tests drive this deterministically and lets a future batch caller
    skip the terminal entirely.
    """
    answers = dict(answers or {})
    doc: dict = {}

    def field(key: str, question: str) -> None:
        doc[key] = answers[key] if key in answers else prompt_fn(question).strip()

    def choice_field(key: str, question: str, options: tuple[str, ...]) -> None:
        value = answers[key] if key in answers else prompt_fn(
            f"{question} ({'/'.join(options)}): ").strip()
        if value not in options:
            raise DesignDocError(f"{key}: {value!r} not in {options}")
        doc[key] = value

    def list_field(key: str, question: str) -> None:
        doc[key] = list(answers[key]) if key in answers else _split(
            prompt_fn(f"{question} (comma-separated): "))

    field("project", "Project name (snake_case): ")
    field("title", "Title: ")
    choice_field("genre", "Genre", GENRES)
    field("core_loop", "Core loop (one paragraph -- what the player does, turn by turn): ")
    field("win_condition", "Win condition: ")
    field("lose_condition", "Lose condition: ")
    choice_field("camera", "Camera", CAMERAS)
    list_field("tone", "Tone words")

    if "art_influences" in answers:
        doc["art_influences"] = dict(answers["art_influences"])
    else:
        print("-- Art influences --")
        doc["art_influences"] = {
            "precedent_games": _split(prompt_fn("Precedent games (comma-separated): ")),
            "adopt": _split(prompt_fn("What to adopt from them (comma-separated): ")),
            "reject": _split(prompt_fn("What to reject, if anything (comma-separated): ")),
            "target": prompt_fn("Target look, one paragraph: ").strip(),
        }

    if "asset_categories" in answers:
        doc["asset_categories"] = list(answers["asset_categories"])
    else:
        doc["asset_categories"] = _split(prompt_fn(
            f"Asset categories, subset of {ASSET_CATEGORIES} (comma-separated): "))

    if "subjects" in answers:
        doc["subjects"] = [dict(s) for s in answers["subjects"]]
    else:
        print("-- Subjects (blank id to finish) --")
        subjects = []
        while True:
            subject_id = prompt_fn("  subject id (blank to finish): ").strip()
            if not subject_id:
                break
            subjects.append({
                "id": subject_id,
                "name": prompt_fn("    name: ").strip(),
                "role": prompt_fn("    role: ").strip(),
                "short_desc": prompt_fn("    short_desc: ").strip(),
                "category": prompt_fn(f"    category {ASSET_CATEGORIES}: ").strip(),
            })
        doc["subjects"] = subjects

    validate(doc)
    return doc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--answers", type=Path,
                    help="JSON file with any subset of design-doc fields pre-filled; "
                         "whatever is missing is prompted for interactively")
    ap.add_argument("--non-interactive", action="store_true",
                    help="fail instead of prompting for any field --answers did not supply")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    answers = json.loads(args.answers.read_text(encoding="utf-8")) if args.answers else {}

    def prompt_fn(question: str) -> str:
        if args.non_interactive:
            raise DesignDocError(f"--non-interactive: no answer supplied for: {question.strip()}")
        return input(question)

    doc = elicit(answers, prompt_fn)
    save(doc, args.out)
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
