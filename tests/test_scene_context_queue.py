import copy
import json
import tempfile
import unittest
from pathlib import Path
from test_line_context_audit import setup
from tools.plan_scene_context import next_scenes, main


def rows():
    return [dict(id=str(i), embedded_path='scene.int', section=section)
            for i, section in enumerate(('S90', 'S100', 'S104', 'S110', 'S20'))]


class SceneContextQueueTests(unittest.TestCase):
    def test_original_order_not_lexical_or_numeric_guess(self):
        source = rows();result = next_scenes(source, 'scene.int', {'0','1','2','3','4'}, set(), 3)
        self.assertEqual([s['section'] for s in result['source_order_sections']], ['S90','S100','S104'])

    def test_skip_observed_and_take_whole_scene(self):
        source = rows();source.insert(3,dict(id='extra',embedded_path='scene.int',section='S104'))
        result = next_scenes(source, 'scene.int', {r['id'] for r in source}, {'0','1'}, 1)
        self.assertEqual((result['scene_entries'],result['planned_scene_entries']), (2,2))

    def test_unplanned_original_is_deferred_not_invented_or_repeated(self):
        source = rows();result = next_scenes(source,'scene.int',{'0','2','3','4'},{'0'},1)
        self.assertEqual(result['source_order_sections'][0]['section'],'S104')
        self.assertEqual(result['deferred_unplanned_sections'],[dict(section='S100',unplanned_original_ids=['1'])])
        self.assertEqual(result['translation_edits'],0);self.assertIs(result['human_finalized'],False)

    def test_partial_planned_scene_rejected_even_after_target(self):
        source=rows();source.append(dict(id='extra',embedded_path='scene.int',section='S20'))
        with self.assertRaisesRegex(ValueError,'partially observed'):
            next_scenes(source,'scene.int',{r['id'] for r in source},{'extra'},1)

    def test_stale_identity_and_duplicate_rejected(self):
        for planned,observed in [({'absent'},set()),({'0'},{'1'})]:
            with self.assertRaisesRegex(ValueError,'stale'):next_scenes(rows(),'scene.int',planned,observed)
        with self.assertRaisesRegex(ValueError,'duplicate'):next_scenes(rows()+rows()[:1],'scene.int',{'0'},set())

    def test_bounds_and_missing_document(self):
        for target in (True,0,301,'180'):
            with self.assertRaises(ValueError):next_scenes(rows(),'scene.int',{'0'},set(),target)
        with self.assertRaises(ValueError):next_scenes(rows(),'missing',{'0'},set())

    def test_no_input_mutation_and_finished_empty_queue(self):
        source=rows();before=copy.deepcopy(source);ids={r['id'] for r in source}
        result=next_scenes(source,'scene.int',ids,ids);self.assertEqual(result['scene_entries'],0)
        self.assertEqual(source,before);self.assertIs(result['runtime_layout_approved'],False)

    def test_mixed_scene_keeps_unknown_source_count(self):
        source=rows();source.append(dict(id='unknown',embedded_path='scene.int',section='S90'))
        result=next_scenes(source,'scene.int',{r['id'] for r in rows()},set(),1)
        self.assertEqual((result['scene_entries'],result['planned_scene_entries']),(2,1))
        self.assertEqual(result['source_order_sections'][0]['unplanned_original_ids'],['unknown'])

    def test_cli_locks_inputs_and_preserves_existing_output(self):
        data,plan,profile=setup()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'source';p=root/'plan';pr=root/'profile';out=root/'out'
            source.write_bytes(data);p.write_text(json.dumps(plan),encoding='utf8');pr.write_text(json.dumps(profile),encoding='utf8')
            args=['--source',str(source),'--plan',str(p),'--profile',str(pr),'--document','fixture.int','--output',str(out)]
            self.assertEqual(main(args),0);self.assertEqual(json.loads(out.read_bytes())['planned_scene_entries'],0)
            before=out.read_bytes();self.assertEqual(main(args),2);self.assertEqual(out.read_bytes(),before)
            out.unlink();profile['input_sha256']='0'*64;pr.write_text(json.dumps(profile),encoding='utf8')
            self.assertEqual(main(args),2);self.assertFalse(out.exists())

    def test_document_filter_does_not_steal_other_resource(self):
        source=rows()+[dict(id='other',embedded_path='other.int',section='S1')]
        result=next_scenes(source,'scene.int',{r['id'] for r in source},set(),300)
        self.assertEqual(result['planned_scene_entries'],5)
