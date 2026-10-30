"""Self-contained desktop bootstrap; only its owned _MEI directory is transient.

PyInstaller's parent process removes that directory after this process exits.
The GUI is waited for, so its tools and deltas remain available throughout work.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys


def sha_file(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify_payload(root, expected):
    root = Path(root).resolve(strict=True)
    manifest = root / 'release-files.json'
    if manifest.is_symlink() or sha_file(manifest) != expected:
        raise ValueError('embedded release identity mismatch')
    data = json.loads(manifest.read_bytes())
    if data.get('schema') != 1 or not data.get('files'):
        raise ValueError('invalid release inventory')
    names = set()
    for name, identity in data['files'].items():
        rel = PurePosixPath(name)
        if (rel.is_absolute() or not rel.parts or any(p in ('..', '.') for p in rel.parts)
                or rel.as_posix() != name or ':' in name or '\\' in name
                or name.casefold() in names):
            raise ValueError('invalid or duplicate release member')
        names.add(name.casefold())
        path = root.joinpath(*rel.parts)
        if (any(part.is_symlink() for part in [path, *path.parents] if part != root.parent)
                or not path.is_file() or not path.resolve().is_relative_to(root)
                or path.stat().st_size != identity['size'] or sha_file(path) != identity['sha256']):
            raise ValueError('release member mismatch: ' + name)
    actual = {p.relative_to(root).as_posix().casefold() for p in root.rglob('*') if p.is_file()}
    if actual != names | {'release-files.json'}:
        raise ValueError('unexpected release member')
    return data


def extract_payload(root, destination, expected):
    verify_payload(root, expected)
    destination = Path(destination).absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError('extraction destination must be new')
    shutil.copytree(root, destination)
    return verify_payload(destination, expected)


def child_environment():
    env = os.environ.copy()
    # The frozen backend is a different PyInstaller executable, not a worker of
    # this onefile process. Never pass the outer runtime directory as its home.
    env['PYINSTALLER_RESET_ENVIRONMENT'] = '1'
    return env


def run(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument('--verify-only', action='store_true')
    actions.add_argument('--extract', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args(argv)
    from singlefile_release import PAYLOAD_SHA256
    root = Path(sys._MEIPASS) / 'payload'
    inventory = verify_payload(root, PAYLOAD_SHA256)
    if os.name == 'nt':
        import ctypes
        ctypes.windll.kernel32.SetDllDirectoryW(None)
    result = dict(status='PASS', version=inventory['version'], files=len(inventory['files']),
                  manifest_sha256=inventory['manifest_sha256'], payload_sha256=PAYLOAD_SHA256,
                  temporary_root=str(root.parent), game_started=False)
    if args.extract:
        extract_payload(root, args.extract, PAYLOAD_SHA256)
        result['extracted'] = str(args.extract.absolute())
    elif args.verify_only:
        backend = subprocess.run([str(root / 'backend/mc2-patch.exe'), '--info'],
                                 capture_output=True, env=child_environment(), timeout=120,
                                 creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if backend.returncode:
            raise ValueError('embedded backend self-test failed: ' + backend.stderr.decode('utf-8', 'replace'))
        info = json.loads(backend.stdout)
        if info['manifest_sha256'] != inventory['manifest_sha256']:
            raise ValueError('embedded backend identity mismatch')
        result['backend'] = info
    else:
        return subprocess.call([str(root / 'MC2Installer.exe')], cwd=root, env=child_environment())
    if args.report:
        with args.report.open('x', encoding='utf-8') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    elif sys.stdout is not None:
        print(json.dumps(result, ensure_ascii=False))
    return 0


def main():
    try:
        return run()
    except Exception as error:
        if '--report' in sys.argv:
            report = Path(sys.argv[sys.argv.index('--report') + 1])
            if not report.exists():
                report.write_text(json.dumps(dict(status='FAIL', error=str(error)), ensure_ascii=False), encoding='utf-8')
        if len(sys.argv) == 1 and os.name == 'nt':
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, str(error), '启动失败', 0x10)
        elif sys.stderr is not None:
            print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
