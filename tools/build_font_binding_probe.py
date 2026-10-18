"""Build undeployed control/geometry/inverse copies for every planned Font alias."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

try:
    from .decompress_package import decompress_copy
    from .font_binding_audit import fingerprint
    from .inspect_font_references import _tables
    from .probe_font_mapping import probe_geometry
    from .ue3_package import FormatError, LzxDecoder, parse_summary, write_report
    from .ue3_ui_styles import StyleGraph
    from .update_resource_sizes import update_sizes
except ImportError:
    from decompress_package import decompress_copy
    from font_binding_audit import fingerprint
    from inspect_font_references import _tables
    from probe_font_mapping import probe_geometry
    from ue3_package import FormatError, LzxDecoder, parse_summary, write_report
    from ue3_ui_styles import StyleGraph
    from update_resource_sizes import update_sizes


def digest(data):
    return hashlib.sha256(data).hexdigest()


def validate_plan(plan):
    if not isinstance(plan,dict) or plan.get('schema_version') != 1 or plan.get('game_rendering_verified') is not False:
        raise FormatError('probe plan requires schema1 and game_rendering_verified=false')
    sources = plan.get('sources')
    count = plan.get('required_source_count')
    if type(count) is not int or not 1 <= count <= 32 or not isinstance(sources,list) or len(sources) != count:
        raise FormatError('probe source count mismatch')
    labels, paths = set(), set()
    for source in sources:
        if not isinstance(source,dict):
            raise FormatError('source must be an object')
        label = source.get('label','')
        if (not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,47}',label)
                or label.casefold() in {'con','prn','aux','nul',*(f'com{i}' for i in range(1,10)),*(f'lpt{i}' for i in range(1,10))}
                or label.casefold() in labels):
            raise FormatError('duplicate or invalid probe source label')
        labels.add(label.casefold())
        path = source.get('path','')
        _relative(path)
        if path.casefold() in paths:
            raise FormatError('duplicate probe source path')
        paths.add(path.casefold())
        _hash(source.get('sha256'))
        if not isinstance(source.get('font_object'),str) or not source['font_object']:
            raise FormatError('font object path required')
    toc = plan.get('toc',{})
    if not isinstance(toc,dict):
        raise FormatError('TOC must be an object')
    _relative(toc.get('path',''));_hash(toc.get('sha256'))
    if toc['path'].casefold() in paths:
        raise FormatError('TOC cannot alias a source package')
    _hash(plan.get('expected_semantic_sha256'))
    if not re.fullmatch('[0-9a-f]{32}',plan.get('expected_namespace_guid','')) or plan['expected_namespace_guid'] == '0'*32:
        raise FormatError('nonzero namespace GUID required')
    if not isinstance(plan.get('canonical_font_path'),str) or not plan['canonical_font_path']:
        raise FormatError('canonical font identity required')
    for field in ('codepoint','expected_glyph','target_glyph'):
        if type(plan.get(field)) is not int or not 0 <= plan[field] <= 65535:
            raise FormatError('invalid '+field)
    if plan['expected_glyph'] == plan['target_glyph']:
        raise FormatError('probe donor must differ')
    return sources


def _hash(value):
    if not isinstance(value,str) or not re.fullmatch('[0-9a-f]{64}',value):
        raise FormatError('expected lowercase SHA256')


def _relative(value):
    if (not isinstance(value,str) or not value or '\\' in value or ':' in value
            or value.startswith('/') or any(p in ('','.','..') for p in value.split('/'))):
        raise FormatError('expected confined slash-separated relative resource path')
    return value


def _read(root, relative, expected):
    target = (root / _relative(relative)).resolve()
    if not target.is_relative_to(root):
        raise FormatError('resource path escapes selected game root')
    data = target.read_bytes()
    if digest(data) != expected:
        raise FormatError('source SHA256 mismatch: '+relative)
    return data, target


def build(plan, game_root, output_root, decoder=None):
    sources = validate_plan(plan)
    if Path(output_root).exists() or Path(output_root).is_symlink():
        raise FormatError('probe output directory must be new')
    game_root, output_root = Path(game_root).resolve(), Path(output_root).resolve()
    if output_root.is_relative_to(game_root):
        raise FormatError('probe outputs must be outside the selected game root')
    contexts, controls, originals, source_paths = {}, {}, {}, []
    toc, toc_path = _read(game_root,plan['toc']['path'],plan['toc']['sha256'])
    source_paths.append((toc_path,plan['toc']['sha256']))
    for source in sources:
        label = source['label'].casefold()
        raw, path = _read(game_root,source['path'],source['sha256'])
        source_paths.append((path,source['sha256']))
        summary = parse_summary(raw,len(raw))
        control = decompress_copy(raw,source['sha256'],decoder)[0] if summary['compression_flags'] else raw
        logical, tables = _tables(control,digest(control),None)
        if logical != control:
            raise FormatError('control must be physically uncompressed')
        contexts[label] = dict(logical=logical,tables=tables,sha256=digest(control),package_guid=summary['guid'])
        controls[label], originals[label] = control, raw
    graph = StyleGraph(contexts)
    variants, changed = {}, []
    for source in sources:
        label = source['label'].casefold()
        matches = graph.paths[label].get(source['font_object'].casefold(),[])
        if len(matches) != 1:
            raise FormatError('font object missing or ambiguous')
        node = label,matches[0]
        before = fingerprint(graph,node,decoder)
        if (before['identity']['canonical_path'] != plan['canonical_font_path'].casefold()
                or before['identity']['namespace_guid'] != plan['expected_namespace_guid']
                or before['semantic_sha256'] != plan['expected_semantic_sha256']):
            raise FormatError('font namespace/GUID/semantic baseline mismatch: '+label)
        candidate, report = probe_geometry(controls[label],digest(controls[label]),source['font_object'],
                                          plan['codepoint'],plan['expected_glyph'],plan['target_glyph'])
        logical, tables = _tables(candidate,digest(candidate),None)
        updated = dict(contexts);updated[label] = dict(contexts[label],logical=logical,tables=tables,sha256=digest(candidate))
        after = fingerprint(StyleGraph(updated),node,decoder)
        if before['atlases'] != after['atlases'] or before['semantic_sha256'] == after['semantic_sha256']:
            raise FormatError('geometry probe must change only glyph semantics, not atlas data')
        if len(originals[label]) != len(candidate):
            changed.append(dict(path=source['path'],expected_size=len(originals[label]),new_size=len(candidate)))
        inverse = bytearray(candidate)
        for field in reversed(report['fields']):
            at = field['offset'];old,new = bytes.fromhex(field['original_hex']),bytes.fromhex(field['modified_hex'])
            if inverse[at:at+len(new)] != new:
                raise FormatError('inverse field verification failed')
            inverse[at:at+len(new)] = old
        if bytes(inverse) != controls[label]:
            raise FormatError('inverse did not reproduce entire control')
        variants[label] = dict(candidate=candidate,restored=bytes(inverse),report=report,before=before,after=after)
    if len({v['after']['semantic_sha256'] for v in variants.values()}) != 1:
        raise FormatError('planned font aliases diverged after probing')
    toc_output = update_sizes(toc,plan['toc']['sha256'],changed) if changed else toc
    inverse_changes = [dict(path=c['path'],expected_size=c['new_size'],new_size=c['expected_size']) for c in changed]
    if (update_sizes(toc_output,digest(toc_output),inverse_changes) if changed else toc_output) != toc:
        raise FormatError('TOC inverse did not reproduce original')
    # No output is published until every source and variant has validated.
    output_root.mkdir(parents=True,exist_ok=False)
    rows = []
    for source in sources:
        label = source['label'].casefold();v = variants[label]
        files = {}
        for kind,data in [('controls',controls[label]),('candidates',v['candidate']),('inverse-check',v['restored'])]:
            path = output_root/kind/(label+'.xxx');path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('xb') as stream:stream.write(data)
            if path.read_bytes() != data:
                raise FormatError('package output reopening mismatch')
            files[kind] = dict(path=str(path),sha256=digest(data),size=len(data))
        report_path = output_root/'reports'/(label+'.json')
        write_report(report_path,v['report'])
        if json.loads(report_path.read_text(encoding='utf-8')) != v['report']:
            raise FormatError('geometry report reopening mismatch')
        rows.append(dict(label=label,source_path=source['path'],source_sha256=source['sha256'],files=files,
                         semantic_before=v['before']['semantic_sha256'],semantic_after=v['after']['semantic_sha256'],
                         atlas_hashes_unchanged=True,inverse_byte_identical=True))
    toc_target = output_root/'Xbox360TOC.txt'
    with toc_target.open('xb') as stream:stream.write(toc_output)
    if toc_target.read_bytes() != toc_output:
        raise FormatError('TOC output reopening mismatch')
    for path,expected in source_paths:
        if digest(path.read_bytes()) != expected:
            raise FormatError('original changed during build')
    manifest = dict(schema_version=1,mode='all-planned-aliases-duplicated-geometry',
        canonical_plan_sha256=digest(json.dumps(plan,sort_keys=True,separators=(',',':')).encode()),
        canonical_font_path=plan['canonical_font_path'],sources=rows,toc_changes=changed,
        toc=dict(path=str(toc_target),sha256=digest(toc_output),inverse_byte_identical=True),
        original_hashes_rechecked=True,game_rendering_verified=False,deployment_performed=False)
    write_report(output_root/'manifest.json',manifest)
    if json.loads((output_root/'manifest.json').read_text(encoding='utf-8')) != manifest:
        raise FormatError('manifest reopening mismatch')
    return manifest


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan',type=Path,required=True);p.add_argument('--game-root',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--lzx-library',type=Path)
    a=p.parse_args(argv)
    try:
        if a.output_dir.exists() or a.output_dir.is_symlink():
            raise FormatError('probe output directory must be new')
        plan=json.loads(a.plan.read_text(encoding='utf-8'))
        r=build(plan,a.game_root,a.output_dir,LzxDecoder(a.lzx_library) if a.lzx_library else None)
        print(json.dumps(dict(sources=len(r['sources']),manifest=str(a.output_dir.resolve()/'manifest.json'),
            inverse_byte_identical=True,deployment_performed=False),sort_keys=True));return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print('ERROR: '+str(exc));return 2


if __name__=='__main__':raise SystemExit(main())
