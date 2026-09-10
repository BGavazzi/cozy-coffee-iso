import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from export_game import export


class ExportApprovalTests(unittest.TestCase):
    def _fixture(self, folder: Path, approved: dict):
        source = folder / 'piece.png'
        source.write_bytes(b'stable-pixels')
        digest = __import__('hashlib').sha256(source.read_bytes()).hexdigest()
        build = folder / 'build.json'
        build.write_text(json.dumps({
            'id': 'tick', 'key': 'new-code-key',
            'status': 'awaiting_visual_review',
            'recipe': {'producer': {'style': 'snes_rpg', 'backend': 'procedural'}},
            'frames': [{'direction': 0, 'path': str(source), 'sha256': digest,
                        'findings': []}],
        }), encoding='utf-8')
        batch = folder / 'batch.json'
        batch.write_text(json.dumps([{'id': 'tick', 'key': 'new-code-key',
                                     'status': 'awaiting_visual_review',
                                     'build': str(build)}]), encoding='utf-8')
        review = folder / 'review.json'
        review.write_text(json.dumps(approved | {'approved_keys': []}), encoding='utf-8')
        return batch, review, source, digest

    def test_unchanged_pixels_can_reuse_approval_after_code_key_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch, review, source, digest = self._fixture(
                Path(tmp), {'approved_sha256': [__import__('hashlib').sha256(
                    b'stable-pixels').hexdigest()]})
            manifest = export(batch, review, Path(tmp) / 'public')
            self.assertEqual(manifest['tick']['sha256'], digest)

    def test_changed_pixels_still_fail_without_matching_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch, review, source, digest = self._fixture(
                Path(tmp), {'approved_sha256': ['different']})
            with self.assertRaisesRegex(ValueError, 'Unapproved'):
                export(batch, review, Path(tmp) / 'public')

    def test_hash_reuse_keeps_existing_canonical_filename(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            batch, review, source, digest = self._fixture(
                folder, {'approved_sha256': [__import__('hashlib').sha256(
                    b'stable-pixels').hexdigest()]})
            public = folder / 'public'
            public.mkdir()
            (public / 'tick-old-key.png').write_bytes(source.read_bytes())
            (public / 'manifest.json').write_text(json.dumps({
                'tick': {'file': 'tick-old-key.png', 'key': 'old-key',
                         'sha256': digest}
            }), encoding='utf-8')
            manifest = export(batch, review, public)
            self.assertEqual(manifest['tick']['file'], 'tick-old-key.png')
            self.assertEqual(manifest['tick']['key'], 'old-key')


if __name__ == '__main__':
    unittest.main()
