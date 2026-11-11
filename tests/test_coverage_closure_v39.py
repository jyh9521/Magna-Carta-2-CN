"""Check the dated decision ledger without original game resources."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


def read(relative):
    return json.loads((ROOT/relative).read_bytes())


class CoverageClosureTests(unittest.TestCase):
    def test_new_screen_only_adds_the_bound_core_read_view(self):
        old=read('locales/zh-Hans/omission-screen-v38.json')
        new=read('locales/zh-Hans/omission-screen-v39.json')
        decoders=new.pop('document_decoders');self.assertEqual(new,old)
        self.assertEqual(len(decoders),1);self.assertEqual(decoders[0]['discs'],[1,2])
        self.assertEqual(decoders[0]['decoder'],'unsigned-byte-to-u16')
        ledger=read('locales/zh-Hans/coverage-closure-v39.json')
        self.assertEqual(decoders[0]['payload_sha256'],ledger['core_document']['payload_sha256'])
        self.assertEqual(ledger['core_document']['profile_sha256'],hashlib.sha256(
            (ROOT/'references/narrow-fstring-profile.json').read_bytes()).hexdigest())

    def test_each_prior_byte_candidate_and_visual_has_a_distinct_disposition(self):
        r=read('locales/zh-Hans/coverage-closure-v39.json')
        for key,count,id_key in [('vm_candidates',198,'id'),('untyped_candidates',445,'candidate_id'),
                                 ('visual_candidates',23,'id'),('ui_defaults',31,'id')]:
            rows=r[key];self.assertEqual(len(rows),count)
            self.assertEqual(len({x[id_key]for x in rows}),count)
        self.assertEqual({v['disposition']for v in r['vm_candidates']},
                         {'not_bytecode_metadata','not_unicode_opcode'})
        self.assertEqual(len(r['metadata_gaps']),15)
        self.assertEqual(len({v['source_id']for v in r['vm_candidates']}),198)
        self.assertEqual(len({v['physical_source_id']for v in r['vm_candidates']}),193)
        self.assertEqual(len(r['native_exports']),39)
        meshes=[v for v in r['native_exports']if v['class_path'].endswith('StaticMesh')]
        shaders=[v for v in r['native_exports']if v['class_path'].endswith('ShaderCache')]
        self.assertEqual(len(meshes),38);self.assertTrue(all(v['native_string_fields']==0 for v in meshes))
        self.assertEqual(len(shaders),1);self.assertIsNone(shaders[0]['native_string_fields'])
        self.assertFalse(shaders[0]['native_semantic_coverage_complete'])
        self.assertEqual(shaders[0]['semantic_unresolved_bytes'],1792)
        self.assertEqual(len(r['ui_functions']),50)
        self.assertTrue(all(v['full_script_consumed']for v in r['ui_functions']))

    def test_english_defaults_and_offline_proofs_do_not_claim_runtime_or_whole_game_acceptance(self):
        r=read('locales/zh-Hans/coverage-closure-v39.json')
        self.assertFalse(r['complete_game_language_coverage_claimed']);self.assertFalse(r['game_started'])
        self.assertEqual(r['game_resource_bytes_changed'],0)
        for row in r['ui_defaults']:
            self.assertTrue(row['text'].isascii());self.assertFalse(row['runtime_visibility_verified'])
            self.assertFalse(row['always_overwritten_verified']);self.assertEqual(row['hangul_codepoints'],0)
        self.assertIn('user-ended-this-round',r['chapter_card_followup'])


if __name__=='__main__':unittest.main()
