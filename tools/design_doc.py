#!/usr/bin/env python3
"""Schema and validation for a game design document.

This is the artifact `tools/design_wizard.py` produces and a future
generalist content pipeline (any 2D game style, from a design doc + art
influences) will consume as input. It sits one abstraction level above
`games/*/pieces.json`: a design doc names subjects and intent ("a tick,
mischievous, small"), not literal SDXL prompts or per-piece traits/seeds --
turning a subject into a rendered prompt is the content pipeline's job, not
this schema's.

`art_influences` deliberately mirrors `style_bible.yaml`'s own
`art_direction: {target, precedent, adopt, reject}` block shape (see the
root `style_bible.yaml`) rather than inventing a new vocabulary -- a design
doc's art influences and a style bible's art direction are the same kind of
statement made at two different times by two different roles (design intent
first, then a style pack that may or may not fully realise it), and keeping
the shape identical means a future tool can compare or fold one into the
other without a translation layer.

Validation follows this repo's existing rigor in `tools/game_factory.py`'s
`prepare()`: explicit regex identity checks, duplicate-ID rejection, closed
enums for the fields that drive downstream code branches (genre, camera),
open free text for the fields that only drive creative judgment (tone,
core_loop, art_influences prose). Fail loudly and specifically; never
silently coerce or drop an invalid field.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

PROJECT_RE = re.compile(r"[a-z0-9_]+")
SUBJECT_ID_RE = re.compile(r"[a-z0-9_-]+")

# Closed enums: fields a downstream pipeline will branch on. New values are
# a deliberate schema change, not a typo a validator should shrug past.
GENRES = ("tabletop", "arcade", "puzzle", "roguelike", "platformer", "adventure", "sim")
CAMERAS = ("top_down", "isometric", "side_view", "portrait_grid")
ASSET_CATEGORIES = ("characters", "props", "ui", "tiles", "pieces", "fx")

REQUIRED_STRINGS = ("project", "title", "genre", "core_loop",
                     "win_condition", "lose_condition", "camera")


class DesignDocError(ValueError):
    """A design document failed validation. Message names the exact field."""


def _require_str(doc: dict, field: str) -> None:
    value = doc.get(field)
    if not isinstance(value, str) or not value.strip():
        raise DesignDocError(f"{field}: required non-empty string")


def _require_str_list(doc: dict, field: str, allow_empty: bool = False) -> None:
    value = doc.get(field)
    if not isinstance(value, list) or (not allow_empty and not value):
        raise DesignDocError(f"{field}: required non-empty list of strings")
    if not all(isinstance(v, str) and v.strip() for v in value):
        raise DesignDocError(f"{field}: every entry must be a non-empty string")


def validate(doc: dict) -> None:
    """Raise DesignDocError on the first structural problem found.

    Mirrors `game_factory.prepare()`'s discipline: validate the whole
    document before any caller treats it as usable, not field-by-field as
    a caller happens to read it.
    """
    if not isinstance(doc, dict):
        raise DesignDocError("design doc must be a JSON object")

    if not PROJECT_RE.fullmatch(doc.get("project", "")):
        raise DesignDocError("project: must be snake_case (a-z0-9_ only)")

    for field in REQUIRED_STRINGS:
        if field == "project":
            continue
        _require_str(doc, field)

    if doc["genre"] not in GENRES:
        raise DesignDocError(f"genre: {doc['genre']!r} not in {GENRES}")
    if doc["camera"] not in CAMERAS:
        raise DesignDocError(f"camera: {doc['camera']!r} not in {CAMERAS}")

    _require_str_list(doc, "tone")

    influences = doc.get("art_influences")
    if not isinstance(influences, dict):
        raise DesignDocError("art_influences: required object")
    _require_str_list(influences, "precedent_games")
    _require_str_list(influences, "adopt")
    _require_str_list(influences, "reject", allow_empty=True)
    if "target" not in influences:
        raise DesignDocError("art_influences.target: required")
    _require_str(influences, "target")

    categories = doc.get("asset_categories")
    if not isinstance(categories, list) or not categories:
        raise DesignDocError("asset_categories: required non-empty list")
    unknown = [c for c in categories if c not in ASSET_CATEGORIES]
    if unknown:
        raise DesignDocError(f"asset_categories: unknown {unknown}, "
                             f"must be a subset of {ASSET_CATEGORIES}")

    subjects = doc.get("subjects")
    if not isinstance(subjects, list) or not subjects:
        raise DesignDocError("subjects: required non-empty list")
    seen_ids = set()
    for i, subject in enumerate(subjects):
        if not isinstance(subject, dict):
            raise DesignDocError(f"subjects[{i}]: must be an object")
        for field in ("id", "name", "role", "short_desc"):
            _require_str(subject, field)
        if not SUBJECT_ID_RE.fullmatch(subject["id"]):
            raise DesignDocError(f"subjects[{i}].id: {subject['id']!r} "
                                 f"must match [a-z0-9_-]+")
        if subject["id"] in seen_ids:
            raise DesignDocError(f"subjects: duplicate id {subject['id']!r}")
        seen_ids.add(subject["id"])
        # A closed enum, not free text like `role` -- a content pipeline
        # needs to know which default height/geometry bucket a subject
        # belongs to without guessing from prose. Must also be one of the
        # doc's own declared `asset_categories`, so a design doc can never
        # name a subject in a category it didn't say the game would need.
        category = subject.get("category")
        if category not in ASSET_CATEGORIES:
            raise DesignDocError(f"subjects[{i}].category: {category!r} "
                                 f"not in {ASSET_CATEGORIES}")
        if category not in categories:
            raise DesignDocError(f"subjects[{i}].category: {category!r} not "
                                 f"in this doc's own asset_categories {categories}")
        # Optional relative size multiplier against whatever baseline height
        # a downstream pipeline assigns `category` -- NOT an absolute height,
        # because `category` is the semantic bucket (a subject is "a
        # character") and a design doc has no business declaring pipeline-
        # specific absolute measurements. Added after a real, measured gap:
        # a wasp and the player fox both landing in `characters` gave them
        # the same generic upright-figure height with no way to say "this
        # one instance is small." Defaults to 1.0 (trust the category
        # baseline) so every subject that doesn't need this stays terse.
        if "scale" in subject:
            scale = subject["scale"]
            if not isinstance(scale, (int, float)) or isinstance(scale, bool) or scale <= 0:
                raise DesignDocError(f"subjects[{i}].scale: must be a positive number")


def load(path: Path) -> dict:
    doc = json.loads(path.read_text(encoding="utf-8"))
    validate(doc)
    return doc


def save(doc: dict, path: Path) -> None:
    """Validate, then write. Never write a document this module would reject."""
    validate(doc)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
