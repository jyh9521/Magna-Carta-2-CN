"""Build a hash-locked, undeployed supplement bundle for all planned Font aliases."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path

try:
    from .font_binding_plan import digest, validate_binding_plan, _hash, _relative, _read
    from .font_binding_audit import fingerprint
    from .inspect_font_references import _tables
    from .supplement_font import rasterize_plan, supplement_package, validate_plan as validate_glyph_plan
    from .ue3_package import FormatError, LzxDecoder, parse_summary, write_report
    from .ue3_ui_styles import StyleGraph
    from .update_resource_sizes import update_sizes
except ImportError:
    from font_binding_plan import digest, validate_binding_plan, _hash, _relative, _read
    from font_binding_audit import fingerprint
    from inspect_font_references import _tables
    from supplement_font import rasterize_plan, supplement_package, validate_plan as validate_glyph_plan
    from ue3_package import FormatError, LzxDecoder, parse_summary, write_report
    from ue3_ui_styles import StyleGraph
    from update_resource_sizes import update_sizes


def validate_plan(plan):
    sources = validate_binding_plan(plan)
    supplement = plan.get('supplement')
    if not isinstance(supplement, dict):
        raise FormatError('supplement plan reference required')
    _relative(supplement.get('path'))
    _hash(supplement.get('sha256'))
    _hash(plan.get('font_source_sha256'))
    _hash(plan.get('expected_supplement_semantic_sha256'))
    if plan['expected_semantic_sha256'] == plan['expected_supplement_semantic_sha256']:
        raise FormatError('supplement must change font semantics')
    return sources


def context(data, decoder):
    logical, tables = _tables(data, digest(data), decoder)
    return dict(logical=logical, tables=tables, sha256=digest(data),
                package_guid=parse_summary(data, len(data))['guid'])


def select_font(graph, source, plan):
    label = source['label'].casefold()
    matches = graph.paths[label].get(source['font_object'].casefold(), [])
    if len(matches) != 1:
        raise FormatError('font object missing or ambiguous: ' + label)
    node = label, matches[0]
    identity = graph.canonical_identity(node)
    if (identity['canonical_path'] != plan['canonical_font_path'].casefold()
            or identity['namespace_guid'] != plan['expected_namespace_guid']):
        raise FormatError('font namespace/GUID mismatch: ' + label)
    return node


def restore_copy(candidate, control, output, candidate_sha256, original_sha256):
    """Exercise guarded backup restoration on a NEW isolated candidate copy.

    This is not reconstruction of compressed source bytes from a candidate,
    nor installation/uninstallation against a game directory.
    """
    candidate, control, output = Path(candidate), Path(control), Path(output)
    _hash(candidate_sha256); _hash(original_sha256)
    if output.exists() or output.is_symlink():
        raise FormatError('restoration check output must be new')
    modified, original = candidate.read_bytes(), control.read_bytes()
    if digest(modified) != candidate_sha256 or digest(original) != original_sha256:
        raise FormatError('restoration input hash mismatch')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as stream:
        stream.write(modified)
    if digest(output.read_bytes()) != candidate_sha256:
        raise FormatError('restoration candidate copy mismatch')
    output.write_bytes(original)
    if output.read_bytes() != original:
        raise FormatError('restoration original copy mismatch')
    return dict(path=str(output), sha256=original_sha256, byte_identical_to_original=True,
                method='hash-guarded-retained-original-backup')


def save_bytes(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)
    if path.read_bytes() != data:
        raise FormatError('bundle file reopening mismatch')
    return dict(path=str(path), sha256=digest(data), size=len(data))


def save_report(path, report):
    report = json.loads(json.dumps(report))
    write_report(path, report)
    if json.loads(path.read_text(encoding='utf-8')) != report:
        raise FormatError('bundle report reopening mismatch')
    return report


def build(plan, game_root, project_root, font_file, output_root, decoder=None):
    sources = validate_plan(plan)
    game_root, project_root, font_file = Path(game_root).resolve(), Path(project_root).resolve(), Path(font_file).resolve()
    output_root = Path(output_root)
    if output_root.exists() or output_root.is_symlink():
        raise FormatError('supplement output directory must be new')
    output_root = output_root.resolve()
    if output_root.is_relative_to(game_root):
        raise FormatError('supplement outputs must be outside selected game root')
    glyph_bytes, glyph_path = _read(project_root, plan['supplement']['path'], plan['supplement']['sha256'])
    glyph_plan = json.loads(glyph_bytes.decode('utf-8-sig'))
    glyphs = validate_glyph_plan(glyph_plan)
    font_bytes = font_file.read_bytes()
    if digest(font_bytes) != plan['font_source_sha256']:
        raise FormatError('font source SHA256 mismatch')
    toc, toc_path = _read(game_root, plan['toc']['path'], plan['toc']['sha256'])
    inputs = [(glyph_path, plan['supplement']['sha256']), (font_file, plan['font_source_sha256']),
              (toc_path, plan['toc']['sha256'])]
    originals, contexts = {}, {}
    for source in sources:
        label = source['label'].casefold()
        raw, path = _read(game_root, source['path'], source['sha256'])
        originals[label] = raw
        contexts[label] = context(raw, decoder)
        inputs.append((path, source['sha256']))
    graph = StyleGraph(contexts)
    before = {}
    for source in sources:
        label = source['label'].casefold()
        before[label] = fingerprint(graph, select_font(graph, source, plan), decoder)
        if before[label]['semantic_sha256'] != plan['expected_semantic_sha256']:
            raise FormatError('original font semantic mismatch: ' + label)
    # Rasterize once for every alias; the expected complete output fingerprint
    # rejects dependency-version/raster differences instead of silently drifting.
    alphas, rasters = rasterize_plan(font_file, plan['font_source_sha256'], glyph_plan)
    candidates, changes = {}, []
    for source in sources:
        label = source['label'].casefold()
        candidate, report = supplement_package(originals[label], source['sha256'], source['font_object'],
                                                glyph_plan, alphas, decoder)
        updated = dict(contexts); updated[label] = context(candidate, decoder)
        after_graph = StyleGraph(updated)
        after = fingerprint(after_graph, select_font(after_graph, source, plan), decoder)
        if (after['semantic_sha256'] != plan['expected_supplement_semantic_sha256']
                or after['glyph_count'] != before[label]['glyph_count'] + len(glyphs)
                or after['remap_count'] != before[label]['remap_count'] + len(glyphs)):
            raise FormatError('supplement semantic/count mismatch: ' + label)
        candidates[label] = dict(data=candidate, report=report, fingerprint=after)
        if len(candidate) != len(originals[label]):
            changes.append(dict(path=source['path'], expected_size=len(originals[label]), new_size=len(candidate)))
    new_toc = update_sizes(toc, plan['toc']['sha256'], changes) if changes else toc
    reverse = [dict(path=c['path'], expected_size=c['new_size'], new_size=c['expected_size']) for c in changes]
    if (update_sizes(new_toc, digest(new_toc), reverse) if reverse else new_toc) != toc:
        raise FormatError('supplement TOC inverse mismatch')
    for path, expected in inputs:
        if digest(path.read_bytes()) != expected:
            raise FormatError('input changed during supplement build')
    # Publish only after all in-memory candidates and original hashes validate.
    output_root.mkdir(parents=True, exist_ok=False)
    rows = []
    for source in sources:
        label = source['label'].casefold(); candidate = candidates[label]
        control = save_bytes(output_root/'controls'/(label+'.xxx'), originals[label])
        changed = save_bytes(output_root/'candidates'/(label+'.xxx'), candidate['data'])
        restored = restore_copy(changed['path'], control['path'], output_root/'rollback-check'/(label+'.xxx'),
                                changed['sha256'], source['sha256'])
        report_path = output_root/'reports'/(label+'.json')
        save_report(report_path, candidate['report'])
        rows.append(dict(label=label, source_path=source['path'], files=dict(control=control,candidate=changed,restored=restored),
                         semantic_before=before[label]['semantic_sha256'], semantic_after=candidate['fingerprint']['semantic_sha256'],
                         report=str(report_path)))
    toc_file = save_bytes(output_root/'Xbox360TOC.txt', new_toc)
    save_bytes(output_root/'rollback-check'/'Xbox360TOC.txt', toc)
    for path, expected in inputs:
        if digest(path.read_bytes()) != expected:
            raise FormatError('input changed during bundle publication')
    versions = {}
    for name in ('Pillow','fonttools'):
        try: versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: versions[name] = None
    manifest = dict(schema_version=1, mode='all-planned-aliases-font-supplement',
        canonical_build_plan_sha256=digest(json.dumps(plan,sort_keys=True,separators=(',',':')).encode()),
        supplement_plan_sha256=plan['supplement']['sha256'], font_source_sha256=plan['font_source_sha256'],
        canonical_font_path=plan['canonical_font_path'], added_codepoints=[ord(g['character']) for g in glyphs],
        rasters=rasters, raster_alpha_sha256={str(k):digest(v) for k,v in alphas.items()}, dependency_versions=versions,
        sources=rows, toc=toc_file, toc_changes=changes, toc_inverse_byte_identical=True,
        original_hashes_rechecked=True, text_resources_changed=False, raw_atlas_requested=False,
        game_rendering_verified=False, deployment_performed=False)
    return save_report(output_root/'manifest.json', manifest)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan', type=Path, required=True)
    p.add_argument('--game-root', type=Path, required=True)
    p.add_argument('--project-root', type=Path, default=Path('.'))
    p.add_argument('--font-file', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--lzx-library', type=Path, required=True)
    a = p.parse_args(argv)
    try:
        plan = json.loads(a.plan.read_text(encoding='utf-8-sig'))
        report = build(plan,a.game_root,a.project_root,a.font_file,a.output_dir,LzxDecoder(a.lzx_library))
        print(json.dumps(dict(sources=len(report['sources']), added_codepoints=report['added_codepoints'],
                              manifest=str(a.output_dir.resolve()/'manifest.json'), deployment_performed=False),sort_keys=True))
        return 0
    except (OSError,ValueError,KeyError,TypeError,ImportError) as exc:
        print('ERROR: '+str(exc)); return 2


if __name__ == '__main__': raise SystemExit(main())
