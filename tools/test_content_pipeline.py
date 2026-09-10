"""CPU-only regressions for the design-doc -> asset-manifest content pipeline."""
import json
import tempfile
import unittest
from pathlib import Path

from content_pipeline import (
    build_manifest, seed_for, synthesize_prompt, validate_manifest,
)
from design_doc import save


def _doc():
    return {
        "project": "orchard_dash",
        "title": "Orchard Dash",
        "genre": "arcade",
        "core_loop": "The player runs a fox through an orchard catching apples.",
        "win_condition": "Fill the basket before time runs out.",
        "lose_condition": "The basket is knocked over three times.",
        "camera": "isometric",
        "tone": ["cozy", "energetic"],
        "art_influences": {
            "precedent_games": ["Stardew Valley"],
            "adopt": ["warm light / cool shadow hue shifting"],
            "reject": [],
            "target": "A sunlit orchard in the cafe's own warm pixel-constrained look.",
        },
        "asset_categories": ["characters", "props", "ui", "tiles"],
        "subjects": [
            {"id": "fox_runner", "name": "Fox Runner", "role": "player character",
             "short_desc": "small quick fox with a wicker basket on its back",
             "category": "characters"},
            {"id": "wasp", "name": "Wasp", "role": "hazard",
             "short_desc": "small darting insect", "category": "characters",
             "scale": 0.1},
            {"id": "apple_tree", "name": "Apple Tree", "role": "prop",
             "short_desc": "shakeable tree that drops apples", "category": "props"},
            {"id": "basket_meter", "name": "Basket Meter", "role": "ui",
             "short_desc": "fill-level readout for the run's catch count", "category": "ui"},
            {"id": "orchard_ground", "name": "Orchard Ground", "role": "tile",
             "short_desc": "grass tile with dappled leaf-shadow dithering",
             "category": "tiles"},
        ],
    }


