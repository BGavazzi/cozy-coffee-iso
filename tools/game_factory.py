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

from style import DEFAULT_STYLE, load_style

ROOT = Path(__file__).resolve().parent.parent


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def prepare(path: Path, only: str | None = None, producer: str = 'sdxl',
           style: str | None = None):
    """`style`, when given, overrides the manifest's own `"style"` field.

    A game's `pieces.json` names ONE style because a recipe -- prompts,
    traits, seeds -- has to declare what it was written against. That is
    not the same claim as "this recipe can only ever render in that style":
    every prompt in this file already reads as generic sculpted-figurine
    description, not style-specific vocabulary (see `concept.py`'s own
    precedent -- prop prompts are style-agnostic by construction, style is
    applied downstream in shading), and the procedural producer's body
    geometry (`game_pieces.py`) draws on the same six ramp names + three
    spot colours every style pack in this repo declares, so it renders
    under any of them without touching a single coordinate.

    Overriding here, before the config is hashed, is what makes the swap
    show up as a genuinely different build identity rather than a reskin
    nobody can tell apart from the original -- `style` is part of
    `provenance` below, which is part of every row's content-addressed
    `key`, so two styles of the same piece never collide in `out/`.
    """
    config = json.loads(path.read_text(encoding="utf-8"))
    if not re.fullmatch(r"[a-z0-9_]+", config["project"]):
        raise ValueError("Invalid project name")
    if style:
        config["style"] = style
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
    ap.add_argument("--style", help="override the manifest's own style field, "
                                    "e.g. to build the same recipe under a "
                                    "second style pack without editing the "
                                    "JSON (see style.load_style)")
    args = ap.parse_args()
    config, rows = prepare(args.manifest, args.only, args.producer, args.style)
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
            mesh = build(item['kind'], item['traits'], item.get('variant'))
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
    # Suffixed by explicit OVERRIDE, not by comparison to the global
    # DEFAULT_STYLE -- a game's manifest already names its own natural style
    # (this one is snes_rpg, not cozy_ghibli), and every existing command in
    # this game's own README points at the plain `latest-build.json` path.
    # Comparing against the global default would silently move that well-
    # known path out from under anyone who has never touched --style, the
    # first time someone else's build happens to be cozy_ghibli. Suffixing
    # only when `--style` was actually passed keeps every pre-existing
    # command working unchanged and marks an explicit style experiment as
    # exactly that -- a second, clearly-named file, not a replacement.
    latest_name = ("latest-build.json" if not args.style
                   else f"latest-build_{style.name}.json")
    (destination / latest_name).write_text(json.dumps(results, indent=2), encoding="utf-8")
    return int(any(r["status"] != "awaiting_visual_review" for r in results))


if __name__ == "__main__":
    raise SystemExit(main())
