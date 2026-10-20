"""Hash-locked single-disc subtitle/TOC bundles; no fonts, INT or deployment."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from tools.font_binding_plan import digest, read_locked_json, confined_path, _relative, _hash, parse_json_object
from tools.disc_inventory import Disc, sha256_file
from tools.subtitle_text import rebuild, rebuild_reversible
from tools.update_resource_sizes import update_sizes
from tools.build_font_supplement import restore_copy

MAX_MEMBERS = 64
MAX_RESOURCE_BYTES = 8*1024*1024


def encoded(obj):
    return (json.dumps(obj, sort_keys=True, ensure_ascii=True, indent=2)+'\n').encode()


def select_inputs(plan, profile, plans):
    if (type(plan.get('schema_version')) is not int or plan['schema_version'] != 1
            or plan.get('kind') != 'offline-disc-subtitle-bundle'
            or plan.get('game_rendering_verified') is not False
            or type(plan.get('disc')) is not int or plan['disc'] <= 0):
        raise ValueError('invalid single-disc subtitle bundle plan')
    if type(profile.get('schema_version')) is not int or profile['schema_version'] != 1:
        raise ValueError('invalid subtitle source profile')
    sources = profile.get('sources')
    if not isinstance(sources, list) or not 1 <= len(sources) <= 16:
        raise ValueError('subtitle source count outside bound')
    ids = [s['disc'] for s in sources]
    if any(type(d) is not int or d <= 0 for d in ids) or len(set(ids)) != len(ids):
        raise ValueError('ambiguous disc identities')
    selected = [s for s in sources if s['disc'] == plan['disc']]
    if len(selected) != 1:
        raise ValueError('disc not present in subtitle profile')
    source = selected[0]; _relative(source['path']); _hash(source['sha256'])
    if type(source['size']) is not int or source['size'] <= 0:
        raise ValueError('invalid source image size')
    members = source['members']
    if not isinstance(members, list) or not 1 <= len(members) <= MAX_MEMBERS:
        raise ValueError('per-disc subtitle count outside 1..64')
    resources = set()
    for m in members:
        _relative(m['resource']); _hash(m['sha256'])
        if (m['resource'].casefold() in resources or type(m['size']) is not int
                or not 1 <= m['size'] <= MAX_RESOURCE_BYTES):
            raise ValueError('invalid or duplicate subtitle member')
        resources.add(m['resource'].casefold())
    toc = plan['toc']; _relative(toc['path']); _hash(toc['sha256'])
    if toc['path'].casefold() in resources:
        raise ValueError('TOC overlaps subtitle role')
    if not isinstance(plans, list) or not 1 <= len(plans) <= 256:
        raise ValueError('subtitle plan count outside bound')
    known = {(m['resource'], m['sha256']) for s in sources for m in s['members']}
    if any((p['resource'],p['input_sha256']) not in known for p in plans):
        raise ValueError('subtitle plan has no source provenance')
    relevant = [p for p in plans if (p['resource'],p['input_sha256']) in
                {(m['resource'],m['sha256']) for m in members}]
    if {p['resource'] for p in relevant} != {m['resource'] for m in members}:
        raise ValueError('selected disc has an unplanned subtitle member')
    return source, relevant


def prepare(plan, profile, plans, originals):
    source, relevant = select_inputs(plan, profile, plans)
    toc = plan['toc']; required = {m['resource'] for m in source['members']} | {toc['path']}
    if set(originals) != required:
        raise ValueError('bundle inputs must match this disc exactly')
    if digest(originals[toc['path']]) != toc['sha256']:
        raise ValueError('source TOC identity mismatch')
    current, reports = {}, []
    for m in source['members']:
        path = m['resource']; raw = originals[path]
        if len(raw) != m['size'] or digest(raw) != m['sha256']:
            raise ValueError('subtitle member identity mismatch')
        edits = []
        for p in relevant:
            if p['resource'] == path:
                rebuild(raw, p); edits.extend(p['entries'])
        merged = dict(schema_version=1, kind='timed-subtitle-text', resource=path,
                      input_sha256=m['sha256'], entries=edits)
        current[path], report = rebuild_reversible(raw, merged)
        reports.append(dict(resource=path, **report))
    changes = [dict(path=p, expected_size=len(originals[p]), new_size=len(b))
               for p,b in current.items() if len(b) != len(originals[p])]
    new_toc = update_sizes(originals[toc['path']], toc['sha256'], changes) if changes else originals[toc['path']]
    reverse = [dict(path=c['path'],expected_size=c['new_size'],new_size=c['expected_size']) for c in changes]
    if (update_sizes(new_toc,digest(new_toc),reverse) if reverse else new_toc) != originals[toc['path']]:
        raise ValueError('subtitle TOC inverse mismatch')
    current[toc['path']] = new_toc
    files = {}; rows = []
    for path in sorted(required):
        for kind,b in [('controls',originals[path]),('candidate',current[path]),('rollback-check',originals[path])]:
            files[kind+'/'+path] = b
        rows.append(dict(path=path,original_sha256=digest(originals[path]),candidate_sha256=digest(current[path]),
                         original_size=len(originals[path]),candidate_size=len(current[path])))
    files['reports/subtitles.json'] = encoded(reports)
    manifest = dict(schema_version=1,kind=plan['kind'],disc=source['disc'],source_image_sha256=source['sha256'],
                    plan_canonical_sha256=digest(encoded(plan)),subtitle_resources=len(reports),
                    translated_cues=sum(r['edited_cues'] for r in reports),resources=rows,toc_changes=changes,
                    toc_inverse_byte_identical=True,member_sha256={p:digest(b) for p,b in files.items()},
                    cumulative_INT_included=False,fonts_verified=False,game_rendering_verified=False,deployment_performed=False)
    files['manifest.json'] = encoded(manifest)
    return files, manifest


def load_inputs(plan, root):
    profile,path,raw = read_locked_json(root,plan['profile']); snapshots = [(path,raw)]
    if not isinstance(profile.get('plans'),list) or not 1 <= len(profile['plans']) <= 256:
        raise ValueError('subtitle profile plan count outside bound')
    plans = []
    for ref in profile['plans']:
        obj,path,raw = read_locked_json(root,ref); plans.append(obj); snapshots.append((path,raw))
    select_inputs(plan,profile,plans)
    return profile,plans,snapshots


def check_inputs(snapshots):
    if any(p.read_bytes() != b for p,b in snapshots):
        raise ValueError('subtitle bundle input changed')


def build(plan, root, output):
    if Path(output).is_symlink():
        raise ValueError('subtitle output cannot be a symlink')
    root,output = Path(root).resolve(),Path(output).resolve()
    if output.exists() or not output.is_relative_to(root) or output == root:
        raise ValueError('subtitle bundle output must be new and inside project')
    profile,plans,snapshots = load_inputs(plan,root); source,_ = select_inputs(plan,profile,plans)
    image = confined_path(root,source['path']); before = image.stat()
    if before.st_size != source['size'] or sha256_file(image) != source['sha256']:
        raise ValueError('source image size/SHA256 mismatch')
    disc = Disc(image); inventory = {e['path']:e for e in disc.inventory() if not e['directory']}
    originals = {}
    for path in [m['resource'] for m in source['members']]+[plan['toc']['path']]:
        e = inventory.get(path)
        if e is None or not 1 <= e['size'] <= MAX_RESOURCE_BYTES:
            raise ValueError('subtitle bundle resource missing or too large')
        originals[path] = disc.read(e['offset'],e['size'])
    files,manifest = prepare(plan,profile,plans,originals)
    def stable():
        check_inputs(snapshots); now = image.stat()
        if (now.st_size,now.st_mtime_ns) != (before.st_size,before.st_mtime_ns):
            raise ValueError('source image changed during subtitle build')
    stable(); output.mkdir(parents=True,exist_ok=False)
    for path,b in files.items():
        target = confined_path(output,path)
        if path.startswith('rollback-check/'):
            relative = path[len('rollback-check/'):]
            restore_copy(output/'candidate'/relative,output/'controls'/relative,target,
                         digest(files['candidate/'+relative]),digest(b))
        else:
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as stream:stream.write(b)
        if target.read_bytes() != b:
            raise ValueError('subtitle bundle output reopening mismatch')
    stable(); return manifest


def verify(plan, root, output):
    if Path(output).is_symlink():
        raise ValueError('subtitle verify root cannot be a symlink')
    root,output = Path(root).resolve(),Path(output).resolve()
    profile,plans,snapshots = load_inputs(plan,root); source,_ = select_inputs(plan,profile,plans)
    paths = [m['resource'] for m in source['members']]+[plan['toc']['path']]
    originals = {p:confined_path(output/'controls',p).read_bytes() for p in paths}
    files,manifest = prepare(plan,profile,plans,originals)
    actual = {p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()}
    if actual != set(files) or any(p.is_symlink() for p in output.rglob('*')):
        raise ValueError('subtitle bundle file set drift')
    for path,b in files.items():
        if confined_path(output,path).read_bytes() != b:
            raise ValueError('subtitle bundle independent replay mismatch: '+path)
    check_inputs(snapshots); return manifest


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan',type=Path,required=True); p.add_argument('--project-root',type=Path,default=Path('.'))
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--output-dir',type=Path);g.add_argument('--verify-root',type=Path)
    a = p.parse_args(argv)
    try:
        raw = a.plan.read_bytes(); plan = parse_json_object(raw)
        result = (build(plan,a.project_root,a.output_dir) if a.output_dir else verify(plan,a.project_root,a.verify_root))
        if a.plan.read_bytes() != raw:raise ValueError('subtitle bundle plan changed')
        print(json.dumps(dict(disc=result['disc'],resources=result['subtitle_resources'],
            cues=result['translated_cues'],verified=bool(a.verify_root),deployment_performed=False),sort_keys=True));return 0
    except (OSError,ValueError,KeyError,TypeError) as e:
        print('ERROR: '+str(e));return 2


if __name__ == '__main__':raise SystemExit(main())