class ContentPipelineTests(unittest.TestCase):
    def test_builds_one_piece_per_prompt_driven_subject_and_skips_procedural(self):
        manifest, skipped = build_manifest(_doc(), "cozy_ghibli")
        self.assertEqual({p["id"] for p in manifest["pieces"]},
                         {"fox_runner", "wasp", "apple_tree", "basket_meter"})
        self.assertEqual([s["id"] for s in skipped], ["orchard_ground"])
        self.assertEqual(skipped[0]["category"], "tiles")

    def test_subject_scale_multiplies_the_category_height_baseline(self):
        manifest, _ = build_manifest(_doc(), "cozy_ghibli")
        pieces = {p["id"]: p for p in manifest["pieces"]}
        # wasp (scale 0.1) shares `characters` with fox_runner (no scale,
        # implicit 1.0) -- without scale both would get the same baseline
        # height, which is exactly the gap this field closes.
        self.assertAlmostEqual(pieces["wasp"]["height"], pieces["fox_runner"]["height"] * 0.1)
        self.assertLess(pieces["wasp"]["height"], pieces["fox_runner"]["height"])

    def test_direction_includes_adopt_and_reject_not_just_target_and_tone(self):
        # Real regression: an earlier version of _direction() silently
        # dropped art_influences.adopt/reject, even though a design doc
        # author explicitly wrote them as constraints -- the same class of
        # data-loss bug as the flat per-category height (see
        # test_subject_scale_multiplies_the_category_height_baseline).
        doc = _doc()
        doc["art_influences"]["reject"] = ["photoreal foliage texture"]
        manifest, _ = build_manifest(doc, "cozy_ghibli")
        self.assertIn("warm light / cool shadow hue shifting", manifest["direction"])
        self.assertIn("photoreal foliage texture", manifest["direction"])
        self.assertIn("cozy", manifest["direction"])

    def test_direction_omits_empty_reject_cleanly(self):
        doc = _doc()
        doc["art_influences"]["reject"] = []
        manifest, _ = build_manifest(doc, "cozy_ghibli")
        self.assertNotIn("Avoid:", manifest["direction"])

    def test_manifest_matches_game_factorys_pieces_json_shape(self):
        manifest, _ = build_manifest(_doc(), "cozy_ghibli")
        self.assertEqual(set(manifest) - {"project", "style", "direction", "pieces"}, set())
        for piece in manifest["pieces"]:
            self.assertEqual(set(piece), {"id", "name", "prompt", "height", "seed"})
            self.assertIsInstance(piece["prompt"], str)
            self.assertGreater(piece["height"], 0)
            self.assertIsInstance(piece["seed"], int)

    def test_prompts_never_contain_style_direction_language(self):
        # The whole point of applying style downstream, not in the prompt
        # (see game_factory.py's own docstring): a subject's prompt must
        # read identically no matter which style pack built the manifest.
        cozy, _ = build_manifest(_doc(), "cozy_ghibli")
        snes, _ = build_manifest(_doc(), "snes_rpg")
        cozy_prompts = {p["id"]: p["prompt"] for p in cozy["pieces"]}
        snes_prompts = {p["id"]: p["prompt"] for p in snes["pieces"]}
        self.assertEqual(cozy_prompts, snes_prompts)
        for word in ("ghibli", "16-bit", "snes", "pixel"):
            for prompt in cozy_prompts.values():
                self.assertNotIn(word, prompt.lower())

    def test_style_name_is_recorded_and_must_exist(self):
        manifest, _ = build_manifest(_doc(), "snes_rpg")
        self.assertEqual(manifest["style"], "snes_rpg")
        with self.assertRaises(SystemExit):
            build_manifest(_doc(), "not_a_real_style")

    def test_seed_is_deterministic_and_subject_specific(self):
        self.assertEqual(seed_for("orchard_dash", "fox_runner"),
                         seed_for("orchard_dash", "fox_runner"))
        self.assertNotEqual(seed_for("orchard_dash", "fox_runner"),
                            seed_for("orchard_dash", "apple_tree"))
        self.assertNotEqual(seed_for("orchard_dash", "fox_runner"),
                            seed_for("other_project", "fox_runner"))

    def test_synthesize_prompt_wraps_short_desc_with_correct_article(self):
        self.assertEqual(
            synthesize_prompt({"id": "x", "short_desc": "small quick fox."}),
            "a small quick fox")
        self.assertEqual(
            synthesize_prompt({"id": "y", "short_desc": "old brass key"}),
            "an old brass key")

    def test_synthesize_prompt_does_not_double_an_existing_article(self):
        # Real regression: "a single round red apple..." (a design doc
        # author already wrote its own article) produced "an a single
        # round red apple...", a doubled article -- caught by an actual
        # SDXL run, not by inspection.
        self.assertEqual(
            synthesize_prompt({"id": "z", "short_desc": "a single round red apple"}),
            "a single round red apple")
        self.assertEqual(
            synthesize_prompt({"id": "w", "short_desc": "An old brass key"}),
            "an old brass key")
        self.assertEqual(
            synthesize_prompt({"id": "v", "short_desc": "the last apple on the tree"}),
            "a last apple on the tree")

    def test_validate_manifest_rejects_duplicate_ids(self):
        manifest, _ = build_manifest(_doc(), "cozy_ghibli")
        manifest["pieces"].append(dict(manifest["pieces"][0]))
        with self.assertRaises(ValueError):
            validate_manifest(manifest)

    def test_validate_manifest_rejects_overlong_prompt(self):
        manifest, _ = build_manifest(_doc(), "cozy_ghibli")
        manifest["pieces"][0]["prompt"] = " ".join(["word"] * 40)
        with self.assertRaises(ValueError):
            validate_manifest(manifest)

    def test_no_prompt_driven_subjects_is_an_error_not_an_empty_manifest(self):
        doc = _doc()
        tile = next(s for s in doc["subjects"] if s["category"] == "tiles")
        doc["subjects"] = [tile]
        doc["asset_categories"] = ["tiles"]
        with self.assertRaises(ValueError):
            build_manifest(doc, "cozy_ghibli")

    def test_full_round_trip_from_a_real_design_doc_file(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        path = Path(folder.name) / "design_doc.json"
        save(_doc(), path)
        from content_pipeline import load_design_doc
        manifest, skipped = build_manifest(load_design_doc(path), "cozy_ghibli")
        self.assertEqual(len(manifest["pieces"]), 4)
        self.assertEqual(len(skipped), 1)


if __name__ == "__main__":
    unittest.main()
