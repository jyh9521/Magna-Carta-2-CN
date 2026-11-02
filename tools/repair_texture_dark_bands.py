"""Build a hash-locked sparse RGB-band revision; never deploy or launch a game."""
import argparse
import importlib.metadata
import json
from pathlib import Path

from .repair_texture_labels import locked, confined, revise
from .reface_font import sha
from .replace_texture_regions import selected, replace_tiles
from .runtime_envelope import require_raw_envelope, ALIGNMENT
from .texture_dark_bands import repair, repair_dark_outline
from .texture_layout import rect_units


def load_labels(profile, project):
    labels = {}
    refs = profile['label_plans']
    if not isinstance(refs, list) or not 1 <= len(refs) <= 16:
        raise ValueError('bounded label plan list required')
    for ref in refs:
        plan = json.loads(locked(project, ref))
        versions = plan.get('rasterizer_versions')
        if not versions or any(importlib.metadata.version(k) != v for k, v in versions.items()):
            raise ValueError('rasterizer version mismatch')
        for row in plan['labels']:
            labels[row['id']] = dict(row, font=row.get('font', plan.get('font')))
    for ref in profile['prior_gradient_revisions']:
        for row in json.loads(locked(project, ref))['labels']:
            labels[row['id']] = revise(labels[row['id']], row['remove_gradient_positions'])
    return labels


def validate(profile):
    if (set(profile) != {'schema_version', 'kind', 'label_plans', 'prior_gradient_revisions',
                         'requests', 'resources'} or profile['schema_version'] != 1
            or profile['kind'] != 'native-rgb-band-repair-v1'):
        raise ValueError('unsupported RGB band profile')
    for name, bound in [('requests', 2048), ('resources', 1024)]:
        rows = profile[name]
        if not isinstance(rows, list) or not 1 <= len(rows) <= bound:
            raise ValueError('bounded ' + name + ' required')
    requests = {}
    for row in profile['requests']:
        if (set(row)-{'id', 'remove_gradient_positions', 'refit_rows', 'restore_outline_rgb'}
                or not {'id', 'remove_gradient_positions'} <= row.keys() or row['id'] in requests):
            raise ValueError('invalid or duplicate RGB band request')
        if 'restore_outline_rgb' in row and row['restore_outline_rgb'] is not True:
            raise ValueError('outline restoration must be explicitly true')
        requests[row['id']] = row
    seen = set()
    for row in profile['resources']:
        if (set(row) != {'path', 'sha256', 'discs', 'textures'} or row['path'].casefold() in seen
                or not row['path'].lower().endswith('.xxx')
                or row['discs'] not in ([1], [2], [1, 2])):
            raise ValueError('invalid or duplicate native resource')
        seen.add(row['path'].casefold())
        textures = row['textures']; objects = set()
        if not isinstance(textures, list) or not 1 <= len(textures) <= 512:
            raise ValueError('bounded native texture list required')
        for t in textures:
            if (set(t) != {'object', 'tiled_sha256', 'labels'} or t['object'] in objects
                    or not isinstance(t['labels'], list) or not 1 <= len(t['labels']) <= 32
                    or len(set(t['labels'])) != len(t['labels'])
                    or not set(t['labels']) <= requests.keys()):
                raise ValueError('invalid native texture request')
            objects.add(t['object'])
    return requests


