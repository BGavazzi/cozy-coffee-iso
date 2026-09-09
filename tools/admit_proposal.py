#!/usr/bin/env python3
"""Classify a local-model proposal without granting it game authority."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from local_designer import SCHEMA, validate

# These are the only trigger/effect pairs currently close enough to the game's
# authored rule vocabulary to enter simulation. Everything else needs a human
# rule-template implementation before it can affect a card.
SIMULATABLE = {
    ('after_steps', 'spawn_egg'),
    ('after_steps', 'spawn_tick'),
    ('after_steps', 'spawn_tack'),
    ('on_eaten', 'spawn_tick'),
    ('on_feed', 'spawn_egg'),
}


def admit(proposal: dict) -> dict:
    try:
        validate(proposal)
    except Exception as exc:
        return {'status': 'rejected', 'reasons': [str(exc)]}
    reasons = []
    if not proposal['name'].strip() or proposal['name'].strip().lower() in {'x', 'tbd', 'new piece'}:
        reasons.append('name is not meaningful enough for a discovery')
    if not proposal['concept'].strip():
        reasons.append('concept is empty')
    attachments = proposal['art']['attachments']
    if len(set(attachments)) != len(attachments):
        reasons.append('duplicate art attachment')
    if proposal['effect'].startswith('spawn_') and proposal['target'] == 'board':
        reasons.append('board-wide spawning is unbounded')
    pair = (proposal['trigger'], proposal['effect'])
    if reasons:
        return {'status': 'rejected', 'reasons': reasons}
    if pair not in SIMULATABLE:
        return {'status': 'needs_authoring', 'reasons': ['no implemented runtime rule template for this trigger/effect pair']}
    return {'status': 'eligible_for_simulation', 'reasons': [], 'template': f'{pair[0]}:{pair[1]}'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('proposal', type=Path)
    args = parser.parse_args()
    result = admit(json.loads(args.proposal.read_text(encoding='utf-8')))
    print(json.dumps(result, indent=2))
