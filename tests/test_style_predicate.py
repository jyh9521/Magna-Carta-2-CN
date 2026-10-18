"""Self-authored PPC words and PE records, never execution of target code."""
import copy
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

import test_native_class_tables as fixtures
from tools.inspect_native_bindings import main
from tools.ppc_style_predicate import predicate_words
from tools.xex_image import digest


class PredicateFixture(fixtures.ClassFixture):
    def __init__(self):
        super().__init__(); v = self.base
        c = dict(profile='ppc-style-predicate-v1',start=v+0x1d00,reference_helper=v+0x1a00)
        self.plan['style_predicate'] = c
        self.words(c['start'],predicate_words(c['start'],c['reference_helper']))
        self.put(self.plan['class_tables']['classes'][0]['table_address']+0x124,c['start'])
        self.le(0x5018+124,48); self.le(0x5018+0xe0+8,48)
        self.put(v+0x628,c['start']); self.put(v+0x62c,0x40002403)
        self.refresh_predicate()

    def refresh_predicate(self):
        c = self.plan['style_predicate']; at = c['start']-self.base
        c['sha256'] = digest(self.image[at:at+144]); self.refresh_class()


class PredicateTests(unittest.TestCase):
    def test_exact_words_edges_and_distinct_getter_routes(self):
        f = PredicateFixture(); before = bytes(f.image); r = f.run()['style_predicate']; s = f.plan['style_predicate']['start']
        self.assertEqual(r['instruction_count'],36); self.assertEqual(r['declared_record']['end'],s+144)
        self.assertEqual(r['four_word_gate']['offsets'],[0x100,0xfc,0xf8,0xf4])
        self.assertEqual([(e['address']-s,e['taken']-s) for e in r['conditional_edges']],[(32,128),(40,128),(76,124),(104,124),(120,128)])
        self.assertEqual(r['helper_call']['returned_pointer_read_offsets'],[0,4])
        self.assertEqual(r['literal_return_assignments'][0]['value'],0); self.assertEqual(r['literal_return_assignments'][1]['value'],1)
        self.assertEqual(bytes(f.image),before)

    def test_independent_literal_encodings_not_just_generator_roundtrip(self):
        f = PredicateFixture(); s = f.plan['style_predicate']['start']; raw = f.image[s-f.base:s-f.base+144]
        self.assertEqual(struct.unpack_from('>I',raw,12)[0],0x81430104)
        self.assertEqual(struct.unpack_from('>II',raw,24),(0x312affff,0x7c695111))
        self.assertEqual(struct.unpack_from('>I',raw,32)[0],0x40820060)
        self.assertEqual(struct.unpack_from('>I',raw,84)[0],0x388b00e8)
        self.assertEqual(struct.unpack_from('>I',raw,124)[0],0x38600001)

    def test_preserves_unknowns_including_helper_and_field_names(self):
        r = PredicateFixture().run()['style_predicate']
        for name in ['serialized_field_names_verified','native_owner_pointer_identity_verified',
                     'callee_register_preservation_verified','runtime_dispatch_verified','active_font_verified','executed','image_modified',
                     'direct_entry_object_stores_present','helper_effects_verified']:
            self.assertIs(r[name],False)
        self.assertFalse(r['helper_call']['semantics_verified']); self.assertIsNone(r['helper_call']['declared_record'])
        self.assertTrue(r['static_class_slot_target_verified'])

    def test_every_byte_mutation_rejected_even_with_refreshed_hashes(self):
        for i in range(144):
            f = PredicateFixture(); f.image[0x1d00+i] ^= 1; f.refresh_predicate()
            with self.subTest(i=i), self.assertRaisesRegex(ValueError,'predicate structural'): f.run()

    def test_hash_and_slot_mutations_fail_separately(self):
        f = PredicateFixture(); f.plan['style_predicate']['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError,'window hash'): f.run()
        f = PredicateFixture(); f.put(f.plan['class_tables']['classes'][0]['table_address']+0x124,f.base+0x810); f.refresh_predicate()
        with self.assertRaisesRegex(ValueError,'every supplied class slot124'): f.run()

    def test_declared_extent_and_prologue_required_not_next_start(self):
        for count,packed in [(40,0x40002403),(48,0x40002303),(48,0x40002404)]:
            f = PredicateFixture(); f.le(0x5018+124,count); f.le(0x5018+0xe0+8,count); f.put(f.base+0x62c,packed); f.refresh_predicate()
            with self.subTest(count=count,packed=packed), self.assertRaisesRegex(ValueError,'predicate declared'): f.run()

    def test_profile_keys_address_types_ranges_and_helper_fail(self):
        for key,value in [('profile','other'),('start',True),('start',0x82001d01),('start',0x82002000),
                          ('reference_helper',True),('reference_helper',0x82001a01),('reference_helper',0x82002000),
                          ('reference_helper',0x82001d04),('extra',0)]:
            f = PredicateFixture(); f.plan['style_predicate'][key] = value
            with self.subTest(key=key,value=value), self.assertRaises(ValueError): f.run()
        for config in [None,True,{},[]]:
            f = PredicateFixture(); f.plan['style_predicate'] = config
            with self.subTest(config=config), self.assertRaises(ValueError): f.run()

    def test_explicit_class_prerequisite_and_old_opt_in_compatibility(self):
        f = PredicateFixture(); del f.plan['class_tables']
        with self.assertRaisesRegex(ValueError,'explicit class table'): f.run()
        f = fixtures.ClassFixture(); before = f.run(); self.assertNotIn('style_predicate',before)
        f = PredicateFixture(); del f.plan['style_predicate']; self.assertNotIn('style_predicate',f.run())

    def test_class_getter_association_guards(self):
        from tools.ppc_style_predicate import verify_style_predicate
        from tools.xex_image import VirtualImage
        f = PredicateFixture(); r = f.run()['class_tables']
        for key,value in [('selection_virtual_slot',0x120),('nonzero_result_base',{'addend':0xe4}),('zero_result_base',{'addend':0x170})]:
            bad = copy.deepcopy(r); bad['getter'][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError,'getter association'):
                verify_style_predicate(VirtualImage(bytes(f.image),f.base),f.plan['style_predicate'],bad,f.plan['code_ranges'])
        r['classes'] = []
        with self.assertRaisesRegex(ValueError,'every supplied class'):
            verify_style_predicate(VirtualImage(bytes(f.image),f.base),f.plan['style_predicate'],r,f.plan['code_ranges'])

    def test_cli_new_output_readback_and_unmodified_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); f = PredicateFixture(); image=root/'image.bin'; plan=root/'plan.json'; meta=root/'meta.json'; out=root/'report.json'
            image.write_bytes(f.image); plan.write_bytes(json.dumps(f.plan).encode()); meta.write_bytes(f.metadata_raw)
            args=[str(image),'--sha256',digest(f.image),'--plan',str(plan),'--plan-sha256',digest(plan.read_bytes()),'--native-report',str(meta),'--output',str(out)]
            before=[p.read_bytes() for p in [image,plan,meta]]
            self.assertEqual(main(args),0); self.assertEqual(json.loads(out.read_text())['style_predicate']['instruction_count'],36)
            self.assertEqual(main(args),2); self.assertEqual(before,[p.read_bytes() for p in [image,plan,meta]])

    def test_cli_late_source_mutation_removes_only_own_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); f=PredicateFixture(); image=root/'image.bin'; plan=root/'plan.json'; meta=root/'meta.json'; out=root/'report.json'
            image.write_bytes(f.image); plan.write_bytes(json.dumps(f.plan).encode()); meta.write_bytes(f.metadata_raw)
            args=[str(image),'--sha256',digest(f.image),'--plan',str(plan),'--plan-sha256',digest(plan.read_bytes()),'--native-report',str(meta),'--output',str(out)]
            read=Path.read_bytes
            def mutate(path):
                data=read(path)
                if path==out: image.write_bytes(b'changed synthetic fixture')
                return data
            with patch.object(Path,'read_bytes',mutate): self.assertEqual(main(args),2)
            self.assertFalse(out.exists())


if __name__=='__main__':
    unittest.main()
