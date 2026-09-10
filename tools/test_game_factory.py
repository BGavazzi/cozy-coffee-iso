"""CPU-only regressions for the recipe-to-existing-factory adapter."""
import json
import tempfile
import unittest
from pathlib import Path
from game_factory import ROOT, prepare


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

    def test_style_flag_overrides_manifest_without_editing_it(self):
        """The CLI --style override, not the JSON edit above.

        Same identity change as `test_style_is_part_of_cache_identity`, but
        via the `style` param on `prepare()` -- the manifest's own field is
        left untouched on disk, which is the whole point: building a second
        style should not require a second copy of the recipe file.
        """
        self.path.write_text(json.dumps(self.config))
        on_disk = json.loads(self.path.read_text())
        self.assertEqual(on_disk['style'], 'snes_rpg')
        default_key = prepare(self.path, 'tick')[1][0]['key']
        config, rows = prepare(self.path, 'tick', style='cozy_ghibli')
        self.assertEqual(config['style'], 'cozy_ghibli')
        self.assertNotEqual(default_key, rows[0]['key'])
        # The file on disk never changed -- the override is call-scoped.
        self.assertEqual(json.loads(self.path.read_text())['style'], 'snes_rpg')
        # No override at all still resolves the manifest's own declared style.
        self.assertEqual(prepare(self.path, 'tick')[0]['style'], 'snes_rpg')

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


if __name__ == '__main__':
    unittest.main()
