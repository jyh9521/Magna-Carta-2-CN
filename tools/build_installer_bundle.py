"""Build a content-addressed release bundle from originals and locked candidates.

The recipe is build-only input (paths may point at ignored local build products).
The result contains manifest metadata and source-dependent deltas, never ISOs,
XEX executables, STFS containers or complete localized UE3 packages.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

from .disc_inventory import Disc
from .decompress_package import decompress_copy
from .installer_core import Bundle, execution_id, sha_file, safe_relative, validate_manifest
from .installer_delta import create_delta, apply_delta, digest
from .runtime_envelope import require_raw_envelope
from .stfs_package import StfsPackage
from .ue3_package import LzxDecoder, parse_summary


def build(recipe_path, expected, output):
    recipe_path, output = Path(recipe_path).resolve(), Path(output).resolve()
    raw = recipe_path.read_bytes()
    if digest(raw) != expected:
        raise ValueError('recipe SHA256 mismatch')
    recipe = json.loads(raw)
    if output.exists():
        raise FileExistsError('bundle output must be new')
    output.mkdir(parents=True)
    (output / 'patches').mkdir()
    (output / 'tools').mkdir()
    manifest = dict(schema_version=1, kind='localization-installer', version=recipe['version'],
                    title_id=recipe['title_id'], output_name=recipe['output_name'], discs=[], dlc=[], tools={},
                    candidate_provenance=recipe.get('provenance', []), game_runtime_tested=False)
    for name, tool in recipe['tools'].items():
        path = Path(tool['file']).resolve()
        if sha_file(path) != tool['sha256']:
            raise ValueError('tool identity mismatch: ' + name)
        relative = 'tools/' + path.name
        safe_relative(relative)
        shutil.copyfile(path, output / relative)
        manifest['tools'][name] = dict(path=relative, sha256=tool['sha256'])
    decoder = None
    cache = {}

    def patch_entry(source, target, envelope=False):
        nonlocal decoder
        key = (digest(source), digest(target), envelope)
        if key in cache:
            return dict(cache[key])
        transform, base = 'identity', source
        if envelope:
            require_raw_envelope(target)
            if parse_summary(source, len(source))['compression_flags'] == 4:
                if decoder is None:
                    decoder = LzxDecoder(output / manifest['tools']['lzx']['path'])
                base, _ = decompress_copy(source, digest(source), decoder, alignment=1)
                transform = 'ue3-raw-v1'
        patch = create_delta(base, target)
        if apply_delta(base, patch) != target:
            raise ValueError('independent delta replay failed')
        patch_hash = digest(patch)
        name = 'patches/' + patch_hash + '.mcdelta'
        path = output / name
        if path.exists():
            if sha_file(path) != patch_hash:
                raise ValueError('patch cache identity mismatch')
        else:
            with path.open('xb') as stream:
                stream.write(patch)
        result = dict(transform=transform, base_sha256=digest(base), output_size=len(target),
                      output_sha256=digest(target), patch=name, patch_sha256=patch_hash,
                      runtime_envelope=envelope)
        cache[key] = result
        return dict(result)

    for n, definition in enumerate(recipe['discs'], 1):
        iso = Path(definition['iso']).resolve()
        print(f'VERIFY ISO {n}', flush=True)
        if sha_file(iso) != definition['sha256']:
            raise ValueError('original ISO SHA256 mismatch')
        disc = Disc(iso)
        inventory = [e for e in disc.inventory() if not e['directory']]
        overlays = {}
        for entry in definition['resources']:
            path = safe_relative(entry['path'])
            if path in overlays:
                raise ValueError('duplicate candidate path')
            overlays[path] = entry
        if not set(overlays) <= {e['path'] for e in inventory}:
            raise ValueError('candidate resource not on this disc')
        profile = dict(size=disc.size, partition_base=disc.base, sha256=definition['sha256'], files=[])
        with iso.open('rb') as stream:
            for i, entry in enumerate(inventory):
                name = entry['path']
                record = dict(path=name, size=entry['size'], sha256=disc.resource_hash(entry))
                if name == 'default.xex':
                    profile['execution_id'] = execution_id(disc.read(entry['offset'], entry['size']))
                    if name in overlays:
                        raise ValueError('XEX modification is not part of this release')
                if name in overlays:
                    overlay = overlays[name]
                    target_path = Path(overlay['file']).resolve()
                    target = target_path.read_bytes()
                    if digest(target) != overlay['sha256']:
                        raise ValueError('candidate SHA256 mismatch: ' + name)
                    if digest(target) != record['sha256']:
                        stream.seek(entry['offset'])
                        source = stream.read(entry['size'])
                        record.update(patch_entry(source, target, name.lower().endswith('.xxx')))
                profile['files'].append(record)
                if i % 50 == 0:
                    print(f'DISC {n} {i+1}/{len(inventory)} PATCHES {len(cache)}', flush=True)
        manifest['discs'].append(profile)
    for definition in recipe['dlc']:
        source = Path(definition['source']).read_bytes()
        target = Path(definition['candidate']).read_bytes()
        if digest(source) != definition['sha256'] or digest(target) != definition['output_sha256']:
            raise ValueError('DLC identity mismatch')
        for data in (source, target):
            info = StfsPackage(data).inventory()
            if info['title_id'] != recipe['title_id'] or info['content_type'] != '00000002':
                raise ValueError('DLC title/content identity mismatch')
        entry = dict(name=definition['name'], label=definition['label'], size=len(source), sha256=digest(source))
        entry.update(patch_entry(source, target))
        manifest['dlc'].append(entry)
    usage = Path(recipe['usage']).read_bytes()
    (output / 'USAGE.txt').write_bytes(usage)
    manifest['usage_sha256'] = digest(usage)
    validate_manifest(manifest)
    data = (json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True)+'\n').encode()
    (output / 'manifest.json').write_bytes(data)
    Bundle(output, digest(data))
    print(json.dumps(dict(manifest_sha256=digest(data), unique_patches=len(cache),
                         bundle_bytes=sum(p.stat().st_size for p in output.rglob('*') if p.is_file())), sort_keys=True), flush=True)
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recipe', type=Path, required=True)
    parser.add_argument('--recipe-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    build(args.recipe, args.recipe_sha256, args.output)


if __name__ == '__main__':
    main()
