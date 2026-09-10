#!/usr/bin/env python3
"""Ask a local Ollama model for a bounded discovery proposal.

This is deliberately a proposal tool: it never edits game code, grants a card,
or calls the renderer. The game-side validator remains the authority.
"""
from __future__ import annotations

import argparse
import json
import urllib.request
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


def ask(model: str, parents: list[str], endpoint: str) -> dict:
    prompt = (
        "You are a game-piece concept designer. Propose exactly one novel but bounded "
        "discovery for Tick Tack Toe. Parents: " + ", ".join(parents) + ". "
        "Choose only enum values in the supplied schema. No arbitrary code, money, "
        "network actions, recursive rules, or balance claims."
    )
    body = json.dumps({"model": model, "stream": False, "format": SCHEMA,
                       "prompt": prompt, "options": {"temperature": 0.7, "num_predict": 220}}).encode()
    request = urllib.request.Request(endpoint.rstrip("/") + "/api/generate", data=body,
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=120) as response:
        outer = json.loads(response.read())
    proposal = json.loads(outer["response"])
    validate(proposal)
    return proposal


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
    args = parser.parse_args()
    result = ask(args.model, args.parents, args.endpoint)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote bounded proposal to {args.out}")
