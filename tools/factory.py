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

`prompt` defaults to `name` with underscores turned to spaces. `height` is in
tile units and is required -- `ingest.fit()` has no other way to know a
teapot from a table. `reference` is optional; when given, stage 1 conditions
on that image via IP-Adapter as well as `prompt`.

Each stage is skipped when its output file already exists, so a batch that
fails partway through resumes rather than re-spending GPU time stage 1 already
paid for. `--force` clears one subject's outputs first.
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
        })
    return subs


def _clear(name: str) -> None:
    for p in (CONCEPT_DIR / f"{name}.png", CONCEPT_DIR / f"{name}_raw.png",
             CONCEPT_DIR / f"{name}.json", MESH_DIR / f"{name}.obj",
             MESH_DIR / f"{name}_bound.obj"):
        p.unlink(missing_ok=True)


def run_subject(spec: dict, pipe, model, ramps) -> dict:
    """Concept -> lift -> ingest -> render, skipping stages already done.

    Returns a result dict rather than raising, because one bad subject in a
    batch of thirty should not cost the other twenty-nine their GPU time --
    the whole point of this file is to survive that.
    """
    import concept as C
    import ingest as I
    import lift as L
    from mesh import save_obj

    name = spec["name"]
    result = {"name": name, "stage": None, "ok": False, "detail": ""}

    png = CONCEPT_DIR / f"{name}.png"
    try:
        if not png.exists():
            CONCEPT_DIR.mkdir(parents=True, exist_ok=True)
            ref_kwargs = {"reference": spec["reference"]}
            if spec["ip_scale"] is not None:
                ref_kwargs["ip_scale"] = spec["ip_scale"]
            C.concept(spec["prompt"], spec["seed"], out=png, pipe=pipe,
                      **ref_kwargs)
        fitness = C.check_concept_fitness(png)
        if fitness:
            result.update(stage="concept", detail="; ".join(fitness))
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
        r = run_subject(spec, pipe, model, ramps)
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
