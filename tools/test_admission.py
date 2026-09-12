import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from admit_proposal import admit


def proposal(**changes):
    value = {
        'name': 'Egg Warden', 'concept': 'A delayed egg that creates one ally.',
        'trigger': 'after_steps', 'target': 'adjacent_empty', 'effect': 'spawn_egg',
        'cost': 2, 'art': {'base_kind': 'tack', 'attachments': ['shell']},
    }
    value.update(changes)
    return value


class AdmissionTests(unittest.TestCase):
    def test_known_bounded_pair_is_simulatable(self):
        result = admit(proposal())
        self.assertEqual(result['status'], 'eligible_for_simulation')
        self.assertEqual(result['runtime_rule'], 'lay-once-v1')

    def test_allowlisted_template_requires_compatible_body_family(self):
        result = admit(proposal(art={'base_kind': 'tick', 'attachments': []}))
        self.assertEqual(result['status'], 'needs_authoring')
        self.assertIn('requires base_kind tack', result['reasons'][0])
        result = admit(proposal(trigger='after_steps', effect='spawn_tick',
                                concept='A delayed tick that hatches from an egg.',
                                art={'base_kind': 'tick', 'attachments': []}))
        self.assertEqual(result['status'], 'needs_authoring')
        self.assertIn('requires base_kind egg', result['reasons'][0])

    def test_concept_must_describe_declared_effect(self):
        result = admit(proposal(concept='A playful shield for the board.'))
        self.assertEqual(result['status'], 'rejected')
        self.assertTrue(any('declared effect spawn_egg' in reason
                            for reason in result['reasons']))

    def test_runtime_duplicate_is_not_a_discovery(self):
        result = admit(proposal(
            name='Nest Guardian',
            concept='When this Tick feeds an adjacent Toe, it lays one Egg in an adjacent empty cell.',
            trigger='on_feed',
            art={'base_kind': 'tick', 'attachments': ['egg_sac']},
        ))
        self.assertEqual(result['status'], 'rejected')
        self.assertIn('duplicates existing fertile Tick behavior', result['reasons'][0])

    def test_unknown_effect_pair_needs_authored_runtime_template(self):
        result = admit(proposal(trigger='on_play', effect='remove_enemy'))
        self.assertEqual(result['status'], 'needs_authoring')

    def test_unbounded_and_low_quality_proposals_are_rejected(self):
        self.assertEqual(admit(proposal(target='board'))['status'], 'rejected')
        self.assertEqual(admit(proposal(name='X'))['status'], 'rejected')
        self.assertEqual(admit(proposal(name='spawn_tick'))['status'], 'rejected')
        self.assertEqual(admit(proposal(name='Tick Tack Toe'))['status'], 'rejected')
        self.assertEqual(admit(proposal(name='TickTackToe'))['status'], 'rejected')
        self.assertEqual(admit(proposal(name='tick', concept='A real decision here'))['status'], 'rejected')
        self.assertEqual(admit(proposal(concept='a game piece'))['status'], 'rejected')
        self.assertEqual(admit(proposal(concept='food'))['status'], 'rejected')
        self.assertEqual(admit(proposal(art={'base_kind': 'egg', 'attachments': ['shell', 'shell']}))['status'], 'rejected')

    def test_redundant_parent_mechanic_is_not_meaningful_novelty(self):
        result = admit(proposal(trigger='on_feed'), parents=['Tick', 'Toe'])
        self.assertEqual(result['status'], 'rejected')
        self.assertIn('adds no new decision', result['reasons'][0])

    def test_parent_name_collision_is_rejected(self):
        result = admit(proposal(name='TICK'), parents=['Tick', 'Toe'])
        self.assertEqual(result['status'], 'rejected')
        self.assertTrue(any('duplicates a parent' in reason for reason in result['reasons']))

    def test_runtime_duplicate_is_rejected_without_known_parent_pair(self):
        result = admit(proposal(trigger='on_feed',
                                art={'base_kind': 'tick', 'attachments': []}),
                       parents=['Egg', 'Tack'])
        self.assertEqual(result['status'], 'rejected')

    def test_admission_envelope_is_promotion_ready(self):
        payload = proposal(name='Brood Warden')
        decision = admit(payload, parents=['Egg', 'Tack'])
        envelope = {'parents': ['Egg', 'Tack'], 'proposal': payload,
                    'admission': decision}
        self.assertEqual(envelope['admission']['status'],
                         'eligible_for_simulation')
        self.assertEqual(envelope['proposal']['name'], 'Brood Warden')


if __name__ == '__main__':
    unittest.main()
