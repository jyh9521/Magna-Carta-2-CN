import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.audit_terminal_punctuation import corrected, needs_stop
from tools.audit_skill_number_spacing import pair_gap
from tools.build_texture_alias_update import build
from tools.replace_texture_regions import replace_tiles
from tools.texture_layout import rect_units
from test_runtime_package import fixture, texture, sha, stored_decoder

ROOT = Path(__file__).resolve().parents[1]


class TerminalPunctuationTests(unittest.TestCase):
    def setUp(self):
        self.rules = json.loads((ROOT/'locales/zh-Hans/terminal-punctuation-v24.json').read_bytes())['rules']

    def test_wrapped_sentence_is_not_two_independent_fragments(self):
        a = '为了让村民能安全地工作，\\n请消灭海边的3只克洛普斯'
        self.assertEqual(corrected(a, 'quest_description', self.rules), a+'。')
        self.assertEqual(corrected(a+'。', 'quest_description', self.rules), a+'。')

    def test_plain_clause_story_name_and_fragment_are_preserved(self):
        for text, kind in [('消灭3只克洛普斯', 'quest_description'),
                           ('别走，我还没说完', 'dialogue'), ('所以，请去', 'fragment'),
                           ('忍法：隐影', 'skill_name'), ('配方：力量戒指', 'item_name')]:
            self.assertEqual(corrected(text, kind, self.rules), text)

    def test_token_order_and_numeric_stats_are_untouched(self):
        a = '使用后，体力恢复\\n攻击+24 防御+5'
        self.assertEqual(corrected(a, 'item_description', self.rules), '使用后，体力恢复。\\n攻击+24 防御+5')
        a = '用于制作「戒指」的配方\\n防御ＬＶ3（3）+防御ＬＶ2（2）'
        self.assertEqual(corrected(a, 'item_description', self.rules), a.replace('配方', '配方。'))
        a = '任务%s：完成{0}'
        self.assertEqual(corrected(a, 'quest_progress', self.rules), a+'。')

    def test_decimal_and_annotation_are_not_sentence_punctuation(self):
        for a in ['恢复1.5倍体力', '击败北部军（1/15）', '你了解斯特拉斯吗？ (2)']:
            self.assertFalse(needs_stop(a, self.rules))

    def test_independent_choices_do_not_leak_punctuation_across_lines(self):
        a = '<Styles:MC2_StyleFont_0>X<Styles:/> 好累，我要休息\\n<Styles:MC2_StyleFont_0>Y<Styles:/> 我还有事要做'
        self.assertEqual(corrected(a, 'menu_option', self.rules), a.replace('休息\\n', '休息。\\n'))

    def test_existing_stops_quotes_and_tone_are_preserved(self):
        for a in ['等一等，这是“真的！”', '大家好，准备好了？', '大家好，出发吧～']:
            self.assertFalse(needs_stop(a, self.rules))


class SkillNumberInkTests(unittest.TestCase):
    def test_shift_name_without_moving_numeric_ink(self):
        name = dict(advance=101, box=[2, 1, 98, 21])
        one = dict(advance=10, box=[3, 2, 8, 16])
        ten = dict(advance=23, box=[3, 2, 21, 16])
        self.assertEqual(pair_gap(name, one, 202, 229), 23)
        self.assertEqual(pair_gap(name, one, 210, 229), 15)
        self.assertEqual(pair_gap(name, ten, 210, 229), 2)
        self.assertEqual(229-one['advance']+one['box'][2], 227)
        self.assertEqual(229-ten['advance']+ten['box'][2], 227)

    def test_only_five_parent_x_fields_change(self):
        p = json.loads((ROOT/'locales/zh-Hans/skill-number-fields-v23.json').read_bytes())
        self.assertEqual(len(p['objects']), 5)
        for o in p['objects']:
            self.assertNotIn('KanNum', o['object_path'])
            self.assertEqual([(f['before'], f['after']) for f in o['fields']], [(200.0,208.0)])


