"""Self-authored script bytes and model cases; no shipped assets or VM execution."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from tools.inspect_digit_tag_formatter import script_shape,verify_script,model_positive_digits,main
class DigitTagFormatterTests(unittest.TestCase):
 def fixture(self):
  refs=dict(zip(['input','result','text','char','markup','length','index'],range(17,24)));prefix='<Strings:Example.Digits.Num_';script,edges=script_shape(refs,prefix);return refs,prefix,script,edges
 def test_exact_loop_shape(self):
  refs,prefix,script,edges=self.fixture();r=verify_script(script,refs,prefix);self.assertEqual(r['control_flow'],edges);self.assertFalse(r['executed']);self.assertEqual(r['conversion_token'],'PrimitiveCast:0x53')
 def test_back_edge_mutation_rejected(self):
  refs,prefix,script,edges=self.fixture();raw=bytearray(script);at=script.rfind(b'\x06');raw[at+2]^=1
  with self.assertRaisesRegex(ValueError,'shape'):verify_script(raw,refs,prefix)
 def test_prefix_change_rejected(self):
  refs,prefix,script,edges=self.fixture()
  with self.assertRaisesRegex(ValueError,'shape'):verify_script(script,refs,prefix+'Other')
 def test_duplicate_binding_rejected(self):
  refs,prefix,script,edges=self.fixture();refs['length']=refs['index']
  with self.assertRaisesRegex(ValueError,'duplicate'):script_shape(refs,prefix)
 def test_malformed_lookup_rejected(self):
  refs,prefix,script,edges=self.fixture()
  with self.assertRaisesRegex(ValueError,'prefix'):script_shape(refs,'<Other:Bad>')
 def test_positive_digit_model_keeps_each_digit(self):
  refs,prefix,script,edges=self.fixture();self.assertEqual(model_positive_digits(0,prefix),prefix+'0>');self.assertEqual(model_positive_digits(140,prefix),prefix+'1>'+prefix+'4>'+prefix+'0>');self.assertEqual(model_positive_digits(10,prefix).count(prefix),2)
 def test_model_domain_explicit(self):
  for v in [-1,True,2147483648,'12']:
   with self.assertRaisesRegex(ValueError,'nonnegative'):model_positive_digits(v,'<Strings:Example.Digits.Num_')
 def test_cli_guards_without_game_files(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);p=root/'p';c=root/'c';plan=root/'plan';out=root/'out';p.write_bytes(b'x');c.write_bytes(b'y');plan.write_bytes(b'{}');args=[str(p),'--sha256','0'*64,'--core',str(c),'--core-sha256','0'*64,'--plan',str(plan),'--plan-sha256','0'*64,'--output',str(out)];self.assertEqual(main(args),2);self.assertFalse(out.exists());out.write_bytes(b'keep');self.assertEqual(main(args),2);self.assertEqual(out.read_bytes(),b'keep')
 def test_published_digit_probe_identity(self):
  R=Path(__file__).resolve().parents[1];d=json.loads((R/'locales/zh-Hans/candidate-decisions/stat-strong-digit-markup.json').read_bytes());self.assertEqual(hashlib.sha256((R/d['plan']).read_bytes()).hexdigest(),d['plan_sha256']);self.assertEqual(d['digit_lookup_count'],10);self.assertEqual(d['scenario_count'],80);self.assertTrue(d['script_source_shape_verified']);self.assertFalse(d['game_rendering_verified']);self.assertFalse(d['canonical_translation_applied'])
if __name__=='__main__':unittest.main()
