#!/usr/bin/env python3
"""The gate catalog: every automated pass-or-fail judgment this pipeline makes,
named and classified in one place.

The premise this file operationalizes: taste is the one thing a machine
cannot be handed. Everything else -- is this palette-exact, does this eye
render enough pixels to read as an eye, does this room have a focal point --
is a matter of finding the right gate for the specific problem. This repo
already has 62 of them, built one hard-won defect at a time, scattered as
`check_*` functions across twenty files with no shared vocabulary. This file
does not replace any of them; it catalogs them, so "what actually has to be
true before this ships" is a question with a queryable answer instead of a
grep.

Three kinds, in the order a real review actually applies them:

    deterministic   pure math/geometry/pixel-index checks -- everything this
                    repo has shipped so far. Cheap, exhaustive, no API call,
                    and the honest majority of what "passable" means here.
    llm             a vision-capable model asked to judge something no
                    numeric floor captures well. NONE are wired yet -- see
                    `PLANNED_LLM_GATES` below for why the composition/focal-
                    hierarchy family is the strongest candidate, and why
                    wiring one is a deliberate decision (which model, what it
                    costs, how credentials are handled) rather than a data
                    change like this catalog.
    taste           the human looking at the proof sheet. Every feature this
                    repo has shipped -- palette variants, the font, portraits
                    -- passed every automated gate and STILL waited on a
                    human opening the PNG before it was called done. That is
                    not a gap in the automation; it is the one gate that
                    stays a gate on purpose.

    python tools/gates.py --list                # every gate, grouped by kind
    python tools/gates.py --list deterministic   # one kind only
    python tools/gates.py --producer character.py  # one producer's gates
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass

KINDS = ("deterministic", "llm", "taste")


@dataclass(frozen=True)
class Gate:
    name: str            # the check_* function name, or a taste-gate's own name
    producer: str        # file it lives in (blank for a taste gate: it lives nowhere)
    kind: str            # one of KINDS
    rationale: str       # the check's own first docstring line, verbatim where one exists
    scope: str           # what this gate is evaluated against -- one sprite, a
                         # roster, a whole room, a library -- since that is what
                         # determines when re-running it is even meaningful


# --- deterministic ------------------------------------------------------
# Sourced from every `check_*` function's own docstring (first line), not
# re-described by hand, so this catalog cannot drift into claiming a check
# does something it does not. `rationale` blank means the function's own
# docstring is blank too -- recorded honestly rather than invented.

_DETERMINISTIC = [
    # (producer, name, rationale, scope)
    ("animate.py", "check_direction_labels", "", "sprite direction set"),
    ("art_review.py", "check_alpha", "", "one sprite"),
    ("art_review.py", "check_palette", "", "one sprite"),
    ("art_review.py", "check_ramp_coherence",
     "Look for shading that wanders between ramps.", "one sprite"),
    ("art_review.py", "check_grid",
     "Detect art that was upscaled and is no longer on its native pixel grid.",
     "one sprite"),
    ("art_review.py", "check_extremes", "", "one sprite"),
    ("art_review.py", "check_light_direction",
     "Highlights should sit upper-left. A rough check, hence only a note.",
     "one sprite"),
    ("art_review.py", "check_silhouette", "", "one sprite"),
    ("art_review.py", "check_speckle",
     "Pixels that match none of their four neighbours.", "one sprite"),
    ("art_review.py", "check_member_thickness",
     "Thinnest drawn member, measured rather than modelled.", "one mesh"),
    ("art_review.py", "check_spread_floor_regression",
     "Prove DEFAULT_SPREAD_FLOOR and CLOSEST_PAIR_FLOOR are not redundant.",
     "generator suite"),
    ("art_review.py", "check_generator_range",
     "Do the seeded generators actually generate different shapes?",
     "generator suite"),
    ("art_review.py", "check_symmetry_claims",
     "Cross-check every declared symmetry class against measured geometry.",
     "asset manifest"),
    ("art_review.py", "check_buried_detail",
     "Front-facing geometry that is nonetheless completely hidden.", "one mesh"),
    ("bitmap_font.py", "check_distinct",
     "Do any two glyphs rasterise to the same pixels?", "font, one cap height"),
    ("bitmap_font.py", "check_counters",
     "Does every glyph that should have a hole still have one?",
     "font, one cap height"),
    ("bitmap_font.py", "check_bounds",
     "Ink inside its own cell, on the baseline, and descending only where "
     "it should.", "font, one cap height"),
    ("bitmap_font.py", "check_pairs",
     "No two adjacent glyphs' ink may touch, in any ordered pair.",
     "font, one cap height"),
    ("bitmap_font.py", "check_render",
     "Rendered text held to the UI gate, at the same threshold.", "one string"),
    ("build_plan.py", "check_stool_occupancy",
     "Somebody must actually be sitting at the window bars.", "generated room"),
    ("build_plan.py", "check_focal_contrast",
     "A generated room's counter must still read as the place to look.",
     "generated room"),
    ("build_plan.py", "check_built_rooms",
     "Every room built from a generated plan must satisfy the room checks.",
     "generated room batch"),
    ("character.py", "check_contrast",
     "Hair that sits too close to skin in lightness merges into the face.",
     "roster"),
    ("character.py", "check_roster_variety",
     "Are any two characters in this cast the same person?", "roster"),
    ("character.py", "check_accessory_distinct",
     "Every accessory must read as a different thing from every other one.",
     "accessory set"),
    ("character.py", "check_cast_silhouette",
     "Are any two characters in this cast the same SHAPE?", "roster"),
    ("character.py", "check_eye_legibility",
     "Can the eyes be seen, at every skin tone the generator may draw?",
     "roster x skin tones"),
    ("character.py", "check_spec_coverage",
     "Does every dimension of the generator actually vary?", "generator"),
    ("character.py", "check_waistline",
     "A shirt and trousers that resolve to the same value have no edge "
     "between them.", "roster"),
    ("character.py", "check_palette_spread",
     "No character may spend more than max_share of its parts on one ramp.",
     "roster"),
    ("character.py", "check_direction_stability",
     "Every direction must stay above a readable pixel width at game scale.",
     "one character x 8 directions"),
    ("concept.py", "check_concept_fitness",
     "Is this image something stage 2 can lift, measured on the matte.",
     "one SDXL render"),
    ("export_godot.py", "check_nine_slice_roundtrip",
     "Do the margins in the written .tres match the insets that were drawn?",
     "engine export"),
    ("export_godot.py", "check_palette_lut_godot",
     "Does the ENGINE see the palettes Python forged, and see them "
     "unfiltered?", "engine export"),
    ("export_godot.py", "check_font_layout",
     "Does Godot lay these glyphs out where bitmap_font says it will?",
     "engine export"),
    ("floorplan.py", "check_plan",
     "Everything a floor plan has to be true for. Errors, not warnings.",
     "one plan"),
    ("floorplan.py", "check_plan_range",
     "Do consecutive seeds actually produce different rooms?", "plan generator"),
    ("floorplan.py", "check_generated_plans",
     "Every plan the generator returns must pass the rules it solved "
     "against.", "plan generator"),
    ("furnish.py", "check_distinct",
     "Do any two ids render the same eight images?", "prop library"),
    ("fx.py", "check_loops",
     "A looping clip must return to its start.", "one FX clip"),
    ("ingest.py", "check_roundtrip",
     "Ingesting a colour the palette already contains must return that "
     "colour.", "ingest pipeline"),
    ("ingest.py", "check_albedo_regression",
     "Exercise check_albedo_centre on both of ingest's two paths.",
     "ingest pipeline"),
    ("ingest.py", "check_transform",
     "A full pass over a mesh that looks like something a generator "
     "emitted.", "ingest pipeline"),
    ("ingest.py", "check_albedo_centre",
     "Is the bound albedo where authored albedo lives?", "one mesh"),
    ("manifest.py", "check_ui",
     "Does every declared cat: ui entry exist, and does it still hold up?",
     "asset manifest"),
    ("package_godot.py", "check_anim_layout",
     "Do the resolved rects fit the sheet, and does each one belong to one "
     "clip?", "engine export"),
    ("package_godot.py", "check_palette_lut",
     "Read the written texture back and require it to BE the palettes.",
     "engine export"),
    ("palette_forge.py", "check_separation",
     "Every pair of SHIPPED palettes must be at least min_delta_e apart.",
     "palette + variants"),
    ("palette_swap.py", "check_total", "", "swap tables"),
    ("palette_swap.py", "check_injective", "", "swap tables"),
    ("palette_swap.py", "check_exact",
     "Palette-exact in the TARGET palette, on every written file.",
     "variant library"),
    ("palette_swap.py", "check_roundtrip",
     "base -> variant -> base recovers the original image, byte for byte.",
     "asset library"),
    ("portrait.py", "check_eyes_visible",
     "Does EACH eye, specifically, render enough pixels to read as an eye?",
     "roster"),
    ("portrait.py", "check_distinct",
     "No two characters render the same PNG bytes.", "roster"),
    ("portrait.py", "check_determinism",
     "Same spec, rendered twice, byte-identical.", "roster"),
    ("portrait.py", "check_palette_exact", "", "roster"),
    ("review_queue.py", "check_direction_set",
     "Cross-sprite check: is the key light consistent across a direction "
     "set?", "one sprite x 8 directions"),
    ("tileset.py", "check_lattice",
     "Does the tile size put the lattice step on whole pixels?", "tileset"),
    ("tileset.py", "check_collapse",
     "Do two materials in this pattern resolve to the same colour?",
     "tileset"),
    ("tileset.py", "check_manifest_placement",
     "Can a consumer rebuild the room from the published numbers alone?",
     "tileset manifest"),
    ("ui_chrome.py", "check_nine_slice",
     "Do the declared stretch bands actually tile?", "one UI frame"),
    ("ui_forge.py", "check_icon",
     "Is this a usable icon? Same shape of answer as check_concept_fitness.",
     "one icon"),
]

REGISTRY: list[Gate] = [
    Gate(name=name, producer=producer, kind="deterministic",
        rationale=rationale, scope=scope)
    for producer, name, rationale, scope in _DETERMINISTIC
]

# --- llm -----------------------------------------------------------------
# Real category, honestly empty. `art_review`/`build_plan`'s focal-contrast
# family is the strongest candidate for the first one -- ART_CRITIQUE.md
# records a multi-pass history of that check being re-derived, mis-projected,
# and re-tuned specifically because it is approximating a judgment call
# ("does this room have a focal point") with an ever-more-specific numeric
# proxy. A vision-capable model asked the question directly is a plausible
# replacement or supplement. Not wired here: it needs a model/cost/
# credential-handling decision this catalog should not make unilaterally.
PLANNED_LLM_GATES = [
    Gate(name="focal_hierarchy (planned)", producer="build_plan.py / art_review.py",
        kind="llm",
        rationale="does this room read as having a focal point, asked "
                  "directly instead of approximated by percentile contrast",
        scope="generated room"),
]

# --- taste -----------------------------------------------------------------
# The gate every feature in this repo has always waited on, whether or not
# it was ever written down as one: a human opens the proof sheet. Palette
# variants, the bitmap font, portraits -- each passed every gate above and
# still did not ship until that happened.
TASTE_GATES = [
    Gate(name="human_review", producer="(none -- a person, not a script)",
        kind="taste",
        rationale="does this actually look good, asked of a human, last, "
                  "after everything cheaper has already filtered out what "
                  "is obviously broken",
        scope="whatever the feature's proof sheet is"),
]

ALL_GATES: list[Gate] = REGISTRY + PLANNED_LLM_GATES + TASTE_GATES


def by_kind(kind: str) -> list[Gate]:
    return [g for g in ALL_GATES if g.kind == kind]


def by_producer(producer: str) -> list[Gate]:
    return [g for g in ALL_GATES if g.producer == producer]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", nargs="?", const="all", choices=[*KINDS, "all"])
    ap.add_argument("--producer", metavar="FILE")
    args = ap.parse_args()

    if args.producer:
        gates = by_producer(args.producer)
        if not gates:
            print(f"no gates catalogued for {args.producer!r}")
            return 1
        for g in gates:
            print(f"  {g.name:<28s} {g.rationale}")
        return 0

    kind = args.list or "all"
    kinds = KINDS if kind == "all" else (kind,)
    for k in kinds:
        gates = by_kind(k)
        print(f"\n{k} ({len(gates)})")
        by_prod: dict[str, list[Gate]] = {}
        for g in gates:
            by_prod.setdefault(g.producer, []).append(g)
        for prod in sorted(by_prod):
            print(f"  {prod}")
            for g in by_prod[prod]:
                print(f"    {g.name:<28s} {g.rationale}")
    print(f"\n{len(ALL_GATES)} gates total: {len(REGISTRY)} deterministic, "
          f"{len(PLANNED_LLM_GATES)} llm (planned), {len(TASTE_GATES)} taste")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
