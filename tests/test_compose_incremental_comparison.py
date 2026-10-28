"""Small authored packet fixtures; no ISO, codec, or game execution."""
import copy
import errno
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import compose_incremental_comparison as view
from tools import refresh_oneclick_probe as refresh
from tools.restore_probe_refresh import restore
from tools.verify_resource_phase import inspect, sha


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2)+'\n').encode()


def tree(root):
    return {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}


class Fixture:
    def __init__(self, root):
        self.root=root; self.base=root/'base'; self.delta=root/'delta'; self.out=root/'view'
        self.delta.mkdir(); self.a='Game/font.xxx'; self.keep='Game/keep.dat'
        self.movie='Game/Movies/new.bik'; self.toc='Game/Xbox360TOC.txt'
        self.original_movie=b'BIKi original authored movie'
        originals={self.a:b'original A', self.keep:b'original B'}
        raw={self.a:b'raw uncompressed original A', self.keep:originals[self.keep]}
        candidate={self.a:b'old translated A', self.keep:b'unchanged translated B'}
        for files in (originals,raw,candidate):
            files[self.toc]=self.make_toc(files)
        self.manifest=dict(schema_version=1,kind='offline-disc-locale-raw-comparison',disc=1,
            raw_package_outputs=True,raw_control_method='source-derived-uncompressed-fonts-original-text-disc-toc',
            unknown_control_syntax_resolved=False,deployment_performed=False,game_rendering_verified=False,
            composition_manifest_sha256='1'*64,comparison_plan_canonical_sha256='2'*64,
            source_image_sha256='3'*64,resources=[],member_sha256={})
        for phase,files in [('controls',originals),('raw-controls',raw),('candidate',candidate)]:
            for name,data in files.items():
                p=self.base/phase/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
                self.manifest['member_sha256'][phase+'/'+name]=sha(data)
        for name in originals:
            row=dict(path=name)
            for key,files in [('original',originals),('raw',raw),('candidate',candidate)]:
                row.update({key+'_size':len(files[name]),key+'_sha256':sha(files[name])})
            self.manifest['resources'].append(row)
        self.save_base()
        (self.delta/'replacement.xxx').write_bytes(b'new translated payload A; deliberately longer')
        (self.delta/'movie-original.bik').write_bytes(self.original_movie)
        (self.delta/'movie-candidate.bik').write_bytes(b'BIKi authored localized movie; different bytes')
        self.replacements=dict(schema_version=1,kind='incremental-comparison-replacements',disc=1,
            toc_path=self.toc,resources=[
                self.row(self.a,'replacement.xxx',sha(candidate[self.a])),
                dict(self.row(self.movie,'movie-candidate.bik',sha(self.original_movie)),
                     original=dict(file='movie-original.bik',size=len(self.original_movie),sha256=sha(self.original_movie)))])
        self.save_delta()

    def make_toc(self, files):
        return (''.join(f'{len(files[p])} 7 {100+i} ../{p} 9\r\n' for i,p in enumerate((self.a,self.keep)))+
                f'{len(self.original_movie)} 3 200 ../{self.movie} 8\r\n'+
                f'0 0 250 ../{self.toc} 0\r\n').encode()

    def row(self, name, file, before):
        data=(self.delta/file).read_bytes()
        return dict(path=name,file=file,before_sha256=before,size=len(data),sha256=sha(data))

    def save_base(self):
        data=encoded(self.manifest);(self.base/'manifest.json').write_bytes(data);self.base_hash=sha(data)

    def save_delta(self):
        data=encoded(self.replacements);self.delta_path=self.delta/'manifest.json'
        self.delta_path.write_bytes(data);self.delta_hash=sha(data)

    def args(self):
        return self.base,self.base_hash,self.delta_path,self.delta_hash,self.out


class IncrementalComparisonTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name).resolve();self.f=Fixture(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_shared_old_members_new_raw_and_changed_candidate_are_distinct(self):
        f=self.f;before_base=tree(f.base);before_delta=tree(f.delta)
        result=view.build(*f.args())
        self.assertEqual(len(result['resources']),4)
        self.assertEqual(tree(f.base),before_base);self.assertEqual(tree(f.delta),before_delta)
        for phase in ('controls','raw-controls','candidate'):
            self.assertTrue(os.path.samefile(f.base/phase/f.keep,f.out/phase/f.keep))
            checked,_=inspect(f.out,sha((f.out/'manifest.json').read_bytes()),f.out/phase,phase)
            self.assertTrue(checked['all_resources_match'])
        self.assertTrue(os.path.samefile(f.base/'raw-controls'/f.a,f.out/'raw-controls'/f.a))
        self.assertNotEqual((f.out/'raw-controls'/f.a).read_bytes(),(f.out/'controls'/f.a).read_bytes())
        self.assertFalse(os.path.samefile(f.delta/'replacement.xxx',f.out/'candidate'/f.a))
        self.assertFalse(os.path.samefile(f.delta/'movie-original.bik',f.out/'controls'/f.movie))
        self.assertTrue(os.path.samefile(f.out/'controls'/f.movie,f.out/'raw-controls'/f.movie))
        self.assertEqual((f.out/'raw-controls'/f.movie).read_bytes(),f.original_movie)
        self.assertEqual(view.verify(*f.args())['status'],'PASS')

    def test_toc_only_changes_size_and_exact_inverse_is_saved(self):
        f=self.f;view.build(*f.args())
        old=(f.base/'candidate'/f.toc).read_bytes();new=(f.out/'candidate'/f.toc).read_bytes()
        for a,b in zip(old.splitlines(),new.splitlines()):
            self.assertEqual(a.split(b' ',1)[1],b.split(b' ',1)[1])
        self.assertEqual((f.out/'rollback/candidate-toc.txt').read_bytes(),old)
        proof=json.loads((f.out/'reports/toc.json').read_bytes())
        from tools.update_resource_sizes import update_sizes
        self.assertEqual(update_sizes(new,sha(new),proof['inverse_changes']),old)
        self.assertTrue(proof['inverse_byte_identical'])

    def test_all_preflight_conflicts_leave_no_output(self):
        f=self.f
        for location in ('base-hash','manifest-hash','before-hash','source-bytes','original-hash'):
            with self.subTest(location=location):
                a=list(f.args());saved=copy.deepcopy(f.replacements);source=(f.delta/'replacement.xxx').read_bytes()
                if location=='base-hash':a[1]='0'*64
                if location=='manifest-hash':a[3]='0'*64
                if location=='before-hash':f.replacements['resources'][0]['before_sha256']='0'*64
                if location=='source-bytes':(f.delta/'replacement.xxx').write_bytes(b'changed')
                if location=='original-hash':f.replacements['resources'][1]['original']['sha256']='0'*64
                if location in ('before-hash','original-hash'):f.save_delta();a[3]=f.delta_hash
                with self.assertRaises(ValueError):view.build(*a)
                self.assertFalse(f.out.exists())
                (f.delta/'replacement.xxx').write_bytes(source);f.replacements=saved;f.save_delta()

    def test_duplicate_escape_executable_and_toc_replacement_rejected(self):
        f=self.f; original=copy.deepcopy(f.replacements)
        for mode in ('duplicate','escape','xex','toc','missing-original'):
            with self.subTest(mode=mode):
                f.replacements=copy.deepcopy(original)
                if mode=='duplicate':
                    r=copy.deepcopy(f.replacements['resources'][0]);r['path']=r['path'].upper();f.replacements['resources'].append(r)
                if mode=='escape':f.replacements['resources'][0]['file']='../outside.xxx'
                if mode=='xex':f.replacements['resources'][0]['path']='default.XEX'
                if mode=='toc':f.replacements['resources'][0]['path']=f.toc
                if mode=='missing-original':del f.replacements['resources'][1]['original']
                f.save_delta()
                with self.assertRaises(ValueError):view.build(*f.args())
                self.assertFalse(f.out.exists())

    def test_rehashed_toc_size_conflict_is_not_accepted(self):
        f=self.f;p=f.base/'candidate'/f.toc
        changed=p.read_bytes().replace(b'16 7 100',b'99 7 100');self.assertNotEqual(changed,p.read_bytes());p.write_bytes(changed)
        f.manifest['member_sha256']['candidate/'+f.toc]=sha(changed)
        next(r for r in f.manifest['resources'] if r['path']==f.toc).update(candidate_size=len(changed),candidate_sha256=sha(changed))
        f.save_base()
        with self.assertRaisesRegex(ValueError,'TOC.*size'):view.build(*f.args())
        self.assertFalse(f.out.exists())

    def test_unselected_predecessor_toc_size_is_also_validated(self):
        f=self.f;p=f.base/'candidate'/f.toc;lines=p.read_bytes().splitlines(keepends=True)
        lines=[b'999 '+line.split(b' ',1)[1] if f.keep.encode() in line else line for line in lines]
        changed=b''.join(lines);p.write_bytes(changed)
        f.manifest['member_sha256']['candidate/'+f.toc]=sha(changed)
        next(r for r in f.manifest['resources'] if r['path']==f.toc).update(candidate_size=len(changed),candidate_sha256=sha(changed))
        f.save_base()
        with self.assertRaisesRegex(ValueError,'TOC.*size'):view.build(*f.args())
        self.assertFalse(f.out.exists())

    def test_output_must_be_new_and_disjoint_from_inputs(self):
        f=self.f
        for p in (f.base,f.base/'nested',f.delta,f.root):
            with self.subTest(path=p),self.assertRaises(ValueError):view.build(*f.args()[:-1],p)

    def test_link_failure_cleans_only_owned_output(self):
        f=self.f;before=tree(f.base);counts={p:p.stat().st_nlink for p in f.base.rglob('*') if p.is_file()}
        real=os.link;count=0
        def fail_after_one(src,dst):
            nonlocal count
            count+=1
            if count==2:raise OSError(errno.EXDEV,'injected link failure')
            return real(src,dst)
        with patch.object(view.os,'link',side_effect=fail_after_one),self.assertRaises(OSError):view.build(*f.args())
        self.assertFalse(f.out.exists());self.assertEqual(tree(f.base),before)
        self.assertEqual({p:p.stat().st_nlink for p in counts},counts)

    def test_failure_preserves_foreign_file_and_all_input_bytes(self):
        f=self.f;before=tree(f.base);real=os.link
        def fail(src,dst):
            (f.out/'foreign.txt').write_bytes(b'not owned by builder')
            raise OSError('injected failure with foreign output')
        with patch.object(view.os,'link',side_effect=fail),self.assertRaises(OSError):view.build(*f.args())
        self.assertEqual(tree(f.out),{'foreign.txt':b'not owned by builder'})
        self.assertEqual(tree(f.base),before)

    def test_verify_detects_changed_input_and_unexpected_output(self):
        f=self.f;view.build(*f.args());(f.out/'foreign.txt').write_bytes(b'extra')
        with self.assertRaises(ValueError):view.verify(*f.args())
        (f.out/'foreign.txt').unlink()
        (f.delta/'replacement.xxx').write_bytes(b'changed source')
        with self.assertRaises(ValueError):view.verify(*f.args())

    def test_verify_rejects_unexpected_empty_directory(self):
        f=self.f;view.build(*f.args());(f.out/'empty-foreign-directory').mkdir()
        with self.assertRaisesRegex(ValueError,'unexpected.*directory'):view.verify(*f.args())

    def test_source_growth_during_copy_is_bounded_and_cleans_output(self):
        f=self.f;real=view.create_member;expected_size=f.replacements['resources'][0]['size'];observed=[]
        original_state=view.file_state
        def observe(path):
            if path==f.out/'candidate'/f.a and path.exists():observed.append(path.stat().st_size)
            return original_state(path)
        def grow(path,op,*args):
            if path==f.out/'candidate'/f.a:
                source=f.delta/'replacement.xxx';source.write_bytes(source.read_bytes()+b'grow'*1000)
            return real(path,op,*args)
        with patch.object(view,'create_member',side_effect=grow),patch.object(view,'file_state',side_effect=observe):
            with self.assertRaisesRegex(ValueError,'grew'):view.build(*f.args())
        self.assertFalse(f.out.exists())
        self.assertTrue(all(size<=expected_size for size in observed))

    def test_cleanup_preserves_a_foreign_replacement_of_an_owned_path(self):
        f=self.f;real=view.create_member;foreign=[];before=tree(f.base)
        def replace(path,op,*args):
            result=real(path,op,*args)
            if op['method']=='link' and 'source' in op:
                path.unlink();path.write_bytes(b'foreign replacement');foreign.append(path)
                raise OSError('injected replacement of an owned link')
            return result
        with patch.object(view,'create_member',side_effect=replace),self.assertRaises(OSError):view.build(*f.args())
        self.assertEqual(len(foreign),1)
        self.assertEqual(tree(f.out),{foreign[0].relative_to(f.out).as_posix():b'foreign replacement'})
        self.assertEqual(tree(f.base),before)

    def test_cleanup_does_not_follow_a_replaced_owned_parent(self):
        f=self.f;real=view.create_member;foreign=[];before=tree(f.base)
        def replace_parent(path,op,*args):
            result=real(path,op,*args)
            if op['method']=='link' and 'source' in op:
                previous=f.out/'foreign-moved-directory'
                path.parent.rename(previous);path.parent.mkdir()
                os.link(previous/path.name,path);foreign.append(path)
                raise OSError('injected replacement of an owned directory')
            return result
        with patch.object(view,'create_member',side_effect=replace_parent),self.assertRaises(OSError):view.build(*f.args())
        self.assertEqual(len(foreign),1)
        self.assertTrue(foreign[0].exists())
        self.assertEqual(tree(f.base),before)

    def test_a_noop_selection_reuses_old_candidate_without_materializing(self):
        f=self.f;raw=(f.base/'candidate'/f.a).read_bytes();(f.delta/'replacement.xxx').write_bytes(raw)
        f.replacements['resources'][0].update(size=len(raw),sha256=sha(raw));f.save_delta()
        view.build(*f.args())
        self.assertTrue(os.path.samefile(f.base/'candidate'/f.a,f.out/'candidate'/f.a))

    def test_view_is_reusable_as_next_generation_base(self):
        f=self.f;m=view.build(*f.args());first=f.out
        f.base=first;f.base_hash=sha((first/'manifest.json').read_bytes());f.out=self.root/'second-view'
        f.replacements['resources']=f.replacements['resources'][:1]
        f.replacements['resources'][0]['before_sha256']=next(r for r in m['resources'] if r['path']==f.a)['candidate_sha256']
        raw=b'third generation A';(f.delta/'replacement.xxx').write_bytes(raw)
        f.replacements['resources'][0].update(size=len(raw),sha256=sha(raw));f.save_delta()
        view.build(*f.args());self.assertEqual(view.verify(*f.args())['status'],'PASS')
        self.assertTrue(os.path.samefile(first/'candidate'/f.movie,f.out/'candidate'/f.movie))

    def test_existing_folder_refresh_enrollment_and_rollback_consume_view(self):
        f=self.f;m=view.build(*f.args());live=self.root/'live';originals=self.root/'originals';originals.mkdir()
        for phase in ('candidate','raw-controls'):
            for r in f.manifest['resources']:
                p=live/phase/r['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((f.base/phase/r['path']).read_bytes())
            p=live/phase/f.movie;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(f.original_movie)
            (live/phase/'default.xex').write_bytes(b'authored XEX placeholder')
        exe=self.root/'emulator.exe';exe.write_bytes(b'never executed');config=self.root/'config.toml';config.write_bytes(b'unchanged=1')
        prepared=dict(schema_version=1,kind='prepared-oneclick-warning-probe',source_root=str(originals),
            packet_root=str(f.base),packet_manifest_sha256=f.base_hash,full_independent_copies=True,
            game_sha256=sha(b'authored XEX placeholder'),config_sha256=sha(config.read_bytes()),
            phases=[dict(phase=p,resource_count=3,files=5) for p in ('candidate','raw-controls')])
        (live/'PREPARED.json').write_bytes(encoded(prepared))
        for n in ('开始中文测试.cmd','开始原文对照.cmd'):(live/n).write_bytes(b'old launcher never executed')
        before=tree(live);mh=sha((f.out/'manifest.json').read_bytes())
        enrollment=dict(schema_version=1,kind='explicit-resource-enrollment',disc=1,
            prepared_sha256=sha((live/'PREPARED.json').read_bytes()),old_packet_manifest_sha256=f.base_hash,
            new_packet_manifest_sha256=mh,game_rendering_verified=False,
            additions=[dict(path=f.movie,original_size=len(f.original_movie),original_sha256=sha(f.original_movie))])
        ep=self.root/'enrollment.json';ep.write_bytes(encoded(enrollment));backup=self.root/'backup'
        result=refresh.refresh(live,enrollment['prepared_sha256'],f.out,mh,exe,config,backup,
            enrollment=ep,enrollment_sha256=sha(ep.read_bytes()))
        self.assertEqual(result['status'],'committed')
        for phase in ('candidate','raw-controls'):self.assertTrue(inspect(f.out,mh,live/phase,phase)[0]['all_resources_match'])
        restore(live,backup,sha((backup/'REFRESH.json').read_bytes()),self.root/'restore-receipt.json')
        self.assertEqual(tree(live),before)


if __name__=='__main__':unittest.main()
