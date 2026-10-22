"""Actual tail adoption: source gaps stay gaps; consumers establish word order."""
import hashlib
import json
import re
import struct
from pathlib import Path
import unittest
from tools.translation_fragments import whitespace_suffixes

ROOT = Path(__file__).resolve().parents[1]
BASE = 'locales/zh-Hans/'


def load(path):
    return json.loads((ROOT / path).read_bytes())


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def local(ref):
    return b'\x00' + struct.pack('>I', ref)


def literal(value):
    return b'\x1f' + value.encode() + b'\0'


def concat(*values):
    result = values[0]
    for value in values[1:]:
        result = b'\x70' + result + value + b'\x16'
    return result


class PartialFieldAdoptionTests(unittest.TestCase):
    def setUp(self):
        self.d = load(BASE + 'candidate-decisions/preserved-partials-adoption.json')
        self.evidence = load(self.d['evidence']['path'])
        self.plan = load(self.d['plan'])
        self.review = load(self.d['review'])
        self.byid = {e['id']: e for e in self.plan['entries']}
        self.bykey = {e['key']: self.byid[e['id']] for e in self.d['entries']}

    def test_forty_real_drafts_and_exact_source_target_locks(self):
        self.assertEqual(len(self.byid), 40)
        self.assertEqual(self.d['new_translations'], 40)
        self.assertEqual(self.review['status'], 'draft')
        for field in ['plan', 'review', 'evidence']:
            ref = self.d[field] if field == 'evidence' else {'path': self.d[field], 'sha256': self.d[field + '_sha256']}
            self.assertEqual(digest((ROOT / ref['path']).read_bytes()), ref['sha256'])
        for e in self.d['entries']:
            p = self.byid[e['id']]
            self.assertEqual(p['source_sha256'], e['source_sha256'])
            self.assertEqual(digest(p['translation'].encode()), e['translation_sha256'])
        self.assertFalse(self.d['human_finalized'])
        self.assertFalse(self.d['game_rendering_verified'])

    def test_eighteen_equipment_gaps_plus_breaks_and_tail_space_preserved(self):
        equipment = [e for e in self.d['entries'] if e['document'].endswith('MC2Item.int')]
        self.assertEqual(len(equipment), 18)
        for e in equipment:
            target = self.byid[e['id']]['translation']
            shape = e['source_shape']
            self.assertEqual(shape['numeric_literals'], [])
            self.assertEqual(re.findall(r'[0-9]+', target), [])
            self.assertEqual(target.count('+'), shape['plus_count'])
            self.assertEqual(target.count('\\n'), shape['functional_break_count'])
            self.assertEqual(target[len(target.rstrip(' \t')):], shape['trailing_horizontal_space'])
        self.assertTrue(self.bykey['308_ax_D']['translation'].endswith('+ '))

    def test_hp_six_pairs_are_atomic_and_form_complete_offline_examples(self):
        self.assertEqual(whitespace_suffixes(self.plan, self.review), set())
        group = self.review['fragment_groups'][0]
        self.assertEqual((len(group['members']), len(group['joins'])), (12, 6))
        self.assertEqual({e['role'] for e in group['members']}, {'prefix', 'suffix'})
        for stem in ['Astarot', 'Leviathan', 'Beliel', 'beeljebub', 'Purson', 'Stras']:
            prefix, suffix = [self.bykey[stem + 'Recover_' + str(n)]['translation'] for n in [1, 2]]
            self.assertTrue(prefix.endswith('恢复了'))
            self.assertEqual(suffix, '点HP')
            for number in [0, 1, 100, 9999]:
                example = prefix + str(number) + suffix
                self.assertEqual(example.count('恢复了'), 1)
                self.assertIn(str(number) + '点HP', example)
        damaged = json.loads(json.dumps(self.plan))
        damaged['entries'] = [e for e in damaged['entries'] if e['id'] != group['members'][0]['id']]
        with self.assertRaisesRegex(ValueError, 'lock'):
            whitespace_suffixes(damaged, self.review)

    def test_combo_complete_assignments_reconstruct_from_concat_grammar(self):
        proof = self.evidence['combo']
        bindings = {e['name']: e for e in proof['function']['bindings']}
        self.assertEqual(bindings['nComboNum']['kind'], 'IntProperty')
        self.assertEqual(bindings['tempString']['kind'], 'StrProperty')
        self.assertEqual(proof['concat_declaration']['native_token'], 112)
        self.assertEqual(proof['concat_declaration']['parameters'], ['StrProperty', 'StrProperty'])
        call = bytes.fromhex('1b0000228100000000190000002d2d0005000100003f100000002d2c16')
        self.assertEqual(proof['function']['virtual_call']['name'], 'GetStyleName')
        self.assertEqual(proof['function']['virtual_call']['name_index'], 8833)
        windows = proof['function']['four_assignment_windows']
        self.assertEqual(len(windows), 4)
        for window in windows:
            label = call if window['branch'] == 'GetStyleName' else literal('<Strings:MC2UI.Level_Up.Juto_Village_Yupa>')
            expression = concat(literal('<Styles:MC2UITextStyle_0>'), label, literal('<Styles:/>'), literal('<Strings:MC2UI.Level_Up.Combo_'), b'\x38\x53' + local(bindings['nComboNum']['object_ref']), literal('>'))
            assignment = b'\x0f' + local(bindings['tempString']['object_ref']) + expression
            self.assertEqual(assignment.hex(), window['hex'])
            self.assertEqual(digest(assignment), window['sha256'])
        for n in range(1, 10):
            self.assertEqual(self.bykey['Combo_' + str(n)]['translation'], f'的普通攻击<Styles:MC2UITextStyle_0>第{n}击<Styles:/>已可使用')

    def test_getter_has_twelve_style_labels_not_assumed_character_prefixes(self):
        getter = self.evidence['combo']['getter']
        self.assertEqual(len(getter['branches']), 6)
        self.assertEqual(getter['comparison_tokens'], {'EqualEqual_StrStr': 122, 'EqualEqual_IntInt': 154})
        for branch in getter['branches']:
            for field, n in [('zero_return', 0), ('other_return', 1)]:
                self.assertRegex(branch[field], r'^<Strings:MC2UI\.Battle_Style\.[A-Za-z]+_Style_' + str(n) + r'>$')
        self.assertEqual(self.bykey['GetEXP']['translation'], '点经验值已获得')

    def test_experience_origin_is_unique_typed_cast_not_digit_tag_loop(self):
        functions = self.evidence['experience_numeric_origin']['functions']
        self.assertEqual(len(functions), 2)
        for function in functions:
            source, target = function['source_binding'], function['destination_binding']
            self.assertEqual((source['kind'], target['kind']), ('FloatProperty', 'StrProperty'))
            expected = b'\x0f' + local(target['object_ref']) + b'\x38\x53\x38\x44' + local(source['object_ref'])
            self.assertEqual(expected.hex(), function['assignment_hex'])
            self.assertEqual(digest(expected), function['assignment_sha256'])
            self.assertEqual(function['ExpNum_assignment_count'], 1)
            self.assertFalse(function['calls_GetStringFromNumber'])
            self.assertFalse(function['tag_constructor_in_assignment'])

    def test_direct_reference_coverage_does_not_claim_all_dynamic_consumers(self):
        proof = self.evidence['recovery_reference_coverage']
        self.assertEqual(len(proof['functions']), 7)
        self.assertEqual(len(proof['direct_tag_searches']), 12)
        total = 0
        for row in proof['direct_tag_searches']:
            self.assertTrue(row['all_direct_references_covered'])
            for search in row['searches']:
                if search['source'] == 'native':
                    self.assertEqual(search['offsets'], [])
                else:
                    total += len(search['offsets'])
        self.assertEqual(total, 14)
        # False means their existence was not ruled out by the direct search.
        self.assertFalse(proof['dynamic_constructed_keys_excluded'])
        self.assertIn('not other packages or dynamic constructed keys', proof['scope'])
        for key in ['HuarenRecover_1', 'HuarenRecover_2', 'GetSP', 'GetItem2']:
            self.assertNotIn(key, self.bykey)
        for proposal in self.d['name_proposals']:
            self.assertEqual(proposal['status'], 'candidate')
            self.assertFalse(proposal['official_name_verified'])


if __name__ == '__main__':
    unittest.main()
