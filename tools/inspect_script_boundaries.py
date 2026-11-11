"""Read hash-locked 446/25 Function source-byte boundaries without execution."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from .inspect_font_references import _tables
    from .ue3_package import FormatError, LzxDecoder, parse_summary, write_report
    from .ue3_ui_styles import StyleGraph
    from .ue3_script_boundaries import native_declarations, function_boundary_report
except ImportError:
    from inspect_font_references import _tables
    from ue3_package import FormatError, LzxDecoder, parse_summary, write_report
    from ue3_ui_styles import StyleGraph
    from ue3_script_boundaries import native_declarations, function_boundary_report


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('package', type=Path)
    p.add_argument('--sha256', required=True)
    p.add_argument('--object', action='append', required=True, help='exact Function export path; repeat for a bounded inventory')
    p.add_argument('--reference-package', nargs=3, action='append', default=[], metavar=('LABEL', 'PATH', 'SHA256'))
    p.add_argument('--lzx-library', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(argv)
    try:
        inputs = [(a.package.stem, a.package, a.sha256)] + [(k, Path(f), h) for k, f, h in a.reference_package]
        paths = [path.resolve() for _, path, _ in inputs] + ([a.lzx_library.resolve()] if a.lzx_library else [])
        if a.output.exists() or a.output.is_symlink() or a.output.resolve() in paths:
            raise FormatError('script report must be new and distinct from all inputs')
        labels = [key.casefold() for key, _, _ in inputs]
        if len(labels) != len(set(labels)):
            raise FormatError('duplicate package label')
        snapshots = []
        # Verify every artifact before loading a native decompressor.
        for key, path, sha in inputs:
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != sha:
                raise FormatError('package SHA256 mismatch: '+key)
            summary = parse_summary(raw, len(raw))
            if summary['byte_order'] != 'big' or summary['version'] != 446 or summary['licensee_version'] != 25:
                raise FormatError('script reader requires big-endian 446/25')
            snapshots.append((key.casefold(), path, sha, raw))
        decoder = LzxDecoder(a.lzx_library) if a.lzx_library else None
        packages = {}
        for key, path, sha, raw in snapshots:
            logical, tables = _tables(raw, sha, decoder)
            packages[key] = dict(logical=logical, tables=tables, sha256=sha)
        graph = StyleGraph(packages)
        native = native_declarations(graph)
        results, errors = [], []
        for name in a.object:
            try:
                matches = graph.paths[labels[0]].get(name.casefold(), [])
                if len(matches) != 1:
                    raise FormatError('missing/ambiguous Function definition')
                results.append(function_boundary_report(graph, (labels[0], matches[0]), native['bindings']))
            except (ValueError, KeyError) as exc:
                errors.append(dict(object=name, reason=str(exc)))
        report = dict(schema_version=1, profile='446/25-big-function-source-boundaries',
                      source_sha256=a.sha256, selected_objects=a.object,
                      reference_sources=[dict(package=k, sha256=h) for k, _, h, _ in snapshots[1:]],
                      functions=results, unparsed=errors,
                      native_declarations={k:len(v) for k, v in native.items()},
                      runtime_execution_observed=False, game_rendering_verified=False)
        write_report(a.output, report)
        if json.loads(a.output.read_text(encoding='utf8')) != report:
            raise FormatError('script report reopening mismatch')
        if any(path.read_bytes() != raw for _, path, _, raw in snapshots):
            raise FormatError('input changed during inspection')
        print(json.dumps(dict(functions=len(results), unparsed=len(errors),
                              game_rendering_verified=False), sort_keys=True))
        return int(bool(errors))
    except (OSError, ValueError, KeyError) as exc:
        print('ERROR: '+str(exc))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
