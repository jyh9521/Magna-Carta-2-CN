"""Installer regressions use synthetic discs/STFS; real game inputs are optional."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import threading
import unittest
import zlib
from unittest.mock import patch

from tools.disc_inventory import Disc, MAGIC
from tools.installer_core import (Bundle, Installer, InstallError, Cancelled, execution_id,
                                  safe_relative, sha_file, validate_manifest, guarded_remove,
                                  publish_no_replace)
from tools.installer_core import recover_interrupted
from tools.installer_delta import create_delta, apply_delta, digest, HEADER, BLOCK
from test_stfs_package import fixture as stfs_fixture


def iso_fixture(number):
    xex = bytearray(256)
    xex[:4] = b'XEX2'
    struct.pack_into('>I', xex, 20, 1)
    struct.pack_into('>II', xex, 24, 0x40006, 64)
    struct.pack_into('>4I4BI', xex, 64, 0x100 + number, 1, 1, 0x12345678, 0, 0, number, 2, 0)
    data = bytearray(44 * 2048)
    data[0x10000:0x10014] = MAGIC
    data[0x10800-20:0x10800] = MAGIC
    struct.pack_into('<II', data, 0x10014, 36, 2048)
    for offset, right, sector, name, payload in ((0, 16, 40, b'default.xex', xex), (64, 0, 42, b'text.txt', b'original')):
        struct.pack_into('<HHIIBB', data, 36*2048+offset, 0, right, sector, len(payload), 0x80, len(name))
        data[36*2048+offset+14:36*2048+offset+14+len(name)] = name
        data[sector*2048:sector*2048+len(payload)] = payload
    return bytes(data)


def make_bundle(root, native=None):
    root = Path(root).resolve()
    bundle = root / 'bundle'
    bundle.mkdir()
    (bundle / 'patches').mkdir()
    images, discs = [], []
    def patch_record(before, after):
        delta = create_delta(before, after)
        name = 'patches/' + digest(delta) + '.mcdelta'
        (bundle/name).write_bytes(delta)
        return dict(transform='identity', base_sha256=digest(before), output_size=len(after),
                    output_sha256=digest(after), patch=name, patch_sha256=digest(delta), runtime_envelope=False)
    for n in (1,2):
        path = root / f'original {n}.iso'
        path.write_bytes(iso_fixture(n))
        images.append(path)
        disc = Disc(path)
        files = []
        for entry in disc.inventory():
            record = dict(path=entry['path'],size=entry['size'],sha256=disc.resource_hash(entry))
            if entry['path'] == 'text.txt':
                record.update(patch_record(b'original', '译文'.encode()))
            files.append(record)
        xex = next(e for e in disc.inventory() if e['path']=='default.xex')
        discs.append(dict(size=disc.size,partition_base=disc.base,sha256=sha_file(path),files=files,
                          execution_id=execution_id(disc.read(xex['offset'],xex['size']))))
    dlc_root = root / 'dlc'
    dlc_root.mkdir()
    name = 'A'*42
    before = stfs_fixture([('sample.txt',b'original')])
    after = stfs_fixture([('sample.txt','汉化'.encode())])
    (dlc_root/name).write_bytes(before)
    dlc = dict(name=name,label='合成DLC',size=len(before),sha256=digest(before),**patch_record(before,after))
    (bundle/'USAGE.txt').write_bytes(b'usage')
    m = dict(schema_version=1,kind='localization-installer',version='fixture',title_id='12345678',
             output_name='Fixture',discs=discs,dlc=[dlc],tools={},usage_sha256=digest(b'usage'))
    if native:
        (bundle/'tools').mkdir()
        target=bundle/'tools'/Path(native).name
        shutil.copyfile(native,target)
        m['tools']['zar']=dict(path='tools/'+target.name,sha256=sha_file(target))
    raw=(json.dumps(m)+'\n').encode()
    (bundle/'manifest.json').write_bytes(raw)
    return Bundle(bundle,digest(raw)),images,dlc_root


class DeltaTests(unittest.TestCase):
    def test_versioned_zip_name_keeps_all_dots(self):
        from tools.package_installer import archive_path
        self.assertEqual(archive_path(Path('MC2-0.1.0-rc.1-win64')).name,'MC2-0.1.0-rc.1-win64.zip')
    def test_roundtrip_growth_shrink_empty_random_multiblock(self):
        for before,after in ((b'',b''),(b'abc',b''),(b'',b'xyz'),(b'a'*100,b'b'*500),(os.urandom(BLOCK+30),os.urandom(BLOCK+300))):
            with self.subTest(length=len(after)):
                self.assertEqual(apply_delta(before,create_delta(before,after)),after)
    def test_wrong_source_rejected(self):
        with self.assertRaises(ValueError):apply_delta(b'bad',create_delta(b'abc',b'def'))
    def test_truncation_trailing_and_corruption(self):
        delta=create_delta(b'abc',b'def')
        for bad in (delta[:3],delta[:-1],delta+b'junk',delta[:HEADER.size]+b'\xff'*4,delta[:HEADER.size+4]+b'x'):
            with self.subTest(length=len(bad)),self.assertRaises((ValueError,zlib.error)):
                apply_delta(b'abc',bad)
    def test_bomb_header_rejected(self):
        delta=bytearray(create_delta(b'a',b'b'));struct.pack_into('>Q',delta,12,2**40)
        with self.assertRaises(ValueError):apply_delta(b'a',bytes(delta))
    def test_cancel_checked(self):
        def cancel():raise Cancelled()
        with self.assertRaises(Cancelled):apply_delta(b'a',create_delta(b'a',b'b'),cancel)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();self.bundle,self.images,self.dlc=make_bundle(self.root)
    def test_xex_dlc_and_originals_unchanged(self):
        before=[sha_file(p) for p in self.images]
        result=Installer(self.bundle).install(self.images,self.root/'out','xex',self.dlc)
        self.assertEqual((self.root/'out/Disc1/text.txt').read_text(encoding='utf-8'),'译文')
        self.assertEqual(len(result['discs']),2);self.assertEqual(len(result['dlc']),1)
        self.assertTrue((self.root/'out'/result['dlc'][0]['path']).is_file())
        self.assertEqual(before,[sha_file(p) for p in self.images])
        self.assertFalse(list(self.root.glob('*.install-lock')))
        self.assertFalse(list(self.root.glob('*.partial')))
    def test_swapped_discs(self):
        with self.assertRaisesRegex(InstallError,'身份不符'):Installer(self.bundle).inspect(list(reversed(self.images)))
    def test_full_hash_rejects_changed_padding(self):
        data=bytearray(self.images[0].read_bytes());data[-1]=1;self.images[0].write_bytes(data)
        with self.assertRaisesRegex(InstallError,'SHA256'):Installer(self.bundle).inspect(self.images,full=True)
    def test_unknown_magic(self):
        self.images[0].write_bytes(b'bad')
        with self.assertRaises(ValueError):Installer(self.bundle).inspect(self.images)
    def test_existing_output_never_touched(self):
        out=self.root/'out';out.mkdir();(out/'save').write_bytes(b'keep')
        with self.assertRaises(InstallError):Installer(self.bundle).install(self.images,out,'xex',self.dlc)
        self.assertEqual((out/'save').read_bytes(),b'keep')
    def test_low_space(self):
        with patch('tools.installer_core.shutil.disk_usage',return_value=shutil._ntuple_diskusage(100,99,1)):
            with self.assertRaisesRegex(InstallError,'空间不足'):Installer(self.bundle).install(self.images,self.root/'out','xex')
    def test_bad_dlc(self):
        (self.dlc/('A'*42)).write_bytes(b'bad')
        with self.assertRaises(InstallError):Installer(self.bundle).check_dlc(self.dlc)
    def test_cancellation_cleans_stage(self):
        event=threading.Event()
        def emit(e):
            if e['stage']=='patch':event.set()
        with self.assertRaises(Cancelled):Installer(self.bundle,emit,event).install(self.images,self.root/'out','xex',self.dlc)
        self.assertFalse((self.root/'out').exists());self.assertFalse(list(self.root.glob('*.partial')))
        self.assertTrue(list((self.root/'MC2-Installer-Logs').glob('*.jsonl')))
    def test_corrupt_patch_cleans_stage_and_keeps_input(self):
        patch_path=next((self.bundle.root/'patches').iterdir());patch_path.write_bytes(b'corrupt')
        before=[sha_file(p) for p in self.images]
        with self.assertRaises(InstallError):Installer(self.bundle).install(self.images,self.root/'out','xex')
        self.assertEqual(before,[sha_file(p) for p in self.images]);self.assertFalse((self.root/'out').exists())
    def test_manifest_tamper(self):
        with self.assertRaises(InstallError):Bundle(self.bundle.root,'0'*64)
    def test_manifest_duplicate_case_and_traversal(self):
        for name in ('../escape','C:/temp','/root','a//b','CON.txt','dir/NUL','a\\b','a.','a\n'):
            with self.subTest(name=name),self.assertRaises(InstallError):safe_relative(name)
        m=copy.deepcopy(self.bundle.data);m['discs'][0]['files'].append(dict(m['discs'][0]['files'][0]))
        with self.assertRaises(InstallError):validate_manifest(m)
    def test_same_disc_twice_rejected(self):
        with self.assertRaises(InstallError):Installer(self.bundle).inspect([self.images[0]]*2)
    def test_cancel_before_work(self):
        cancel=threading.Event();cancel.set()
        with self.assertRaises(Cancelled):Installer(self.bundle,cancel=cancel).install(self.images,self.root/'out','xex')
    def test_without_dlc_explicit(self):
        events=[];result=Installer(self.bundle,events.append).install(self.images,self.root/'out','xex')
        self.assertEqual(result['dlc'],[]);self.assertTrue(any(e['level']=='warning' for e in events))
    def test_publication_no_replace(self):
        src=self.root/'a';dst=self.root/'b';src.mkdir();dst.mkdir()
        with self.assertRaises(OSError):publish_no_replace(src,dst)
        self.assertTrue(src.is_dir());self.assertTrue(dst.is_dir())
    def test_guarded_cleanup_cannot_remove_parent(self):
        with self.assertRaises(InstallError):guarded_remove(self.root,self.root)
    def test_runtime_profiles_do_not_patch_xex(self):
        m=copy.deepcopy(self.bundle.data);m['discs'][0]['files'][0].update({k:v for k,v in m['discs'][0]['files'][1].items() if k not in ('path','size','sha256')})
        with self.assertRaises(InstallError):validate_manifest(m)
    def test_tool_hash_is_checked_before_execution(self):
        self.bundle.data['tools']['zar']=dict(path='USAGE.txt',sha256='0'*64)
        with self.assertRaises(InstallError):self.bundle.tool('zar')
    def test_execution_header_boundaries(self):
        for data in (b'',b'XEX2'+bytes(24),b'XEX1'+bytes(300)):
            with self.assertRaises(InstallError):execution_id(data)
    def test_log_directory_conflict_does_not_leave_lock(self):
        (self.root/'MC2-Installer-Logs').write_bytes(b'keep')
        with self.assertRaises(OSError):Installer(self.bundle).install(self.images,self.root/'out','xex')
        self.assertFalse((self.root/'.out.install-lock').exists())
        self.assertEqual((self.root/'MC2-Installer-Logs').read_bytes(),b'keep')
    def test_explicit_recovery_and_running_guard(self):
        token='a'*32;out=self.root/'out';stage=self.root/('.mc2-'+token+'.partial');stage.mkdir()
        lock=self.root/'.out.install-lock';lock.write_text(token)
        owner=dict(token=token,output=str(out),bundle=self.bundle.sha256,pid=os.getpid())
        (stage/'.owner.json').write_text(json.dumps(owner));(stage/'temporary').write_bytes(b'owned')
        with self.assertRaisesRegex(InstallError,'仍在运行'):recover_interrupted(out,self.bundle.sha256)
        with patch('tools.installer_core.process_alive',return_value=False):
            result=recover_interrupted(out,self.bundle.sha256)
        self.assertEqual(result['stage'],'recovered');self.assertFalse(stage.exists());self.assertFalse(lock.exists())
    def test_recovery_rejects_other_release(self):
        token='b'*32;out=self.root/'out';stage=self.root/('.mc2-'+token+'.partial');stage.mkdir()
        (self.root/'.out.install-lock').write_text(token)
        (stage/'.owner.json').write_text(json.dumps(dict(token=token,output=str(out),bundle='0'*64,pid=1)))
        with self.assertRaises(InstallError):recover_interrupted(out,self.bundle.sha256)
        self.assertTrue(stage.exists())
    def test_source_changed_during_install_prevents_publish(self):
        def emit(e):
            if e['stage']=='source-readback':
                data=bytearray(self.images[0].read_bytes());data[-1]^=1;self.images[0].write_bytes(data)
        with self.assertRaisesRegex(InstallError,'其他程序更改'):
            Installer(self.bundle,emit).install(self.images,self.root/'out','xex')
        self.assertFalse((self.root/'out').exists())
    def test_bundle_build_and_replay(self):
        from tools.build_installer_bundle import build
        target=self.root/'candidate';target.write_text('译文',encoding='utf-8')
        recipe=dict(version='fixture',title_id='12345678',output_name='Fixture',tools={},
                    usage=str(self.bundle.root/'USAGE.txt'),dlc=[],discs=[])
        for image in self.images:
            recipe['discs'].append(dict(iso=str(image),sha256=sha_file(image),resources=[dict(path='text.txt',file=str(target),sha256=sha_file(target))]))
        path=self.root/'recipe.json';path.write_text(json.dumps(recipe))
        build(path,sha_file(path),self.root/'rebuilt')
        new=Bundle(self.root/'rebuilt',sha_file(self.root/'rebuilt/manifest.json'))
        result=Installer(new).install(self.images,self.root/'rebuilt-output','xex')
        self.assertEqual(len(result['discs']),2)
        with patch('tools.build_installer_bundle.create_delta',side_effect=AssertionError('must reuse verified delta')):
            reused=build(path,sha_file(path),self.root/'reused',new.root,new.sha256)
        self.assertEqual(reused,new.data)
        with self.assertRaises(ValueError):
            build(path,sha_file(path),self.root/'missing-trust',new.root)


NATIVE=Path(os.environ.get('MC2_ZAR_TOOL','build/phase-334-installer/native/Release/mc2-zar.exe'))
@unittest.skipUnless(NATIVE.is_file(),'optional locally built ZArchive adapter')
class NativeArchiveTests(unittest.TestCase):
    def test_real_zar_roundtrip_dlc_and_corrupt_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();bundle,images,dlc=make_bundle(root,NATIVE.resolve())
            result=Installer(bundle).install(images,root/'out','zar',dlc)
            self.assertEqual(len(result['discs']),2)
            zar=root/'out'/result['discs'][0]['path'];data=bytearray(zar.read_bytes());data[0]^=1;zar.write_bytes(data)
            p=subprocess.run([str(bundle.tool('zar')),'verify',str(zar),str(root/'bad.tsv')],capture_output=True)
            self.assertNotEqual(p.returncode,0);self.assertFalse((root/'bad.tsv').exists())


if __name__=='__main__':unittest.main()
