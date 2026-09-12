#!/usr/bin/env python3
"""Ask a local Ollama model for a bounded discovery proposal.

This is deliberately a proposal tool: it never edits game code, grants a card,
or calls the renderer. The game-side validator remains the authority.
"""
from __future__ import annotations

import argparse
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = {
    "type": "object",
    "required": ["name", "concept", "trigger", "target", "effect", "cost", "art"],
    "properties": {
        "name": {"type": "string", "maxLength": 40},
        "concept": {"type": "string", "maxLength": 240},
        "trigger": {"type": "string", "enum": ["on_play", "on_feed", "on_eaten", "after_steps", "on_line"]},
        "target": {"type": "string", "enum": ["self", "adjacent_empty", "adjacent_enemy", "board"]},
        "effect": {"type": "string", "enum": ["spawn_egg", "spawn_tick", "spawn_tack", "move_self", "remove_enemy", "score_line"]},
        "cost": {"type": "integer", "minimum": 1, "maximum": 4},
        "art": {"type": "object", "required": ["base_kind", "attachments"], "properties": {"base_kind": {"type": "string", "enum": ["tick", "tack", "toe", "egg"]}, "attachments": {"type": "array", "items": {"type": "string", "enum": ["shell", "legs", "egg_sac", "spike", "collar", "glow"]}, "maxItems": 3}}},
    },
}


SIMULATABLE_HINT = (
    " For this batch, restrict the mechanic to exactly one implemented runtime "
    "template: after_steps + spawn_egg, after_steps + spawn_tick, after_steps + "
    "spawn_tack, on_eaten + spawn_tick, or on_feed + spawn_egg. Match the body "
    "to the runtime template: Egg for after_steps spawning, Toe for on_eaten "
    "spawning a Tick, and Tick for on_feed spawning an Egg. Do not use "
    "move_self, remove_enemy, or score_line. Give it a new player-facing noun "
    "phrase (never a schema token or the game title), explain the player "
    "decision in a concrete sentence, and explicitly describe the declared "
    "effect outcome (egg, tick, or tack) instead of an unrelated transformation."
)


def build_prompt(parents: list[str], target_templates: bool = False) -> str:
    prompt = (
        "You are a game-piece concept designer. Propose exactly one novel but bounded "
        "discovery for Tick Tack Toe. Parents: " + ", ".join(parents) + ". "
        "Choose only enum values in the supplied schema. No arbitrary code, money, "
        "network actions, recursive rules, or balance claims."
    )
    return prompt + (SIMULATABLE_HINT if target_templates else "")


def ask(model: str, parents: list[str], endpoint: str,
        target_templates: bool = False) -> dict:
    prompt = build_prompt(parents, target_templates)
    body = json.dumps({"model": model, "stream": False, "format": SCHEMA,
                       "prompt": prompt, "options": {"temperature": 0.7, "num_predict": 220}}).encode()
    request = urllib.request.Request(endpoint.rstrip("/") + "/api/generate", data=body,
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=120) as response:
        outer = json.loads(response.read())
    proposal = json.loads(outer["response"])
    validate(proposal)
    return proposal


def record(model: str, parents: list[str], endpoint: str, proposal: dict,
           created: str | None = None, target_templates: bool = False) -> dict:
    """Wrap a validated proposal with replay/audit provenance."""
    return {
        "schema": "tick-tack-toe.discovery-proposal.v1",
        "created": created or datetime.now(timezone.utc).isoformat(),
        "model": model,
        "endpoint": endpoint,
        "parents": parents,
        "prompt": build_prompt(parents, target_templates),
        "proposal": proposal,
        "safety": {"local_only": endpoint.startswith("http://127.0.0.1") or
                    endpoint.startswith("http://localhost")},
    }


def validate(p: dict) -> None:
    required = set(SCHEMA["required"])
    if set(p) != required:
        raise ValueError("proposal fields must match the allowlist exactly")
    if not (1 <= p["cost"] <= 4):
        raise ValueError("cost outside bounded budget")
    if len(p["art"]["attachments"]) > 3:
        raise ValueError("too many art attachments")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("parents", nargs=2)
    parser.add_argument("--model", default="qwen3:4b")
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434")
    parser.add_argument("--out", type=Path, default=Path("proposal.json"))
    parser.add_argument("--record", type=Path,
                        help="also write model/prompt/parent provenance")
    parser.add_argument("--target-templates", action="store_true",
                        help="ask only for currently simulatable trigger/effect pairs")
    args = parser.parse_args()
    result = ask(args.model, args.parents, args.endpoint, args.target_templates)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.record:
        args.record.write_text(json.dumps(record(args.model, args.parents,
                                                 args.endpoint, result,
                                                 target_templates=args.target_templates), indent=2) +
                               "\n", encoding="utf-8")
    print(f"Wrote bounded proposal to {args.out}")
