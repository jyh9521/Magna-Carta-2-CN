"""Assemble a verified font/text/TOC candidate tree, never install or run it."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

try:
    from .audit_text_font_coverage import audit
    from .build_coalesced import rebuild
    from .build_font_supplement import context, select_font, restore_copy, save_bytes, save_report, validate_plan as validate_font_plan
    from .font_binding_audit import fingerprint
    from .font_binding_plan import digest, _hash, _relative, _read, read_locked_json
    from .supplement_font import validate_plan as validate_glyph_plan
    from .ue3_package import FormatError, LzxDecoder
    from .ue3_ui_styles import StyleGraph
    from .update_resource_sizes import update_sizes
except ImportError:
    from audit_text_font_coverage import audit
    from build_coalesced import rebuild
    from build_font_supplement import context, select_font, restore_copy, save_bytes, save_report, validate_plan as validate_font_plan
    from font_binding_audit import fingerprint
    from font_binding_plan import digest, _hash, _relative, _read, read_locked_json
    from supplement_font import validate_plan as validate_glyph_plan
    from ue3_package import FormatError, LzxDecoder
    from ue3_ui_styles import StyleGraph
    from update_resource_sizes import update_sizes


def validate_plan(plan):
    if (not isinstance(plan,dict) or type(plan.get('schema_version')) is not int or plan['schema_version'] != 1
            or plan.get('kind') != 'offline-locale-candidate' or plan.get('game_rendering_verified') is not False):
        raise FormatError('candidate plan requires schema1, offline kind and unverified rendering')
    for field in ('font_plan','text_plan'):
        ref = plan.get(field)
        if not isinstance(ref,dict): raise FormatError('missing '+field+' reference')
        _relative(ref.get('path')); _hash(ref.get('sha256'))
    _relative(plan.get('text_resource'))
    _hash(plan.get('expected_text_sha256')); _hash(plan.get('expected_toc_sha256'))
    candidates = plan.get('font_candidates')
    if not isinstance(candidates,list) or not 1 <= len(candidates) <= 32:
        raise FormatError('candidate font hash list required')
    expected = {}
    for row in candidates:
        if (not isinstance(row,dict) or not isinstance(row.get('label'),str)
                or not re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,47}',row['label'])
                or row['label'].casefold() in expected):
            raise FormatError('invalid or duplicate candidate font label')
        _hash(row.get('sha256')); expected[row['label'].casefold()] = row['sha256']
    return expected


def check_inputs(inputs):
    for path,sha in inputs:
        _hash(sha)
        if digest(Path(path).read_bytes()) != sha:
            raise FormatError('candidate dependency changed: '+str(path))


def build(plan, game_root, project_root, font_bundle, output_root, decoder=None, extra_inputs=()):
    expected = validate_plan(plan)
    game_root, project_root, font_bundle = (Path(p).resolve() for p in (game_root,project_root,font_bundle))
    output_root = Path(output_root)
    if output_root.exists() or output_root.is_symlink():
        raise FormatError('candidate output directory must be new')
    output_root = output_root.resolve()
    if output_root.is_relative_to(game_root) or output_root.is_relative_to(font_bundle):
        raise FormatError('candidate output must be outside original and font input roots')
    font_plan, font_path, font_raw = read_locked_json(project_root,plan['font_plan'])
    text_plan, text_path, text_raw = read_locked_json(project_root,plan['text_plan'])
    glyph_plan, glyph_path, glyph_raw = read_locked_json(project_root,font_plan.get('supplement'))
    sources = validate_font_plan(font_plan); validate_glyph_plan(glyph_plan)
    if set(expected) != {s['label'].casefold() for s in sources}:
        raise FormatError('candidate hashes must cover every planned font exactly')
    text_resource = plan['text_resource']
    if text_plan.get('resource') != text_resource:
        raise FormatError('text resource identity does not match candidate path')
    reserved = {s['path'].casefold() for s in sources} | {font_plan['toc']['path'].casefold()}
    if text_resource.casefold() in reserved:
        raise FormatError('text resource aliases Font or TOC resource')
    inputs = list(extra_inputs) + [(font_path,digest(font_raw)),(text_path,digest(text_raw)),(glyph_path,digest(glyph_raw))]
    check_inputs(inputs)
    toc, toc_path = _read(game_root,font_plan['toc']['path'],font_plan['toc']['sha256'])
    _hash(text_plan.get('input_sha256'))
    text, original_text_path = _read(game_root,text_resource,text_plan['input_sha256'])
    inputs.extend([(toc_path,digest(toc)),(original_text_path,digest(text))])
    original_contexts, candidate_contexts, resources, font_inputs = {}, {}, [], []
    for source in sources:
        label = source['label'].casefold()
        original, path = _read(game_root,source['path'],source['sha256'])
        # Derive filenames from the validated plan. Never trust an upstream
        # manifest's file paths, success booleans, omissions or byte hashes.
        candidate, candidate_path = _read(font_bundle,'candidates/'+label+'.xxx',expected[label])
        inputs.extend([(path,source['sha256']),(candidate_path,expected[label])])
        original_contexts[label], candidate_contexts[label] = context(original,decoder), context(candidate,decoder)
        resources.append(dict(path=source['path'],kind='font',original=original,candidate=candidate))
        font_inputs.append(dict(label=source['label'],data=candidate,sha256=expected[label],font_object=source['font_object']))
    before_graph, after_graph = StyleGraph(original_contexts), StyleGraph(candidate_contexts)
    font_reports = []
    for source in sources:
        before = fingerprint(before_graph,select_font(before_graph,source,font_plan),decoder)
        after = fingerprint(after_graph,select_font(after_graph,source,font_plan),decoder)
        if (before['semantic_sha256'] != font_plan['expected_semantic_sha256']
                or after['semantic_sha256'] != font_plan['expected_supplement_semantic_sha256']):
            raise FormatError('candidate Font semantic baseline/output mismatch')
        font_reports.append(dict(label=source['label'],original=before,candidate=after))
    coverage = audit(text,text_plan,font_inputs,decoder)
    if not coverage['all_supplied_fonts_cover_literals']:
        raise FormatError('candidate text is not covered by every supplied Font')
    candidate_text = rebuild(text,text_plan)
    if digest(candidate_text) != plan['expected_text_sha256']:
        raise FormatError('candidate text output hash mismatch')
    resources.append(dict(path=text_resource,kind='text',original=text,candidate=candidate_text))
    changes = [dict(path=r['path'],expected_size=len(r['original']),new_size=len(r['candidate']))
               for r in resources if len(r['original']) != len(r['candidate'])]
    candidate_toc = update_sizes(toc,digest(toc),changes) if changes else toc
    reverse = [dict(path=c['path'],expected_size=c['new_size'],new_size=c['expected_size']) for c in changes]
    if ((update_sizes(candidate_toc,digest(candidate_toc),reverse) if reverse else candidate_toc) != toc
            or digest(candidate_toc) != plan['expected_toc_sha256']):
        raise FormatError('candidate TOC output/inverse mismatch')
    resources.append(dict(path=font_plan['toc']['path'],kind='toc',original=toc,candidate=candidate_toc))
    check_inputs(inputs)
    output_root.mkdir(parents=True,exist_ok=False)
    rows = []
    for resource in resources:
        path = resource['path']
        control = save_bytes(output_root/'controls'/path,resource['original'])
        candidate = save_bytes(output_root/'candidate'/path,resource['candidate'])
        restored = restore_copy(candidate['path'],control['path'],output_root/'rollback-check'/path,
                                candidate['sha256'],control['sha256'])
        for item in (control,candidate,restored):
            item['path'] = Path(item['path']).relative_to(output_root).as_posix()
        rows.append(dict(resource=path,kind=resource['kind'],control=control,candidate=candidate,restored=restored))
    coverage_path = output_root/'reports'/'text-font-coverage.json'
    font_report_path = output_root/'reports'/'font-validation.json'
    save_report(coverage_path,coverage); save_report(font_report_path,dict(fonts=font_reports))
    check_inputs(inputs)
    for row in rows:
        for key in ('control','candidate','restored'):
            item = row[key]
            if digest((output_root/item['path']).read_bytes()) != item['sha256']:
                raise FormatError('candidate resource changed during publication')
    manifest = dict(schema_version=1,kind='offline-locale-candidate',
        candidate_plan_canonical_sha256=digest(json.dumps(plan,sort_keys=True,separators=(',',':')).encode()),
        font_plan_sha256=digest(font_raw), text_plan_sha256=digest(text_raw), glyph_plan_sha256=digest(glyph_raw),
        font_source_sha256_expected=font_plan['font_source_sha256'], source_font_file_rechecked=False,
        additional_input_hashes=[dict(name=Path(path).name,sha256=sha) for path,sha in extra_inputs],
        resources=rows,toc_changes=changes,toc_inverse_byte_identical=True,
        text_inverse_byte_identical=coverage['inverse_rebuild_byte_identical'],
        reports=[dict(path=p.relative_to(output_root).as_posix(),sha256=digest(p.read_bytes()))
                 for p in (coverage_path,font_report_path)],
        all_resource_hashes_rechecked=True,input_hashes_rechecked=True,upstream_manifest_trusted=False,
        runtime_font_selection_verified=False,game_rendering_verified=False,deployment_performed=False)
    return save_report(output_root/'manifest.json',manifest)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan',type=Path,required=True); p.add_argument('--game-root',type=Path,required=True)
    p.add_argument('--font-bundle',type=Path,required=True); p.add_argument('--project-root',type=Path,default=Path('.'))
    p.add_argument('--output-dir',type=Path,required=True); p.add_argument('--lzx-library',type=Path)
    a = p.parse_args(argv)
    try:
        raw = a.plan.read_bytes(); plan = json.loads(raw.decode('utf-8-sig')); extra = [(a.plan,digest(raw))]
        if a.lzx_library: extra.append((a.lzx_library,digest(a.lzx_library.read_bytes())))
        r = build(plan,a.game_root,a.project_root,a.font_bundle,a.output_dir,
                  LzxDecoder(a.lzx_library) if a.lzx_library else None,extra)
        print(json.dumps(dict(resources=len(r['resources']),manifest=str(a.output_dir.resolve()/'manifest.json'),
                              deployment_performed=False,game_rendering_verified=False),sort_keys=True))
        return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print('ERROR: '+str(exc)); return 2


if __name__ == '__main__': raise SystemExit(main())
