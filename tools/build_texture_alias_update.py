"""Apply bounded label donors to all explicitly hash-locked physical aliases.

Rendering uses the existing overlay pipeline. A donor never replaces a whole
current package; unrelated fonts, UI fields and cumulative texture fixes stay.
"""
import argparse
import json
from pathlib import Path

from .build_texture_overlay import prepare
from .build_texture_region_update import transfer
from .font_binding_plan import confined_path
from .patch_tagged_fields import digest
from .replace_texture_regions import selected
from .ue3_package import LzxDecoder


def build(profile, project, source, output, decoder):
    project, source, output = (Path(p).resolve() for p in (project, source, output))
    if (set(profile) != {'schema_version', 'kind', 'overlay_plan', 'resources'}
            or profile['schema_version'] != 1 or profile['kind'] != 'texture-alias-update-v1'):
        raise ValueError('unsupported alias update profile')
    if output.exists() or output.is_relative_to(source) or source.is_relative_to(output):
        raise ValueError('new disjoint output required')
    ref = profile['overlay_plan']; plan_path = confined_path(project, ref['path'])
    plan_raw = plan_path.read_bytes()
    if digest(plan_raw) != ref['sha256']:
        raise ValueError('overlay plan SHA256 mismatch')
    plan = json.loads(plan_raw)
    resources = profile['resources']
    if not isinstance(resources, list) or not 1 <= len(resources) <= 256:
        raise ValueError('alias resource count bound')
    names = [r['path'] for r in resources]
    if len(set(n.casefold() for n in names)) != len(names):
        raise ValueError('duplicate alias resource')
    # All donor objects are shared between discs. Physical target membership is
    # explicit per resource and is never inferred from a matching leaf name.
    if any(s.get('discs') != [1, 2] for s in plan['sources']):
        raise ValueError('shared donor provenance required')
    snapshots = []
    for r in resources:
        if (set(r) != {'path', 'sha256', 'discs', 'textures'}
                or r['discs'] not in ([1], [2], [1, 2])
                or not r['path'].lower().endswith('.xxx')):
            raise ValueError('alias resource fields/discs')
        path = confined_path(source, r['path'])
        if digest(path.read_bytes()) != r['sha256']:
            raise ValueError('alias source SHA256 mismatch')
        snapshots.append((path, r['sha256']))
    donors, donor_manifest, dependencies = prepare(plan, project, decoder, 1)
    snapshots += dependencies
    files, records, proofs = {}, [], []
    for r in resources:
        original = confined_path(source, r['path']).read_bytes(); data = original
        textures = r['textures']
        if not 1 <= len(textures) <= 64 or len({t['object'] for t in textures}) != len(textures):
            raise ValueError('duplicate/excessive alias textures')
        for t in textures:
            if set(t) != {'object', 'tiled_sha256', 'donor_resource', 'donor_object', 'rectangles'}:
                raise ValueError('alias texture fields')
            tx = selected(data, t['object'], decoder)[3]
            if digest(tx['tiles']) != t['tiled_sha256']:
                raise ValueError('alias texture SHA256 mismatch')
            donor = donors['candidate/' + t['donor_resource']]
            data, proof, _ = transfer(data, digest(data), t['object'], donor,
                                      t['donor_object'], t['rectangles'], decoder)
            proofs.append(dict(resource=r['path'], **proof))
        if data == original:
            raise ValueError('empty alias revision')
        name = 'candidate/' + r['path']; files[name] = data
        records.append(dict(path=r['path'], file=name, before_sha256=r['sha256'],
                            sha256=digest(data), size=len(data), discs=r['discs']))
    manifest = dict(schema_version=1, resources=records, proofs=proofs,
                    donor_manifest=donor_manifest, game_started=False, game_rendering_verified=False)
    metadata = {'manifest.json': manifest}
    for disc in (1, 2):
        metadata[f'replacements-disc{disc}.json'] = dict(schema_version=1,
            kind='incremental-comparison-replacements', disc=disc, toc_path='MC2Game/Xbox360TOC.txt',
            resources=[{k:v for k,v in r.items() if k != 'discs'} for r in records if disc in r['discs']])
    for name, value in metadata.items():
        files[name] = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
    for path, expected in snapshots:
        if digest(path.read_bytes()) != expected:
            raise ValueError('alias dependency changed during build')
    if plan_path.read_bytes() != plan_raw:
        raise ValueError('overlay plan changed during build')
    for name, data in files.items():
        p = confined_path(output, name); p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('xb') as stream:
            stream.write(data)
        if p.read_bytes() != data:
            raise ValueError('alias output readback mismatch')
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('profile', 'project-root', 'source-root', 'output', 'lzx-library'):
        p.add_argument('--' + key, type=Path, required=True)
    p.add_argument('--profile-sha256', required=True)
    a = p.parse_args(); raw = a.profile.read_bytes()
    if digest(raw) != a.profile_sha256:
        raise ValueError('profile SHA256 mismatch')
    result = build(json.loads(raw), a.project_root, a.source_root, a.output, LzxDecoder(a.lzx_library))
    if a.profile.read_bytes() != raw:
        raise ValueError('profile changed during build')
    print(f"RESOURCES={len(result['resources'])} ALIASES={len(result['proofs'])} RESULT=PASS")


if __name__ == '__main__':
    main()
