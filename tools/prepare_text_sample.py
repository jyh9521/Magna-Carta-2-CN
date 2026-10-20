"""Derive hash-locked font/route plans from a source-locked text sample.

Uses existing Font atlases only, finds disjoint BC3 cells, and leaves originals
untouched. Generated plans can be rebuilt by build_font_route_probe.py.
"""
from __future__ import annotations
import argparse
import copy
import json
import unicodedata
from pathlib import Path

from tools.font_binding_plan import digest, read_locked_json, _read, parse_json_object
from tools.build_font_supplement import context, select_font, validate_plan
from tools.build_font_route_probe import encoded
from tools.font_binding_audit import fingerprint
from tools.ue3_ui_styles import StyleGraph
from tools.ue3_fonts import parse_font_payload
from tools.supplement_font import (parse_atlas_payload, block_rect,
                                   rasterize_plan, supplement_package, MAX_ADDITIONAL_GLYPHS)
from tools.audit_text_font_coverage import literal_codepoints
from tools.build_coalesced import rebuild, resolve_changes
from tools.ue3_package import LzxDecoder, parse_summary
from tools.decompress_package import decompress_copy


def classify_font_demand(font, codepoints, transparent=()):
    """Separate drawable additions from layout/control policy; never drop demand.

    The 256-entry non-remapped model is the existing supplement conversion
    contract, not a claim about arbitrary non-remapped runtime fonts.
    """
    requested = list(codepoints)
    if any(type(cp) is not int or not 0 <= cp <= 0x10ffff or 0xd800 <= cp <= 0xdfff
           for cp in requested):
        raise ValueError('font demand requires Unicode scalar integers')
    wanted = set(requested)
    if font['is_remapped']:
        mapped = {r['codepoint'] for r in font['remap']}
        model = 'explicit-remap'
    else:
        if len(font['characters']) != 256:
            raise ValueError('non-remapped demand requires the existing 256-glyph conversion model')
        mapped, model = set(range(256)), '256-glyph-identity-conversion'
    blank = set(transparent)
    if not blank <= wanted & mapped:
        raise ValueError('transparent repairs must be requested and already mapped')
    needed = (wanted - mapped) | blank
    layout = {cp for cp in needed if chr(cp).isspace() or unicodedata.category(chr(cp)).startswith('C')}
    outside = {cp for cp in needed if cp > 0xffff}
    return dict(mapping_model=model, requested_codepoints=sorted(wanted),
                missing_codepoints=sorted(wanted - mapped), transparent_repairs=sorted(blank),
                required_additions=sorted(needed), layout_or_control_additions=sorted(layout),
                outside_bmp_additions=sorted(outside),
                drawable_additions=sorted(needed - layout - outside))


def allocate(font, texture, characters, template):
    """Deterministic first-fit in block coordinates; never reuses old glyph cells."""
    index = template['texture_index']
    w, h = template['width'], template['height']
    rectangles = [block_rect((g['StartU'], g['StartV'], g['USize'], g['VSize']))
            for g in font['characters'] if g['TextureIndex'] == index and g['USize'] and g['VSize']]
    # BC3 block occupancy preserves first-fit ordering without a scan of every
    # existing glyph for each candidate cell in a larger translation batch.
    def blocks(rect):
        x0, y0, width, height = rect
        return {(x, y) for y in range(y0, y0+height) for x in range(x0, x0+width)}
    used = set().union(*(blocks(rect) for rect in rectangles))
    result = []
    # Occupancy only grows: a rejected earlier position can never become free.
    # Keep a monotonic cursor instead of restarting at (0, 0) for every glyph.
    positions = ((x, y) for y in range(0, texture['height']-h+1, 4)
                        for x in range(0, texture['width']-w+1, 4))
    for char in characters:
        found = None
        for x, y in positions:
            occupied = blocks(block_rect((x, y, w, h)))
            if not occupied & used:
                found = dict(character=char, texture_index=index, x=x, y=y, width=w, height=h)
                used.update(occupied)
                break
        if found is None:
            raise ValueError('insufficient unused atlas cells for sample')
        result.append(found)
    return result


