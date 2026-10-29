"""Compose locked resource revisions, tagged fields and bounded native tiles.

Components remain immutable. This offline tool does not refresh a test copy or
disc image. It refuses unknown inputs and never replaces an entire package with
a texture donor, which could discard an earlier font or UI-field revision.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from .build_font_supplement import context
from .font_binding_plan import confined_path
from .patch_tagged_fields import patch
from .reface_font import sha
from .replace_texture_regions import selected, replace_tiles
from .ue3_package import LzxDecoder
from .verify_resource_phase import relative, hash_value, unique


def compose(plan, root, decoder=None):
    root = Path(root).resolve()
    if (set(plan) != {'schema_version', 'kind', 'resources'}
            or type(plan.get('schema_version')) is not int or plan['schema_version'] != 1
            or plan.get('kind') != 'offline-resource-revision-layers'):
        raise ValueError('revision layer schema')
    rows = plan['resources']
    if not isinstance(rows, list) or not 1 <= len(rows) <= 512:
        raise ValueError('revision resource bound')
    names = [relative(r['path']) for r in rows]
    if len(set(p.casefold() for p in names)) != len(names) or any(p.lower().endswith('.xex') for p in names):
        raise ValueError('duplicate or executable resource')
    snapshots, result, reports = {}, {}, []

    def locked(ref):
        if set(ref) != {'file', 'sha256'}:
            raise ValueError('locked input requires file and SHA256')
        path = confined_path(root, ref['file'])
        if not path.is_file() or not 0 < path.stat().st_size <= 512*1024*1024:
            raise ValueError('component file bound')
        data = path.read_bytes()
        if sha(data) != hash_value(ref['sha256']):
            raise ValueError('component SHA256 mismatch: '+ref['file'])
        snapshots[path] = ref['sha256']
        return data

    for row in rows:
        if set(row) - {'path', 'discs', 'before', 'base', 'fields', 'textures'}:
            raise ValueError('unknown revision resource field')
        discs = row['discs']
        if not discs or discs != sorted(set(discs)) or any(type(d) is not int or d not in (1, 2) for d in discs):
            raise ValueError('explicit disc membership required')
        before = locked(row['before']); data = locked(row['base'])
        proof = dict(path=row['path'], discs=discs, before_sha256=sha(before),
                     before_size=len(before), base_sha256=sha(data), operations=[])
        if 'fields' in row:
            field_plan = json.loads(locked(row['fields']), object_pairs_hook=unique)
            data, p = patch(data, context(data, decoder), field_plan)
            proof['operations'].append(dict(kind='tagged-fields', proof=p))
        textures = row.get('textures', [])
        if len(textures) > 32 or len({e['object'] for e in textures}) != len(textures):
            raise ValueError('duplicate or excessive texture edits')
        for edit in textures:
            if set(edit) != {'object', 'rects', 'before_tiles_sha256', 'tiles'}:
                raise ValueError('invalid texture transfer')
            old = selected(data, edit['object'], decoder)[3]['tiles']
            if sha(old) != hash_value(edit['before_tiles_sha256']):
                raise ValueError('native texture input SHA256 mismatch')
            data, p = replace_tiles(data, sha(data), edit['object'], locked(edit['tiles']), edit['rects'], decoder)
            proof['operations'].append(dict(kind='native-tiles', proof=p))
        if data == before:
            raise ValueError('selected revision has no changes')
        proof.update(sha256=sha(data), size=len(data))
        result[row['path']] = data; reports.append(proof)
    for path, digest in snapshots.items():
        if sha(path.read_bytes()) != digest:
            raise ValueError('component changed during composition')
    return result, dict(schema_version=1, kind='offline-composed-resource-revision',
                        resources=reports, game_started=False, game_rendering_verified=False)


def build(plan, root, output, decoder=None):
    root, output = Path(root).resolve(), Path(output).absolute()
    if (output.exists() or output.is_symlink()
            or getattr(output, 'is_junction', lambda: False)()
            or output.resolve() != output or output.parent.resolve() != output.parent):
        raise ValueError('new canonical output directory required')
    for row in plan['resources']:
        refs = [row['before'], row['base']]
        if 'fields' in row: refs.append(row['fields'])
        refs.extend(e['tiles'] for e in row.get('textures', []))
        if any(confined_path(root, r['file']).is_relative_to(output) for r in refs):
            raise ValueError('output overlaps component inputs')
    files, report = compose(plan, root, decoder)
    for name, data in files.items():
        path = confined_path(output, 'candidate/'+name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as f: f.write(data)
        if path.read_bytes() != data:
            raise ValueError('composed resource reopening mismatch')
    raw = (json.dumps(report, ensure_ascii=False, indent=2)+'\n').encode()
    (output/'manifest.json').write_bytes(raw)
    if (output/'manifest.json').read_bytes() != raw:
        raise ValueError('manifest reopening mismatch')
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('plan', 'root', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--plan-sha256', required=True)
    p.add_argument('--lzx-library', type=Path)
    a = p.parse_args()
    raw = a.plan.read_bytes()
    if sha(raw) != hash_value(a.plan_sha256):
        raise ValueError('revision plan SHA256 mismatch')
    plan = json.loads(raw, object_pairs_hook=unique)
    report = build(plan, a.root, a.output, LzxDecoder(a.lzx_library) if a.lzx_library else None)
    print(json.dumps(dict(resources=len(report['resources']), game_started=False, status='PASS')))


if __name__ == '__main__':
    main()
