"""Compose a new hash-locked comparison phase view without rebuilding packages.

Unchanged generated members share same-volume hardlinks with the locked previous
packet. Supplied candidates and newly enrolled originals are copied, never
overwritten in place. Raw controls stay unchanged; only candidate TOC size fields
are rebuilt. This tool never touches a live test directory, ISO, or executable.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path, PurePosixPath

from .build_disc_image import toc_rows, transfer, TOC_LIMIT
from .update_resource_sizes import update_sizes_reversible
from .verify_resource_phase import (MAX_FILE, MAX_PACKET_RESOURCES, PHASES,
    file_state, hash_value, inspect, relative, sha, stable, unique)

KIND = 'incremental-comparison-replacements'
PACKET_KIND = 'offline-disc-locale-raw-comparison'
JSON_LIMIT = 4 * 1024 * 1024


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=True, indent=2)+'\n').encode()


def unlinked(path, root):
    """Hardlinked immutable files are allowed; path redirection is not."""
    path, root = Path(path), Path(root)
    if not path.is_relative_to(root):
        raise ValueError('path outside declared root')
    while True:
        if path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
            raise ValueError('linked input or output path')
        if path == root:
            return
        path = path.parent


def locked_json(path, expected):
    path = Path(path)
    if path.stat().st_size > JSON_LIMIT:
        raise ValueError('manifest exceeds size bound')
    raw = path.read_bytes()
    if len(raw) > JSON_LIMIT or sha(raw) != hash_value(expected):
        raise ValueError('manifest SHA256 mismatch')
    return json.loads(raw, object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('non-finite manifest JSON'))), raw


def source_file(root, ref, snapshots):
    if not isinstance(ref, dict) or set(ref) != {'file', 'size', 'sha256'}:
        raise ValueError('source requires file, size and SHA256')
    name = relative(ref['file']); path = root/name
    unlinked(path, root)
    if path.resolve() != path:
        raise ValueError('source path must be canonical')
    if type(ref['size']) is not int or not 0 < ref['size'] <= MAX_FILE:
        raise ValueError('source size outside bounded profile')
    expected = dict(size=ref['size'], sha256=hash_value(ref['sha256']))
    if file_state(path) != expected:
        raise ValueError('supplied source identity mismatch')
    snapshots[path] = expected
    return path, expected


def prepare(base_packet, base_manifest_sha256, replacement_manifest,
            replacement_manifest_sha256, output, existing=False):
    base = Path(base_packet).absolute(); manifest_path = Path(replacement_manifest).absolute()
    out = Path(output).absolute()
    for path in (base, manifest_path):
        unlinked(path, Path(path.anchor))
    base = base.resolve(); manifest_path = manifest_path.resolve()
    if (out.parent.resolve() != out.parent or not out.parent.is_dir()
            or out.is_symlink() or getattr(out, 'is_junction', lambda: False)()
            or out.is_relative_to(base) or base.is_relative_to(out)
            or manifest_path.is_relative_to(out)
            or (out.exists() if not existing else not out.is_dir())):
        raise ValueError('view must be new, canonical and disjoint from inputs')
    old, old_raw = locked_json(base/'manifest.json', base_manifest_sha256)
    spec, spec_raw = locked_json(manifest_path, replacement_manifest_sha256)
    if not isinstance(old, dict) or old.get('kind') != PACKET_KIND:
        raise ValueError('a disc comparison predecessor is required')
    if (not isinstance(spec, dict) or set(spec) != {'schema_version','kind','disc','toc_path','resources'}
            or type(spec.get('schema_version')) is not int or spec['schema_version'] != 1
            or spec.get('kind') != KIND or type(spec.get('disc')) is not int
            or spec['disc'] != old.get('disc') or spec['disc'] not in (1, 2)):
        raise ValueError('unsupported replacement contract or wrong disc')
    selected = spec['resources']
    if not isinstance(selected, list) or not 1 <= len(selected) <= MAX_PACKET_RESOURCES:
        raise ValueError('replacement count outside bounded profile')
    snapshots = {base/'manifest.json':dict(size=len(old_raw),sha256=sha(old_raw)),
                 manifest_path:dict(size=len(spec_raw),sha256=sha(spec_raw))}
    base_members = {}
    for phase in PHASES:
        result, checked = inspect(base, base_manifest_sha256, base/phase, phase)
        if not result['all_resources_match']:
            raise ValueError('predecessor phase mismatch')
        snapshots.update(checked)
        for row in result['resources']:
            source = base/phase/row['path']; unlinked(source, base)
            if source.stat().st_dev != out.parent.stat().st_dev:
                raise ValueError('unchanged members require the same volume')
            base_members[phase+'/'+row['path']] = (source, row['expected'])
    old_rows = {r['path']:r for r in old['resources']}
    toc = relative(spec['toc_path'])
    if toc not in old_rows or old_rows[toc]['candidate_size'] > TOC_LIMIT:
        raise ValueError('TOC must be a bounded predecessor resource')
    toc_inputs = {}
    for phase in PHASES:
        source, state = base_members[phase+'/'+toc]
        if state['size'] > TOC_LIMIT:
            raise ValueError('TOC exceeds size bound')
        raw = source.read_bytes(); parsed = {r['path']:r for r in toc_rows(raw)}
        if toc not in parsed or parsed[toc]['size'] != 0:
            raise ValueError('TOC self entry must retain zero size')
        key = {'controls':'original','raw-controls':'raw','candidate':'candidate'}[phase]
        for name, row in old_rows.items():
            expected_size = 0 if name == toc else row[key+'_size']
            if name not in parsed or parsed[name]['size'] != expected_size:
                raise ValueError('predecessor '+phase+' TOC member size mismatch: '+name)
        toc_inputs[phase] = (raw, parsed)
    rows = copy.deepcopy(old_rows); candidates = {}; originals = {}; seen = set(); additions = []
    expected_fields = {'path','before_sha256','file','size','sha256'}
    old_folded = {p.casefold():p for p in old_rows}
    for row in selected:
        if not isinstance(row, dict) or set(row) not in (expected_fields, expected_fields | {'original'}):
            raise ValueError('invalid replacement fields')
        name = relative(row['path']); folded = name.casefold()
        if (folded in seen or name == toc or folded.endswith('.xex')
                or (folded in old_folded and old_folded[folded] != name)):
            raise ValueError('duplicate, aliased, executable or TOC replacement')
        seen.add(folded)
        before = hash_value(row['before_sha256'])
        supplied, after = source_file(manifest_path.parent,
            {k:row[k] for k in ('file','size','sha256')}, snapshots)
        if supplied.is_relative_to(out):
            raise ValueError('output overlaps supplied input')
        if name in old_rows:
            if 'original' in row or before != old_rows[name]['candidate_sha256']:
                raise ValueError('existing candidate before hash or original role mismatch')
            old_size = old_rows[name]['candidate_size']
        else:
            if 'original' not in row:
                raise ValueError('new resource requires its locked original')
            source, original = source_file(manifest_path.parent, row['original'], snapshots)
            if source.is_relative_to(out) or original['sha256'] != before:
                raise ValueError('new original before identity mismatch')
            originals[name] = (source, original)
            rows[name] = dict(path=name,original_size=original['size'],original_sha256=original['sha256'],
                             raw_size=original['size'],raw_sha256=original['sha256'])
            additions.append(dict(path=name,original_size=original['size'],original_sha256=original['sha256']))
            old_size = original['size']
            for phase in ('controls','raw-controls'):
                entry = toc_inputs[phase][1].get(name)
                if entry is None or entry['size'] != old_size:
                    raise ValueError('original TOC member size mismatch: '+name)
        entry = toc_inputs['candidate'][1].get(name)
        if entry is None or entry['size'] != old_size:
            raise ValueError('candidate TOC member size mismatch: '+name)
        rows[name].update(candidate_size=after['size'],candidate_sha256=after['sha256'])
        if name not in old_rows or before != after['sha256']:
            candidates[name] = (supplied, after)
    if len(rows) > MAX_PACKET_RESOURCES:
        raise ValueError('complete view resource count outside bound')
    if not candidates:
        raise ValueError('selection contains no changed or added resources')
    sizes = []
    for name in sorted(candidates):
        old_size = old_rows[name]['candidate_size'] if name in old_rows else rows[name]['original_size']
        if old_size != rows[name]['candidate_size']:
            sizes.append(dict(path=name,expected_size=old_size,new_size=rows[name]['candidate_size']))
    toc_before = toc_inputs['candidate'][0]
    toc_after, toc_proof = update_sizes_reversible(toc_before, sha(toc_before), sizes)
    inverse = [dict(path=c['path'],expected_size=c['new_size'],new_size=c['expected_size']) for c in sizes]
    toc_proof.update(path=toc, changes=sizes, inverse_changes=inverse,
                     rollback_member='rollback/candidate-toc.txt',sector_fields_changed=False)
    rows[toc].update(candidate_size=len(toc_after),candidate_sha256=sha(toc_after))
    plan = dict(schema_version=1,kind='incremental-comparison-view-plan',disc=spec['disc'],toc_path=toc,
        base_manifest_sha256=base_manifest_sha256,replacement_manifest_sha256=replacement_manifest_sha256,
        unchanged_method='same-volume-hardlink',changed_method='exclusive-file-copy',
        game_started=False,game_rendering_verified=False)
    operations = []
    for phase in PHASES:
        key = {'controls':'original','raw-controls':'raw','candidate':'candidate'}[phase]
        for name in sorted(rows):
            member = phase+'/'+name
            expected = dict(size=rows[name][key+'_size'],sha256=rows[name][key+'_sha256'])
            op = dict(member=member,expected=expected)
            if phase == 'candidate' and name == toc and toc_after != toc_before:
                op.update(method='bytes',data=toc_after)
            elif phase == 'candidate' and name in candidates:
                op.update(method='copy',source=candidates[name][0])
            elif name in originals:
                if phase == 'raw-controls':
                    op.update(method='link',output_source='controls/'+name)
                else:
                    op.update(method='copy',source=originals[name][0])
            else:
                op.update(method='link',source=base_members[member][0])
            operations.append(op)
    operations.append(dict(member='rollback/candidate-toc.txt',method='link',
        source=base/'candidate'/toc,expected=dict(size=len(toc_before),sha256=sha(toc_before))))
    composition = dict(schema_version=1,kind='incremental-comparison-resource-composition',
        disc=spec['disc'],base_manifest_sha256=base_manifest_sha256,
        replacement_manifest_sha256=replacement_manifest_sha256,additions=sorted(additions,key=lambda r:r['path']),
        changed_candidates=sorted(candidates),toc=toc_proof,full_composition_replayed=False,
        original_and_raw_inputs_preserved=True,game_started=False,game_rendering_verified=False,
        operations=[dict(member=o['member'],method=o['method'],**o['expected']) for o in operations])
    reports = {'reports/view-plan.json':encoded(plan),
               'reports/composition.json':encoded(composition),'reports/toc.json':encoded(toc_proof)}
    members = {o['member']:o['expected']['sha256'] for o in operations}
    members.update({n:sha(data) for n,data in reports.items()})
    manifest = dict(schema_version=1,kind=PACKET_KIND,disc=spec['disc'],
        raw_package_outputs=True,raw_control_method=old['raw_control_method'],
        unknown_control_syntax_resolved=False,deployment_performed=False,game_rendering_verified=False,
        source_image_sha256=hash_value(old['source_image_sha256']),
        composition_manifest_sha256=sha(reports['reports/composition.json']),
        comparison_plan_canonical_sha256=sha(reports['reports/view-plan.json']),
        resources=[rows[n] for n in sorted(rows)],member_sha256=members,
        incremental_view=dict(base_manifest_sha256=base_manifest_sha256,
                              replacement_manifest_sha256=replacement_manifest_sha256,
                              full_composition_replayed=False))
    reports['manifest.json'] = encoded(manifest)
    if len(reports['manifest.json']) > JSON_LIMIT:
        raise ValueError('output manifest exceeds size bound')
    stable(snapshots.items())
    return dict(output=out,base=base,manifest=manifest,operations=operations,reports=reports,
                snapshots=list(snapshots.items()))


def identity(path):
    state = path.stat(follow_symlinks=False)
    return state.st_dev, state.st_ino


def make_parents(path, root, owned_dirs):
    missing = []
    while not path.exists():
        if not path.is_relative_to(root):
            raise ValueError('directory outside owned output')
        missing.append(path); path = path.parent
    unlinked(path, root)
    for directory in reversed(missing):
        directory.mkdir(); owned_dirs.append((directory,identity(directory)))


def create_member(path, op, root, owned_files, owned_dirs):
    make_parents(path.parent,root,owned_dirs)
    if op['method'] == 'link':
        source = root/op['output_source'] if 'output_source' in op else op['source']
        os.link(source,path); owned_files.append((path,identity(path)))
    else:
        with path.open('xb') as target:
            state=os.fstat(target.fileno());owned_files.append((path,(state.st_dev,state.st_ino)))
            if op['method'] == 'bytes':
                target.write(op['data'])
            else:
                with op['source'].open('rb') as source:
                    transfer(source,target,op['expected']['size'])
                    if source.read(1):
                        raise ValueError('supplied source grew during bounded copy')
    if file_state(path) != op['expected']:
        raise ValueError('materialized member identity mismatch')


def cleanup_owned(root, files, directories):
    """Only unlink recorded creations; foreign files and replaced paths survive."""
    directory_ids = dict(directories)
    def owned_ancestors(path):
        for parent in path.parents:
            if parent not in directory_ids or identity(parent) != directory_ids[parent]:
                return False
            if parent == root:
                return True
        return False
    for path, expected in reversed(files):
        try:
            unlinked(path,root)
            if not owned_ancestors(path) or identity(path) != expected:
                continue
            path.unlink()
        except (OSError,ValueError):
            pass
    for path, expected in reversed(directories):
        try:
            unlinked(path,root)
            if identity(path) == expected and (path == root or owned_ancestors(path)):
                path.rmdir()  # Never recursively delete foreign content.
        except (OSError,ValueError):
            pass


def check_output(prepared):
    root = prepared['output']; expected = {o['member'] for o in prepared['operations']} | set(prepared['reports'])
    expected_dirs = {p.as_posix() for name in expected for p in PurePosixPath(name).parents
                     if p.as_posix() != '.'}
    found = set(); pending = [root]
    while pending:
        parent = pending.pop(); unlinked(parent,root)
        for path in parent.iterdir():
            unlinked(path,root)
            if path.is_dir():
                if path.relative_to(root).as_posix() not in expected_dirs:
                    raise ValueError('unexpected view directory')
                pending.append(path)
            elif path.is_file():
                found.add(path.relative_to(root).as_posix())
            else:
                raise ValueError('non-file view member')
            if len(found)+len(pending) > 6*MAX_PACKET_RESOURCES+64:
                raise ValueError('view tree outside size bound')
    if found != expected:
        raise ValueError('unexpected or missing view member')
    input_identities = {identity(path) for path, _ in prepared['snapshots']}
    for op in prepared['operations']:
        path = root/op['member']
        if file_state(path) != op['expected']:
            raise ValueError('view member identity mismatch')
        if op['method'] == 'link':
            source = root/op['output_source'] if 'output_source' in op else op['source']
            if not os.path.samefile(source,path):
                raise ValueError('unchanged member is not the declared hardlink')
        elif identity(path) in input_identities:
            raise ValueError('copied view member unexpectedly shares an input')
    for member, data in prepared['reports'].items():
        if (root/member).read_bytes() != data:
            raise ValueError('view proof or manifest mismatch')
    stable(prepared['snapshots'])
    return dict(status='PASS',resources=len(prepared['manifest']['resources']),
        manifest_sha256=sha(prepared['reports']['manifest.json']),
        game_started=False,game_rendering_verified=False,raw_controls_preserved=True)


def build(base_packet, base_manifest_sha256, replacement_manifest,
          replacement_manifest_sha256, output):
    p = prepare(base_packet,base_manifest_sha256,replacement_manifest,replacement_manifest_sha256,output)
    root=p['output'];root.mkdir();files=[];directories=[(root,identity(root))]
    try:
        for op in p['operations']:
            create_member(root/op['member'],op,root,files,directories)
        # The immutable manifest is published last; an incomplete view is not usable.
        for member,data in p['reports'].items():
            create_member(root/member,dict(method='bytes',data=data,
                expected=dict(size=len(data),sha256=sha(data))),root,files,directories)
        check_output(p)
    except BaseException:
        cleanup_owned(root,files,directories)
        raise
    return p['manifest']


def verify(base_packet, base_manifest_sha256, replacement_manifest,
           replacement_manifest_sha256, output):
    return check_output(prepare(base_packet,base_manifest_sha256,replacement_manifest,
                                replacement_manifest_sha256,output,existing=True))


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-packet',type=Path,required=True)
    parser.add_argument('--base-manifest-sha256',required=True)
    parser.add_argument('--replacement-manifest',type=Path,required=True)
    parser.add_argument('--replacement-manifest-sha256',required=True)
    output=parser.add_mutually_exclusive_group(required=True)
    output.add_argument('--output-dir',type=Path);output.add_argument('--verify-root',type=Path)
    a=parser.parse_args(argv)
    try:
        args=(a.base_packet,a.base_manifest_sha256,a.replacement_manifest,a.replacement_manifest_sha256)
        if a.verify_root:
            result=verify(*args,a.verify_root)
        else:
            m=build(*args,a.output_dir)
            result=dict(status='BUILT',resources=len(m['resources']),
                manifest_sha256=sha(encoded(m)),game_started=False,game_rendering_verified=False)
        print(json.dumps(result,sort_keys=True));return 0
    except (OSError,ValueError,KeyError,TypeError) as e:
        print('ERROR: '+str(e));return 2


if __name__=='__main__':raise SystemExit(main())
