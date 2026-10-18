"""Independently replay a relocated candidate tree against trusted project plans."""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import unicodedata

try:
    from .audit_text_font_coverage import audit
    from .build_coalesced import rebuild
    from .build_font_supplement import context, select_font, validate_plan as validate_font_plan
    from .build_locale_candidate import validate_plan, check_inputs
    from .font_binding_audit import fingerprint
    from .font_binding_plan import digest, _hash, confined_path, read_locked_json, parse_json_object
    from .supplement_font import validate_plan as validate_glyph_plan
    from .ue3_package import FormatError, LzxDecoder, write_report
    from .ue3_ui_styles import StyleGraph
    from .update_resource_sizes import update_sizes
except ImportError:
    from audit_text_font_coverage import audit
    from build_coalesced import rebuild
    from build_font_supplement import context, select_font, validate_plan as validate_font_plan
    from build_locale_candidate import validate_plan, check_inputs
    from font_binding_audit import fingerprint
    from font_binding_plan import digest, _hash, confined_path, read_locked_json, parse_json_object
    from supplement_font import validate_plan as validate_glyph_plan
    from ue3_package import FormatError, LzxDecoder, write_report
    from ue3_ui_styles import StyleGraph
    from update_resource_sizes import update_sizes


def canonical_json(value):
    # Dict equality treats False==0 and 1==1.0; metadata contracts must not.
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)


def scan_tree(root, expected):
    dirs = {p.as_posix() for name in expected for p in PurePosixPath(name).parents if p.as_posix() != '.'}
    files = set()
    for path in root.rglob('*'):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink() or path.is_junction():
            raise FormatError('linked candidate member: '+relative)
        if path.is_dir():
            if relative not in dirs: raise FormatError('unexpected candidate directory: '+relative)
        elif path.is_file():
            files.add(relative)
        else:
            raise FormatError('non-regular candidate member: '+relative)
    if files != expected:
        raise FormatError('candidate member set mismatch; missing='+str(sorted(expected-files))+'; extra='+str(sorted(files-expected)))


