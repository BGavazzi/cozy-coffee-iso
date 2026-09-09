#!/usr/bin/env python3
"""Audit benchmark proposals through the deterministic admission gate."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from admit_proposal import admit


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('benchmark', type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    source = json.loads(args.benchmark.read_text(encoding='utf-8'))
    rows = []
    for row in source['rows']:
        decision = admit(row['proposal']) if row['ok'] else {'status': 'rejected', 'reasons': ['model output was invalid']}
        rows.append({**row, 'admission': decision})
    result = {**source, 'admission_counts': dict(Counter(r['admission']['status'] for r in rows)), 'rows': rows}
    if args.out:
        args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'model': source['model'], 'count': len(rows), 'admission_counts': result['admission_counts']}))
