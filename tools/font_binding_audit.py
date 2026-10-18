"""Normalize Font payloads across cooked/standalone namespace candidates."""
from __future__ import annotations

import hashlib
import json

try:
    from .ue3_package import FormatError
    from .ue3_fonts import parse_font_payload
    from .supplement_font import parse_atlas_payload, atlas_tiles
except ImportError:
    from ue3_package import FormatError
    from ue3_fonts import parse_font_payload
    from supplement_font import parse_atlas_payload, atlas_tiles


def fingerprint(graph, node, decoder=None):
    """Hash full validated glyph/remap data and every referenced decoded atlas.

    NetIndex, table-local property-name/object indices, bulk headers/offsets and
    compression representation are not rendered data and are excluded explicitly.
    No raw glyph table or proprietary image is emitted in the report.
    """
    e = graph.export(*node)
    if e['class_path'].rsplit('.', 1)[-1] != 'Font':
        raise FormatError('semantic fingerprint supports exact Font payloads only')
    ctx = graph.packages[node[0]]
    logical, names = ctx['logical'], ctx['tables']['names']
    start, size = e['serial_offset'], e['serial_size']
    if start < 0 or size < 4 or start + size > len(logical):
        raise FormatError('Font payload outside logical package')
    payload = logical[start:start + size]
    font = parse_font_payload(payload, names)
    atlases = []
    for ref in font['textures']:
        target = graph.reference(node[0], ref)
        if target is None:
            raise FormatError('null Font atlas')
        te = graph.export(*target); tc = graph.packages[target[0]]
        if te['class_path'].rsplit('.', 1)[-1] != 'Texture2D':
            raise FormatError('Font atlas has wrong class')
        offset, length = te['serial_offset'], te['serial_size']
        if offset < 0 or length < 4 or offset + length > len(tc['logical']):
            raise FormatError('atlas outside logical package')
        raw = tc['logical'][offset:offset + length]
        metadata = parse_atlas_payload(raw, tc['tables']['names'], offset)
        tiled = atlas_tiles(raw, metadata, decoder)
        if tiled is None:
            raise FormatError('compressed atlas requires an explicit decoder')
        atlases.append(dict(width=metadata['width'], height=metadata['height'],
                            tiled_sha256=hashlib.sha256(tiled).hexdigest()))
    canonical = dict(characters=[{k:v[k] for k in ('StartU','StartV','USize','VSize','TextureIndex')}
                                 for v in font['characters']],
                     remap=[(v['codepoint'],v['glyph_index']) for v in font['remap']],
                     is_remapped=font['is_remapped'], atlases=atlases)
    digest = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return dict(owner=graph.describe(node), identity=graph.canonical_identity(node),
                payload_sha256=hashlib.sha256(payload).hexdigest(), semantic_sha256=digest,
                glyph_count=len(font['characters']), remap_count=len(font['remap']), atlases=atlases)


def audit_font_candidates(graph, nodes, decoder=None):
    requested = {}
    for node in nodes:
        identity = graph.canonical_identity(node)
        key = identity['canonical_path'], identity['class_path']
        requested[key] = []
    identity_errors = []
    for package, ctx in graph.packages.items():
        for index, e in enumerate(ctx['tables']['exports'], 1):
            if e['class_path'].rsplit('.', 1)[-1] not in ('Font','MultiFont'):
                continue
            node = package, index
            try:
                identity = graph.canonical_identity(node)
                key = identity['canonical_path'], identity['class_path']
                if key in requested:
                    requested[key].append(node)
            except (ValueError, KeyError) as exc:
                identity_errors.append(dict(owner=graph.describe(node), reason=str(exc)))
    groups = []
    for (path, kind), candidates in sorted(requested.items()):
        fingerprints, errors = [], []
        for node in candidates:
            try:
                fingerprints.append(fingerprint(graph, node, decoder))
            except (ValueError, KeyError) as exc:
                errors.append(dict(owner=graph.describe(node), reason=str(exc)))
        guids = {f['identity']['namespace_guid'] for f in fingerprints}
        known_guid = bool(fingerprints) and len(guids) == 1 and None not in guids and '0' * 32 not in guids
        groups.append(dict(canonical_path=path, class_path=kind, candidate_count=len(candidates),
            fingerprints=fingerprints, errors=errors,
            same_known_namespace_guid=known_guid,
            all_supplied_candidates_semantically_equal=bool(fingerprints) and not errors
                and len({f['semantic_sha256'] for f in fingerprints}) == 1,
            runtime_precedence_resolved=False))
    return dict(groups=groups, identity_errors=identity_errors,
                interpretation='all supplied namespace candidates retained; matching GUID/data do not establish load order')
