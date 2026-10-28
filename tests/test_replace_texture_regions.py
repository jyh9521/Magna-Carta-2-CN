import unittest
from tools import texture_overlay as overlay
from tools.replace_texture_regions import replace, selected
from tools.reface_font import sha
from test_texture_layout import profile_fixture
from test_supplement_font import stored_decoder


class TextureRegionTransferTests(unittest.TestCase):
    def pair(self,compressed=False):
        source,edit,layers=profile_fixture(compressed=compressed)
        donor,_=overlay.patch_package(source,sha(source),[edit],layers,stored_decoder)
        return source,donor,edit['object']

    def test_raw_and_compressed_storage_roundtrip(self):
        for compressed in (False,True):
            before,donor,obj=self.pair(compressed)
            after,proof=replace(before,sha(before),obj,donor,sha(donor),obj,[[8,4,8,8]],stored_decoder)
            self.assertEqual(selected(after,obj,stored_decoder)[3]['tiles'],
                             selected(donor,obj,stored_decoder)[3]['tiles'])
            self.assertTrue(proof['outside_blocks_preserved'])
            self.assertTrue(proof['unselected_exports_preserved'])

    def test_identity_and_outside_region_guards(self):
        before,donor,obj=self.pair()
        with self.assertRaisesRegex(ValueError,'SHA256'):
            replace(before,'0'*64,obj,donor,sha(donor),obj,[[8,4,8,8]],stored_decoder)
        with self.assertRaisesRegex(ValueError,'outside'):
            replace(before,sha(before),obj,donor,sha(donor),obj,[[0,0,4,4]],stored_decoder)


if __name__=='__main__':unittest.main()
