"""Bounded native-BC baseline/modified/rollback probe for region-repair data.

Only selected texture allocations and preview PNGs are emitted. No package,
candidate tree, executable, game or disc image is produced or launched.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path

from .texture_region_repair import (digest, locked_bytes, merge_delta, resolve_layers,
                                   alpha_support_mask, protect_mask_rects, source_alpha_preservation)


def output_file(output, name):
    if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,160}',name):
        raise ValueError('invalid native fixture filename')
    path=(output/name).resolve()
    if path.parent != output.resolve() or (output/name).is_symlink():
        raise ValueError('native fixture escaped output directory')
    return path


def evaluate_pixels(case, rgba, original, width, labels):
    from .texture_overlay import rgba_crop
    checks = {}
    required = case['required_label']
    checks['required_translation_binding'] = labels.get(required, {}).get('text') == case['required_text']
    for index, rect in enumerate(case.get('empty_alpha_rects', [])):
        crop = rgba_crop(rgba, width, rect)
        checks['empty_alpha_%d' % index] = not any(crop[3::4])
    if 'required_change_rect' in case:
        rect = case['required_change_rect']
        checks['native_caption_changed'] = rgba_crop(rgba,width,rect) != rgba_crop(original,width,rect)
    for index, rect in enumerate(case.get('protected_rects', [])):
        checks['protected_pixels_%d' % index] = rgba_crop(rgba,width,rect) == rgba_crop(original,width,rect)
    return checks


def rollback(output):
    """Apply exact guarded changed-unit inverse data to isolated modified copies."""
    output = Path(output).resolve()
    manifest = json.loads((output/'DIFF_FILE.json').read_bytes())
    restored = []
    for case in manifest['cases']:
        source = output_file(output,case['modified_file'])
        modified = source.read_bytes()
        if digest(modified) != case['modified_sha256']:
            raise ValueError('rollback modified fixture SHA256 mismatch')
        data = bytearray(modified)
        for unit in case['units']:
            offset = unit['offset']; old = bytes.fromhex(unit['before']); new = bytes.fromhex(unit['after'])
            if (type(offset) is not int or offset < 0 or not old or offset+len(old)>len(data)
                    or len(old) != len(new) or data[offset:offset+len(new)] != new):
                raise ValueError('rollback expected native bytes mismatch')
            data[offset:offset+len(old)] = old
        if digest(data) != case['baseline_sha256']:
            raise ValueError('rollback did not restore baseline native data')
        target = output_file(output,case['id']+'-ROLLBACK.native')
        target.write_bytes(data)
        if target.read_bytes() != output_file(output,case['baseline_file']).read_bytes():
            raise ValueError('rollback reopen differs from baseline')
        sampled = {}
        if 'dimensions' in case:
            from PIL import Image
            from .texture_layout import unit_layout, decode_texture
            width,height=case['dimensions']
            pixels=decode_texture(dict(layout=unit_layout(width,height,case['format']),tiles=bytes(data)))
            if digest(pixels) != case['baseline_rgba_sha256']:
                raise ValueError('rollback native sampling differs from baseline')
            preview=output_file(output,case['id']+'-ROLLBACK.png')
            Image.frombytes('RGBA',(width,height),pixels).save(preview)
            if Image.open(preview).convert('RGBA').tobytes() != pixels:
                raise ValueError('rollback preview reopen mismatch')
            sampled=dict(sampled_rgba_sha256=digest(pixels),sampling='native-bc',preview=str(preview))
        restored.append(dict(id=case['id'],path=str(target),sha256=digest(data),
                             restored_status='baseline-native-identical',**sampled))
        if source.read_bytes() != modified:
            raise ValueError('rollback modified the delivered native fixture')
    (output/'ROLLBACK-report.json').write_text(json.dumps(restored,indent=2)+'\n',encoding='utf-8')
    print('PASS ROLLBACK %d/%d native copies restored; MODIFIED unchanged' % (len(restored),len(restored)))
    return 0


def verify_recipes(delta, contract, root, decoder):
    """Recompute tracked alpha masks from exact native crops, without writing art."""
    import io
    from PIL import Image
    from .build_font_supplement import context
    from .texture_overlay import select_texture_export, rgba_crop
    from .texture_layout import read_texture, decode_texture
    cases = {row['id']:row for row in contract['cases']}
    labels = {row['label']['id']:row['label'] for row in delta['labels']}
    results = []
    for recipe in delta['restoration_recipes']:
        if recipe['kind'] != 'transparent-alpha-support':
            raise ValueError('unsupported restoration recipe')
        case = cases[recipe['case_id']]; label = labels[recipe['label_id']]
        ctx = context(locked_bytes(root,case['source']['original']),decoder)
        target = case['texture']; ex=select_texture_export(ctx['tables'],target['object'])
        off=ex['serial_offset']; payload=ctx['logical'][off:off+ex['serial_size']]
        if digest(payload) != target['payload_sha256']:
            raise ValueError('restoration recipe payload mismatch')
        texture=read_texture(payload,ctx['tables']['names'],off,target['profile'],decoder)
        rgba=decode_texture(texture); crop=rgba_crop(rgba,texture['width'],label['rect'])
        if digest(rgba) != recipe['native_rgba_sha256'] or digest(crop) != recipe['source_rgba_sha256']:
            raise ValueError('restoration recipe source pixel hash mismatch')
        w,h=label['rect'][2:]
        mask=alpha_support_mask(crop,w,h,recipe['seed'])
        mask=protect_mask_rects(mask,w,h,recipe.get('preserve_rects',[]))
        if sum(v>0 for v in mask) != recipe['selected_pixels']:
            raise ValueError('restoration recipe alpha count mismatch')
        stored_mask=Image.open(io.BytesIO(locked_bytes(root,label['restoration']['mask'])))
        stored_patch=Image.open(io.BytesIO(locked_bytes(root,label['restoration']['patch'])))
        if (stored_mask.mode != 'L' or stored_mask.size != (w,h) or stored_mask.tobytes() != mask
                or stored_patch.mode != 'RGBA' or stored_patch.size != (w,h)
                or any(stored_patch.tobytes())):
            raise ValueError('restoration PNG differs from source-alpha recipe')
        results.append(dict(label_id=label['id'],selected_pixels=recipe['selected_pixels'],passed=True))
    return results


def run(plan, contract, root, output, decoder, mode):
    from PIL import Image
    from .build_font_supplement import context
    from .texture_overlay import select_texture_export, layer_ids, overlay_profile_regions
    from .texture_layout import read_texture, decode_texture, rect_units
    root = Path(root).resolve(); output = Path(output).resolve(); output.mkdir(parents=True,exist_ok=True)
    labels = {row['id']:row for row in plan['labels']}
    sources = {row['path']:row for row in plan['sources']}
    cases = contract['cases']
    if (contract.get('kind') != 'native-texture-region-repair-contracts'
            or contract.get('schema_version') != 1 or not 1 <= len(cases) <= 128):
        raise ValueError('unsupported native texture contract')
    if len({c['id'] for c in cases}) != len(cases):
        raise ValueError('duplicate native case ID')
    for case in cases:
        output_file(output,case['id']+'-MODIFIED.native')
    results = []; differences = []; aliases = {}
    for source_path in dict.fromkeys(case['source']['path'] for case in cases):
        selected = [case for case in cases if case['source']['path'] == source_path]
        source = selected[0]['source']; original_raw = locked_bytes(root,source['original'])
        ctx = context(original_raw,decoder)
        for case in selected:
            target = case['texture']; ex = select_texture_export(ctx['tables'],target['object'])
            off = ex['serial_offset']; payload = ctx['logical'][off:off+ex['serial_size']]
            if digest(payload) != target['payload_sha256']:
                raise ValueError('native payload hash mismatch')
            texture = read_texture(payload,ctx['tables']['names'],off,target['profile'],decoder)
            if digest(texture['tiles']) != target['tiled_sha256']:
                raise ValueError('native tiles hash mismatch')
            original = decode_texture(texture); width,height = texture['width'],texture['height']
            edits = sources.get(source_path,{}).get('textures',[])
            edit = next((e for e in edits if e['object'] == target['object']),None)
            tiles = texture['tiles']
            if edit is not None:
                if any(edit.get(k) != target.get(k) for k in ['payload_sha256','tiled_sha256','dimensions','profile']):
                    raise ValueError('plan/contract native identity mismatch')
                layers = resolve_layers(root,plan,layer_ids(edit))
                tiles,_ = overlay_profile_regions(texture,edit,layers,{})
            rgba = decode_texture(texture,tiles)
            checks = evaluate_pixels(case,rgba,original,width,labels)
            measurements = {}
            for index, rect in enumerate(case.get('protected_rects', [])):
                size=texture['layout']['unit_bytes']
                checks['protected_native_blocks_%d' % index] = all(
                    tiles[offset:offset+size] == texture['tiles'][offset:offset+size]
                    for offset in rect_units(texture['layout'],rect))
            if 'preserve_source_alpha' in case:
                import io
                guard=case['preserve_source_alpha']
                mask=Image.open(io.BytesIO(locked_bytes(root,guard['mask']))).convert('L')
                measurements.update(source_alpha_preservation(original,rgba,width,guard['rect'],mask.tobytes()))
                checks['source_art_alpha_pixels_unchanged'] = measurements['changed_source_pixels'] == 0
            prefix = case['id']+'-'+mode.upper()
            native_file = prefix+'.native'; image_file = prefix+'.png'
            (output/native_file).write_bytes(tiles)
            Image.frombytes('RGBA',(width,height),rgba).save(output/image_file)
            if (output/native_file).read_bytes() != tiles:
                raise ValueError('native fixture reopen mismatch')
            if Image.open(output/image_file).convert('RGBA').tobytes() != rgba:
                raise ValueError('native preview reopen mismatch')
            if mode == 'modified':
                baseline_file = case['id']+'-BASELINE.native'; baseline = (output/baseline_file).read_bytes()
                allowed = set()
                for rect in case['allowed_change_rects']:
                    allowed.update(rect_units(texture['layout'],rect))
                unit_size = texture['layout']['unit_bytes']; units = []
                for i in range(0,len(tiles),unit_size):
                    a,b = baseline[i:i+unit_size],tiles[i:i+unit_size]
                    if a != b:
                        if i not in allowed:
                            raise ValueError('delta changed a native block outside the requested caption')
                        units.append(dict(offset=i,before=a.hex(),after=b.hex()))
                checks['outside_caption_native_blocks_unchanged'] = True
                checks['changed_native_units'] = bool(units)
                differences.append(dict(id=case['id'],baseline_file=baseline_file,modified_file=native_file,
                    baseline_sha256=digest(baseline),modified_sha256=digest(tiles),units=units,
                    dimensions=[width,height],format=texture['layout']['format'],
                    baseline_rgba_sha256=digest(decode_texture(texture,baseline))))
            key = case.get('alias_group')
            if key is not None:
                if key in aliases and aliases[key] != digest(tiles):
                    raise ValueError('native alias output mismatch')
                aliases[key] = digest(tiles)
            results.append(dict(id=case['id'],source=source_path,object=target['object'],
                source_sha256=digest(original_raw),payload_sha256=digest(payload),
                original_tiled_sha256=digest(texture['tiles']),native_sha256=digest(tiles),
                rgba_sha256=digest(rgba),native_file=native_file,preview=image_file,
                checks=checks,measurements=measurements,passed=all(checks.values())))
        if digest(locked_bytes(root,source['original'])) != digest(original_raw):
            raise ValueError('original package changed during probe')
        del ctx, original_raw
    passed = sum(row['passed'] for row in results)
    report = dict(mode=mode,game_rendering_verified=False,cases=results,passed=passed,total=len(results))
    (output/(mode.upper()+'-report.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    if mode == 'modified':
        (output/'DIFF_FILE.json').write_text(json.dumps(dict(kind='native-texture-unit-delta',cases=differences),indent=2)+'\n',encoding='utf-8')
        (output/'MODIFIED_FILE.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('%s %s %d/%d native caption cases' % ('PASS' if passed==len(results) else 'FAIL',mode.upper(),passed,len(results)))
    for row in results:
        if not row['passed']:
            print(row['id']+': '+', '.join(k for k,v in row['checks'].items() if not v))
    return 0 if passed == len(results) else 1


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=['baseline','modified','rollback'],required=True)
    p.add_argument('--plan',type=Path)
    p.add_argument('--delta',type=Path)
    p.add_argument('--contract',type=Path)
    p.add_argument('--project-root',type=Path,default=Path('.'))
    p.add_argument('--lzx-library',type=Path)
    p.add_argument('--output',type=Path,required=True)
    args = p.parse_args()
    if args.mode == 'rollback':
        return rollback(args.output)
    if args.plan is None or args.contract is None or args.lzx_library is None:
        raise ValueError('plan, contract and LZX library required')
    from .ue3_package import LzxDecoder
    plan=json.loads(args.plan.read_bytes()); contract=json.loads(args.contract.read_bytes())
    recipes = []
    decoder=LzxDecoder(args.lzx_library)
    if args.delta is not None:
        if args.mode != 'modified': raise ValueError('delta is only valid for modified probe')
        delta=json.loads(args.delta.read_bytes())
        recipes=verify_recipes(delta,contract,args.project_root,decoder)
        plan=merge_delta(plan,delta)
    result=run(plan,contract,args.project_root,args.output,decoder,args.mode)
    if recipes:
        (args.output/'restoration-recipes-report.json').write_text(json.dumps(recipes,indent=2)+'\n',encoding='utf-8')
        print('PASS %d/%d transparent restoration recipes reproduced from native alpha' % (len(recipes),len(recipes)))
    return result


if __name__ == '__main__':
    raise SystemExit(main())
