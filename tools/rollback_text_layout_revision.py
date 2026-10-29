"""Hash-guarded restoration of an isolated text-layout candidate copy."""
import argparse
import json
import os
from pathlib import Path
import tempfile

from .font_binding_plan import confined_path
from .reface_font import sha


def restore(build_root, baseline_root, copy_root):
    build_root, baseline_root, copy_root = [Path(x).resolve() for x in (build_root, baseline_root, copy_root)]
    for source in (build_root, baseline_root):
        if copy_root.is_relative_to(source) or source.is_relative_to(copy_root):
            raise ValueError('rollback requires a disjoint candidate copy')
    manifest = json.loads((build_root/'manifest.json').read_bytes())
    if manifest.get('schema_version') != 1 or manifest.get('kind') != 'text-layout-revision-build':
        raise ValueError('rollback manifest mismatch')
    pending = []
    paths = set()
    for spec in manifest['resources']:
        if spec['path'].casefold() in paths:
            raise ValueError('duplicate rollback resource')
        paths.add(spec['path'].casefold())
        source = confined_path(baseline_root, spec['path']).read_bytes()
        current = confined_path(copy_root, spec['path'])
        retained_candidate = confined_path(build_root, 'candidate/'+spec['path']).read_bytes()
        if sha(source) != spec['before_sha256'] or sha(current.read_bytes()) != spec['sha256'] or sha(retained_candidate) != spec['sha256']:
            raise ValueError('rollback source/candidate identity mismatch')
        pending.append((current, source, retained_candidate))
    for path, source, _ in pending:
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as f:
                temporary = Path(f.name)
                f.write(source)
            os.replace(temporary, path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        if path.read_bytes() != source:
            raise ValueError('rollback readback mismatch')
    for spec in manifest['resources']:
        if sha(confined_path(build_root, 'candidate/'+spec['path']).read_bytes()) != spec['sha256']:
            raise ValueError('retained candidate changed during rollback')
    return dict(restored_resources=len(pending), baseline_bytes_restored=True, retained_candidate_unchanged=True)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('build-root', 'baseline-root', 'copy-root'):
        p.add_argument('--'+key, type=Path, required=True)
    a = p.parse_args(argv)
    print(json.dumps(restore(a.build_root, a.baseline_root, a.copy_root)))


if __name__ == '__main__': main()
