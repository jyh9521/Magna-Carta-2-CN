import json
from pathlib import Path
import struct
import unittest

from tools.set_ui_font_overrides import override_payload
from tools.patch_tagged_fields import select_field
from test_tagged_fields import Fixture

ROOT=Path(__file__).resolve().parents[1]


class RendererOverrideTests(unittest.TestCase):
    def fixture(self):
        f=Fixture();f.names += ['TextStyleCustomization','UITextStyleOverride','DrawFont',
                              'ObjectProperty','bOverrideDrawFont','TextAlignment']
        children=f.tag('TextAlignment','ByteProperty',b'\x02')+f.name('None')
        raw=bytes(8)+f.tag('TextStyleCustomization','StructProperty',children,structure='UITextStyleOverride')+f.name('None')+b'native-tail'
        return f,raw

    def test_only_nested_font_override_added_and_tail_preserved(self):
        f,raw=self.fixture();out=override_payload(raw,f.names,8,123)
        self.assertTrue(out.endswith(b'native-tail'))
        for key,expected in [('DrawFont',struct.pack('>i',123)),('bOverrideDrawFont',struct.pack('>I',1)),('TextAlignment',b'\x02')]:
            pp=[dict(name=n,array_index=0)for n in ('TextStyleCustomization',key)]
            self.assertEqual(select_field(out,f.names,8,pp)[2],expected)

    def test_duplicate_missing_and_wrong_prefix_are_rejected(self):
        f,raw=self.fixture();out=override_payload(raw,f.names,8,1)
        with self.assertRaisesRegex(ValueError,'existing'):
            override_payload(out,f.names,8,1)
        with self.assertRaisesRegex(ValueError,'prefix'):
            override_payload(raw,f.names,4,1)
        names=list(f.names);names[names.index('DrawFont')]='NotAFont'
        with self.assertRaisesRegex(ValueError,'missing'):
            override_payload(raw,names,8,1)


class FontSelectionTests(unittest.TestCase):
    def load(self,p):return json.loads((ROOT/'locales/zh-Hans'/p).read_bytes())

    def test_numeric_height_and_all_five_bindings_are_explicit(self):
        p=self.load('dynamic-font-numerals-v25.json')
        self.assertEqual(p['roles'][0]['optical_fit'],dict(height=20,top=1,advance=13,left=1,right=2))
        self.assertEqual(len(p['sources']),3)
        self.assertEqual(p['roles'][0]['codepoints'],list(range(48,58))+[65297])
        binding=self.load('skill-number-font-binding-v25.json')
        self.assertEqual(len(binding['renderers']),5)
        self.assertTrue(all('.KanNum' in r['object']for r in binding['renderers']))
        fields=self.load('skill-number-fields-v25.json')
        self.assertEqual(len(fields['objects']),10)
        self.assertTrue(all(f['property_path'][-1]['array_index']in(0,1)for r in fields['objects']for f in r['fields']))
        import hashlib
        lock=json.loads((ROOT/'references/numeric-font-v25.lock.json').read_bytes())
        self.assertEqual(hashlib.sha256((ROOT/'licenses/LXGWZhenKai-OFL.txt').read_bytes()).hexdigest(),lock['license_sha256'])

    def test_entire_small_monster_family_has_one_font_and_original_colour_ramps(self):
        base=self.load('texture-overlays/ui-labels-gameplay-v9.json')
        labels={l['id']:l for l in base['labels']}
        labels.update({l['id']:l for l in self.load('texture-overlays/name-consistency-v22.json')['labels']})
        changed=self.load('texture-overlays/monster-font-v26.json')
        before=dict(labels);labels.update({l['id']:l for l in changed['labels']})
        review=self.load('candidate-decisions/monster-font-20261103.json')
        self.assertEqual(len(review['ordinary_label_ids']),295)
        self.assertIn('img_ui_monster_name_jpn_165',review['ordinary_label_ids'])
        self.assertIn('img_ui_monster_name_jpn_184',review['ordinary_label_ids'])
        self.assertEqual(len(review['large_title_font_preserved_ids']),12)
        for identity in review['ordinary_label_ids']:
            l=labels[identity];self.assertEqual(l['font'],review['target_font'])
            self.assertEqual(l['appearance']['glow_radius'],0)
            if 'appearance' in before[identity]:
                self.assertEqual(l['appearance']['gradient'],before[identity]['appearance']['gradient'])
        for identity in review['large_title_font_preserved_ids']:
            self.assertEqual(labels[identity]['font'],before[identity]['font'])

    def test_native_reconciliation_covers_stale_aliases_without_changing_label_data(self):
        review=self.load('candidate-decisions/monster-font-20261103.json')
        ids=set(review['native_reconciliation_label_ids'])
        self.assertEqual(len(ids),23)
        self.assertFalse(ids&set(review['changed_label_ids']))
        plan=self.load('texture-overlays/monster-font-native-reconcile-v26.overlay.json')
        profile=self.load('texture-overlays/monster-font-native-reconcile-v26.json')
        self.assertEqual({r['id']for r in plan['labels']},ids)
        self.assertEqual(sum(len(r['textures'])for r in profile['resources']),96)
        self.assertEqual(len(profile['resources']),58)
        self.assertTrue(all(r['font']==review['target_font']for r in plan['labels']))
        import hashlib
        self.assertEqual(hashlib.sha256((ROOT/profile['overlay_plan']['path']).read_bytes()).hexdigest(),profile['overlay_plan']['sha256'])


if __name__=='__main__':unittest.main()
