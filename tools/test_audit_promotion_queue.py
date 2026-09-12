import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from audit_promotion_queue import audit


class PromotionQueueAuditTests(unittest.TestCase):
    def test_audit_aggregates_proposals_admissions_and_promotion_blockers(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "proposal.json").write_text(json.dumps({
                "schema": "tick-tack-toe.discovery-proposal.v1",
                "proposal": {"name": "Warden"},
            }), encoding="utf-8")
            (root / "admission.json").write_text(json.dumps({
                "admission": {"status": "needs_authoring",
                              "reasons": ["missing rule template"]},
            }), encoding="utf-8")
            (root / "promotion.json").write_text(json.dumps({
                "status": "blocked", "blocked_reasons": ["simulation_runs",
                                                            "visual_approval"],
            }), encoding="utf-8")
            (root / "build.json").write_text(json.dumps({"status": "awaiting_visual_review"}),
                                              encoding="utf-8")
            result = audit(root)
        self.assertEqual(result["files"], 4)
        self.assertEqual(result["statuses"]["proposal_only"], 1)
        self.assertEqual(result["statuses"]["needs_authoring"], 1)
        self.assertEqual(result["statuses"]["blocked"], 1)
        self.assertEqual(result["statuses"]["ignored"], 1)
        self.assertEqual(result["blockers"]["visual_approval"], 1)

    def test_malformed_json_is_visible_and_does_not_abort_queue_scan(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "broken.json").write_text("{", encoding="utf-8")
            result = audit(root)
        self.assertEqual(result["statuses"], {"malformed": 1})
        self.assertEqual(result["blockers"], {"malformed": 1})

    def test_benchmark_batches_expand_admission_rows(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "batch.json").write_text(json.dumps({
                "model": "local-test",
                "rows": [
                    {"ok": True, "proposal": {"name": "A"},
                     "admission": {"status": "needs_authoring",
                                    "reasons": ["missing rule template"]}},
                    {"ok": False, "error": "bad json"},
                    {"ok": True, "proposal": {"name": "B"}},
                ],
            }), encoding="utf-8")
            result = audit(root)
        self.assertEqual(result["files"], 1)
        self.assertEqual(result["statuses"], {
            "needs_authoring": 1, "proposal_only": 1, "rejected": 1,
        })
        self.assertEqual(result["blockers"], {
            "missing rule template": 1, "model output was invalid": 1,
        })
        self.assertEqual(len(result["records"][0]["entries"]), 3)


if __name__ == "__main__":
    unittest.main()
