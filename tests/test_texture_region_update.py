import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from tools.build_texture_region_update import transfer,build
from tools.runtime_envelope import require_raw_envelope
from tools.texture_layout import rect_units
from tools.replace_texture_regions import replace_tiles
from test_runtime_package import fixture,texture,sha,stored_decoder


class NativeRegionUpdateTests(unittest.TestCase):
    def setUp(self):
        self.source=fixture();self.source+=bytes(-len(self.source)%32768)
        _,_,export,self.tx=texture(self.source);self.obj=export['path']

    def test_transfers_only_selected_native_blocks(self):
        rectangles=[[0,0,4,4]];offset=rect_units(self.tx['layout'],rectangles[0])[0]
        other=rect_units(self.tx['layout'],[4,0,4,4])[0]
        tiles=bytearray(self.tx['tiles']);tiles[offset]^=1;tiles[other]^=2
        donor,_=replace_tiles(self.source,sha(self.source),self.obj,bytes(tiles),[[0,0,8,4]],stored_decoder)
        output,proof,(_,after)=transfer(self.source,sha(self.source),self.obj,donor,self.obj,rectangles,stored_decoder)
        expected=bytearray(self.tx['tiles']);expected[offset]^=1
        self.assertEqual(after['tiles'],bytes(expected));self.assertEqual(proof['changed_blocks'],1)
        self.assertTrue(proof['unselected_exports_preserved']);require_raw_envelope(output)
        self.assertEqual(texture(self.source)[3]['tiles'],self.tx['tiles'])

    def test_rejects_wrong_source_hash_and_unchanged_selection(self):
        with self.assertRaisesRegex(ValueError,'SHA256'):
            transfer(self.source,'0'*64,self.obj,self.source,self.obj,[[0,0,4,4]],stored_decoder)
        with self.assertRaisesRegex(ValueError,'donor changes'):
            transfer(self.source,sha(self.source),self.obj,self.source,self.obj,[[0,0,4,4]],stored_decoder)

    def test_rejects_unaligned_and_overlapping_windows(self):
        for rectangles in ([[1,0,4,4]],[[0,0,4,4],[0,0,4,4]],[]):
            with self.subTest(rectangles=rectangles),self.assertRaises(ValueError):
                transfer(self.source,sha(self.source),self.obj,self.source,self.obj,rectangles,stored_decoder)

    def test_build_publishes_only_new_reopened_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);current=root/'input';current.mkdir();name='MC2Game/Label.xxx'
            source=current/name;source.parent.mkdir();source.write_bytes(self.source)
            plan=root/'plan.json';plan.write_text(json.dumps({'sources':[{'path':name,'discs':[1,2]}]}))
            offset=rect_units(self.tx['layout'],[0,0,4,4])[0]
            tiles=bytearray(self.tx['tiles']);tiles[offset]^=1
            donor,_=replace_tiles(self.source,sha(self.source),self.obj,bytes(tiles),[[0,0,4,4]],stored_decoder)
            profile={'schema_version':1,'kind':'native-texture-region-update','game_rendering_verified':False,
                'disc':1,'overlay_plan':{'path':'plan.json','sha256':sha(plan.read_bytes())},
                'resources':[{'path':name,'input_sha256':sha(self.source),'discs':[1,2],
                              'object':self.obj,'donor_object':self.obj,'rectangles':[[0,0,4,4]]}]}
            with patch('tools.build_texture_region_update.prepare',return_value=({'candidate/'+name:donor},{},[])):
                output=root/'output';manifest=build(profile,root,current,output,stored_decoder)
                for member,expected in manifest['member_sha256'].items():
                    self.assertEqual(sha((output/member).read_bytes()),expected)
                self.assertEqual(source.read_bytes(),self.source)
                self.assertEqual((output/'baseline'/name).read_bytes(),self.source)
                require_raw_envelope((output/'candidate'/name).read_bytes())
                self.assertEqual(manifest['resources'][0]['discs'],[1,2])
                with self.assertRaisesRegex(ValueError,'output must be new'):
                    build(profile,root,current,output,stored_decoder)
                for bad in (current/'output',root.parent/'escaped'):
                    with self.subTest(bad=bad),self.assertRaisesRegex(ValueError,'output must be new'):
                        build(profile,root,current,bad,stored_decoder)

    def test_build_rejects_plan_hash_and_disc_mismatch_without_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);current=root/'input';current.mkdir();out=root/'output'
            plan=root/'plan.json';plan.write_text(json.dumps({'sources':[{'path':'a.xxx','discs':[1]}]}))
            profile={'schema_version':1,'kind':'native-texture-region-update','game_rendering_verified':False,
                'disc':1,'overlay_plan':{'path':'plan.json','sha256':'0'*64},
                'resources':[{'path':'a.xxx','discs':[1,2]}]}
            with self.assertRaisesRegex(ValueError,'plan SHA256'):
                build(profile,root,current,out,stored_decoder)
            profile['overlay_plan']['sha256']=sha(plan.read_bytes())
            with patch('tools.build_texture_region_update.prepare',return_value=({}, {}, [])):
                with self.assertRaisesRegex(ValueError,'disc provenance'):
                    build(profile,root,current,out,stored_decoder)
            self.assertFalse(out.exists())


class VoiceDramaDataTests(unittest.TestCase):
    root=Path(__file__).resolve().parents[1]

    def test_heading_uses_exact_existing_synopsis_style(self):
        p=json.loads((self.root/'locales/zh-Hans/texture-overlays/voice-drama-headings-v10.json').read_bytes())
        upper,lower=p['labels']
        self.assertEqual(upper['font'],lower['font']);self.assertEqual(upper['font_size'],lower['font_size'])
        a,b=copy.deepcopy(upper['appearance']),copy.deepcopy(lower['appearance'])
        a['ink_box'][1]=b['ink_box'][1]
        self.assertEqual(a,b);self.assertEqual(a['ink_box'][3],20)
        self.assertEqual(len(p['sources']),2)

    def test_synopsis_delta_is_exactly_five_punctuation_insertions(self):
        before=json.loads((self.root/'locales/zh-Hans/batch-097.json').read_bytes())
        before={e['id']:e['translation'] for e in before['entries']}
        after=json.loads((self.root/'locales/zh-Hans/voice-drama-punctuation-v10.json').read_bytes())
        inserted=[]
        for entry in after['entries']:
            source=before[entry['id']];target=entry['translation'];i=j=0
            while i<len(source) and j<len(target):
                if source[i]==target[j]:i+=1;j+=1
                else:inserted.append(target[j]);j+=1
            self.assertEqual(i,len(source));inserted.extend(target[j:])
            self.assertEqual(source.count('\\n'),target.count('\\n'))
        self.assertEqual(inserted,['。','，','。','。','。']);self.assertEqual(len(after['entries']),3)


if __name__=='__main__':unittest.main()
