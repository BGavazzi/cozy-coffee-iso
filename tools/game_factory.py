#!/usr/bin/env python3
"""Adapt the existing SDXL -> TripoSR -> ingest -> render factory to game recipes.

No alternate image provider. Content-addressed builds isolate game artifacts
from cafe output. Rendering, technical review and human approval stay distinct.
Run --plan first; --only tick is a bounded GPU pilot. No automatic publication.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
import re
from pathlib import Path

from style import load_style

ROOT = Path(__file__).resolve().parent.parent


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def prepare(path: Path, only: str | None = None, producer: str = 'sdxl'):
    config = json.loads(path.read_text(encoding="utf-8"))
    if not re.fullmatch(r"[a-z0-9_]+", config["project"]):
        raise ValueError("Invalid project name")
    style = load_style(config["style"])
    # Includes transitive local producer/check dependencies, not only the bible.
    code = {p.name: digest(p.read_bytes()) for p in sorted((ROOT / "tools").glob("*.py"))}
    versions = {}
    for package in ("torch", "diffusers", "transformers", "Pillow", "numpy"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "missing"
    provenance = {"backend": producer, "style": style.name, "bible": digest(style.bible_path.read_bytes()),
                  "palette": digest(style.palette_path.read_bytes()), "code": code,
                  "packages": versions, "target": 64, "factor": 4,
                  "direction": config.get("direction", ""),
                  "models": {"concept": "stabilityai/stable-diffusion-xl-base-1.0",
                             "mesh": "stabilityai/TripoSR"}}
    # Pin the locally resolved model revisions where the installed cache exposes them.
    cache = ROOT.parent / ".hf-cache" / "hub"
    provenance["cached_model_refs"] = {
        str(p.relative_to(cache)): p.read_text(encoding="utf-8").strip()
        for p in sorted(cache.glob("models--*/refs/*")) if p.is_file()
    }
    if producer == 'procedural':
        provenance['models'] = {}
        provenance['cached_model_refs'] = {}
    rows = []
    ids = [p["id"] for p in config["pieces"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate piece IDs")
    wanted = set(only.split(",")) if only else set(ids)
    if wanted - set(ids):
        raise ValueError(f"Unknown pieces: {sorted(wanted - set(ids))}")
    for entry in config["pieces"]:
        if entry["id"] not in wanted:
            continue
        if not re.fullmatch(r"[a-z0-9_-]+", entry["id"]) or entry["height"] <= 0:
            raise ValueError("Invalid piece identity or height")
        recipe = {"piece": entry, "producer": provenance}
        key = digest(json.dumps(recipe, sort_keys=True).encode())[:20]
        rows.append({"recipe": recipe, "key": key,
                     "name": f"{config['project']}_{entry['id']}_{key}"})
    return config, rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("manifest", type=Path)
    ap.add_argument("--only")
    ap.add_argument('--producer', choices=('sdxl', 'procedural'), default='sdxl')
    ap.add_argument("--plan", action="store_true", help="validate and print identities; no GPU work")
    args = ap.parse_args()
    config, rows = prepare(args.manifest, args.only, args.producer)
    if args.plan:
        print(json.dumps({"project": config["project"], "style": config["style"],
                          "pieces": [{"id": r["recipe"]["piece"]["id"], "key": r["key"]} for r in rows]}, indent=2))
        return 0
    import factory as F
    import concept as C
    import lift as L
    import art_review as A
    from pixelize import load_palette
    style = load_style(config["style"])
    ramps = load_palette(style.palette_path)
    by_rgb, review_ramps, entries = A.load_palette(style.palette_path)
    destination = ROOT / "out" / "games" / config["project"]
    destination.mkdir(parents=True, exist_ok=True)
    # Isolate every stage. Original factory outputs and cache remain untouched.
    F.CONCEPT_DIR = destination / "concept"
    F.MESH_DIR = destination / "mesh"
    pipe = model = None
    if args.producer == 'sdxl':
        print("Loading the existing cafe SDXL and TripoSR models...", flush=True)
        pipe, model = C._pipe(), L._model()
    results = []
    for row in rows:
        item = row["recipe"]["piece"]
        out = destination / row["key"]
        out.mkdir(parents=True, exist_ok=True)
        spec = {"name": row["name"], "prompt": item["prompt"], "height": item["height"],
                "seed": item.get("seed", 1), "reference": None, "kind": "prop", "ip_scale": None}
        print(f"Generating {item['name']} ({row['key']})", flush=True)
        if args.producer == 'sdxl':
            result = F.run_subject(spec, pipe, model, ramps, style.name, out, retries=1)
        else:
            from game_pieces import build
            from render_batch import frame_all, render_sprite, footprint
            from mesh import save_obj
            from ingest import fit
            mesh = build(item['kind'], item['traits'])
            fit(mesh, height=item['height'])
            save_obj(mesh, out / 'source.obj')
            span, centre = frame_all(mesh)
            frames = []
            for k in range(8):
                image, pixels = render_sprite(mesh, 45 + k * 45, 64, 4, ramps, span=span, centre=centre)
                filename = f"{row['name']}_dir{k}.png"
                image.save(out / filename)
                frames.append({'file': filename, 'direction': k, **(footprint(pixels, 64) or {})})
            (out / 'manifest.json').write_text(json.dumps(frames, indent=2), encoding='utf-8')
            result = {'name': row['name'], 'stage': 'render', 'ok': True, 'detail': 'Procedural mesh through existing cafe renderer; not AI-generated.'}
        result.update(id=item["id"], recipe=row["recipe"], key=row["key"],
                      status="generation_failed", human_approved=False, frames=[])
        if result["ok"]:
            blocked = False
            for k in range(8):
                png = out / f"{row['name']}_dir{k}.png"
                findings = A.review(png, by_rgb, review_ramps, entries)
                blocked |= any(f["severity"] == "blocker" for f in findings)
                result["frames"].append({"direction": k, "path": str(png),
                                         "sha256": digest(png.read_bytes()), "findings": findings})
            result["status"] = "review_blocked" if blocked else "awaiting_visual_review"
        # Never conflate upstream ok/rendered with approved/releasable.
        result["rendered"] = result.pop("ok")
        (out / "build.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        results.append({"id": item["id"], "key": row["key"], "status": result["status"],
                        "build": str(out / "build.json")})
        print(json.dumps(results[-1]), flush=True)
    (destination / "latest-build.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    return int(any(r["status"] != "awaiting_visual_review" for r in results))


if __name__ == "__main__":
    raise SystemExit(main())