class TextureAliasUpdateTests(unittest.TestCase):
    def test_reviewed_name_changes_cover_every_explicit_physical_alias(self):
        base=ROOT/'locales/zh-Hans'
        d=json.loads((base/'candidate-decisions/name-consistency-20261103.json').read_bytes())
        p=json.loads((base/'texture-overlays/name-consistency-v22.json').read_bytes())
        aliases=json.loads((base/'texture-overlays/name-alias-update-v22.json').read_bytes())
        expected={r['id']:r['after']for r in d['decisions']}
        self.assertEqual(len(expected),45)
        self.assertEqual({r['id']:r['text']for r in p['labels']},expected)
        self.assertEqual(len(aliases['resources']),86)
        self.assertEqual(sha((ROOT/aliases['overlay_plan']['path']).read_bytes()),aliases['overlay_plan']['sha256'])
        self.assertNotIn(b'\r\n',(base/'texture-overlays/name-consistency-v22.json').read_bytes())
        self.assertEqual(sum(len(r['textures'])for r in aliases['resources']),136)
        self.assertEqual(len(d['candidate_review']),136)
        text=json.loads((base/'name-text-consistency-v22.json').read_bytes())
        self.assertEqual(len(text['entries']),9)
        self.assertFalse(any('编队潜入部队' in r['translation']for r in text['entries']))

    def prepare_fixture(self, root):
        raw = fixture(); raw += bytes(-len(raw)%32768)
        _,_,e,tx = texture(raw); rect = [0,0,4,4]
        tiles = bytearray(tx['tiles']);tiles[rect_units(tx['layout'],rect)[0]] ^= 1
        donor,_ = replace_tiles(raw,sha(raw),e['path'],bytes(tiles),[rect],stored_decoder)
        source=root/'input';source.mkdir();(source/'a.xxx').write_bytes(raw)
        plan=root/'plan.json';plan.write_text(json.dumps(dict(sources=[dict(path='donor.xxx',discs=[1,2])])))
        p=dict(schema_version=1,kind='texture-alias-update-v1',overlay_plan=dict(path='plan.json',sha256=sha(plan.read_bytes())),resources=[dict(path='a.xxx',sha256=sha(raw),discs=[2],textures=[dict(object=e['path'],tiled_sha256=sha(tx['tiles']),donor_resource='donor.xxx',donor_object=e['path'],rectangles=[rect])])])
        return raw,donor,source,p

    def test_real_native_alias_transfer_and_disc_specific_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw,donor,source,p=self.prepare_fixture(root)
            with patch('tools.build_texture_alias_update.prepare',return_value=({'candidate/donor.xxx':donor},{},[])):
                out=root/'out';m=build(p,root,source,out,stored_decoder)
                self.assertTrue(m['proofs'][0]['unselected_exports_preserved'])
                self.assertEqual((source/'a.xxx').read_bytes(),raw)
                self.assertNotEqual((out/'candidate/a.xxx').read_bytes(),raw)
                self.assertFalse(json.loads((out/'replacements-disc1.json').read_bytes())['resources'])
                self.assertEqual(len(json.loads((out/'replacements-disc2.json').read_bytes())['resources']),1)
                with self.assertRaisesRegex(ValueError,'new disjoint'):
                    build(p,root,source,out,stored_decoder)

    def test_hash_and_duplicate_guards_publish_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw,donor,source,p=self.prepare_fixture(root)
            bad=copy.deepcopy(p);bad['resources'][0]['sha256']='0'*64
            with self.assertRaisesRegex(ValueError,'source SHA256'):
                build(bad,root,source,root/'bad',stored_decoder)
            self.assertFalse((root/'bad').exists())
            bad=copy.deepcopy(p);bad['resources']*=2
            with self.assertRaisesRegex(ValueError,'duplicate'):
                build(bad,root,source,root/'bad',stored_decoder)

    def test_expanded_texture_count_remains_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw,donor,source,p=self.prepare_fixture(root)
            texture=p['resources'][0]['textures'][0]
            p['resources'][0]['textures']=[dict(texture,object=f'name_{i}')for i in range(257)]
            with patch('tools.build_texture_alias_update.prepare',return_value=({'candidate/donor.xxx':donor},{},[])):
                with self.assertRaisesRegex(ValueError,'excessive'):
                    build(p,root,source,root/'bad',stored_decoder)
            self.assertFalse((root/'bad').exists())


if __name__ == '__main__':
    unittest.main()
