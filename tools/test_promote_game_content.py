import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from promote_game_content import promote


def fixtures():
    proposal = {
        "parents": ["Egg", "Tack"],
        "proposal": {"name": "Warden"},
        "admission": {"status": "eligible_for_simulation"},
    }
    simulation = {"status": "passed", "runs": 100, "failures": 0, "bounded": True}
    build = {
        "id": "warden-v1", "key": "new-key", "rendered": True,
        "status": "awaiting_visual_review",
        "frames": [{"direction": 0, "sha256": "abc", "findings": []}],
    }
    review = {"approved_keys": [], "approved_sha256": ["abc"]}
    return proposal, simulation, build, review


class PromotionTests(unittest.TestCase):
    def test_all_gates_promote_without_catalog_mutation(self):
        result = promote(*fixtures())
        self.assertEqual(result["status"], "promoted")
        self.assertEqual(result["approval_basis"], "pixel_hash")
        self.assertTrue(all(result["checks"].values()))

    def test_needs_authoring_proposal_is_blocked(self):
        proposal, simulation, build, review = fixtures()
        proposal["admission"]["status"] = "needs_authoring"
        result = promote(proposal, simulation, build, review)
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["checks"]["admission"])

    def test_insufficient_simulation_is_blocked(self):
        proposal, simulation, build, review = fixtures()
        simulation["runs"] = 99
        result = promote(proposal, simulation, build, review)
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["checks"]["simulation_runs"])

    def test_unreviewed_or_blocked_art_is_blocked(self):
        proposal, simulation, build, review = fixtures()
        review["approved_sha256"] = []
        build["frames"][0]["findings"] = [{"severity": "blocker"}]
        result = promote(proposal, simulation, build, review)
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["checks"]["visual_approval"])
        self.assertFalse(result["checks"]["art_no_blockers"])

    def test_malformed_simulation_evidence_is_blocked_not_executed(self):
        proposal, simulation, build, review = fixtures()
        simulation["runs"] = "not-a-number"
        simulation["failures"] = None
        result = promote(proposal, simulation, build, review)
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["checks"]["simulation_runs"])
        self.assertFalse(result["checks"]["simulation_failures"])


if __name__ == "__main__":
    unittest.main()
