"""Replay hash-locked sparse native-pixel transport for inline BC textures."""
import argparse
import io
import json
from pathlib import Path

from .build_font_supplement import context
from .font_binding_plan import confined_path, _hash
from .native_pixel_transport import transport_rgba
from .patch_tagged_fields import digest
from .sparse_artifact_paths import validate_patch_paths
from .texture_layout import read_texture, decode_texture
from .texture_overlay import select_texture_export
from .ue3_package import LzxDecoder


MAX_SOURCE_BYTES = 256 * 1024 * 1024
MAX_MASK_BYTES = 1024 * 1024
MAX_RECIPE_BYTES = 8 * 1024 * 1024


def locked_bytes(path, expected, limit):
    """Bound allocation even if a dependency grows after its initial stat."""
    _hash(expected)
    if type(limit) is not int or not 1 <= limit <= MAX_SOURCE_BYTES:
        raise ValueError('Native repair input limit bound')
    path = Path(path)
    if path.stat().st_size > limit:
        raise ValueError('Native repair dependency size bound')
    with path.open('rb') as stream:
        raw = stream.read(limit+1)
    if not raw or len(raw) > limit:
        raise ValueError('Native repair dependency size bound')
    if digest(raw) != expected:
        raise ValueError('Native repair dependency SHA256 mismatch')
    return raw


def build(recipe, root, output, decoder):
    from PIL import Image
    root, output = Path(root).resolve(), Path(output).resolve()
    if (recipe.get('schema_version') != 1
            or recipe.get('kind') != 'native-pixel-transport-texture-repair-v1'
            or recipe.get('method') != 'nearest-source-pixel-rgb-preserve-alpha-v1'
            or recipe.get('hidden_background') != 'native-motif-continuation-not-original-recovery'
            or not isinstance(recipe.get('cases'), list)
            or not 1 <= len(recipe['cases']) <= 128):
        raise ValueError('Unsupported native pixel repair recipe')
    if output.exists() or not output.is_relative_to(root) or output == root:
        raise ValueError('New project-contained repair output required')
    validate_patch_paths(recipe['cases'], output)
    contexts, snapshots, files, records = {}, {}, {}, []

    def locked(ref, limit=MAX_SOURCE_BYTES):
        if not isinstance(ref, dict) or set(ref) != {'path', 'sha256'}:
            raise ValueError('Explicit native repair dependency required')
        _hash(ref['sha256'])
        path = confined_path(root, ref['path'])
        raw = locked_bytes(path, ref['sha256'], limit)
        snapshots[path] = (ref['sha256'], limit)
        return raw

    def verify_snapshots():
        for path, (expected, limit) in snapshots.items():
            locked_bytes(path, expected, limit)

    def native(ref):
        key = ref['source']['path']
        if key not in contexts:
            contexts[key] = context(locked(ref['source']), decoder)
        c = contexts[key]
        if c['sha256'] != ref['source']['sha256']:
            raise ValueError('Inconsistent native repair source identity')
        e = select_texture_export(c['tables'], ref['object'])
        payload = c['logical'][e['serial_offset']:e['serial_offset']+e['serial_size']]
        t = read_texture(payload, c['tables']['names'], e['serial_offset'], ref['profile'], decoder)
        rgba = decode_texture(t)
        if ([t['width'], t['height']] != ref['dimensions']
                or digest(rgba) != ref['rgba_sha256']):
            raise ValueError('Native repair decoded source identity mismatch')
        return rgba, t['width'], t['height']

    seen = set()
    for case in recipe['cases']:
        if (not isinstance(case.get('id'), str) or not case['id'] or case['id'] in seen):
            raise ValueError('Unique native repair case identity required')
        seen.add(case['id'])
        source, width, height = native(case)
        raw = locked(case['mask'], MAX_MASK_BYTES)
        if len(raw) > 1024*1024:
            raise ValueError('Native repair mask size bound')
        with Image.open(io.BytesIO(raw)) as im:
            if im.format != 'PNG' or im.mode != 'L' or im.size != (width, height):
                raise ValueError('Native repair mask PNG geometry/mode mismatch')
            mask = im.tobytes()
        donors = {}
        if not isinstance(case['donors'], list) or not 1 <= len(case['donors']) <= 16:
            raise ValueError('Native donor count bound')
        for donor in case['donors']:
            if donor['id'] in donors:
                raise ValueError('Duplicate native donor')
            pixels, dw, dh = native(donor)
            donors[donor['id']] = dict(rgba=pixels, width=dw, height=dh,
                                     clean_rectangles=donor['clean_rectangles'])
        result, proof = transport_rgba(source, width, height, mask, donors, case['runs'])
        if digest(result) != case['result_rgba_sha256']:
            raise ValueError('Native repair result replay mismatch')
        sparse = b''.join(result[i*4:i*4+4] if value else bytes(4)
                          for i, value in enumerate(mask))
        buffer = io.BytesIO()
        Image.frombytes('RGBA', (width, height), sparse).save(buffer, format='PNG')
        patch = buffer.getvalue()
        if digest(patch) != case['patch']['sha256']:
            raise ValueError('Native repair patch PNG replay mismatch')
        files[case['patch']['path']] = patch
        records.append(dict(id=case['id'], source_rgba_sha256=digest(source),
                            result_rgba_sha256=digest(result),
                            patch_sha256=digest(patch), **proof))
    verify_snapshots()
    result = dict(schema_version=1, cases=records, game_rendering_verified=False,
                  hidden_background=recipe['hidden_background'])
    metadata = (json.dumps(result, indent=2)+'\n').encode('utf8')
    files['manifest.json'] = metadata
    output.mkdir()
    for name, raw in files.items():
        path = confined_path(output, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(raw)
    if any(confined_path(output, name).read_bytes() != raw for name, raw in files.items()):
        raise ValueError('Native repair artifact final readback mismatch')
    verify_snapshots()
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('recipe', 'project-root', 'output-dir', 'lzx-library'):
        p.add_argument('--'+key, required=True, type=Path)
    p.add_argument('--recipe-sha256', required=True)
    a = p.parse_args()
    raw = locked_bytes(a.recipe, a.recipe_sha256, MAX_RECIPE_BYTES)
    result = build(json.loads(raw), a.project_root, a.output_dir, LzxDecoder(a.lzx_library))
    if locked_bytes(a.recipe, a.recipe_sha256, MAX_RECIPE_BYTES) != raw:
        raise ValueError('Native repair recipe changed during build')
    print(f"REPAIRS={len(result['cases'])} NATIVE_DONORS=ALL UNMASKED_PRESERVED=ALL RESULT=PASS")


if __name__ == '__main__':
    main()
