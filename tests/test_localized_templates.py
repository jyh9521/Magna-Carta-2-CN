"""Self-authored image words and lookup strings; no game assets or execution."""
import copy,hashlib,json,struct,tempfile,unittest
from pathlib import Path
from tools.inspect_localized_templates import inspect_templates,main
H=lambda b:hashlib.sha256(b).hexdigest()
class LocalizedTemplateTests(unittest.TestCase):
 def fixture(self):
  b=bytearray(1024);base=0x82000000;ptr=base+256;site=base+32;target=base+128
  text='<Strings:Fixture.Attributes.Base>%s<Strings:Fixture.Attributes.Up>\n%s';raw=(text+'\0').encode('utf-16-be');b[256:256+len(raw)]=raw
  code=struct.pack('>4I',15<<26|11<<21|0x8200,14<<26|3<<21|31<<16|96,14<<26|4<<21|11<<16|256,18<<26|((target-(site+12))&0x3fffffc)|1);b[32:48]=code
  p=dict(schema_version=1,profile='ppc-localized-wide-template-v1',image_base=base,image_size=len(b),image_sha256=H(b),format_call_target=target,templates=[dict(prefix='Fixture.Attributes.Base',suffix='Fixture.Attributes.Up',address=ptr,call_setup=site,code_sha256=H(code))]);return b,p
 def test_valid_static_sequence(self):
  b,p=self.fixture();r=inspect_templates(b,p);self.assertEqual(r['templates'][0]['sequence'],['localized-prefix','string-argument-1','localized-suffix','LF','string-argument-2']);self.assertFalse(r['executed']);self.assertFalse(r['formatter_implementation_verified']);self.assertEqual(bytes(b),bytes(self.fixture()[0]))
 def test_input_hash_guard(self):
  b,p=self.fixture();b[0]=1
  with self.assertRaisesRegex(ValueError,'hash'):inspect_templates(b,p)
 def test_unknown_profile(self):
  b,p=self.fixture();p['profile']='unknown'
  with self.assertRaisesRegex(ValueError,'profile'):inspect_templates(b,p)
 def test_wide_template_and_range_guard(self):
  b,p=self.fixture();p['templates'][0]['address']+=2
  with self.assertRaisesRegex(ValueError,'template'):inspect_templates(b,p)
 def test_linked_branch_target_guard(self):
  b,p=self.fixture();p['format_call_target']+=4
  with self.assertRaisesRegex(ValueError,'target'):inspect_templates(b,p)
 def test_argument_register_guard(self):
  b,p=self.fixture();b[40:44]=struct.pack('>I',14<<26|5<<21|11<<16|256);p['image_sha256']=H(b);p['templates'][0]['code_sha256']=H(b[32:48])
  with self.assertRaisesRegex(ValueError,'register'):inspect_templates(b,p)
 def test_duplicate_template_guard(self):
  b,p=self.fixture();p['templates'].append(copy.deepcopy(p['templates'][0]))
  with self.assertRaisesRegex(ValueError,'duplicate'):inspect_templates(b,p)
 def test_cli_new_report_and_plan_hash(self):
  b,p=self.fixture()
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);image=root/'image.bin';plan=root/'plan.json';out=root/'report.json';image.write_bytes(b);plan.write_text(json.dumps(p),encoding='utf-8');args=[str(image),'--sha256',H(b),'--plan',str(plan),'--plan-sha256',H(plan.read_bytes()),'--output',str(out)];self.assertEqual(main(args),0);self.assertEqual(main(args),2);self.assertEqual(image.read_bytes(),b);out.unlink();args[-3]='0'*64;self.assertEqual(main(args),2);self.assertFalse(out.exists())
 def test_published_stat_strong_scope_and_plan_identity(self):
  R=Path(__file__).resolve().parents[1];d=json.loads((R/'locales/zh-Hans/candidate-decisions/stat-strong-native-template-order.json').read_bytes());plan=R/d['plan'];self.assertEqual(H(plan.read_bytes()),d['plan_sha256']);self.assertEqual(len(d['templates']),8);self.assertEqual(len(d['source_fragments']),10);self.assertTrue(d['static_template_order_verified']);self.assertFalse(d['runtime_concatenation_verified']);self.assertFalse(d['game_rendering_verified']);self.assertEqual({e['key'] for e in d['source_fragments']},{'HP','STR','DEF','ESP','ESR','DEX','STA','SRV','PercentUP','normalUP'})
if __name__=='__main__':unittest.main()
