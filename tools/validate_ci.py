"""Single local/hosted validation entry point; every failed check remains fatal."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
STEPS = (
    ('dependencies', ('-m', 'pip', 'check')),
    ('repository', ('tools/check_repository.py',)),
    ('bytecode', ('-m', 'compileall', '-q', 'tools', 'tests')),
    ('glossary', ('tools/series_terms.py', 'render', '--check')),
    ('tests-native', ('tools/run_test_suite.py', '--temp-layout', 'native')),
    ('tests-alias', ('tools/run_test_suite.py', '--temp-layout', 'alias')),
    ('references-fetch', ('tools/series_terms.py', 'fetch')),
    ('references-check', ('tools/series_terms.py', 'check', '--with-references')),
)


def validation_commands(python, report_dir):
    for name, arguments in STEPS:
        command = [str(python), '-X', 'utf8', *arguments]
        if name.startswith('tests-'):
            command += ['--report', str(Path(report_dir) / (name + '.json'))]
        yield name, command


def validate(report_dir):
    report_dir = Path(report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8', PYTHONNOUSERSITE='1')
    rows = []
    for name, command in validation_commands(sys.executable, report_dir):
        start = time.monotonic()
        log = report_dir / (name + '.log')
        print(f'CI_CHECK {name} START', flush=True)
        try:
            with log.open('wb') as stream:
                process = subprocess.run(command, cwd=ROOT, env=env, stdout=stream,
                                         stderr=subprocess.STDOUT, timeout=900)
            code = process.returncode
        except (OSError, subprocess.TimeoutExpired) as error:
            with log.open('a', encoding='utf-8') as stream:
                stream.write('\n' + str(error) + '\n')
            code = 2
        rows.append(dict(name=name, command=command, exit_code=code,
                         elapsed_seconds=round(time.monotonic() - start, 3), log=log.name))
        print(f'CI_CHECK {name} exit={code}', flush=True)
        if code:
            print(log.read_text(encoding='utf-8', errors='replace')[-16000:], flush=True)
    versions = {}
    for name in ('Pillow', 'fonttools', 'numpy'):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    passed = all(row['exit_code'] == 0 for row in rows)
    summary = dict(schema_version=1, passed=passed, python=sys.version,
                   platform=platform.platform(), dependencies=versions, checks=rows)
    (report_dir / 'ci-results.json').write_text(
        json.dumps(summary, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(f"CI_RESULT checks={len(rows)} failed={sum(r['exit_code'] != 0 for r in rows)} "
          f"status={'PASS' if passed else 'FAIL'}", flush=True)
    return 0 if passed else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report-dir', type=Path, default=ROOT / 'build/ci')
    args = parser.parse_args(argv)
    return validate(args.report_dir)


if __name__ == '__main__':
    raise SystemExit(main())
