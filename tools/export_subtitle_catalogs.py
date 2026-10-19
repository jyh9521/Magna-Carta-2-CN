"""Export hash-locked movie sidecars from original discs, never full game copies."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile

try:
    from .disc_inventory import Disc, sha256_file
    from .export_translation_catalogs import digest, write_json
    from .prepare_translation_workspace import read_locked
    from .subtitle_text import parse, rebuild
except ImportError:
    # subtitle_text uses package imports; CLI is deliberately python -m tools....
    raise SystemExit('Run as python -m tools.export_subtitle_catalogs')


def catalog(data, resource, plans):
    _, cues = parse(data)
    starts = [int(m[2]) for m in cues]
    if len(starts) != len(set(starts)):
        raise ValueError('ambiguous cue start')
    edits = {}
    for plan in plans:
        if plan['resource'] != resource or plan['input_sha256'] != digest(data):
            raise ValueError('subtitle plan resource/hash mismatch')
        rebuild(data, plan)  # verifies timings, markers and source value hashes
        for entry in plan['entries']:
            if entry['start'] in edits:
                raise ValueError('overlapping subtitle plans')
            edits[entry['start']] = entry['translation']
    rows = []
    for cue in cues:
        start, end = int(cue[2]), int(cue[6])
        identity = json.dumps([resource, start, end], separators=(',', ':')).encode()
        rows.append(dict(id='subtitle:'+digest(identity), start=start, end=end,
            cue_class=cue[3], source=cue[4], source_sha256=digest(cue[4].encode('utf8')),
            translation=edits.get(start, ''), status='draft' if start in edits else 'untranslated',
            reviewer='', text_kind='story_subtitle'))
    empty = dict(schema_version=1, kind='timed-subtitle-text', input_sha256=digest(data), entries=[])
    if rebuild(data, empty) != data:
        raise ValueError('subtitle byte roundtrip mismatch')
    return dict(schema_version=1, kind='timed-subtitle-catalog', resource=resource,
        input_sha256=digest(data), entries=rows)


def export(root, profile, output):
    root, output = Path(root).resolve(), Path(output)
    if output.exists() or output.is_symlink():
        raise ValueError('output must be new')
    if profile.get('schema_version') != 1:
        raise ValueError('unsupported subtitle profile')
    snapshots, plans = {}, []
    for spec in profile['plans']:
        plans.append(read_locked(root, spec, snapshots))
    grouped, matched, images, disc_ids = {}, set(), [], set()
    for source in profile['sources']:
        image = root / source['path']
        if not image.resolve().is_relative_to(root) or source['disc'] in disc_ids:
            raise ValueError('invalid disc source')
        disc_ids.add(source['disc'])
        if image.stat().st_size != source['size'] or sha256_file(image) != source['sha256']:
            raise ValueError('original image size/SHA256 mismatch')
        image_stat = image.stat()
        disc = Disc(image)
        inventory = {e['path']:e for e in disc.inventory() if not e['directory']}
        movie_txt = {name for name in inventory if name.startswith('MC2Game/Movies/') and name.endswith('.txt')}
        if movie_txt != {e['resource'] for e in source['members']} or len(movie_txt)!=len(source['members']):
            raise ValueError('movie subtitle inventory not closed')
        for member in source['members']:
            entry = inventory[member['resource']]
            if entry['size'] != member['size'] or entry['size'] > 8*1024*1024:
                raise ValueError('subtitle size mismatch/limit')
            data = disc.read(entry['offset'], entry['size'])
            if digest(data) != member['sha256']:
                raise ValueError('subtitle SHA256 mismatch')
            identity = (member['resource'], member['sha256'])
            selected = [p for p in plans if (p['resource'],p['input_sha256'])==identity]
            matched.update(id(p) for p in selected)
            if identity in grouped:
                grouped[identity]['discs'].append(source['disc'])
            else:
                grouped[identity] = dict(discs=[source['disc']], catalog=catalog(data,member['resource'],selected))
        if image.stat().st_mtime_ns != image_stat.st_mtime_ns or image.stat().st_size != image_stat.st_size:
            raise ValueError('image changed during extraction')
        images.append(dict(disc=source['disc'], sha256=source['sha256'], members=len(movie_txt)))
    if len(matched)!=len(plans):
        raise ValueError('unmatched subtitle plan')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.subtitles-', dir=output.parent) as temporary:
        stage = Path(temporary)/'catalogs'
        resources = []
        for (resource, sha), group in sorted(grouped.items()):
            path = digest((resource+':'+sha).encode())+'.json'
            document = dict(group['catalog'], discs=sorted(group['discs']))
            write_json(stage/path, document)
            resources.append(dict(resource=resource, sha256=sha, discs=document['discs'], path=path,
                cues=len(document['entries']), translated=sum(bool(e['translation']) for e in document['entries'])))
        report = dict(schema_version=1, sources=images, resources=resources,
            catalogs=len(resources), cues=sum(r['cues'] for r in resources),
            translated=sum(r['translated'] for r in resources), game_started=False)
        write_json(stage/'manifest.json', report)
        if any(p.read_bytes()!=raw for p,raw in snapshots.items()):
            raise ValueError('subtitle plan changed during export')
        stage.rename(output)
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args=parser.parse_args(argv)
    try:
        report=export(args.source_root,json.loads(args.profile.read_bytes()),args.output)
        print(json.dumps({k:report[k] for k in ('catalogs','cues','translated','game_started')},sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print('ERROR: '+str(error))
        return 2


if __name__=='__main__':
    raise SystemExit(main())
