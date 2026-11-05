"""Generated patch metadata refresh preserves identity, writes and user toggles."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import tomllib
import unittest

from tools.runtime_patch import digest,patch_toml
from tools.runtime_patch_metadata import machine_signature,profile,refresh,main
from test_runtime_patch_sections import plan as fixture_plan


def fixture():
    old=fixture_plan();old['patch_sections'][0]['is_enabled']=True;data=patch_toml(old)
    new=copy.deepcopy(old);new['comments']=['Présentation']
    for s in new['patch_sections']:
        s.update(name='表示 '+s['name'],description='説明',comments=['日本語'],is_enabled=False)
    return data,new


class RuntimeMetadataTests(unittest.TestCase):
    def test_refresh_preserves_user_flags_and_machine_data(self):
        data,p=fixture();new=refresh(data,p)
        self.assertEqual(profile(new,p)['enabled'],[True,False])
        self.assertEqual(machine_signature(new),machine_signature(data))
        self.assertEqual(profile(new,p)['comments'],3)
        self.assertIn('表示',new.decode());self.assertNotIn('\\u',new.decode())

    def test_enable_selects_only_requested_section(self):
        data,p=fixture();new=refresh(data,p,[0x1080])
        self.assertEqual(profile(new,p)['enabled'],[True,True])
        with self.assertRaisesRegex(ValueError,'unknown enable'):refresh(data,p,[0x9999])

    def test_header_and_machine_write_tamper_rejected(self):
        data,p=fixture();text=data.decode()
        for old,new in [('12345678','87654321'),('0123456789ABCDEF','1123456789ABCDEF'),
                        ('address = 0x00001020','address = 0x00001024'),('value = 0x48000060','value = 0x48000064')]:
            changed=text.replace(old,new).encode()
            self.assertNotEqual(changed,data)
            with self.subTest(old=old),self.assertRaises(ValueError):refresh(changed,p)

    def test_unknown_fields_and_write_types_are_not_dropped(self):
        data,p=fixture()
        for text in [data.decode()+'\n[[patch.be8]]\naddress=0x1100\nvalue=0\n',
                     'media_id=["12345678"]\n'+data.decode(),
                     data.decode().replace('is_enabled = true','is_enabled = "true"')]:
            with self.assertRaises(ValueError):refresh(text.encode(),p)

    def test_refresh_cli_writes_new_copy_and_keeps_source(self):
        data,p=fixture()
        with tempfile.TemporaryDirectory() as d,contextlib.redirect_stdout(io.StringIO()):
            root=Path(d);source=root/'patch.toml';source.write_bytes(data);plan=root/'plan.json';plan.write_text(json.dumps(p))
            out=root/'out.toml';args=['refresh',str(source),'--plan',str(plan),'--sha256',digest(data),'--enable','0x1080','--output',str(out)]
            self.assertEqual(main(args),0);self.assertEqual(source.read_bytes(),data)
            self.assertEqual(profile(out.read_bytes(),p)['enabled'],[True,True])
            self.assertEqual(main(args),2);self.assertEqual(source.read_bytes(),data)
            self.assertEqual(main(['inspect',str(out),'--plan',str(plan)]),0)

    def test_cli_wrong_hash_and_same_path_fail_without_source_changes(self):
        data,p=fixture()
        with tempfile.TemporaryDirectory() as d,contextlib.redirect_stdout(io.StringIO()):
            root=Path(d);source=root/'patch.toml';source.write_bytes(data);plan=root/'plan.json';plan.write_text(json.dumps(p))
            base=['refresh',str(source),'--plan',str(plan),'--output',str(source)]
            self.assertEqual(main(base+['--sha256',digest(data)]),2)
            out=root/'new.toml';self.assertEqual(main(base[:-1]+[str(out),'--sha256','0'*64]),2)
            self.assertFalse(out.exists());self.assertEqual(source.read_bytes(),data)

    def test_size_encoding_and_overlapping_writes_fail(self):
        data,p=fixture()
        for bad in [b'',b'\xff',b'x'*(1024*1024+1),data.replace(b'0x00001080',b'0x00001020')]:
            with self.subTest(size=len(bad)),self.assertRaises(ValueError):refresh(bad,p)

    def test_current_plan_is_readable_chinese_and_stays_default_off(self):
        root=Path(__file__).resolve().parents[1];p=json.loads((root/'references/probes/mc2-graphics-offline.json').read_bytes())
        data=patch_toml(p);t=tomllib.loads(data.decode())
        self.assertEqual(profile(data,p),dict(enabled=[False,False,False],literal_utf8=True,comments=9,writes=4))
        self.assertEqual([s['name'] for s in t['patch']],['60帧','光照／阴影异常修复','关闭后处理链（实验）'])
        self.assertFalse(p['evidence']['runtime_verified'])
        self.assertFalse(p['evidence']['user_feedback']['automated_game_execution'])


if __name__=='__main__':unittest.main()
