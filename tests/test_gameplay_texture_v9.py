import json,unittest
from pathlib import Path
from PIL import Image
from tools.texture_region_repair import merge_delta,digest

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'locales/zh-Hans/texture-overlays'


class GameplayTextureV9Tests(unittest.TestCase):
    def test_master_replays_guarded_delta_without_implicit_replacements(self):
        before=json.loads((BASE/'ui-labels-gameplay-v7.json').read_bytes())
        delta=json.loads((BASE/'ui-labels-gameplay-v9.delta.json').read_bytes())
        after=json.loads((BASE/'ui-labels-gameplay-v9.json').read_bytes())
        self.assertEqual(merge_delta(before,delta),after)
        self.assertEqual(len(delta['labels']),37)
        self.assertEqual(len(delta['source_additions']),25)
        self.assertEqual(sum(c['source']['discs']==[1,2] for c in delta['source_additions']),22)
        self.assertEqual(sum(c['source']['discs']==[2] for c in delta['source_additions']),3)
        self.assertFalse(any('17_Albedo' in c['source']['path'] for c in delta['source_additions']))

    def test_quest_masks_and_protected_art_are_explicit_and_hashed(self):
        delta=json.loads((BASE/'ui-labels-gameplay-v9.delta.json').read_bytes())
        labels={c['label']['id']:c['label'] for c in delta['labels']}
        for source in delta['source_additions']:
            edit=source['textures'][0];label=labels[edit['label']]
            with self.subTest(resource=source['source']['path']):
                self.assertEqual(edit['protected_regions'][0]['rect'],[0,0,256,220])
                self.assertEqual(label['rect'],[32,220,192,36])
                for key in ['mask','patch']:
                    ref=label['restoration'][key];path=ROOT/ref['path']
                    self.assertEqual(digest(path.read_bytes()),ref['sha256'])
                    with Image.open(path) as im:
                        self.assertEqual(im.size,(192,36))
                        if key=='mask':self.assertTrue(set(im.tobytes())<=set([0,255]))
                        else:self.assertIsNone(im.getbbox())

    def test_shop_uv_contracts_cover_all_rows_and_six_subtitle_checks(self):
        contracts=json.loads((BASE/'gameplay-consumer-contracts-v9.json').read_bytes())
        self.assertEqual(len(contracts['cases']),15)
        self.assertEqual(sum(c['mode']=='alpha-after' for c in contracts['cases']),3)
        self.assertEqual(sum(c['name'].startswith('category ') for c in contracts['cases']),8)
