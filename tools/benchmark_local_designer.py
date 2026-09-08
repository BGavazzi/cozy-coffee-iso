#!/usr/bin/env python3
"""Run a small local-only proposal benchmark without changing game state."""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from local_designer import ask

PAIRS = [
    ('Tick', 'Tack'), ('Tick', 'Toe'), ('Tack', 'Toe'), ('Egg', 'Tack'),
    ('Egg', 'Toe'), ('Stone', 'Lure'), ('Wild Seed', 'Toe'), ('Sap', 'Tweezers'),
    ('Iron Tick', 'Brood Tick'), ('Iron Brood Tick', 'Mimic Toe'),
    ('Decoy Egg', 'Toe'), ('Mimic Toe', 'Brood Tick'), ('Hatchery Trap', 'Lure'),
    ('Tick', 'Stone'), ('Tack', 'Wild Seed'), ('Toe', 'Lure'), ('Egg', 'Stone'),
    ('Amber Toe', 'Anchor Tack'), ('Brood Tick', 'Lure'), ('Mimic Toe', 'Decoy Egg'),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default='qwen2.5:7b')
    parser.add_argument('--endpoint', default='http://127.0.0.1:11434')
    parser.add_argument('--limit', type=int, default=len(PAIRS))
    parser.add_argument('--out', type=Path, default=Path('local-designer-benchmark.json'))
    args = parser.parse_args()
    rows = []
    for parents in PAIRS[:max(0, min(args.limit, len(PAIRS)))]:
        started = time.perf_counter()
        try:
            proposal = ask(args.model, list(parents), args.endpoint)
            rows.append({'parents': parents, 'ok': True, 'proposal': proposal,
                         'seconds': round(time.perf_counter() - started, 2)})
        except Exception as exc:  # Keep one bad proposal from hiding the batch rate.
            rows.append({'parents': parents, 'ok': False, 'error': str(exc),
                         'seconds': round(time.perf_counter() - started, 2)})
    result = {'model': args.model, 'endpoint': args.endpoint,
              'created': datetime.now(timezone.utc).isoformat(), 'count': len(rows),
              'valid': sum(row['ok'] for row in rows), 'rows': rows}
    args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'model': args.model, 'count': len(rows), 'valid': result['valid'],
                      'invalid': len(rows) - result['valid'], 'out': str(args.out)}))
    return 0 if result['valid'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
