#!/usr/bin/env python3
"""Summarise local proposal/admission/promotion records without mutating them."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def audit(directory: Path) -> dict:
    statuses = Counter()
    blockers = Counter()
    records = []
    for path in sorted(directory.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            statuses["malformed"] += 1
            blockers["malformed"] += 1
            records.append({"file": path.name, "status": "malformed"})
            continue
        if not isinstance(payload, dict):
            status, reasons = "ignored", []
        elif ("checks" in payload or "blocked_reasons" in payload) and "status" in payload:
            status = payload["status"]
            reasons = payload.get("blocked_reasons", []) if status == "blocked" else []
        elif "admission" in payload:
            status = payload["admission"].get("status", "malformed")
            reasons = payload["admission"].get("reasons", [])
        elif (payload.get("schema") == "tick-tack-toe.discovery-proposal.v1" or
              {"name", "trigger", "effect"}.issubset(payload)):
            # Designer records are intentionally proposals only, not decisions.
            status = "proposal_only"
            reasons = []
        else:
            # Build/export reports can share the directory but are not queue
            # records. Keep them visible without inflating proposal counts.
            status, reasons = "ignored", []
        statuses[str(status)] += 1
        for reason in reasons:
            blockers[str(reason)] += 1
        records.append({"file": path.name, "status": status,
                        "blocked_reasons": reasons})
    return {"schema": "tick-tack-toe.promotion-queue-audit.v1",
            "directory": str(directory), "files": len(records),
            "statuses": dict(sorted(statuses.items())),
            "blockers": dict(sorted(blockers.items())), "records": records}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = audit(args.directory)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.out:
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
