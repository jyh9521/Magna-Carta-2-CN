import copy,hashlib,json,unittest
from pathlib import Path
from tools.translation_fragments import whitespace_suffixes
H=lambda s:hashlib.sha256(s.encode()).hexdigest()
class AtomicFragmentAdoptionTests(unittest.TestCase):
 def fixture(self):
  p=dict(entries=[dict(id='p',source_sha256='a'*64,translation='属性提高 '),dict(id='s',source_sha256='b'*64,translation=' ')]);g=dict(kind='source-locked-atomic-fragments',reason='paired source context',members=[dict(id=e['id'],source_sha256=e['source_sha256'],translation_sha256=H(e['translation']),role='prefix' if e['id']=='p' else 'suffix') for e in p['entries']],joins=[dict(prefix='p',suffix='s')],evidence=[dict(path='proof.json',sha256='c'*64)]);r=dict(entries=[dict(id=e['id'],text_kind='fragment') for e in p['entries']],fragment_groups=[g]);return p,r
 def test_exact_atomic_suffix_permission(self):
  p,r=self.fixture();self.assertEqual(whitespace_suffixes(p,r),{'s'})
 def test_stale_target_hash_rejected(self):
  p,r=self.fixture();p['entries'][0]['translation']='changed'
  with self.assertRaisesRegex(ValueError,'lock'):whitespace_suffixes(p,r)
 def test_missing_member_rejected(self):
  p,r=self.fixture();p['entries'].pop()
  with self.assertRaisesRegex(ValueError,'lock'):whitespace_suffixes(p,r)
 def test_unjoined_member_rejected(self):
  p,r=self.fixture();r['fragment_groups'][0]['joins']=[]
  with self.assertRaisesRegex(ValueError,'joins'):whitespace_suffixes(p,r)
 def test_nonspace_or_prefix_blank_rejected(self):
  p,r=self.fixture();p['entries'][1]['translation']='\t';r['fragment_groups'][0]['members'][1]['translation_sha256']=H('\t')
  with self.assertRaisesRegex(ValueError,'single-space'):whitespace_suffixes(p,r)
 def test_catalog_default_strict_and_explicit_suffix(self):
  from tools.coalesced import EmbeddedFile,SerializedString,serialize,parse,extract_entries
  from tools.sample_catalog import export_catalog,import_plan
  from tools.build_coalesced import rebuild
  raw=serialize([EmbeddedFile(SerializedString('Game.int','ascii',0),SerializedString('[Stats]\r\nPrefix=Attribute \r\nSuffix= increase\r\n','utf-16-le',0))]);rows=extract_entries(parse(raw),'Game/Coalesced.int');plan=dict(schema_version=1,source_mode='sha256-utf8',resource='Game/Coalesced.int',input_sha256=hashlib.sha256(raw).hexdigest(),entries=[dict(id=e['id'],source_sha256=H(e['source']),translation='属性提高 ' if i==0 else ' ') for i,e in enumerate(rows)]);cat=export_catalog(raw,plan)
  with self.assertRaisesRegex(ValueError,'empty'):import_plan(raw,cat)
  merged=import_plan(raw,cat,whitespace_fragments={rows[1]['id']});self.assertEqual(rebuild(raw,plan),rebuild(raw,merged))
 def test_actual_twelve_drafts_and_preserved_source_syntax(self):
  R=Path(__file__).resolve().parents[1];L=lambda p:json.loads((R/p).read_bytes());p=L('locales/zh-Hans/batch-117.json');r=L('locales/zh-Hans/batch-117.review.json');d=L('locales/zh-Hans/candidate-decisions/held-original-adoptions.json');self.assertEqual(len(p['entries']),12);self.assertEqual(r['status'],'draft');self.assertEqual(len(whitespace_suffixes(p,r)),1);self.assertEqual({e['id'] for e in p['entries']},{e['id'] for e in d['entries']});self.assertEqual(H((R/d['plan']).read_text(encoding='utf-8')),d['plan_sha256']);self.assertFalse(d['human_finalized'])
  for e in p['entries']:
   a=next(a for a in d['entries'] if a['id']==e['id']);self.assertEqual(H(e['translation']),a['translation_sha256'])
if __name__=='__main__':unittest.main()
