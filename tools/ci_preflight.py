"""Validate the exact pushed commit in a source-only snapshot and fresh venv.

No game files, developer build caches, unstaged edits, or user site packages are
copied. Reports and the snapshot stay in build/ci-preflight for diagnosis.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tarfile
import uuid

ROOT = Path(__file__).resolve().parents[1]


def isolated_environment():
    env = os.environ.copy()
    # Git explicitly exports repository-local variables when invoking hooks.
    # Never let them redirect a snapshot's `git add` into the user's index.
    names = subprocess.check_output(['git', 'rev-parse', '--local-env-vars'],
                                    text=True, encoding='utf-8').splitlines()
    for name in [*names, 'PYTHONPATH', 'PYTHONHOME', 'VIRTUAL_ENV', '__PYVENV_LAUNCHER__']:
        env.pop(name, None)
    env.update(PYTHONUTF8='1', PYTHONIOENCODING='utf-8', PYTHONNOUSERSITE='1',
               PIP_DISABLE_PIP_VERSION_CHECK='1')
    return env


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], env=isolated_environment())


def extract_source(raw, destination):
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=False)
    identities = {}
    seen = set()
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as archive:
        for member in archive:
            path = PurePosixPath(member.name)
            if (path.is_absolute() or '..' in path.parts or '\\' in member.name
                    or ':' in member.name or '.git' in path.parts
                    or not (member.isfile() or member.isdir())):
                raise ValueError('unsupported source archive member: ' + member.name)
            target = destination.joinpath(*path.parts)
            if not target.resolve().is_relative_to(destination):
                raise ValueError('source archive escaped snapshot')
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if member.name.casefold() in seen:
                raise ValueError('duplicate source archive path')
            seen.add(member.name.casefold())
            data = archive.extractfile(member).read()
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream:
                stream.write(data)
            target.chmod(member.mode & 0o777)
            identities[member.name] = hashlib.sha256(data).hexdigest()
    return identities


def export_revision(root, revision, destination):
    commit = git(root, 'rev-parse', '--verify', revision + '^{commit}').decode().strip()
    raw = git(root, '-c', 'core.autocrlf=false', '-c', 'core.eol=lf',
              'archive', '--format=tar', commit)
    identities = extract_source(raw, destination)
    # archive attributes must not silently exclude/substitute checkout bytes.
    tree = git(root, 'ls-tree', '-r', '-z', '--full-tree', commit)
    expected = {}
    for row in tree.split(b'\0'):
        if not row:
            continue
        metadata, name = row.split(b'\t', 1)
        mode, kind, oid = metadata.decode().split()
        name = name.decode('utf-8')
        if kind != 'blob' or mode not in ('100644', '100755'):
            raise ValueError('unsupported source tree entry: ' + name)
        expected[name] = oid
    if expected.keys() != identities.keys():
        raise ValueError('source archive differs from committed file inventory')
    for name, oid in expected.items():
        data = (Path(destination) / name).read_bytes()
        digest = hashlib.new('sha1' if len(oid) == 40 else 'sha256',
                             f'blob {len(data)}\0'.encode() + data).hexdigest()
        if digest != oid:
            raise ValueError('source archive differs from committed bytes: ' + name)
    git(destination, 'init', '-q')
    git(destination, 'add', '--all')
    return commit, identities


def check_revision(root, revision, output):
    output = Path(output).absolute()
    if output.exists() or output.is_symlink() or output.is_junction():
        raise ValueError('preflight output must be a new directory')
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    source = output / 'source'
    commit, identities = export_revision(root, revision, source)
    (output / 'source-sha256.json').write_text(json.dumps(identities, indent=2) + '\n', encoding='utf-8')
    if not (source / 'tools/validate_ci.py').is_file():
        raise ValueError('revision does not contain the shared CI entry point')
    env = isolated_environment()
    venv = output / 'venv'
    python = venv / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    setup = [
        ('venv', [sys.executable, '-m', 'venv', str(venv)]),
        ('install', [str(python), '-m', 'pip', 'install', '-r', 'requirements-font.txt']),
    ]
    result = dict(schema_version=1, commit=commit, passed=False,
                  interpreter=sys.executable, python=sys.version,
                  source_files=len(identities), setup=[], source_unchanged=False)
    code = 0
    try:
        for name, command in setup:
            print(f'PREFLIGHT {commit[:12]} {name}', flush=True)
            with (output / (name + '.log')).open('wb') as log:
                p = subprocess.run(command, cwd=source, env=env, stdout=log,
                                   stderr=subprocess.STDOUT, timeout=600)
            result['setup'].append(dict(name=name, command=command, exit_code=p.returncode))
            if p.returncode:
                print((output / (name + '.log')).read_text(encoding='utf-8', errors='replace')[-4000:])
                code = p.returncode
                break
        if not code:
            command = [str(python), '-X', 'utf8', 'tools/validate_ci.py',
                       '--report-dir', str(output / 'checks')]
            p = subprocess.run(command, cwd=source, env=env, timeout=2400)
            code = p.returncode
            result['validation_command'] = command
        changed = [name for name, digest in identities.items()
                   if not (source / name).is_file()
                   or hashlib.sha256((source / name).read_bytes()).hexdigest() != digest]
        result.update(source_unchanged=not changed, changed_source_files=changed)
        if changed:
            code = 1
        result.update(exit_code=code, passed=code == 0)
    except (OSError, subprocess.TimeoutExpired) as error:
        code = 2
        result.update(exit_code=code, error=str(error))
    finally:
        (output / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(f"PREFLIGHT commit={commit} status={'PASS' if code == 0 else 'FAIL'} report={output}", flush=True)
    return code


def pushed_revisions(data):
    revisions = []
    for line in data.splitlines():
        fields = line.split()
        if len(fields) != 4 or not all(re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', fields[i]) for i in (1, 3)):
            raise ValueError('invalid Git pre-push input')
        local = fields[1]
        if set(local) != {'0'} and local not in revisions:
            revisions.append(local)
    return revisions


def install_hook(root):
    # Do not change a global/custom hooksPath or overwrite another hook.
    custom = subprocess.run(['git', '-C', str(root), 'config', '--get', 'core.hooksPath'],
                            env=isolated_environment(), capture_output=True, text=True)
    if custom.returncode == 0:
        raise ValueError('custom core.hooksPath already configured; integrate the versioned hook explicitly')
    hook = Path(git(root, 'rev-parse', '--git-path', 'hooks/pre-push').decode().strip())
    if not hook.is_absolute():
        hook = Path(root) / hook
    data = (Path(root) / '.githooks/pre-push').read_bytes()
    if hook.is_symlink() or (hook.exists() and hook.read_bytes() != data):
        raise ValueError('existing pre-push hook differs; preserved unchanged')
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_bytes(data)
    hook.chmod(0o755)
    print('PREFLIGHT_HOOK installed=' + str(hook.resolve()))
    return hook


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('install-hook')
    check = commands.add_parser('check')
    check.add_argument('--revision', default='HEAD')
    check.add_argument('--output', type=Path)
    commands.add_parser('push')
    args = parser.parse_args(argv)
    try:
        if args.command == 'install-hook':
            install_hook(ROOT)
            return 0
        revisions = pushed_revisions(sys.stdin.read()) if args.command == 'push' else [args.revision]
        for revision in revisions:
            output = (getattr(args, 'output', None) or ROOT / 'build/ci-preflight' /
                      (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:8]))
            code = check_revision(ROOT, revision, output)
            if code:
                return code
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print('PREFLIGHT_ERROR ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
