#!/usr/bin/env python3
"""Join proposal, admission, and asset evidence without skipping lifecycle gates."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")


def _proposal(payload: Any) -> dict:
    candidate = payload.get("proposal", payload) if isinstance(payload, dict) else {}
    return candidate if isinstance(candidate, dict) else {}


def _admission(payload: Any) -> dict:
    candidate = payload.get("admission", payload) if isinstance(payload, dict) else {}
    return candidate if isinstance(candidate, dict) else {}


def _asset_index(payload: Any) -> dict[str, dict]:
    assets = payload.get("assets", []) if isinstance(payload, dict) else []
    return {str(asset["id"]): asset for asset in assets
            if isinstance(asset, dict) and asset.get("id")}


def join(
    proposal_path: Path,
    admission_path: Path,
    build_path: Path | None = None,
    export_path: Path | None = None,
) -> dict:
    proposal_record = _read(proposal_path)
    admission_record = _read(admission_path)
    proposal = _proposal(proposal_record)
    admission = _admission(admission_record)
    status = str(admission.get("status", "malformed"))
    proposal_hash = hashlib.sha256(
        json.dumps(proposal, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:16]
    candidate_ids = [_slug(str(proposal.get("name", "")))]
    if candidate_ids[0] and not candidate_ids[0].endswith("-v1"):
        candidate_ids.append(f"{candidate_ids[0]}-v1")

    build_candidates: list[dict] = []
    if build_path and build_path.exists():
        payload = _read(build_path)
        if isinstance(payload, list):
            rows = payload
        elif isinstance(payload, dict) and isinstance(payload.get("rows"), list):
            rows = payload["rows"]
        elif isinstance(payload, dict) and payload.get("id") and payload.get("key"):
            # Accept the canonical per-piece build.json as well as the
            # latest-build summary list.  The single-record form carries the
            # frame hashes needed for an auditable sprite link.
            rows = [payload]
        else:
            rows = []
        build_candidates = [row for row in rows if isinstance(row, dict)]
    build_match = next(
        (row for row in build_candidates if row.get("id") in candidate_ids), None
    )
    exported_asset = None
    if export_path and export_path.exists() and status == "eligible_for_simulation":
        exported_asset = next(
            (asset for asset in _asset_index(_read(export_path)).values()
             if asset.get("id") in candidate_ids),
            None,
        )

    eligible = status == "eligible_for_simulation"
    lifecycle = {
        "simulation": "awaiting" if eligible else "not_attempted",
        "render": "present" if eligible and build_match else
                  "awaiting" if eligible else "not_attempted",
        "visual_review": "approved" if eligible and exported_asset else
                         "awaiting" if eligible else "not_attempted",
        "export": "exported" if eligible and exported_asset else
                  "awaiting" if eligible else "not_attempted",
    }
    return {
        "schema": "tick-tack-toe.factory-record.v1",
        "proposal_hash": proposal_hash,
        "sources": {
            "proposal": str(proposal_path),
            "admission": str(admission_path),
            "build": str(build_path) if build_path else None,
            "export": str(export_path) if export_path else None,
        },
        "parents": admission_record.get("parents", []) if isinstance(admission_record, dict) else [],
        "model": proposal_record.get("model") if isinstance(proposal_record, dict) else None,
        "proposal": proposal,
        "admission": {
            "status": status,
            "reasons": admission.get("reasons", []),
            "template": admission.get("template"),
            "runtime_rule": admission.get("runtime_rule"),
        },
        "lifecycle": lifecycle,
        "asset_link": {
            "status": "candidate" if build_match and eligible else "not_attempted",
            "candidate_ids": candidate_ids,
            "build": build_match,
            "export": exported_asset,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("proposal", type=Path)
    parser.add_argument("admission", type=Path)
    parser.add_argument("--build", type=Path)
    parser.add_argument("--export", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = join(args.proposal, args.admission, args.build, args.export)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.out:
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
