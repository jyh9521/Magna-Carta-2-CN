"""Public translation/plan contracts plus synthetic larger-font safeguards."""
import json
from pathlib import Path
import unittest

from tools import supplement_font as s
from tools.font_binding_plan import digest
from tools.translation_style import style_errors
from tools.series_terms import validate_terms
from tools.prepare_text_sample import allocate
from test_supplement_font import package_fixture, plan, stored_decoder

ROOT = Path(__file__).resolve().parents[1]
def load(name):
    return json.loads((ROOT/name).read_bytes())


class OpeningBatchTests(unittest.TestCase):
    def test_public_batch_preserves_previous_translations_and_no_source_dump(self):
        batch=load('locales/zh-Hans/opening-batch.json')
        entries=batch['entries'];index={e['id']:e for e in entries}
        self.assertEqual(len(entries),231)
        self.assertEqual(len(index),len(entries))
        for old in load('locales/zh-Hans/batch-001.json')['entries']:
            self.assertEqual(index[old['id']],old)
        for e in entries:
            self.assertEqual(set(e),{'id','source_sha256','translation'})
            self.assertNotIn('\n',e['translation'])
            self.assertNotIn('\0',e['translation'])
            self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$')

    def test_description_style_and_classification_are_complete(self):
        index={e['id']:e for e in load('locales/zh-Hans/opening-batch.json')['entries']}
        review=load('locales/zh-Hans/opening-batch.review.json')
        self.assertEqual(set(index),{e['id'] for e in review['entries']})
        for r in review['entries']:
            # Historical batch contract predates the broader non-story rule.
            rules=dict(load('locales/zh-Hans/style-rules.json'),non_story_default=False)
            self.assertFalse(style_errors(dict(index[r['id']],text_kind=r['text_kind']),rules))

    def test_larger_glyph_count_requires_explicit_bounded_opt_in(self):
        p=plan();p['glyphs']=[dict(p['glyphs'][0],character=chr(0x4e00+i)) for i in range(129)]
        with self.assertRaisesRegex(ValueError,'1..128'):s.validate_plan(p)
        p['glyph_limit']=1024
        self.assertEqual(len(s.validate_plan(p)),129)
        for limit in [True,0,2049,'1024']:
            p['glyph_limit']=limit
            with self.assertRaisesRegex(ValueError,'glyph_limit'):s.validate_plan(p)

    def test_metric_growth_requires_exact_original_and_preserves_old_records(self):
        raw=package_fixture(font_height=24)
        p=plan();p['glyphs'][0]['height']=28;p['metric_height']=25
        args=(raw,digest(raw),'General',p,{0x4e2d:bytes([255])*24*28},stored_decoder)
        with self.assertRaisesRegex(ValueError,'increases original'):s.supplement_package(*args,raw_atlas=True)
        p['metric_height_growth']=dict(original=24,candidate=25)
        # Last rows must remain transparent, not silently cropped by a metric.
        alpha=bytes([255])*24*25+bytes(24*3)
        out,report=s.supplement_package(raw,digest(raw),'General',p,{0x4e2d:alpha},stored_decoder,raw_atlas=True)
        self.assertNotEqual(raw,out)
        self.assertTrue(report['original_glyphs_and_remap_preserved'])
        self.assertEqual(report['original_max_glyph_height'],24)
        self.assertEqual(report['supplemented_max_glyph_height'],25)
        p['metric_height_growth']['original']=23
        with self.assertRaisesRegex(ValueError,'maximum mismatch'):
            s.supplement_package(raw,digest(raw),'General',p,{0x4e2d:alpha},stored_decoder,raw_atlas=True)

    def test_malformed_growth_and_clipped_pixels_fail(self):
        for growth in [True,dict(original=24,candidate=24),dict(original=24,candidate=26),
                       dict(original=True,candidate=25)]:
            p=plan();p['glyphs'][0]['height']=28;p['metric_height']=25;p['metric_height_growth']=growth
            with self.assertRaisesRegex(ValueError,'metric height growth'):s.validate_plan(p)
        p=plan();p['glyphs'][0]['height']=28;p['metric_height']=25;p['metric_height_growth']=dict(original=24,candidate=25)
        raw=package_fixture()
        with self.assertRaisesRegex(ValueError,'outside metric_height'):
            s.supplement_package(raw,digest(raw),'General',p,{0x4e2d:bytes([255])*24*28},stored_decoder,raw_atlas=True)

    def test_terms_have_provenance_and_remain_candidates(self):
        terms=load('locales/zh-Hans/terms.json')
        # This source-free unit contract checks declared identities and pinned
        # commits. The CLI --with-references separately verifies the actual
        # cached upstream bytes; a clean checkout must not require that cache.
        declared=[ref for t in terms['terms'] for ref in t['series_references']]
        pinned={r['id']:r['commit'] for r in load('references/series.lock.json')['references']}
        for ref in declared:
            self.assertEqual(ref['commit'],pinned[ref['reference']])
        self.assertFalse(validate_terms(terms,declared))
        self.assertGreaterEqual(len(terms['terms']),20)
        self.assertTrue(all(t['review_status']=='candidate' for t in terms['terms']))
        # Terms grow beyond the historical opening sample. Check the explicitly
        # selected current batches rather than requiring all future terms to
        # belong to that frozen sample.
        workflow=load('locales/zh-Hans/translation-workflow.json')
        index={e['id']:e['translation'] for batch in workflow['batches']
               for e in load(batch['plan']['path'])['entries']}
        for term in terms['terms']:
            self.assertIn(term['target'],index[term['source_string_id']])

    def test_block_allocator_matches_old_first_fit_order(self):
        import random
        rng=random.Random(42)
        for _ in range(20):
            font=dict(characters=[dict(StartU=rng.randrange(24),StartV=rng.randrange(24),
                       USize=rng.randrange(1,7),VSize=rng.randrange(1,7),TextureIndex=0) for i in range(6)])
            used=[s.block_rect((g['StartU'],g['StartV'],g['USize'],g['VSize'])) for g in font['characters']]
            expected=[]
            for char in 'ABC':
                for y in range(0,25,4):
                    found=False
                    for x in range(0,25,4):
                        rect=s.block_rect((x,y,8,8))
                        if not any(s.overlaps(rect,r) for r in used):
                            expected.append(dict(character=char,texture_index=0,x=x,y=y,width=8,height=8))
                            used.append(rect);found=True;break
                    if found:break
            self.assertEqual(allocate(font,dict(width=32,height=32),'ABC',dict(texture_index=0,width=8,height=8)),expected)

    def test_font_route_locks_text_and_all_three_families(self):
        route=load('locales/zh-Hans/opening-fonts/route.json')
        self.assertEqual(len(route['font_plans']),3)
        self.assertFalse(route['game_rendering_verified'])
        for ref in [route['text_plan'],*route['font_plans']]:
            self.assertEqual(digest((ROOT/ref['path']).read_bytes()),ref['sha256'])
        for i,ref in enumerate(route['font_plans']):
            fp=load(ref['path']);gp=fp['supplement']
            self.assertEqual(digest((ROOT/gp['path']).read_bytes()),gp['sha256'])
            glyphs=load(gp['path'])
            self.assertEqual(len(s.validate_plan(glyphs)),[650,650,648][i])
            self.assertEqual(glyphs['metric_height'],[25,18,29][i])
            self.assertEqual(glyphs['atlas_height'],[1024,1024,2048][i])


if __name__=='__main__':unittest.main()
