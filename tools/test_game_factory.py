"""CPU-only regressions for the recipe-to-existing-factory adapter."""
import json
import tempfile
import unittest
from pathlib import Path
from game_factory import ROOT, prepare
from game_pieces import build


class RecipeBuildTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / 'pieces.json'
        self.config = json.loads((ROOT / 'games/tick_tack_toe/pieces.json').read_text())

    def rows(self, only='tick'):
        self.path.write_text(json.dumps(self.config))
        return prepare(self.path, only)[1]

    def test_deterministic_and_includes_both_parent_traits(self):
        self.assertEqual(self.rows(), self.rows())
        hybrid = self.rows('tick-armored-fertile')[0]
        self.assertEqual(hybrid['recipe']['piece']['traits'], ['armored', 'fertile'])
        self.assertNotEqual(hybrid['key'], self.rows('tick-armored')[0]['key'])

    def test_prompt_seed_height_and_traits_invalidate_build(self):
        original = self.rows()[0]['key']
        for field, value in [('prompt', 'different thing'), ('seed', 77),
                             ('height', 0.7), ('traits', ['charged'])]:
            old = self.config['pieces'][0][field]
            self.config['pieces'][0][field] = value
            self.assertNotEqual(original, self.rows()[0]['key'], field)
            self.config['pieces'][0][field] = old

    def test_style_is_part_of_cache_identity(self):
        original = self.rows()[0]['key']
        self.config['style'] = 'cozy_ghibli'
        self.assertNotEqual(original, self.rows()[0]['key'])

    def test_reject_unknown_duplicate_and_unsafe_identity(self):
        with self.assertRaises(ValueError):
            self.rows('not-a-piece')
        self.config['pieces'].append(self.config['pieces'][0])
        with self.assertRaises(ValueError):
            self.rows()
        self.config['pieces'].pop()
        self.config['project'] = '../cafe'
        with self.assertRaises(ValueError):
            self.rows()

    def test_composed_brood_snare_keeps_both_parent_visual_signatures(self):
        """A composed recipe must not silently collapse to either parent art."""
        plain = build('tack')
        snare = build('tack', variant='snare-tack-v1')
        brood = build('tack', variant='brood-snare-v1')
        materials = {face[2] for face in brood.faces}
        self.assertIn('cream', materials)  # hatchery/brood parent
        self.assertIn('sky', materials)    # snare parent
        self.assertGreater(len(brood.faces), len(snare.faces))
        self.assertGreater(len(snare.faces), len(plain.faces))


if __name__ == '__main__':
    unittest.main()