def verify(plan, candidate_root, project_root, decoder=None, expected_manifest_sha256=None, extra_inputs=()):
    expected_fonts = validate_plan(plan)
    root, project_root = Path(candidate_root).resolve(), Path(project_root).resolve()
    if not root.is_dir(): raise FormatError('candidate root must be an existing directory')
    fp, fp_path, fp_raw = read_locked_json(project_root,plan['font_plan'])
    tp, tp_path, tp_raw = read_locked_json(project_root,plan['text_plan'])
    gp, gp_path, gp_raw = read_locked_json(project_root,fp.get('supplement'))
    sources = validate_font_plan(fp); validate_glyph_plan(gp)
    if set(expected_fonts) != {s['label'].casefold() for s in sources}:
        raise FormatError('verification requires every planned Font hash')
    resource = plan['text_resource']; toc_resource = fp['toc']['path']
    if tp.get('resource') != resource or resource.casefold() in {s['path'].casefold() for s in sources} | {toc_resource.casefold()}:
        raise FormatError('candidate text resource identity/alias mismatch')
    _hash(tp.get('input_sha256'))
    roles = [dict(path=s['path'],kind='font',original=s['sha256'],candidate=expected_fonts[s['label'].casefold()]) for s in sources]
    roles += [dict(path=resource,kind='text',original=tp['input_sha256'],candidate=plan['expected_text_sha256']),
              dict(path=toc_resource,kind='toc',original=fp['toc']['sha256'],candidate=plan['expected_toc_sha256'])]
    report_names = ['reports/text-font-coverage.json','reports/font-validation.json']
    expected_members = {'manifest.json',*report_names} | {kind+'/'+r['path'] for r in roles for kind in ('controls','candidate','rollback-check')}
    scan_tree(root,expected_members)
    inputs = list(extra_inputs)+[(fp_path,digest(fp_raw)),(tp_path,digest(tp_raw)),(gp_path,digest(gp_raw))]
    observed = {}
    def read(relative, expected=None):
        path = confined_path(root,relative); raw = path.read_bytes(); sha = digest(raw)
        if expected is not None and sha != expected:
            raise FormatError('candidate verification SHA256 mismatch: '+relative)
        observed[relative] = sha; inputs.append((path,sha))
        return raw
    if expected_manifest_sha256 is not None: _hash(expected_manifest_sha256)
    manifest_raw = read('manifest.json',expected_manifest_sha256)
    manifest = parse_json_object(manifest_raw)
    if (not isinstance(manifest,dict) or type(manifest.get('schema_version')) is not int
            or manifest['schema_version'] != 1 or manifest.get('kind') != 'offline-locale-candidate'
            or manifest.get('game_rendering_verified') is not False or manifest.get('deployment_performed') is not False):
        raise FormatError('unsupported or contradictory candidate manifest')
    declared_extra = manifest.get('additional_input_hashes')
    if not isinstance(declared_extra,list): raise FormatError('invalid producer additional input declarations')
    for item in declared_extra:
        if (not isinstance(item,dict) or set(item) != {'name','sha256'} or not isinstance(item['name'],str)
                or not item['name'] or item['name'] in ('.','..') or any(c in item['name'] for c in '/\\:')
                or any(unicodedata.category(c).startswith('C') for c in item['name'])):
            raise FormatError('invalid producer additional input name')
        _hash(item['sha256'])
    rows, originals, candidates = [], {}, {}
    for r in roles:
        original = read('controls/'+r['path'],r['original'])
        changed = read('candidate/'+r['path'],r['candidate'])
        restored = read('rollback-check/'+r['path'],r['original'])
        if restored != original: raise FormatError('restored bytes differ from original control')
        originals[r['path']],candidates[r['path']] = original,changed
        rows.append(dict(resource=r['path'],kind=r['kind'],
            control=dict(path='controls/'+r['path'],sha256=r['original'],size=len(original)),
            candidate=dict(path='candidate/'+r['path'],sha256=r['candidate'],size=len(changed)),
            restored=dict(path='rollback-check/'+r['path'],sha256=r['original'],byte_identical_to_original=True,
                          method='hash-guarded-retained-original-backup')))
    original_contexts = {s['label'].casefold():context(originals[s['path']],decoder) for s in sources}
    changed_contexts = {s['label'].casefold():context(candidates[s['path']],decoder) for s in sources}
    before_graph, after_graph = StyleGraph(original_contexts),StyleGraph(changed_contexts)
    font_reports, font_inputs = [], []
    for s in sources:
        before = fingerprint(before_graph,select_font(before_graph,s,fp),decoder)
        after = fingerprint(after_graph,select_font(after_graph,s,fp),decoder)
        if before['semantic_sha256'] != fp['expected_semantic_sha256'] or after['semantic_sha256'] != fp['expected_supplement_semantic_sha256']:
            raise FormatError('candidate replay Font semantic mismatch')
        font_reports.append(dict(label=s['label'],original=before,candidate=after))
        font_inputs.append(dict(label=s['label'],font_object=s['font_object'],data=candidates[s['path']],sha256=expected_fonts[s['label'].casefold()]))
    coverage = audit(originals[resource],tp,font_inputs,decoder)
    if not coverage['all_supplied_fonts_cover_literals'] or rebuild(originals[resource],tp) != candidates[resource]:
        raise FormatError('candidate text replay/coverage mismatch')
    changes = [dict(path=r['path'],expected_size=len(originals[r['path']]),new_size=len(candidates[r['path']]))
               for r in roles if r['kind'] != 'toc' and len(originals[r['path']]) != len(candidates[r['path']])]
    toc = update_sizes(originals[toc_resource],fp['toc']['sha256'],changes) if changes else originals[toc_resource]
    reverse = [dict(path=c['path'],expected_size=c['new_size'],new_size=c['expected_size']) for c in changes]
    if toc != candidates[toc_resource] or (update_sizes(toc,digest(toc),reverse) if reverse else toc) != originals[toc_resource]:
        raise FormatError('candidate TOC replay/inverse mismatch')
    actual_report_meta = []
    for name, expected in zip(report_names,[coverage,dict(fonts=font_reports)]):
        raw = read(name); actual = parse_json_object(raw)
        if canonical_json(actual) != canonical_json(expected):
            raise FormatError('candidate report does not match independent replay: '+name)
        actual_report_meta.append(dict(path=name,sha256=digest(raw)))
    expected_manifest = dict(schema_version=1,kind='offline-locale-candidate',
        candidate_plan_canonical_sha256=digest(json.dumps(plan,sort_keys=True,separators=(',',':')).encode()),
        font_plan_sha256=digest(fp_raw),text_plan_sha256=digest(tp_raw),glyph_plan_sha256=digest(gp_raw),
        font_source_sha256_expected=fp['font_source_sha256'],source_font_file_rechecked=False,
        additional_input_hashes=declared_extra,resources=rows,toc_changes=changes,toc_inverse_byte_identical=True,
        text_inverse_byte_identical=coverage['inverse_rebuild_byte_identical'],reports=actual_report_meta,
        all_resource_hashes_rechecked=True,input_hashes_rechecked=True,upstream_manifest_trusted=False,
        runtime_font_selection_verified=False,game_rendering_verified=False,deployment_performed=False)
    if canonical_json(manifest) != canonical_json(expected_manifest):
        raise FormatError('candidate manifest contract does not match independent replay')
    check_inputs(inputs); scan_tree(root,expected_members)
    return dict(schema_version=1,kind='independent-candidate-revalidation',
        candidate_plan_canonical_sha256=expected_manifest['candidate_plan_canonical_sha256'],
        manifest_sha256=digest(manifest_raw),trusted_manifest_sha256_verified=expected_manifest_sha256 is not None,
        verified_resources=len(roles),verified_member_files=len(observed),resources=rows,
        members=[dict(path=p,sha256=observed[p]) for p in sorted(observed)],
        project_dependencies=[dict(path=ref['path'],sha256=sha) for ref,sha in
                              [(plan['font_plan'],digest(fp_raw)),(plan['text_plan'],digest(tp_raw)),(fp['supplement'],digest(gp_raw))]],
        producer_success_flags_used_as_proof=False,producer_additional_inputs_reopened=False,
        verifier_additional_input_hashes=[dict(name=Path(path).name,sha256=sha) for path,sha in extra_inputs],
        raster_source_font_file_reopened=False,raw_asset_inputs_rehashed=True,
        source_and_candidate_fonts_reparsed=True,text_and_toc_replayed=True,
        original_and_restored_bytes_equal=True,reports_match_independent_replay=True,
        game_rendering_verified=False,runtime_font_selection_verified=False,deployment_performed=False)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan',type=Path,required=True); p.add_argument('--candidate-root',type=Path,required=True)
    p.add_argument('--project-root',type=Path,default=Path('.')); p.add_argument('--manifest-sha256')
    p.add_argument('--lzx-library',type=Path); p.add_argument('--output',type=Path,required=True)
    a = p.parse_args(argv)
    try:
        root = a.candidate_root.resolve()
        if a.output.exists() or a.output.is_symlink() or a.output.resolve().is_relative_to(root):
            raise FormatError('verification report must be new and outside candidate tree')
        raw = a.plan.read_bytes(); plan = parse_json_object(raw); extra=[(a.plan,digest(raw))]
        if a.lzx_library: extra.append((a.lzx_library,digest(a.lzx_library.read_bytes())))
        report = verify(plan,root,a.project_root,LzxDecoder(a.lzx_library) if a.lzx_library else None,a.manifest_sha256,extra)
        write_report(a.output,report)
        if canonical_json(parse_json_object(a.output.read_bytes())) != canonical_json(report):
            raise FormatError('independent verification report reopening mismatch')
        scan_tree(root,{r['path'] for r in report['members']})
        check_inputs(extra+[(confined_path(root,r['path']),r['sha256']) for r in report['members']]
                     +[(confined_path(a.project_root,r['path']),r['sha256']) for r in report['project_dependencies']])
        print(json.dumps(dict(resources=report['verified_resources'],members=report['verified_member_files'],
                              trusted_manifest_sha256_verified=report['trusted_manifest_sha256_verified'],
                              game_rendering_verified=False),sort_keys=True)); return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print('ERROR: '+str(exc)); return 2


if __name__ == '__main__': raise SystemExit(main())
