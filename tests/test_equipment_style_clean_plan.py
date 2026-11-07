"""Source-free contracts for the accepted equipment reconstruction candidate."""
import hashlib
import json
from pathlib import Path
import unittest

from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
PLAN='locales/zh-Hans/texture-overlays/equipment-style-clean-v31.json'
RECIPE='locales/zh-Hans/texture-overlays/equipment-style-clean-repairs-v31.json'


class EquipmentStyleCleanPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=json.loads((ROOT/PLAN).read_bytes())
        cls.recipe=json.loads((ROOT/RECIPE).read_bytes())

    def test_complete_family_uses_existing_names_and_weapon_types(self):
        expected={
            'Style_Argo_Main':('阿尔戈','锤'),'Style_Argo_Sub':('阿尔戈','斧'),
            'Style_Crocell_Main':('克罗塞尔','火球'),'Style_Crocell_Sub':('克罗塞尔','拳套'),
            'Style_Juto_Main':('朱特','单手剑'),'Style_Juto_Sub':('朱特','双手剑'),
            'Style_Juto_W_Main':('朱特','单手剑'),'Style_Juto_W_Sub':('朱特','双手剑'),
            'Style_Ru_Main':('露','太刀'),'Style_Ru_Sub':('露','手里剑'),
            'Style_Serestin_Main':('塞蕾丝汀','香器'),'Style_Serestin_Sub':('塞蕾丝汀','弓'),
            'Style_Zephie_Main':('洁菲','法杖'),'Style_Zephie_Sub':('洁菲','扇')}
        self.assertFalse(self.plan['game_rendering_verified'])
        self.assertEqual(len(self.plan['sources']),1)
        source=self.plan['sources'][0];self.assertEqual(source['discs'],[1,2])
        labels={l['id']:l for l in self.plan['labels']}
        self.assertEqual(len(labels),14)
        self.assertEqual({t['object'].split('.')[0] for t in source['textures']},set(expected))
        terms={t['id']:t for t in json.loads((ROOT/'locales/zh-Hans/terms.json').read_bytes())['terms']}
        for t in source['textures']:
            name=t['object'].split('.')[0];label=labels[t['label']];cn,weapon=expected[name]
            self.assertEqual([p['text']for p in label['parts']],[cn,'流派',weapon])
            self.assertEqual(label['text'],cn+'流派'+weapon)
            self.assertEqual([terms[i]['target']for i in label['term_ids']],[cn,weapon])
            self.assertEqual([terms[i]['source_string_id']for i in label['term_ids']],label['source_ids'])
            self.assertEqual(hashlib.sha256(label['source_text'].encode()).hexdigest(),label['source_text_sha256'])
        self.assertNotIn('Style_CountryJuto',expected)

    def test_saved_repairs_are_sparse_guarded_inputs_not_whole_portraits(self):
        assets=set()
        for label in self.plan['labels']:
            restoration=label['restoration'];size=tuple(label['rect'][2:]);images={}
            for key,mode in [('mask','L'),('patch','RGBA')]:
                ref=restoration[key];raw=(ROOT/ref['path']).read_bytes();assets.add(ref['path'])
                self.assertEqual(hashlib.sha256(raw).hexdigest(),ref['sha256'])
                with Image.open(ROOT/ref['path'])as im:
                    self.assertEqual(im.mode,mode);self.assertEqual(im.size,size);images[key]=im.tobytes()
            mask=images['mask'];patch=images['patch']
            self.assertLessEqual(set(mask),{0,255})
            self.assertGreater(mask.count(255),0)
            self.assertLess(mask.count(255),len(mask)*.85)
            self.assertTrue(all(patch[i*4:i*4+4]==bytes(4)for i,v in enumerate(mask)if not v))
        self.assertEqual(len(assets),28)
        self.assertEqual({p.relative_to(ROOT).as_posix()for p in (ROOT/'locales/zh-Hans/texture-overlays/restorations/equipment-style-clean-v31').glob('*.png')},assets)

    def test_every_native_exterior_is_explicitly_protected(self):
        labels={l['id']:l for l in self.plan['labels']}
        for texture in self.plan['sources'][0]['textures']:
            x,y,w,h=labels[texture['label']]['rect'];expected=[[0,0,512,y],[0,y+h,512,512-y-h],[0,y,x,h],[x+w,y,512-x-w,h]]
            self.assertEqual([p['rect']for p in texture['protected_regions']],[r for r in expected if r[2]>0 and r[3]>0])
            self.assertTrue(texture['preserve_unchanged_blocks'])
            self.assertEqual(texture['dimensions'],[512,512])
            self.assertTrue(all(v%4==0 for v in (x,y,w,h)))

    def test_production_build_uses_small_repairs_not_complete_ai_plates(self):
        self.assertEqual(self.recipe['method'],'premultiplied-harmonic-boundary-v1')
        self.assertEqual(self.recipe['hidden_artwork'],'reconstruction-not-original')
        cases={c['id']:c for c in self.recipe['cases']}
        self.assertEqual(len(cases),14)
        for label in self.plan['labels']:
            case=cases[label['id']]
            self.assertEqual(case['mask'],label['restoration']['mask'])
            self.assertEqual(case['patch'],label['restoration']['patch'])
            self.assertEqual(case['rect'],label['rect'])
            self.assertEqual(case['source_rgba_sha256'],label['restoration']['source_rgba_sha256'])
            self.assertEqual(case['alpha_mode'],'interpolate-source-alpha-v1')
            self.assertEqual(case['iterations'],1000)
            self.assertTrue(case['plate']['path'].startswith('build/'))
            self.assertNotIn('plate',label)


if __name__=='__main__':unittest.main()
