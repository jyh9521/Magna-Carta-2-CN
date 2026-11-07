"""Source-free completeness and terminology contracts for transition movies."""
import json
from pathlib import Path
import unittest


ROOT=Path(__file__).resolve().parents[1]


class WorldMapCaptionPlanTests(unittest.TestCase):
    def setUp(self):
        # Historical extraction/timing contract, explicitly not a production plan.
        self.plan=json.loads((ROOT/'references/rejected-title-prototypes/worldmap-captions-v29.json').read_bytes())

    def test_all_eleven_movies_and_sixteen_disc_memberships_are_explicit(self):
        entries=self.plan['entries']
        self.assertEqual(self.plan['kind'],'bink-audio-caption-plan')
        self.assertEqual(len(entries),11)
        self.assertEqual(len({e['source']['member'] for e in entries}),11)
        self.assertEqual(sum(len(e['source']['discs']) for e in entries),16)
        self.assertEqual(sum(1 in e['source']['discs'] for e in entries),6)
        self.assertEqual(sum(2 in e['source']['discs'] for e in entries),10)
        self.assertEqual([e['id'][14:16] for e in entries],[f'{i:02}' for i in range(1,12)])

    def test_original_audio_and_timing_are_never_silently_dropped(self):
        for entry in self.plan['entries']:
            h=entry['expected_header']
            self.assertEqual(h,dict(width=1280,height=720,frames=360,numerator=10000000,
                                   denominator=333333,magic='BIKi',audio_tracks=6))

    def test_terms_follow_existing_project_labels_without_adding_qualifiers(self):
        expected=['风息岛','阿巴泽特','老狐峡谷','柯塔马雷','海底洞窟','杜南丘陵','杜南平原',
                  '鲁哈尔特','贝尔福特','哨兵研究所','拉·斯特拉达']
        self.assertEqual([e['captions'][0]['text'] for e in self.plan['entries']],expected)
        terms={t['id']:t for t in json.loads((ROOT/'locales/zh-Hans/terms.json').read_bytes())['terms']}
        for entry in self.plan['entries'][1:]:
            self.assertEqual(entry['captions'][0]['text'],terms[entry['term_ids'][0]]['target'])
            self.assertEqual(entry['source_ids'],[terms[entry['term_ids'][0]]['source_string_id']])

    def test_every_erase_is_small_temporal_source_locked_and_excludes_native_icon(self):
        for entry in self.plan['entries']:
            caption=entry['captions'][0];erase=caption['erase'];spec=erase['temporal_static']
            self.assertEqual(erase['rect'],[248,336,300,56])
            self.assertEqual(len(spec['mask_sha256']),64)
            self.assertGreater(spec['pixels'],100)
            self.assertLess(spec['pixels'],9000)
            self.assertEqual(caption['style']['align'],'left')
            self.assertFalse(any('\uac00'<=c<='\ud7a3' for c in caption['text']))
        self.assertFalse(self.plan['game_rendering_verified'])
        self.assertFalse(self.plan['source_font_identity_recovered'])


if __name__=='__main__':unittest.main()
