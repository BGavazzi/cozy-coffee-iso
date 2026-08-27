#!/usr/bin/env python3
"""Stage 1-9, driven off a subject list. NEXT.md task A1.

Before this, producing one prop was five manual commands and the state
between them was undocumented -- generate a concept, check its fitness by
hand, lift it, ingest it, render it, review it, and remember which of those
had already succeeded if any of them failed. There was no way to say "make me
these forty things" and come back to a report.

    python tools/factory.py subjects.yaml
    python tools/factory.py subjects.yaml --only teapot,kettle
    python tools/factory.py subjects.yaml --force teapot   # redo one subject

Subject list format (YAML or JSON, a list of objects):

    - name: teapot
      prompt: a ceramic teapot
      height: 0.28
      reference: photos/teapot.jpg   # optional -- see concept.py's
      ip_scale: 0.45                 # "Reference images" section
      kind: prop                     # prop (default) or character --
                                      # see concept.py's NEGATIVE_CHARACTER

`prompt` defaults to `name` with underscores turned to spaces. `height` is in
tile units and is required -- `ingest.fit()` has no other way to know a
teapot from a table. `reference` is optional -- a single path or a YAML list
of paths -- and when given, stage 1 conditions on it via IP-Adapter as well
as `prompt`. `kind: character` is for a prompt naming a specific character
or franchise, which pulls SDXL toward fan-art/character-sheet training data
harder than a generic prop noun does; see `concept.py`'s module docstring.

Each stage is skipped when its output file already exists, so a batch that
fails partway through resumes rather than re-spending GPU time stage 1 already
paid for. `--force` clears one subject's outputs first.

A concept that fails the stage-1 fitness gate is automatically retried on the
next seed up, twice, before the subject is given up on -- measured to rescue
five of six gated subjects, all on the first retry. `--retry-seeds 0` restores
the old one-shot behaviour. See `RETRY_SEEDS` for the numbers and for the
failure class it does not rescue.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

ROOT = Path(__file__).resolve().parent.parent
CONCEPT_DIR = ROOT / "out" / "concept"
MESH_DIR = ROOT / "out" / "mesh"
SPRITE_DIR = ROOT / "out" / "sprites"

# Extra seeds to try when a concept fails the stage-1 gate, before giving up.
#
# Measured, and measured twice, because the first attempt was wrong. A sweep
# against the stored factory report said five of six gated subjects were
# rescued by reseeding; re-establishing the seed-1 baseline under the CURRENT
# gate showed three of those nine (`book`, `fern`, `bicycle`) already pass on
# seed 1 -- the report predated B1's MAX_SOFT_ALPHA/DETACHED_SOFT_FLOOR split
# and the recalibration, not the reseed, had fixed them.
#
# Corrected tally against a fresh baseline: of four genuinely-gated subjects
# retried, three passed (`wine_glass` 11.9%, `cake_slice` 10.9%, `croissant`
# 2.6% frame fill), all on the FIRST retry. Hence 2 rather than 3 -- the
# third attempt bought nothing in that sample and costs a full SDXL
# generation per subject. See `ART_CRITIQUE.md`, "The 29% that was being
# thrown away", for the full correction.
#
# What it does not fix: `wooden_spoon` failed at all three seeds (7.7%,
# 11.9%, 5.4%). A long thin object is systematically small in frame once
# `STYLE`'s "generous margin" clause has had its way, and no amount of
# reseeding changes the shape of a spoon. Reseeding rescues seed-specific
# noise -- collage, a bad matte, a near-miss crop -- not a subject whose
# geometry fights the framing.
#
# And the hazard, which is worth knowing before raising this number:
# reseeding optimises against the GATE, and the gate is a proxy. `bread_loaf`
# gated on seed 1, passed on seed 2, reached stage 5 -- and its sprites are
# still 5-of-8 blocked, identical to before. Enough retries will eventually
# find a concept that satisfies stage 1's heuristics without reconstructing
# any better, which is tuning to the metric in a thin disguise. 2 is modest
# enough not to grind far. What actually protects the library is downstream:
# `art_review` reads the sprites and blocked `bread_loaf` both times.
RETRY_SEEDS = 2


def _load_subjects(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        import yaml
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    subs = []
    for s in data:
        name = s["name"]
        subs.append({
            "name": name,
            "prompt": s.get("prompt", name.replace("_", " ")),
            "height": s["height"],
            "seed": s.get("seed", 1),
            "reference": s.get("reference"),
            "ip_scale": s.get("ip_scale"),  # None -> concept.py's own default
            "kind": s.get("kind", "prop"),
        })
    return subs


def _clear(name: str) -> None:
    for p in (CONCEPT_DIR / f"{name}.png", CONCEPT_DIR / f"{name}_raw.png",
             CONCEPT_DIR / f"{name}.json", MESH_DIR / f"{name}.obj",
             MESH_DIR / f"{name}_bound.obj"):
        p.unlink(missing_ok=True)


def run_subject(spec: dict, pipe, model, ramps, retries: int = RETRY_SEEDS) -> dict:
    """Concept -> lift -> ingest -> render, skipping stages already done.

    Returns a result dict rather than raising, because one bad subject in a
    batch of thirty should not cost the other twenty-nine their GPU time --
    the whole point of this file is to survive that.

    A concept that fails the stage-1 gate is retried on the next seed up to
    `retries` times. See `RETRY_SEEDS` for why, and for what this does not
    fix. Retries only apply to a concept generated in THIS run: an existing
    `out/concept/<name>.png` is respected exactly as before, because "skip
    what is already done" is what makes a half-finished batch resumable.
    Use `--force <name>` to redo one from scratch.
    """
    import concept as C
    import ingest as I
    import lift as L
    from mesh import save_obj

    name = spec["name"]
    result = {"name": name, "stage": None, "ok": False, "detail": ""}

    png = CONCEPT_DIR / f"{name}.png"
    try:
        if png.exists():
            fitness = C.check_concept_fitness(png)
        else:
            CONCEPT_DIR.mkdir(parents=True, exist_ok=True)
            ref_kwargs = {"reference": spec["reference"], "kind": spec["kind"]}
            if spec["ip_scale"] is not None:
                ref_kwargs["ip_scale"] = spec["ip_scale"]
            for attempt in range(retries + 1):
                seed = spec["seed"] + attempt
                C.concept(spec["prompt"], seed, out=png, pipe=pipe,
                          **ref_kwargs)
                fitness = C.check_concept_fitness(png)
                if not fitness:
                    if attempt:
                        # Reported, never silent: a subject that needed three
                        # tries is a subject whose prompt is marginal, and
                        # that is worth seeing in the report even though the
                        # asset came out fine.
                        result["seed_used"] = seed
                        result["detail"] += (f"gate passed on seed {seed} "
                                             f"after {attempt} reseed(s); ")
                    break
                if attempt < retries:
                    print(f"  seed {seed} gated, reseeding: {fitness[0][:70]}")
        if fitness:
            result.update(stage="concept", detail=result["detail"]
                          + "; ".join(fitness))
            return result
    except Exception as e:
        result.update(stage="concept", detail=f"{type(e).__name__}: {e}")
        return result

    raw_obj = MESH_DIR / f"{name}.obj"
    try:
        if not raw_obj.exists():
            MESH_DIR.mkdir(parents=True, exist_ok=True)
            L.lift(png, raw_obj, model=model)
    except Exception as e:
        result.update(stage="lift", detail=f"{type(e).__name__}: {e}")
        return result

    bound_obj = MESH_DIR / f"{name}_bound.obj"
    try:
        if not bound_obj.exists():
            mesh, report = I.ingest(raw_obj, height=spec["height"])
            for w in report["warnings"]:
                result["detail"] += w + "; "
            result["worst_bind_de"] = report["worst_bind_de"]
            save_obj(mesh, bound_obj)
    except Exception as e:
        result.update(stage="ingest", detail=f"{type(e).__name__}: {e}")
        return result

    try:
        import subprocess
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "render_batch.py"),
             "--mesh", str(bound_obj), "--name", name,
             "--out", str(SPRITE_DIR), "--target", "64"],
            capture_output=True, text=True, timeout=300)
        if proc.returncode != 0:
            result.update(stage="render", detail=proc.stderr[-500:])
            return result
    except Exception as e:
        result.update(stage="render", detail=f"{type(e).__name__}: {e}")
        return result

    result.update(ok=True, stage="render")
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("subjects")
    ap.add_argument("--only", help="comma-separated subject names to run")
    ap.add_argument("--force", help="comma-separated subject names to redo "
                                    "from stage 1")
    ap.add_argument("--retry-seeds", type=int, default=RETRY_SEEDS,
                    metavar="N",
                    help=f"extra seeds to try when a concept fails the "
                         f"stage-1 gate (default {RETRY_SEEDS}; 0 restores "
                         f"the old one-shot behaviour)")
    args = ap.parse_args()

    subjects = _load_subjects(Path(args.subjects))
    if args.only:
        wanted = set(args.only.split(","))
        subjects = [s for s in subjects if s["name"] in wanted]
    if args.force:
        for name in args.force.split(","):
            _clear(name)

    if not subjects:
        print("no subjects selected", file=sys.stderr)
        return 1

    print(f"{len(subjects)} subjects. Loading SDXL and TripoSR once...")
    import concept as C
    import lift as L
    from pixelize import load_palette
    pipe = C._pipe()
    model = L._model()
    ramps = load_palette()

    results = []
    for spec in subjects:
        print(f"\n=== {spec['name']} ===")
        r = run_subject(spec, pipe, model, ramps, retries=args.retry_seeds)
        results.append(r)
        status = "OK" if r["ok"] else f"GATED at {r['stage']}"
        print(f"  {status}" + (f": {r['detail']}" if r["detail"] else ""))

    ok = [r for r in results if r["ok"]]
    print(f"\n{len(ok)}/{len(results)} reached stage 5 clean.")

    if ok:
        import subprocess
        # review_queue.build() globs relative to cwd -- Path().glob rejects an
        # absolute pattern outright -- so this assumes factory.py is invoked
        # from the repo root, the same assumption every other tool here makes.
        rel_sprites = SPRITE_DIR.relative_to(ROOT)
        patterns = [str(rel_sprites / f"{r['name']}_dir*.png") for r in ok]
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "review_queue.py"),
             "build", *patterns], capture_output=True, text=True)
        print(proc.stdout[-1500:])
        if proc.returncode != 0:
            print(proc.stderr[-1000:], file=sys.stderr)

    report_path = ROOT / "out" / "factory_report.json"
    report_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nreport -> {report_path}")
    return 0 if len(ok) == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
