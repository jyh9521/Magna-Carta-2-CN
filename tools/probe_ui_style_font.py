"""Create a same-size, reversible UIStyle StyleFont reference probe, never deploy it."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

try:
    from .inspect_font_references import _tables
    from .ue3_package import FormatError, LzxDecoder, parse_summary, write_report
    from .ue3_ui_styles import StyleGraph
except ImportError:
    from inspect_font_references import _tables
    from ue3_package import FormatError, LzxDecoder, parse_summary, write_report
    from ue3_ui_styles import StyleGraph


def patch_graph(data, graph, package, style_path, expected_font, target_font):
    """Only accepts a graph backed by the exact uncompressed data buffer."""
    package = package.casefold()
    if graph.packages[package]['logical'] != data:
        raise FormatError('patch graph must use the exact physical uncompressed buffer')

    def find(path):
        indices = graph.paths[package].get(path.casefold(), [])
        if len(indices) != 1:
            raise FormatError('expected one selected object: ' + path)
        return package, indices[0]

    style, old_font, new_font = map(find, (style_path, expected_font, target_font))
    for font in (old_font, new_font):
        if graph.export(*font)['class_path'].rsplit('.', 1)[-1] not in ('Font', 'MultiFont'):
            raise FormatError('selected font has wrong class')
    if old_font == new_font:
        raise FormatError('font probe must change the reference')
    changes, seen = [], set()
    for state in graph.state_map(style):
        node = state['data']
        if 'engine.uistyle_combo' in graph.class_chain(node):
            prop = graph.one(node, ['TextStyle', 'CustomStyleData'])
            node = graph.reference(node[0], prop['reference'])
        if node is None or 'engine.uistyle_text' not in graph.class_chain(node):
            raise FormatError('state has no direct text style data')
        prop = graph.one(node, ['StyleFont'])
        if graph.reference(node[0], prop['reference']) != old_font:
            raise FormatError('StyleFont differs from the expected original font')
        if node[0] != package:
            raise FormatError('StyleFont field belongs to another package')
        offset = prop['logical_package_offset']
        if offset in seen:
            continue
        seen.add(offset)
        before, after = struct.pack('>i', prop['reference']), struct.pack('>i', new_font[1])
        if not 0 <= offset <= len(data) - 4 or data[offset:offset + 4] != before:
            raise FormatError('original StyleFont field bytes mismatch')
        changes.append(dict(offset=offset, old_hex=before.hex(), new_hex=after.hex(),
                            owner=graph.describe(node), field='StyleFont'))
    if not changes:
        raise FormatError('style has no patchable state font fields')
    output = bytearray(data)
    for change in changes:
        output[change['offset']:change['offset'] + 4] = bytes.fromhex(change['new_hex'])
    output = bytes(output)
    contexts = dict(graph.packages)
    contexts[package] = dict(contexts[package], logical=output, sha256=hashlib.sha256(output).hexdigest())
    check = StyleGraph(contexts)
    for change in changes:
        node = package, change['owner']['object_index']
        if check.one(node, ['StyleFont'])['reference'] != new_font[1]:
            raise FormatError('patched StyleFont failed structural readback')
    restored = bytearray(output)
    for change in reversed(changes):
        restored[change['offset']:change['offset'] + 4] = bytes.fromhex(change['old_hex'])
    if bytes(restored) != data:
        raise FormatError('inverse probe is not byte-identical')
    return output, dict(schema_version=1, source_sha256=hashlib.sha256(data).hexdigest(),
        output_sha256=hashlib.sha256(output).hexdigest(), size=len(data), style=graph.describe(style),
        expected_font=graph.describe(old_font), target_font=graph.describe(new_font), changes=changes,
        inverse_byte_identical=True, game_rendering_verified=False, deployment_performed=False)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('package', type=Path);p.add_argument('--sha256', required=True)
    p.add_argument('--style-object', required=True);p.add_argument('--expected-font', required=True)
    p.add_argument('--target-font', required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True);p.add_argument('--lzx-library',type=Path)
    p.add_argument('--reference-package',nargs=3,action='append',default=[],metavar=('LABEL','PATH','SHA256'))
    a = p.parse_args(argv)
    try:
        outputs = [a.output.resolve(), a.report.resolve()]
        inputs = [a.package.resolve()] + [Path(row[1]).resolve() for row in a.reference_package]
        if a.lzx_library:inputs.append(a.lzx_library.resolve())
        if len(set(outputs)) != 2 or set(outputs).intersection(inputs):
            raise FormatError('probe outputs must differ from all inputs and each other')
        if any(path.exists() or path.is_symlink() for path in (a.output, a.report)):
            raise FormatError('probe outputs must be new')
        data = a.package.read_bytes()
        if hashlib.sha256(data).hexdigest() != a.sha256.lower():
            raise FormatError('package SHA256 mismatch')
        summary = parse_summary(data, len(data))
        if summary['compression_flags'] or summary['compressed_chunks']:
            raise FormatError('probe requires a separately verified uncompressed package copy')
        logical, tables = _tables(data, a.sha256.lower(), None)
        primary = a.package.stem.casefold()
        contexts = {primary:dict(logical=logical,tables=tables,sha256=a.sha256.lower())}
        decoder = LzxDecoder(a.lzx_library) if a.lzx_library else None
        for label, path, digest in a.reference_package:
            if label.casefold() in contexts:
                raise FormatError('duplicate package label')
            raw = Path(path).read_bytes();logical, tables = _tables(raw,digest.lower(),decoder)
            contexts[label.casefold()] = dict(logical=logical,tables=tables,sha256=digest.lower())
        output, report = patch_graph(data,StyleGraph(contexts),primary,a.style_object,a.expected_font,a.target_font)
        _, reparsed_tables = _tables(output,report['output_sha256'],None)
        if reparsed_tables != contexts[primary]['tables']:
            raise FormatError('probe changed package object tables')
        a.output.parent.mkdir(parents=True,exist_ok=True)
        with a.output.open('xb') as stream:stream.write(output)
        if a.output.read_bytes() != output:
            raise FormatError('probe package reopening mismatch')
        write_report(a.report,report)
        if json.loads(a.report.read_text(encoding='utf-8')) != report:
            raise FormatError('probe report reopening mismatch')
        print(json.dumps(dict(changed_fields=len(report['changes']),size=len(output),
            source_sha256=report['source_sha256'],output_sha256=report['output_sha256'],
            inverse_byte_identical=True,deployment_performed=False),sort_keys=True))
        return 0
    except (OSError,ValueError,KeyError) as exc:
        print('ERROR: '+str(exc));return 2


if __name__=='__main__':raise SystemExit(main())
