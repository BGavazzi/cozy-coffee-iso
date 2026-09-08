"""CPU-only regressions for the design-doc schema and the elicitation wizard."""
import json
import tempfile
import unittest
from pathlib import Path

from design_doc import DesignDocError, load, save, validate
from design_wizard import elicit


def _valid_doc(project="demo_game"):
    return {
        "project": project,
        "title": "Demo Game",
        "genre": "tabletop",
        "core_loop": "Players take turns placing a piece on a shared board.",
        "win_condition": "Three of your pieces in a row.",
        "lose_condition": "The board fills with no winner.",
        "camera": "top_down",
        "tone": ["cozy", "whimsical"],
        "art_influences": {
            "precedent_games": ["Chrono Trigger"],
            "adopt": ["warm palette", "chunky low-poly silhouettes"],
            "reject": [],
            "target": "Warm, rounded, low-poly forms with hard pixel edges.",
        },
        "asset_categories": ["pieces", "ui"],
        "subjects": [
            {"id": "tick", "name": "Tick", "role": "piece", "short_desc": "small round bug",
             "category": "pieces"},
        ],
    }


class DesignDocSchemaTests(unittest.TestCase):
    def test_valid_doc_round_trips_through_disk(self):
        doc = _valid_doc()
        validate(doc)
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        path = Path(folder.name) / "design_doc.json"
        save(doc, path)
        self.assertEqual(load(path), doc)

    def test_rejects_bad_project_name(self):
        with self.assertRaises(DesignDocError):
            validate(_valid_doc(project="Not Snake Case"))

    def test_rejects_unknown_genre(self):
        doc = _valid_doc()
        doc["genre"] = "walking_sim"
        with self.assertRaises(DesignDocError):
            validate(doc)

    def test_rejects_unknown_camera(self):
        doc = _valid_doc()
        doc["camera"] = "first_person"
        with self.assertRaises(DesignDocError):
            validate(doc)

    def test_rejects_duplicate_subject_ids(self):
        doc = _valid_doc()
        doc["subjects"].append(dict(doc["subjects"][0]))
        with self.assertRaises(DesignDocError):
            validate(doc)

    def test_rejects_empty_required_list(self):
        doc = _valid_doc()
        doc["tone"] = []
        with self.assertRaises(DesignDocError):
            validate(doc)

    def test_rejects_unknown_asset_category(self):
        doc = _valid_doc()
        doc["asset_categories"] = ["pieces", "weather"]
        with self.assertRaises(DesignDocError):
            validate(doc)

    def test_rejects_missing_subjects(self):
        doc = _valid_doc()
        doc["subjects"] = []
        with self.assertRaises(DesignDocError):
            validate(doc)

    def test_rejects_unknown_subject_category(self):
        doc = _valid_doc()
        doc["subjects"][0]["category"] = "weather"
        with self.assertRaises(DesignDocError):
            validate(doc)

    def test_rejects_subject_category_not_declared_at_doc_level(self):
        doc = _valid_doc()
        doc["subjects"][0]["category"] = "characters"  # valid enum, but not in asset_categories
        with self.assertRaises(DesignDocError):
            validate(doc)

    def test_save_refuses_to_write_invalid_doc(self):
        doc = _valid_doc(project="bad name")
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        path = Path(folder.name) / "design_doc.json"
        with self.assertRaises(DesignDocError):
            save(doc, path)
        self.assertFalse(path.exists())


class DesignWizardElicitTests(unittest.TestCase):
    def test_fully_prefilled_answers_never_prompt(self):
        doc = _valid_doc()

        def no_prompt(question):
            raise AssertionError(f"should not have prompted for: {question}")

        self.assertEqual(elicit(doc, prompt_fn=no_prompt), doc)

    def test_missing_scalar_field_falls_back_to_prompt_fn(self):
        answers = _valid_doc()
        del answers["title"]
        calls = []

        def fake_prompt(question):
            calls.append(question)
            return "Prompted Title"

        result = elicit(answers, prompt_fn=fake_prompt)
        self.assertEqual(result["title"], "Prompted Title")
        self.assertEqual(len(calls), 1)

    def test_invalid_choice_from_answers_is_rejected(self):
        answers = _valid_doc()
        answers["camera"] = "drone_cam"

        def no_prompt(question):
            raise AssertionError("camera was pre-filled; should not prompt")

        with self.assertRaises(DesignDocError):
            elicit(answers, prompt_fn=no_prompt)

    def test_non_interactive_missing_field_raises_instead_of_blocking(self):
        answers = _valid_doc()
        del answers["win_condition"]

        def refuse(question):
            raise DesignDocError(f"no answer supplied for: {question.strip()}")

        with self.assertRaises(DesignDocError):
            elicit(answers, prompt_fn=refuse)

    def test_interactive_subject_collection_stops_on_blank_id(self):
        answers = _valid_doc()
        del answers["subjects"]
        scripted = iter(["tock", "Tock", "piece", "the other one", "pieces", ""])

        def scripted_prompt(question):
            return next(scripted)

        result = elicit(answers, prompt_fn=scripted_prompt)
        self.assertEqual(len(result["subjects"]), 1)
        self.assertEqual(result["subjects"][0],
                         {"id": "tock", "name": "Tock", "role": "piece",
                          "short_desc": "the other one", "category": "pieces"})

    def test_list_fields_split_on_comma_and_strip_whitespace(self):
        answers = _valid_doc()
        del answers["tone"]
        scripted = iter(["cozy,  whimsical , tense"])

        def scripted_prompt(question):
            return next(scripted)

        result = elicit(answers, prompt_fn=scripted_prompt)
        self.assertEqual(result["tone"], ["cozy", "whimsical", "tense"])


if __name__ == "__main__":
    unittest.main()
