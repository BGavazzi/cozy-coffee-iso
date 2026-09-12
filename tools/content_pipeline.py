#!/usr/bin/env python3
"""Stage A: turn a design doc + a style pack into an asset-generation manifest.

The user chose to build the design wizard (`design_wizard.py`, stage B)
first, explicitly because its output -- a validated `design_doc.json` -- is
this stage's input. This is the missing link between that document and
`games/tick_tack_toe/pieces.json`'s existing, working shape: a list of
`{id, name, prompt, height, seed}` entries that `game_factory.py` (PR #69,
unmerged as of this file) already knows how to hash, render through the
existing SDXL -> TripoSR -> shade -> review pipeline, and gate for export.

What this module does NOT do, on purpose:

  - Invent a new renderer, mesh pipeline, or review gate. `game_factory.py`
    already owns all of that, for any prompt/height/seed recipe, style-
    conditioned only in the shading stage. Rebuilding it here would be the
    generalization nobody asked for.
  - Inject style-pack language into a subject's prompt. `game_factory.py`'s
    own docstring makes this explicit: "every prompt in this file already
    reads as generic sculpted-figurine description, not style-specific
    vocabulary... style is applied downstream in shading" -- confirmed
    against real prompts in `pieces.json` and `ui_forge.py`'s `UI_PROMPTS`,
    both of which are plain sculptural noun phrases with zero art-direction
    words. `synthesize_prompt()` below follows the same convention:
    `subject["short_desc"]`, wrapped in an article, nothing else.
  - Treat every asset category the same way. `characters`/`props`/`ui`/
    `pieces` all go through this exact prompt-driven SDXL convention in
    this codebase (`concept.py`'s fixed `STYLE` template, `ui_forge.py`'s
    `UI_PROMPTS`, `pieces.json`'s own entries). `tiles` and `fx` do not --
    `tileset.py`'s wall/floor patterns and `fx.py`'s particle primitives
    are procedurally generated from `style.materials`, never from a text
    prompt. Subjects in those categories are reported separately, not
    silently dropped or given a meaningless synthetic prompt.

`validate_manifest()` re-implements (does not import) `game_factory.
prepare()`'s own identity rules -- the project/piece-id regexes and the
duplicate-id and positive-height checks -- because PR #69 has not merged
into this branch's base yet. Kept in sync by inspection; see that
function's docstring for the source and the sync risk this creates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from design_doc import load as load_design_doc
from style import DEFAULT_STYLE, load_style

ROOT = Path(__file__).resolve().parent.parent

# Prompt-driven categories: the ones this codebase actually renders from a
# short sculptural text prompt through SDXL, today, for real (see the
# module docstring). Anything else in ASSET_CATEGORIES is procedural.
CATEGORY_HEIGHT = {
    # Generic upright figure scale; no per-style override -- height is a
    # framing choice for stage 2/5, not an art-direction one, and neither
    # existing style pack varies it for the same subject (see PR #69's
    # README: the same pieces.json heights render clean under both).
    "characters": 1.6,
    # Matches assets.yaml's own measured prop range (0.4-1.1, most props
    # 0.5-1.0) rather than a guess.
    "props": 0.6,
    # Matches ui_forge.py's icon scale precedent -- icons are small and
    # deliberately allowed to be thin shapes (see that module's own note
    # on its looser fill-fraction floor).
    "ui": 0.15,
    # Matches games/tick_tack_toe/pieces.json's own measured convention
    # exactly (every existing piece: height 0.3).
    "pieces": 0.3,
}
PROCEDURAL_CATEGORIES = ("tiles", "fx")

PROJECT_RE = re.compile(r"[a-z0-9_]+")
PIECE_ID_RE = re.compile(r"[a-z0-9_-]+")
# SDXL's CLIP text encoder hard-truncates at 77 tokens and concept.py's own
# NEGATIVE prompt already spends most of that budget (see concept.py's
# comment on the "Frog character from chrono trigger" collage failure this
# caused once). A word isn't a token, so this is a conservative proxy, not
# an exact count -- the point is to fail loudly well before 77, not to
# reproduce CLIP's tokenizer here.
MAX_PROMPT_WORDS = 30


def synthesize_prompt(subject: dict) -> str:
    """A concise, style-agnostic sculptural noun phrase for one subject.

    Deliberately just `subject["short_desc"]` wrapped in an article -- see
    the module docstring for why no style or art-direction language belongs
    here. A design doc's `art_influences` still matters, but downstream, at
    shading time, exactly like every other prompt in this repo.
    """
    desc = subject["short_desc"].strip().rstrip(".")
    if not desc:
        raise ValueError(f"subject {subject['id']!r}: empty short_desc")
    # Strip any article the author already wrote, so exactly one is ever
    # added. Found by an actual generation, not review: "a single round red
    # apple..." (already article-led) came out "an a single round red
    # apple...", a doubled article, because this used to prepend based on
    # desc[0] alone without checking for one already there.
    lowered = desc.lower()
    for existing in ("an ", "a ", "the "):
        if lowered.startswith(existing):
            desc = desc[len(existing):]
            break
    article = "an" if desc[0].lower() in "aeiou" else "a"
    return f"{article} {desc}"


def seed_for(project: str, subject_id: str) -> int:
    """Deterministic per-subject seed, stable under reordering or additions
    to the subjects list -- unlike `pieces.json`'s own hand-assigned
    sequential seeds (41, 42, 43, ...), which only stay stable because a
    human never reorders the file. Content-addressed, same spirit as
    `game_factory.py`'s own build-identity hashing.
    """
    digest = hashlib.sha256(f"{project}:{subject_id}".encode()).hexdigest()
    return int(digest[:8], 16) % 100_000


def _direction(doc: dict) -> str:
    """One short paragraph, matching `pieces.json`'s own top-level
    `direction` field convention (a project-level brief `game_factory.py`
    hashes into build identity but never injects into per-piece prompts) --
    including that field's real precedent for mixing positive and negative
    constraints in one statement (its own tick_tack_toe example: "Armor and
    egg sacs must be visible geometry, not just recolors. No gore.").

    An earlier version of this function only used `target` + `tone`,
    silently dropping `adopt`/`reject` even though a design doc author
    explicitly wrote them as real constraints -- the same class of bug as
    the flat per-category height this pipeline already fixed once (see
    `subject.scale`): real, authored design-doc data reaching the manifest
    and then getting thrown away instead of used.
    """
    influences = doc["art_influences"]
    parts = [influences["target"]]
    if influences["adopt"]:
        parts.append("Adopt: " + "; ".join(influences["adopt"]) + ".")
    if influences["reject"]:
        parts.append("Avoid: " + "; ".join(influences["reject"]) + ".")
    parts.append("Tone: " + ", ".join(doc["tone"]) + ".")
    return " ".join(parts)


def build_manifest(doc: dict, style_name: str = DEFAULT_STYLE) -> tuple[dict, list[dict]]:
    """(manifest, skipped) -- `skipped` names every subject this pipeline
    did not generate a prompt for, and why, so a caller can see the gap
    instead of silently losing subjects.
    """
    style = load_style(style_name)  # fail loudly if the style pack doesn't exist
    pieces = []
    skipped = []
    for subject in doc["subjects"]:
        if subject["category"] not in CATEGORY_HEIGHT:
            skipped.append({
                "id": subject["id"], "category": subject["category"],
                "reason": "procedural producer, not prompt-driven (see "
                          "tileset.py / fx.py); out of scope for this pipeline",
            })
            continue
        pieces.append({
            "id": subject["id"],
            "name": subject["name"],
            "prompt": synthesize_prompt(subject),
            "height": CATEGORY_HEIGHT[subject["category"]] * subject.get("scale", 1.0),
            "seed": seed_for(doc["project"], subject["id"]),
        })
    manifest = {"project": doc["project"], "style": style.name,
               "direction": _direction(doc), "pieces": pieces}
    validate_manifest(manifest)
    return manifest, skipped


def validate_manifest(manifest: dict) -> None:
    """Re-implements `game_factory.prepare()`'s own validation rules
    (project regex `[a-z0-9_]+`, piece-id regex `[a-z0-9_-]+`, positive
    height, no duplicate ids) rather than importing that module, which has
    not merged into this branch's base (PR #69). This is a real,
    acknowledged sync risk, not an oversight -- if those regexes ever
    change there, this needs the matching change here, until this pipeline
    can depend on that module directly.
    """
    if not PROJECT_RE.fullmatch(manifest.get("project", "")):
        raise ValueError(f"Invalid project name: {manifest.get('project')!r}")
    pieces = manifest.get("pieces", [])
    if not pieces:
        raise ValueError("Manifest has no prompt-driven pieces to build")
    ids = [p["id"] for p in pieces]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate piece IDs")
    for p in pieces:
        if not PIECE_ID_RE.fullmatch(p["id"]) or p["height"] <= 0:
            raise ValueError(f"Invalid piece identity or height: {p['id']}")
        words = p["prompt"].split()
        if len(words) > MAX_PROMPT_WORDS:
            raise ValueError(f"{p['id']}: prompt too long ({len(words)} words) -- "
                             f"concept.py's SDXL CLIP encoder truncates at 77 tokens")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("design_doc", type=Path)
    ap.add_argument("--style", default=DEFAULT_STYLE,
                    help=f"style pack name (default: {DEFAULT_STYLE})")
    ap.add_argument("--out", type=Path, required=True,
                    help="where to write the pieces.json-shaped manifest")
    args = ap.parse_args()

    doc = load_design_doc(args.design_doc)
    manifest, skipped = build_manifest(doc, args.style)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    print(f"Wrote {args.out}: {len(manifest['pieces'])} prompt-driven pieces, "
         f"{len(skipped)} skipped (procedural, see below)")
    for s in skipped:
        print(f"  skipped {s['id']} ({s['category']}): {s['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
