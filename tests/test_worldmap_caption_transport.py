"""No-codec wrapper tests prove validation precedes all output writes."""
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools.bink_audio import inspect,strip_audio
from tools.build_video_captions import encoded_size_limit
from tools.build_worldmap_captions import run
from test_bink_audio import fixture


class WorldMapTransportTests(unittest.TestCase):
    def arguments(self, root, *, identities=('movie_a',)):
        source=root/'sources';source.mkdir()
        raw=fixture();entries=[]
        for identity in identities:
            filename=identity.replace('/','_')+'.bik'
            (source/filename).write_bytes(raw)
            entries.append(dict(id=identity,source=dict(file=filename,member='MC2Game/Movies/'+filename,
                sha256=hashlib.sha256(raw).hexdigest(),size=len(raw),discs=[1],first_rgb_sha256='0'*64),
                expected_header=inspect(raw)['header'],captions=[dict(text='Owned fixture')]))
        plan=root/'plan.json';plan.write_text(json.dumps(dict(schema_version=1,kind='bink-audio-caption-plan',entries=entries)))
        return SimpleNamespace(project_root=root,source_root=source,output_dir=root/'output',plan=plan,
            plan_sha256=hashlib.sha256(plan.read_bytes()).hexdigest(),entry=None,
            preview=False,verify=False,ffmpeg=Path('FIXTURE'),ffmpeg_sha256='0'*64,
            encoder=Path('FIXTURE'),encoder_sha256='0'*64)

    def test_path_traversal_ids_are_rejected_before_any_write(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);args=self.arguments(root,identities=('../../../escaped',))
            before=sorted(str(p.relative_to(root)) for p in root.rglob('*'))
            with self.assertRaisesRegex(ValueError,'bounded leaf'):
                run(args)
            self.assertEqual(sorted(str(p.relative_to(root)) for p in root.rglob('*')),before)
            self.assertFalse((root.parent/'escaped.silent.bik').exists())

    def test_duplicate_ids_and_source_output_overlap_fail_before_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);args=self.arguments(root)
            plan=json.loads(args.plan.read_bytes());plan['entries']*=2
            args.plan.write_text(json.dumps(plan));args.plan_sha256=hashlib.sha256(args.plan.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError,'Duplicate'):
                run(args)
            self.assertFalse(args.output_dir.exists())
            args.output_dir=args.source_root/'output'
            with self.assertRaisesRegex(ValueError,'disjoint'):
                run(args)
            self.assertFalse(args.output_dir.exists())

    def test_unknown_entry_and_original_hash_mismatch_never_create_output(self):
        with tempfile.TemporaryDirectory() as temp:
            args=self.arguments(Path(temp));args.entry='unknown'
            with self.assertRaisesRegex(ValueError,'Unknown'):
                run(args)
            self.assertFalse(args.output_dir.exists())
            args.entry=None;(args.source_root/'movie_a.bik').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'SHA256'):
                run(args)
            self.assertFalse(args.output_dir.exists())

    def test_filtered_build_and_verify_use_independent_manifests(self):
        with tempfile.TemporaryDirectory() as temp:
            args=self.arguments(Path(temp),identities=('movie_a','movie_b'))
            frames=[b'owned-frame-one',b'owned-frame-two']
            def producer(fake):
                selected=[fake.entry] if fake.entry else ['movie_a','movie_b']
                fake.output_dir.mkdir(parents=True,exist_ok=True)
                for name in selected:
                    original=(args.source_root/(name+'.bik')).read_bytes()
                    (fake.output_dir/(name+'.bik')).write_bytes(strip_audio(original))
                    (fake.output_dir/(name+'.json')).write_text(json.dumps(dict(frames=[dict(decoded_rgb_sha256=hashlib.sha256(f).hexdigest()) for f in frames])))
                return []
            with patch('tools.build_worldmap_captions.captions.run',side_effect=producer),patch(
                    'tools.build_worldmap_captions.decoded_frames',return_value=iter(frames)):
                args.entry='movie_a';run(args)
            with patch('tools.build_worldmap_captions.captions.run',side_effect=producer),patch(
                    'tools.build_worldmap_captions.decoded_frames',return_value=iter(frames)):
                args.entry='movie_b';run(args)
            self.assertTrue((args.output_dir/'manifest-movie_a.json').is_file())
            self.assertTrue((args.output_dir/'manifest-movie_b.json').is_file())
            whole=args.output_dir/'manifest.json';whole.write_text('owned full-batch manifest')
            with patch('tools.build_worldmap_captions.captions.run',side_effect=producer),patch(
                    'tools.build_worldmap_captions.decoded_frames',return_value=iter(frames)):
                args.entry='movie_a';args.verify=True;run(args)
            self.assertEqual(whole.read_text(),'owned full-batch manifest')

    def timed_transport(self, root, *, alpha=(255,0,0), repair_indices=(0,1),
                        changed_indices=(0,1)):
        """Keep native codec I/O at the existing wrapper-test boundary."""
        args=self.arguments(root)
        raw=fixture(videos=(b'one!',b'two!',b'three!'))
        (args.source_root/'movie_a.bik').write_bytes(raw)
        source_frames=[bytes([20+index,40,60])*48 for index in range(3)]
        expected_frames=[(bytes([90,70,50])+frame[3:] if index in changed_indices else frame)
                         for index,frame in enumerate(source_frames)]
        plan=json.loads(args.plan.read_bytes());entry=plan['entries'][0]
        entry['source'].update(sha256=hashlib.sha256(raw).hexdigest(),size=len(raw),
                              first_rgb_sha256=hashlib.sha256(source_frames[0]).hexdigest())
        entry['expected_header']=inspect(raw)['header']
        caption=entry['captions'][0];caption['frame_alpha']=list(alpha)
        if repair_indices is not None:
            caption['erase']=dict(frame_repairs=dict(method='sparse-frame-rgba-v1',
                records=[dict(index=index,source_crop_sha256='0'*64,
                              patch=dict(path=f'patches/{index}.png',sha256='0'*64))
                         for index in repair_indices]))
        args.plan.write_bytes(json.dumps(plan).encode())
        args.plan_sha256=hashlib.sha256(args.plan.read_bytes()).hexdigest()
        def producer(fake):
            fake.output_dir.mkdir(parents=True,exist_ok=True)
            (fake.output_dir/'movie_a.bik').write_bytes(strip_audio(raw))
            (fake.output_dir/'movie_a.json').write_bytes(json.dumps(dict(frames=[
                dict(decoded_rgb_sha256=hashlib.sha256(frame).hexdigest(),
                     expected_rgb_sha256=hashlib.sha256(frame).hexdigest())
                for frame in expected_frames])).encode())
            return []
        def decode(ffmpeg,path,header):
            is_source=Path(path).resolve()==(args.source_root/'movie_a.bik').resolve()
            return iter(source_frames if is_source else expected_frames)
        return args,producer,decode

    def test_background_only_repairs_outlive_text_during_build_and_verify(self):
        for alpha in ((255,0,0),(0,255,0)):
            with self.subTest(alpha=alpha),tempfile.TemporaryDirectory() as temp:
                args,producer,decode=self.timed_transport(Path(temp),alpha=alpha)
                with (patch('tools.build_worldmap_captions.captions.run',side_effect=producer),
                      patch('tools.build_worldmap_captions.decoded_frames',side_effect=decode)):
                    report=run(args)['entries'][0]
                    self.assertEqual(report['timed_caption_verification']['inactive_frames'],1)
                    self.assertTrue(report['timed_caption_verification']['inactive_preencode_source_byte_identical'])
                    self.assertEqual(len(report['timed_caption_verification']['source_frame_rgb_hashes']),3)
                    args.verify=True
                    self.assertEqual(run(args)['entries'][0],report)

    def test_repair_only_activity_does_not_exempt_truly_inactive_frame_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            args,producer,decode=self.timed_transport(Path(temp),changed_indices=(0,1,2))
            with (patch('tools.build_worldmap_captions.captions.run',side_effect=producer),
                  patch('tools.build_worldmap_captions.decoded_frames',side_effect=decode),
                  self.assertRaisesRegex(ValueError,'inactive caption frame changed')):
                run(args)

    def test_alpha_zero_without_an_explicit_repair_record_still_requires_noop(self):
        with tempfile.TemporaryDirectory() as temp:
            args,producer,decode=self.timed_transport(Path(temp),repair_indices=None)
            with (patch('tools.build_worldmap_captions.captions.run',side_effect=producer),
                  patch('tools.build_worldmap_captions.decoded_frames',side_effect=decode),
                  self.assertRaisesRegex(ValueError,'inactive caption frame changed')):
                run(args)

    def test_legacy_movie_size_cap_stays_64_mib_and_explicit_long_clip_cap_is_bounded(self):
        self.assertEqual(encoded_size_limit({}),64*1024*1024)
        self.assertEqual(encoded_size_limit(dict(maximum_encoded_bytes=128*1024*1024)),128*1024*1024)
        for value in (False,0,-1,512*1024*1024+1,'128'):
            with self.subTest(value=value),self.assertRaises(ValueError):
                encoded_size_limit(dict(maximum_encoded_bytes=value))


if __name__=='__main__':unittest.main()
