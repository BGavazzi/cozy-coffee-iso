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

# A proposal can be structurally valid and still fail the game's meaningful
# novelty gate. Keep this small and explicit: it is a record of mechanics the
# authored runtime already gives to a parent pair, not an LLM semantic guess.
# More entries belong here only after the corresponding base interaction is
# documented and covered by a game test.
REDUNDANT_PARENT_MECHANICS = {
    (frozenset({'tick', 'toe'}), ('on_feed', 'spawn_egg')):
        'Tick + Toe already reproduces after feeding; this proposal adds no new decision',
}
GENERIC_NAMES = {
    'x', 'tbd', 'new piece', 'spawn egg', 'spawn tick', 'spawn tack',
    'after steps', 'on play', 'on feed', 'on eaten', 'on line', 'tick tack toe',
}
GENERIC_CONCEPTS = {'a game piece', 'after_steps', 'new piece'}


def _normalise_parent(parent: str) -> str:
    return parent.strip().lower().replace(' ', '_').replace('-', '_')


def novelty_reasons(proposal: dict, parents: list[str] | None = None) -> list[str]:
    """Return deterministic redundancy findings for an optional parent pair."""
    if not parents:
        return []
    parent_ids = frozenset(_normalise_parent(p) for p in parents)
    reason = REDUNDANT_PARENT_MECHANICS.get(
        (parent_ids, (proposal['trigger'], proposal['effect']))
    )
    return [reason] if reason else []


def admit(proposal: dict, parents: list[str] | None = None) -> dict:
    try:
        validate(proposal)
    except Exception as exc:
        return {'status': 'rejected', 'reasons': [str(exc)]}
    reasons = []
    name_key = proposal['name'].strip().lower().replace('_', ' ')
    if not name_key or name_key in GENERIC_NAMES:
        reasons.append('name is not meaningful enough for a discovery')
    if parents:
        name_id = _normalise_parent(proposal['name'])
        parent_ids = {_normalise_parent(parent) for parent in parents}
        if name_id in parent_ids:
            reasons.append('name duplicates a parent piece; discovery names must be novel')
    if not proposal['concept'].strip() or proposal['concept'].strip().lower() in GENERIC_CONCEPTS:
        reasons.append('concept is empty or too generic to describe a player-facing decision')
    attachments = proposal['art']['attachments']
    if len(set(attachments)) != len(attachments):
        reasons.append('duplicate art attachment')
    if proposal['effect'].startswith('spawn_') and proposal['target'] == 'board':
        reasons.append('board-wide spawning is unbounded')
    reasons.extend(novelty_reasons(proposal, parents))
    pair = (proposal['trigger'], proposal['effect'])
    if reasons:
        return {'status': 'rejected', 'reasons': reasons}
    if pair not in SIMULATABLE:
        return {'status': 'needs_authoring', 'reasons': ['no implemented runtime rule template for this trigger/effect pair']}
    return {'status': 'eligible_for_simulation', 'reasons': [], 'template': f'{pair[0]}:{pair[1]}'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('proposal', type=Path)
    parser.add_argument('--parents', nargs=2, metavar=('A', 'B'),
                        help='optional parent names used by the novelty gate')
    parser.add_argument('--out', type=Path,
                        help='also write a promotion-ready admission record')
    args = parser.parse_args()
    payload = json.loads(args.proposal.read_text(encoding='utf-8'))
    result = admit(payload, args.parents)
    if args.out:
        args.out.write_text(json.dumps({
            'schema': 'tick-tack-toe.discovery-admission.v1',
            'parents': args.parents or [],
            'proposal': payload,
            'admission': result,
        }, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
