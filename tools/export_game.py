"""Export explicitly reviewed, hash-verified sprite builds to a web game's public folder."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path


def export(batch: Path, review: Path, destination: Path):
    rows = json.loads(batch.read_text())
    verdict = json.loads(review.read_text())
    staged = []
    existing_manifest = {}
    existing_path = destination / 'manifest.json'
    if existing_path.exists():
        existing_manifest = json.loads(existing_path.read_text())
    manifest = dict(existing_manifest)
    approved_hashes = set(verdict.get('approved_sha256', []))
    # Validate the entire batch before copying any file.
    for row in rows:
        data = json.loads(Path(row['build']).read_text())
        frame = next(f for f in data['frames'] if f['direction'] == 0)
        key_approved = data['key'] in verdict.get('approved_keys', [])
        hash_approved = frame['sha256'] in approved_hashes
        if not (key_approved or hash_approved) or data['status'] != 'awaiting_visual_review':
            raise ValueError(f"Unapproved or technically blocked build: {row['id']}")
        if any(f['severity'] == 'blocker' for frame in data['frames'] for f in frame['findings']):
            raise ValueError('Technical blocker cannot be overridden by this exporter')
        source = Path(frame['path'])
        if hashlib.sha256(source.read_bytes()).hexdigest() != frame['sha256']:
            raise ValueError(f"Sprite changed after review: {source}")
        # A factory code change can produce a new build key without changing
        # the pixels. Reuse the existing canonical filename in that case, so
        # content-addressed approval does not create duplicate public assets.
        old = existing_manifest.get(data['id'])
        reuse = (old and old.get('sha256') == frame['sha256'] and
                 (destination / old.get('file', '')).exists())
        filename = old['file'] if reuse else f"{data['id']}-{data['key']}.png"
        manifest_key = old.get('key', data['key']) if reuse else data['key']
        target = destination / filename
        if target.exists() and target.read_bytes() != source.read_bytes():
            raise ValueError(f"Refusing to overwrite different art: {target}")
        staged.append((source, target))
        manifest[data['id']] = {'file': filename, 'key': manifest_key,
                                'style': data['recipe']['producer']['style'],
                                'producer': data['recipe']['producer']['backend'],
                                'review': 'agent-reviewed prototype', 'sha256': frame['sha256']}
    destination.mkdir(parents=True, exist_ok=True)
    for source, target in staged:
        shutil.copy2(source, target)
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return manifest


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('batch', type=Path)
    ap.add_argument('--review', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    print(f"Exported {len(export(args.batch, args.review, args.out))} reviewed sprites to {args.out}")
