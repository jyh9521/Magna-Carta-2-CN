import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from test_disc_inventory import fixture as disc_fixture
from test_font_binding_audit import alias_package
from test_supplement_font import package_fixture,stored_decoder
from tools.disc_inventory import Disc,sha256_file
from tools.inventory_font_namespaces import header_fonts,scan_disc,main
from tools.ue3_package import parse_tables


class FullNamespaceInventoryTests(unittest.TestCase):
    def fixture(self,root,payload=None):
        payload=alias_package() if payload is None else payload
        raw=disc_fixture(name=b'font.xxx',size=len(payload))
        size=(40*2048+len(payload)+2047)//2048*2048
        raw.extend(bytes(max(0,size-len(raw))));raw[40*2048:40*2048+len(payload)]=payload
        image=root/'source.iso';image.write_bytes(raw);d=Disc(image);entries=d.inventory()
        for e in entries:e['sha256']=d.resource_hash(e)
        manifest=dict(image_size=d.size,partition_base=d.base,root_sector=d.root_sector,root_size=d.root_size,
                      timestamp_raw=d.timestamp_raw,entries=entries,sha256=sha256_file(image))
        return image,manifest

    def test_header_inventory_hash_and_namespace(self):
        data=alias_package();r=header_fonts(data,hashlib.sha256(data).hexdigest(),'cooked')
        self.assertEqual(r['status'],'tables-validated');self.assertFalse(r['font_payloads_validated'])
        font,=r['font_candidates'];self.assertEqual(font['identity']['canonical_path'],'assets.general')
        self.assertLess(r['logical_header_size'],len(data));self.assertFalse(font['class_default'])
        with self.assertRaises(ValueError):header_fonts(data,'0'*64,'sample')

    def test_compressed_header_decoder_and_profile_guards(self):
        data=package_fixture(compressed=True)
        r=header_fonts(data,hashlib.sha256(data).hexdigest(),'font',stored_decoder)
        self.assertEqual(len(r['font_candidates']),1)
        with self.assertRaises(ValueError):header_fonts(data,hashlib.sha256(data).hexdigest(),'font')

    def test_native_payload_is_deliberately_not_validated(self):
        data=bytearray(alias_package());e=parse_tables(data)['exports'][0]
        data[e['serial_offset']:e['serial_offset']+e['serial_size']]=bytes(e['serial_size'])
        r=header_fonts(bytes(data),hashlib.sha256(data).hexdigest(),'sample')
        self.assertEqual(len(r['font_candidates']),1);self.assertFalse(r['font_payloads_validated'])

    def test_disc_inventory_and_cross_disc_cache_preserve_image(self):
        with tempfile.TemporaryDirectory() as d:
            image,m=self.fixture(Path(d));before=sha256_file(image);cache={}
            a=scan_disc(image,m,cache=cache);b=scan_disc(image,m,cache=cache)
            self.assertEqual(a['cache_hits'],0);self.assertEqual(b['cache_hits'],1)
            self.assertEqual(a['packages'],b['packages']);self.assertEqual(sha256_file(image),before)
            self.assertFalse(a['whole_image_hash_reverified']);self.assertTrue(a['packages'][0]['resource_hash_verified'])

    def test_descriptor_entry_hash_and_missing_hash_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            image,m=self.fixture(Path(d))
            for kind in ['descriptor','entry','hash','missing']:
                wrong=copy.deepcopy(m)
                if kind=='descriptor':wrong['root_sector']+=1
                elif kind=='entry':wrong['entries'][0]['size']-=1
                elif kind=='hash':wrong['entries'][0]['sha256']='0'*64
                else:del wrong['entries'][0]['sha256']
                with self.subTest(kind=kind),self.assertRaises(ValueError):scan_disc(image,wrong)
            with self.assertRaises(ValueError):scan_disc(image,[])
            wrong=copy.deepcopy(m);wrong['entries']=[1]
            with self.assertRaises(ValueError):scan_disc(image,wrong)

    def test_unsupported_header_recorded_not_claimed_absent(self):
        with tempfile.TemporaryDirectory() as d:
            image,m=self.fixture(Path(d),b'not a package')
            row,=scan_disc(image,m)['packages'];self.assertEqual(row['status'],'unparsed');self.assertTrue(row['reason'])

    def test_cli_reopens_and_prevents_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);image,m=self.fixture(root);inventory=root/'inventory.json';inventory.write_text(json.dumps(m),encoding='utf-8')
            output=root/'report.json';args=['--disc',str(image),str(inventory),'--canonical-path','assets.general','--output',str(output)]
            self.assertEqual(main(args),0);r=json.loads(output.read_text(encoding='utf-8'));self.assertEqual(len(r['matches']),1)
            self.assertEqual(main(args),2)


if __name__=='__main__':unittest.main()
