import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from local_designer import record


class LocalDesignerRecordTests(unittest.TestCase):
    def test_record_keeps_prompt_model_and_parents_separate_from_payload(self):
        proposal = {
            "name": "Warden", "concept": "A bounded watcher.",
            "trigger": "on_play", "target": "self", "effect": "move_self",
            "cost": 1, "art": {"base_kind": "tick", "attachments": []},
        }
        result = record("qwen2.5:7b", ["Egg", "Tack"],
                        "http://127.0.0.1:11434", proposal,
                        created="2026-09-10T00:00:00+00:00")
        self.assertEqual(result["schema"], "tick-tack-toe.discovery-proposal.v1")
        self.assertEqual(result["proposal"], proposal)
        self.assertEqual(result["parents"], ["Egg", "Tack"])
        self.assertIn("Egg, Tack", result["prompt"])
        self.assertEqual(result["model"], "qwen2.5:7b")
        self.assertTrue(result["safety"]["local_only"])

    def test_remote_endpoint_is_explicitly_marked_non_local(self):
        result = record("model", ["Tick", "Toe"], "https://example.invalid", {},
                        created="now")
        self.assertFalse(result["safety"]["local_only"])


if __name__ == "__main__":
    unittest.main()
