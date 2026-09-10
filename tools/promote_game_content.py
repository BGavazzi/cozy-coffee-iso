#!/usr/bin/env python3
"""Evaluate a game-content proposal against every promotion gate.

This tool records a decision; it never edits the game's catalog.  The explicit
promotion step is intentional: local-model output, simulation evidence, and
art review remain separate inputs, so a successful render cannot accidentally
become canonical content.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _visual_approval(build: dict, review: dict) -> str | None:
    frame = next((f for f in build.get("frames", []) if f.get("direction") == 0), None)
    if not frame:
        return None
    if build.get("key") in review.get("approved_keys", []):
        return "build_key"
    if frame.get("sha256") in review.get("approved_sha256", []):
        return "pixel_hash"
    return None


def promote(proposal: dict, simulation: dict, build: dict, review: dict) -> dict:
    """Return an auditable promotion decision without mutating a catalog."""
    checks = {}
    admission = proposal.get("admission", {})
    checks["admission"] = admission.get("status") == "eligible_for_simulation"
    checks["simulation_status"] = simulation.get("status") == "passed"
    checks["simulation_runs"] = int(simulation.get("runs", 0)) >= 100
    checks["simulation_failures"] = int(simulation.get("failures", 0)) == 0
    checks["simulation_bounded"] = simulation.get("bounded") is True
    checks["art_rendered"] = build.get("rendered") is True
    checks["art_status"] = build.get("status") == "awaiting_visual_review"
    checks["art_no_blockers"] = not any(
        finding.get("severity") == "blocker"
        for frame in build.get("frames", [])
        for finding in frame.get("findings", [])
    )
    approval = _visual_approval(build, review)
    checks["visual_approval"] = approval is not None
    status = "promoted" if all(checks.values()) else "blocked"
    return {
        "status": status,
        "checks": checks,
        "approval_basis": approval,
        "proposal": proposal.get("proposal", proposal),
        "parents": proposal.get("parents", []),
        "simulation": simulation,
        "art": {
            "id": build.get("id"),
            "build_key": build.get("key"),
            "sha256": next((f.get("sha256") for f in build.get("frames", [])
                             if f.get("direction") == 0), None),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("proposal", type=Path)
    parser.add_argument("simulation", type=Path)
    parser.add_argument("build", type=Path)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    decision = promote(
        json.loads(args.proposal.read_text(encoding="utf-8")),
        json.loads(args.simulation.read_text(encoding="utf-8")),
        json.loads(args.build.read_text(encoding="utf-8")),
        json.loads(args.review.read_text(encoding="utf-8")),
    )
    args.out.write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": decision["status"], "out": str(args.out)}))
    return 0 if decision["status"] == "promoted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
