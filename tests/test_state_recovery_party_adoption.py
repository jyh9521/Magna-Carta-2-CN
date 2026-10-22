from pathlib import Path
import copy, hashlib, json, unittest
from tools.translation_fragments import whitespace_suffixes
R = Path(__file__).resolve().parents[1]
L = lambda p: json.loads((R/p).read_bytes())
H = lambda b: hashlib.sha256(b).hexdigest()


class StateRecoveryPartyAdoptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = L('locales/zh-Hans/candidate-decisions/state-recovery-and-party-adoption.json')
        cls.plan = L(cls.record['plan'])
        cls.review = L(cls.record['review'])
        cls.evidence = L(cls.record['evidence']['path'])
        cls.byid = {e['id']: e for e in cls.plan['entries']}

    def test_exact_eleven_new_fields_and_hash_locks(self):
        self.assertEqual((len(self.byid), self.record['new_translations']), (11, 11))
        for field in ['plan', 'review']:
            self.assertEqual(H((R/self.record[field]).read_bytes()), self.record[field+'_sha256'])
        self.assertEqual(H((R/self.record['evidence']['path']).read_bytes()), self.record['evidence']['sha256'])
        for row in self.record['entries']:
            e = self.byid[row['id']]
            self.assertEqual(e['source_sha256'], row['source_sha256'])
            self.assertEqual(H(e['translation'].encode()), row['translation_sha256'])
        self.assertFalse(self.record['game_rendering_verified'])

    def test_state_self_heal_is_complete_numeric_delta_not_target_character(self):
        u = self.evidence['huaren']
        self.assertEqual((u['function']['export'], u['function']['script_size']), (20544, 249))
        self.assertEqual(len(u['function']['statements']), 8)
        self.assertTrue(any(x['path'].endswith('.nAddedHP') and x['kind'] == 'IntProperty' for x in u['function']['locals']))
        self.assertEqual(len(u['direct_coverage']), 2)
        self.assertTrue(all(x['all_direct_hits_in_proven_assignment'] for x in u['direct_coverage']))
        self.assertFalse(u['executed'])
        self.assertFalse(u['dynamic_constructed_keys_excluded'])
        self.assertIn('not other packages', u['direct_scope'])
        self.assertEqual('修亚伦恢复了' + '125' + '点HP', '修亚伦恢复了125点HP')

    def test_party_shared_fragments_are_atomic_and_old_shop_dependency_unchanged(self):
        p = self.evidence['party']
        self.assertEqual(len(p['typed_levelup']['assignments']), 4)
        self.assertEqual(len(p['functions']), 16)
        self.assertEqual(len(self.review['fragment_groups']), 2)
        self.assertEqual(whitespace_suffixes(self.plan, self.review), set())
        broken = copy.deepcopy(self.plan)
        i = self.review['fragment_groups'][0]['members'][0]['id']
        next(e for e in broken['entries'] if e['id'] == i)['translation'] += '改'
        with self.assertRaises(ValueError):
            whitespace_suffixes(broken, self.review)
        dep = p['dependent_existing_targets'][0]
        old = next(e for e in L(dep['existing_batch'])['entries'] if e['id'] == dep['id'])
        self.assertEqual(old['source_sha256'], dep['source_sha256'])
        self.assertEqual(H(old['translation'].encode()), dep['translation_sha256'])
        self.assertNotIn(dep['id'], self.byid)
        for row in self.record['entries']:
            if row['key'] in ['JoinParty', 'LeaveParty', 'JoinGuest', 'LeaveGuest']:
                self.assertTrue(self.byid[row['id']]['translation'].startswith('\\n'))
        self.assertFalse(p['executed'])

    def test_unfinished_quest_clauses_keep_unfinished_ending_and_final_ascii_space(self):
        q = self.evidence['unfinished_quest']
        self.assertTrue(q['jpn_parallel_values_empty'])
        self.assertEqual(q['full_context_field_counts'], [18, 19, 18, 19])
        self.assertTrue(q['missing_continuations_not_reconstructed'])
        for e in q['entries']:
            self.assertEqual(H(e['source'].encode()), e['source_sha256'])
            self.assertTrue(e['source'].endswith(' '))
            self.assertTrue(e['target'].endswith('的 '))
            self.assertEqual(self.byid[e['id']]['translation'], e['target'])
            self.assertFalse(e['target'].strip().endswith(('。', '！', '？')))


if __name__ == '__main__':
    unittest.main()
