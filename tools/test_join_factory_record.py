import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from join_factory_record import join


class FactoryRecordTests(unittest.TestCase):
    def test_rejected_proposal_cannot_claim_an_asset(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            proposal = root / "proposal.json"
            admission = root / "admission.json"
            export = root / "export.json"
            proposal.write_text(json.dumps({
                "model": "local-test",
                "proposal": {"name": "Tick", "effect": "move_self"},
            }), encoding="utf-8")
            admission.write_text(json.dumps({
                "parents": ["Tick", "Toe"],
                "admission": {"status": "rejected", "reasons": ["duplicate"]},
            }), encoding="utf-8")
            export.write_text(json.dumps({"assets": [{"id": "tick", "sha256": "abc"}]}),
                              encoding="utf-8")
            result = join(proposal, admission, export_path=export)
        self.assertEqual(result["admission"]["status"], "rejected")
        self.assertEqual(result["lifecycle"]["simulation"], "not_attempted")
        self.assertEqual(result["asset_link"]["status"], "not_attempted")
        self.assertIsNone(result["asset_link"]["export"])

    def test_eligible_proposal_exposes_candidate_but_not_promotion(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            proposal = root / "proposal.json"
            admission = root / "admission.json"
            build = root / "build.json"
            export = root / "export.json"
            proposal.write_text(json.dumps({"proposal": {"name": "Hatchery Trap"}}),
                                encoding="utf-8")
            admission.write_text(json.dumps({
                "admission": {"status": "eligible_for_simulation", "template": "after_steps:spawn_egg",
                               "runtime_rule": "lay-once-v1"},
            }), encoding="utf-8")
            build.write_text(json.dumps([{"id": "hatchery-trap-v1", "key": "build-key"}]),
                             encoding="utf-8")
            export.write_text(json.dumps({"assets": [{"id": "hatchery-trap-v1", "sha256": "abc"}]}),
                              encoding="utf-8")
            result = join(proposal, admission, build, export)
        self.assertEqual(result["lifecycle"]["simulation"], "awaiting")
        self.assertEqual(result["lifecycle"]["render"], "present")
        self.assertEqual(result["lifecycle"]["visual_review"], "approved")
        self.assertEqual(result["asset_link"]["status"], "candidate")
        self.assertEqual(result["asset_link"]["export"]["sha256"], "abc")
        self.assertEqual(result["lifecycle"]["export"], "exported")
        self.assertEqual(result["admission"]["runtime_rule"], "lay-once-v1")

    def test_single_piece_build_record_keeps_frame_hashes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            proposal = root / "proposal.json"
            admission = root / "admission.json"
            build = root / "build.json"
            proposal.write_text(json.dumps({"proposal": {"name": "Family Tick"}}),
                                encoding="utf-8")
            admission.write_text(json.dumps({
                "admission": {"status": "eligible_for_simulation",
                               "template": "after_steps:spawn_tick"},
            }), encoding="utf-8")
            build.write_text(json.dumps({
                "id": "family-tick", "key": "build-key", "status": "awaiting_visual_review",
                "frames": [{"direction": 0, "sha256": "frame-hash", "findings": []}],
            }), encoding="utf-8")
            result = join(proposal, admission, build)
        self.assertEqual(result["lifecycle"]["render"], "present")
        self.assertEqual(result["asset_link"]["build"]["key"], "build-key")
        self.assertEqual(result["asset_link"]["build"]["frames"][0]["sha256"], "frame-hash")

    def test_passed_simulation_advances_lifecycle(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            proposal = root / "proposal.json"
            admission = root / "admission.json"
            simulation = root / "simulation.json"
            proposal.write_text(json.dumps({"proposal": {"name": "Hatchery Trap"}}), encoding="utf-8")
            admission.write_text(json.dumps({
                "admission": {"status": "eligible_for_simulation"},
            }), encoding="utf-8")
            simulation.write_text(json.dumps({
                "status": "passed", "runs": 100, "failures": 0, "bounded": True,
            }), encoding="utf-8")
            result = join(proposal, admission, simulation_path=simulation)
        self.assertEqual(result["lifecycle"]["simulation"], "passed")
        self.assertEqual(result["simulation"]["runs"], 100)


if __name__ == "__main__":
    unittest.main()
