"""Run the same source tests with native or deliberately aliased temp paths.

The alias is a real, same-file path, not a mocked Path.resolve result. Cleanup
always belongs to the original TemporaryDirectory, never to the alias spelling.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager, nullcontext
import json
from pathlib import Path
import platform
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def aliased_temporary_directories():
    original = tempfile.TemporaryDirectory
    metrics = {'aliased_directories': 0}

    class AliasedDirectory:
        def __init__(self, *args, **kwargs):
            self._directory = original(*args, **kwargs)
            physical = Path(self._directory.name)
            self.name = str(physical / '..' / physical.name)
            if not Path(self.name).samefile(physical):
                self._directory.cleanup()
                raise RuntimeError('temporary directory alias identity mismatch')
            metrics['aliased_directories'] += 1

        def __enter__(self):
            return self.name

        def __exit__(self, *args):
            return self._directory.__exit__(*args)

        def cleanup(self):
            return self._directory.cleanup()

        def __getattr__(self, name):
            return getattr(self._directory, name)

    tempfile.TemporaryDirectory = AliasedDirectory
    try:
        yield metrics
    finally:
        tempfile.TemporaryDirectory = original


def run_tests(layout='native', pattern='test_*.py', report=None):
    for path in (ROOT, ROOT / 'tests'):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    context = (aliased_temporary_directories() if layout == 'alias'
               else nullcontext({'aliased_directories': 0}))
    with context as metrics:
        suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern=pattern)
        result = unittest.TextTestRunner(verbosity=1, buffer=True).run(suite)
    passed = result.wasSuccessful() and result.testsRun > 0
    summary = dict(schema_version=1, passed=passed, layout=layout, pattern=pattern,
                   tests=result.testsRun, failures=len(result.failures),
                   errors=len(result.errors), skipped=len(result.skipped),
                   failed_tests=[t.id() for t, _ in result.failures + result.errors],
                   skip_reasons=[{'test': t.id(), 'reason': reason}
                                 for t, reason in result.skipped],
                   python=sys.version, platform=platform.platform(), **metrics)
    if report:
        report = Path(report)
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(f"TEST_SUITE layout={layout} tests={result.testsRun} "
          f"failures={len(result.failures)} errors={len(result.errors)} "
          f"skipped={len(result.skipped)} status={'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--temp-layout', choices=['native', 'alias'], default='native')
    parser.add_argument('--pattern', default='test_*.py')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args(argv)
    return run_tests(args.temp_layout, args.pattern, args.report)


if __name__ == '__main__':
    raise SystemExit(main())
