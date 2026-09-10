import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from admit_proposal import admit


def proposal(**changes):
    value = {
        'name': 'Egg Warden', 'concept': 'A delayed egg that creates one ally.',
        'trigger': 'after_steps', 'target': 'adjacent_empty', 'effect': 'spawn_egg',
        'cost': 2, 'art': {'base_kind': 'egg', 'attachments': ['shell']},
    }
    value.update(changes)
    return value


class AdmissionTests(unittest.TestCase):
    def test_known_bounded_pair_is_simulatable(self):
        self.assertEqual(admit(proposal())['status'], 'eligible_for_simulation')

    def test_unknown_effect_pair_needs_authored_runtime_template(self):
        result = admit(proposal(trigger='on_play', effect='remove_enemy'))
        self.assertEqual(result['status'], 'needs_authoring')

    def test_unbounded_and_low_quality_proposals_are_rejected(self):
        self.assertEqual(admit(proposal(target='board'))['status'], 'rejected')
        self.assertEqual(admit(proposal(name='X'))['status'], 'rejected')
        self.assertEqual(admit(proposal(art={'base_kind': 'egg', 'attachments': ['shell', 'shell']}))['status'], 'rejected')

    def test_redundant_parent_mechanic_is_not_meaningful_novelty(self):
        result = admit(proposal(trigger='on_feed'), parents=['Tick', 'Toe'])
        self.assertEqual(result['status'], 'rejected')
        self.assertIn('adds no new decision', result['reasons'][0])

    def test_same_template_without_known_parent_pair_remains_eligible(self):
        self.assertEqual(
            admit(proposal(trigger='on_feed'), parents=['Egg', 'Tack'])['status'],
            'eligible_for_simulation',
        )


if __name__ == '__main__':
    unittest.main()
