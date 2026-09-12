import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from local_designer import build_prompt


class LocalDesignerPromptTests(unittest.TestCase):
    def test_default_prompt_remains_open_ended(self):
        prompt = build_prompt(["Tick", "Toe"])
        self.assertNotIn("restrict the mechanic", prompt)

    def test_targeted_prompt_names_only_simulatable_templates(self):
        prompt = build_prompt(["Tick", "Toe"], target_templates=True)
        self.assertIn("after_steps + spawn_egg", prompt)
        self.assertIn("on_feed + spawn_egg", prompt)
        self.assertIn("Do not use move_self, remove_enemy, or score_line", prompt)


if __name__ == "__main__":
    unittest.main()