def prepare(base_route, sample, game_root, project_root, font_file, output, decoder,
            glyph_limit=128, metric_heights=None, repair_blank=False, fit_ink_widths=False, additional_plans=(),ink_padding=None,wide_letter_tracking=None):
    project_root, output = Path(project_root).resolve(), Path(output).resolve()
    game_root = Path(game_root).resolve()
    if type(glyph_limit) is not int or not 1 <= glyph_limit <= MAX_ADDITIONAL_GLYPHS:
        raise ValueError(f'glyph_limit must be within 1..{MAX_ADDITIONAL_GLYPHS}')
    metric_heights = metric_heights or {}
    if ink_padding is not None and not fit_ink_widths:raise ValueError('ink padding requires explicit fit-ink-widths')
    if wide_letter_tracking is not None and (ink_padding is None or type(wide_letter_tracking) is not int or not 0<=wide_letter_tracking<=16):
        raise ValueError('wide letter tracking requires ink padding and bounded integer tracking')
    if (output.exists() or output.is_relative_to(game_root) or game_root.is_relative_to(output)
            or not output.is_relative_to(project_root)):
        raise ValueError('plan output must be new, within project and disjoint from originals')
    route_bytes = Path(base_route).read_bytes(); sample_bytes = Path(sample).read_bytes()
    route = parse_json_object(route_bytes); text_plan = parse_json_object(sample_bytes)
    if (route.get('kind') != 'offline-font-route-probe' or route.get('schema_version') != 1
            or route.get('raw_packages') is not True or route.get('game_rendering_verified') is not False):
        raise ValueError('sample preparation requires an explicit raw font-route probe')
    text, _ = _read(game_root, text_plan['resource'], text_plan['input_sha256'])
    resolved = resolve_changes(text, text_plan)
    wanted = sorted({cp for e in resolved['entries'] for cp in literal_codepoints(e['translation'])})
    changed_text = rebuild(text, text_plan)
    files = {}; refs = []; snapshots = [(Path(base_route), digest(route_bytes)), (Path(sample), digest(sample_bytes)),
                                        (Path(font_file), digest(Path(font_file).read_bytes()))]
    extra_refs=[]
    for path in additional_plans:
        path=Path(path).resolve();raw=path.read_bytes();ep=parse_json_object(raw)
        extra_refs.append(dict(path=path.relative_to(project_root).as_posix(),sha256=digest(raw)))
        snapshots.append((path,digest(raw)))
        wanted=sorted(set(wanted)|{cp for e in ep['entries'] for cp in literal_codepoints(e['translation'])})
    def ref(name, raw):
        files[name] = raw
        return dict(path=(output/name).relative_to(project_root).as_posix(), sha256=digest(raw))
    for i, spec in enumerate(route['font_plans']):
        fp, path, raw = read_locked_json(project_root, spec); validate_plan(fp)
        snapshots.append((path, digest(raw)))
        gp, path, raw = read_locked_json(project_root, fp['supplement'])
        snapshots.append((path, digest(raw)))
        source = fp['sources'][0]
        original, path = _read(game_root, source['path'], source['sha256'])
        snapshots.append((path, source['sha256']))
        raw = (decompress_copy(original, source['sha256'], decoder)[0]
               if parse_summary(original, len(original))['compression_flags'] else original)
        ctx = context(raw, decoder); label = source['label'].casefold()
        graph = StyleGraph({label: ctx}); node = select_font(graph, source, fp)
        if fingerprint(graph, node, decoder)['semantic_sha256'] != fp['expected_semantic_sha256']:
            raise ValueError('baseline font semantics mismatch')
        export = graph.export(*node); logical = ctx['logical']; names = ctx['tables']['names']
        font = parse_font_payload(logical[export['serial_offset']:export['serial_offset']+export['serial_size']], names)
        initial = classify_font_demand(font, wanted)
        mapped = set(wanted) - set(initial['missing_codepoints'])
        blank=[]
        if repair_blank:
            from tools.font_ink import ink_records
            blank=[r['codepoint'] for r in ink_records(ctx,font,[cp for cp in wanted if cp in mapped],decoder) if r['status']=='transparent']
        demand = classify_font_demand(font, wanted, blank)
        if demand['layout_or_control_additions']:
            labels = ', '.join(f'U+{cp:04X}' for cp in demand['layout_or_control_additions'])
            raise ValueError('sample needs explicit layout/control mappings: ' + labels)
        if demand['outside_bmp_additions']:
            raise ValueError('sample needs explicit outside-BMP handling')
        missing = [chr(cp) for cp in demand['drawable_additions']]
        if not 1 <= len(missing) <= glyph_limit:
            raise ValueError(f'sample must require 1..{glyph_limit} additional glyphs in each family')
        gp = copy.deepcopy(gp)
        gp.pop('atlas_height', None)
        gp.pop('replace_blank_codepoints',None)
        if blank:gp['replace_blank_codepoints']=blank
        if ink_padding is not None:
            gp['ink_padding']=dict(left=ink_padding[0],right=ink_padding[1])
            for g in gp['glyphs']:
                g['width']=max(g['width'],(gp['font_size']+sum(ink_padding)+3)//4*4)
        if wide_letter_tracking is not None:
            gp['wide_letter_advance']=gp['font_size']+wide_letter_tracking
            for g in gp['glyphs']:g['width']=max(g['width'],(gp['wide_letter_advance']+3)//4*4)
        if glyph_limit != 128:
            gp['glyph_limit'] = glyph_limit
        if i in metric_heights:
            old_height = max(g['VSize'] for g in font['characters'])
            height = metric_heights[i]
            if type(height) is not int or not old_height < height <= 128:
                raise ValueError('explicit metric height must increase original maximum within 128')
            gp['metric_height'] = height
            gp['metric_height_growth'] = dict(original=old_height, candidate=height)
            for glyph in gp['glyphs']:
                glyph['height'] = max(glyph['height'], (height+3)//4*4)
        template = gp['glyphs'][0]; atlas = ctx['tables']['exports'][font['textures'][template['texture_index']]-1]
        texture = parse_atlas_payload(logical[atlas['serial_offset']:atlas['serial_offset']+atlas['serial_size']], names, atlas['serial_offset'])
        try:
            placements = allocate(font, texture, missing, template)
        except ValueError:
            # Explicit generated opt-in; never silently alter a build plan.
            texture = copy.deepcopy(texture)
            height = 128
            while height <= texture['height']:
                height *= 2
            while height <= 2048:
                texture['height'] = height
                try:
                    placements = allocate(font, texture, missing, template)
                    gp['atlas_height'] = height
                    break
                except ValueError:
                    height *= 2
            else:
                raise ValueError('sample exceeds bounded atlas growth capacity')
        gp['glyphs'] = placements
        gp['purpose'] = 'Text-sample layout probe; game layout pending user acceptance'
        alphas, rasters = rasterize_plan(Path(font_file), fp['font_source_sha256'], gp)
        if fit_ink_widths:
            for g,r in zip(gp['glyphs'],rasters):
                box=r['raster_bbox']
                g['metric_width']=(box[2]-box[0]+sum(ink_padding) if ink_padding is not None
                                   else min(g['width'],box[2]-box[0]+2))
                if wide_letter_tracking is not None and unicodedata.category(g['character']).startswith('L') and unicodedata.east_asian_width(g['character']) in ('W','F'):
                    g['metric_width']=max(g['metric_width'],gp['wide_letter_advance'])
            alphas,_=rasterize_plan(Path(font_file),fp['font_source_sha256'],gp)
        changed, _ = supplement_package(raw, digest(raw), source['font_object'], gp, alphas, decoder, raw_atlas=True)
        new_graph = StyleGraph({label: context(changed, decoder)})
        fp = copy.deepcopy(fp)
        fp['expected_supplement_semantic_sha256'] = fingerprint(new_graph, select_font(new_graph, source, fp), decoder)['semantic_sha256']
        fp['supplement'] = ref(f'glyphs-{i}.json', encoded(gp))
        refs.append(ref(f'font-{i}.json', encoded(fp)))
    route = copy.deepcopy(route); route['font_plans'] = refs
    if extra_refs:route['additional_text_plans']=extra_refs
    if repair_blank:route['verify_glyph_ink']=True
    if set(metric_heights) - set(range(len(refs))):
        raise ValueError('metric height family index outside route')
    route['text_plan'] = dict(path=Path(sample).resolve().relative_to(project_root).as_posix(), sha256=digest(sample_bytes))
    route['expected_text_sha256'] = digest(changed_text)
    files['route.json'] = encoded(route)
    for path, expected in snapshots:
        if digest(path.read_bytes()) != expected:
            raise ValueError('plan source changed during preparation')
    output.mkdir(parents=True, exist_ok=False)
    for name, raw in files.items():
        path = output/name
        with path.open('xb') as f:
            f.write(raw)
        if path.read_bytes() != raw:
            raise ValueError('generated plan reopening mismatch')
    return dict(font_families=len(refs), literal_codepoints=len(wanted), game_started=False)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['base-route','sample','game-root','font-file','output','lzx-library']:
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--project-root', type=Path, default=Path('.'))
    p.add_argument('--glyph-limit', type=int, default=128)
    p.add_argument('--repair-blank', action='store_true')
    p.add_argument('--fit-ink-widths', action='store_true')
    p.add_argument('--additional-plan', action='append',type=Path,default=[])
    p.add_argument('--ink-padding',nargs=2,type=int,metavar=('LEFT','RIGHT'))
    p.add_argument('--wide-letter-tracking',type=int)
    p.add_argument('--metric-height', action='append', default=[], metavar='FAMILY_INDEX=HEIGHT',
                   help='Explicit opt-in to increased new-glyph metrics; old glyphs stay unchanged')
    a = p.parse_args(argv)
    try:
        pairs = [v.split('=') for v in a.metric_height]
        heights = {int(i): int(h) for i,h in pairs}
        if len(heights) != len(pairs):
            raise ValueError('duplicate metric height family')
        print(json.dumps(prepare(a.base_route,a.sample,a.game_root,a.project_root,a.font_file,a.output,LzxDecoder(a.lzx_library),a.glyph_limit,heights,a.repair_blank,a.fit_ink_widths,a.additional_plan,a.ink_padding,a.wide_letter_tracking), sort_keys=True))
        return 0
    except (ValueError, OSError, KeyError, TypeError, ImportError) as e:
        print('ERROR: '+str(e)); return 2


if __name__ == '__main__':
    raise SystemExit(main())
