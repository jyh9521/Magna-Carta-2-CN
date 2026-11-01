import copy
import json
from pathlib import Path
import tempfile
import unittest

from tools.installer_delta import digest
from tools.prepare_installer_sources import apply_resource_updates


class SparseInstallerUpdateTests(unittest.TestCase):
    def test_optional_layer_is_identity_for_existing_recipes(self):
        source = [dict(path='A.int', file='a', sha256='0'*64)]
        result, proof = apply_resource_updates(source, {}, [], Path('.'), 2, 'toc.txt')
        self.assertEqual(result, source)
        self.assertIsNot(result[0], source[0])
        self.assertEqual(proof, [])

    def test_source_locked_disc_specific_update_and_fail_closed_guards(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); candidate = root/'candidate.int'; candidate.write_bytes(b'new')
            previous = [dict(path='A.int', file='old', sha256=digest(b'old'))]
            originals = {'A.int':dict(sha256=digest(b'original'))}
            manifest = dict(schema_version=1,kind='incremental-comparison-replacements',
                disc=2,toc_path='toc.txt',resources=[dict(path='A.int',file='candidate.int',
                before_sha256=digest(b'old'),sha256=digest(b'new'),size=3)])
            def run(m):
                path=root/'manifest.json';path.write_text(json.dumps(m),encoding='utf8')
                refs=[dict(manifest='manifest.json',sha256=digest(path.read_bytes()))]
                return apply_resource_updates(previous,originals,refs,root,2,'toc.txt')
            result, proof = run(manifest)
            self.assertEqual(result[0]['sha256'],digest(b'new'))
            self.assertEqual(proof[0]['resources'],1)
            self.assertEqual(previous[0]['sha256'],digest(b'old'))
            for key,value in [('before_sha256','0'*64),('sha256','0'*64),
                              ('file','../candidate.int'),('path','toc.txt'),('size',4)]:
                bad=copy.deepcopy(manifest);bad['resources'][0][key]=value
                with self.assertRaises(ValueError):run(bad)
            bad=copy.deepcopy(manifest);bad['disc']=1
            with self.assertRaises(ValueError):run(bad)
            bad=copy.deepcopy(manifest);bad['resources']*=2
            with self.assertRaises(ValueError):run(bad)


if __name__ == '__main__':
    unittest.main()