def build(profile, project, source, output):
    project, source, output = [Path(p).resolve() for p in (project, source, output)]
    if output.exists() or source.is_relative_to(output) or output.is_relative_to(source):
        raise ValueError('new disjoint output directory required')
    requests = validate(profile); labels = load_labels(profile, project)
    fonts = {}; tile_cache = {}; results = []; operations = []
    # Preflight the entire input set before creating any output.
    for row in profile['resources']:
        locked(source, dict(path=row['path'], sha256=row['sha256']))
    for lid in requests:
        label = labels[lid]
        if label.get('glyph_mask') or label.get('appearance', {}).get('kind') != 'source-style-v1':
            raise ValueError('explicit raster lettering required')
        revise(label, requests[lid]['remove_gradient_positions'])
        ref = label['font']
        if ref['sha256'] not in fonts:
            fonts[ref['sha256']] = locked(project, ref)
    output.mkdir(parents=True)
    for row in profile['resources']:
        original = locked(source, dict(path=row['path'], sha256=row['sha256']))
        require_raw_envelope(original); current = original
        for spec in row['textures']:
            t = selected(current, spec['object'], None)[3]
            if sha(t['tiles']) != spec['tiled_sha256']:
                raise ValueError('native texture SHA256 mismatch')
            used = set()
            for lid in spec['labels']:
                units = set(rect_units(t['layout'], labels[lid]['rect']))
                if units & used:
                    raise ValueError('RGB band label rectangles overlap')
                used.update(units)
            key = (spec['tiled_sha256'], tuple(spec['labels']))
            if key not in tile_cache:
                tiles = t['tiles']; proofs = []
                for lid in spec['labels']:
                    label = labels[lid]
                    request = requests[lid]; proof = {}
                    if request['remove_gradient_positions'] or request.get('refit_rows') or not request.get('restore_outline_rgb'):
                        tiles, proof = repair(dict(t, tiles=tiles), label,
                                              fonts[label['font']['sha256']],
                                              request['remove_gradient_positions'],
                                              request.get('refit_rows', []))
                    if request.get('restore_outline_rgb'):
                        tiles, edge = repair_dark_outline(dict(t, tiles=tiles),
                            revise(label, request['remove_gradient_positions']), fonts[label['font']['sha256']])
                        proof['outline_rgb'] = edge
                    proofs.append(dict(id=lid, **proof))
                tile_cache[key] = tiles, proofs
            tiles, proofs = tile_cache[key]
            if tiles == t['tiles']:
                raise ValueError('empty native band repair')
            current, proof = replace_tiles(current, sha(current), spec['object'], tiles,
                                           [labels[lid]['rect'] for lid in spec['labels']], None)
            operations.append(dict(resource=row['path'], before_tiled_sha256=spec['tiled_sha256'],
                                   after_tiled_sha256=sha(tiles), labels=proofs, **proof))
        current += bytes((-len(current)) % ALIGNMENT)
        require_raw_envelope(current)
        target = confined(output, 'candidate/' + row['path'])
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(current)
        if target.read_bytes() != current:
            raise ValueError('candidate readback mismatch')
        results.append(dict(path=row['path'], file='candidate/' + row['path'],
                            before_sha256=row['sha256'], sha256=sha(current),
                            size=len(current), discs=row['discs']))
    for row in profile['resources']:
        locked(source, dict(path=row['path'], sha256=row['sha256']))
    manifest = dict(schema_version=1, resources=results, operations=operations,
                    label_count=len(requests), game_started=False, game_rendering_verified=False)
    files = {'manifest.json': manifest}
    for disc in (1, 2):
        files[f'replacements-disc{disc}.json'] = dict(schema_version=1,
            kind='incremental-comparison-replacements', disc=disc,
            toc_path='MC2Game/Xbox360TOC.txt', resources=[{k: v for k, v in r.items() if k != 'discs'}
                                                      for r in results if disc in r['discs']])
    for name, obj in files.items():
        data = (json.dumps(obj, ensure_ascii=False, indent=2)+'\n').encode()
        path = output/name; path.write_bytes(data)
        if path.read_bytes() != data:
            raise ValueError('manifest readback mismatch')
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('profile', 'source-root', 'output'):
        p.add_argument('--'+key, type=Path, required=True)
    p.add_argument('--profile-sha256', required=True)
    p.add_argument('--project-root', type=Path, default=Path('.'))
    a = p.parse_args(); raw = a.profile.read_bytes()
    if sha(raw) != a.profile_sha256:
        raise ValueError('profile SHA256 mismatch')
    result = build(json.loads(raw), a.project_root, a.source_root, a.output)
    print(f'LABELS={result["label_count"]} TEXTURES={len(result["operations"])} '
          f'RESOURCES={len(result["resources"])} ALPHA=UNCHANGED RESULT=PASS')


if __name__ == '__main__':
    main()
