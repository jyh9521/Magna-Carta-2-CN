"""Keep label PrimaryStyle evidence separate from component StringStyle links.

No default merging, fallback order, native-pointer identity or active skin is
inferred. Every serialized selector is an independent candidate observation.
"""
from __future__ import annotations

try:
    from .ue3_ui_styles import object_flags
    from .ue3_package import FormatError
except ImportError:
    from ue3_ui_styles import object_flags
    from ue3_package import FormatError


def style_font_paths(graph, style):
    paths, errors = [], []
    try:
        states = graph.state_map(style)
    except (ValueError, KeyError) as exc:
        return paths, [dict(style=graph.describe(style), reason=str(exc))]
    for state in states:
        try:
            data = state['data']
            hops = [graph.describe(style), graph.describe(data)]
            if 'engine.uistyle_combo' in graph.class_chain(data):
                field = graph.one(data, ['TextStyle', 'CustomStyleData'])
                data = graph.reference(data[0], field['reference'])
                if data is None:
                    raise FormatError('null CustomStyleData; inherited/source-style resolution pending')
                hops.append(graph.describe(data))
            if 'engine.uistyle_text' not in graph.class_chain(data):
                raise FormatError('text style data has wrong class')
            audit = graph.archetype_audit(data, prefixes=('StyleFont',))
            planes = [('explicit-archetype', audit['explicit_archetypes'])]
            planes += [('class-default-candidate', chain) for chain in audit['class_default_candidates']]
            observed = False
            for plane, chain in planes:
                for record in chain['nodes']:
                    if not record['fields']:
                        continue
                    observed = True
                    owner = record['owner']; source = owner['package'], owner['object_index']
                    try:
                        field = graph.one(source, ['StyleFont'])
                        if field['type'] != 'ObjectProperty':
                            raise FormatError('StyleFont must be ObjectProperty')
                        font = graph.reference(source[0], field['reference'])
                        if font is None or graph.export(*font)['class_path'].rsplit('.', 1)[-1] not in ('Font', 'MultiFont'):
                            raise FormatError('StyleFont is not a resolved Font/MultiFont')
                        paths.append(dict(state=state['state'], state_map_offset=state['logical_package_offset'],
                            hops=hops, font=graph.describe(font), font_reference_offset=field['logical_package_offset'],
                            font_source_plane=plane, font_source_owner=owner, text_data_prototype_audit=audit,
                            inherited_values_merged=False, status='serialized-font-candidate-not-runtime-selection'))
                    except (ValueError, KeyError) as exc:
                        errors.append(dict(style=graph.describe(style), state=state['state'], owner=owner, reason=str(exc)))
            if not observed or audit['unresolved']:
                errors.append(dict(style=graph.describe(style), state=state['state'],
                    reason='no explicit StyleFont observation' if not observed else 'text data prototype audit unresolved',
                    text_data_prototype_audit=audit))
        except (ValueError, KeyError) as exc:
            errors.append(dict(style=graph.describe(style), state=state['state'], reason=str(exc)))
    return paths, errors


def audit_owner_primary_style(graph, node):
    """Audit the matched label, not the renderer's serialized Outer by guesswork."""
    audit = graph.archetype_audit(node, prefixes=('PrimaryStyle',))
    by_id, by_tag, catalog_errors = {}, {}, []
    for label, context in graph.packages.items():
        for index, export in enumerate(context['tables']['exports'], 1):
            if (not export['class'] or export['class_path'].rsplit('.', 1)[-1] != 'UIStyle'
                    or object_flags(export)[1] & 0x200):
                continue
            style = label, index
            for name, catalog, value_key in [('StyleID', by_id, 'style_id'), ('StyleTag', by_tag, 'value')]:
                try:
                    if not graph.fields(style, [name]):
                        continue  # Absence is not an implicit zero ID/None tag.
                    field = graph.one(style, [name])
                    if name == 'StyleID':
                        if field['type'] != 'StructProperty' or field.get('struct') != 'STYLE_ID':
                            raise FormatError('StyleID must be STYLE_ID')
                        value = field[value_key]
                    else:
                        if field['type'] != 'NameProperty':
                            raise FormatError('StyleTag must be NameProperty')
                        value = field[value_key]
                        value = value['name'].casefold(), value['number']
                    catalog.setdefault(value, []).append(style)
                except (ValueError, KeyError) as exc:
                    catalog_errors.append(dict(owner=graph.describe(style), field=name, reason=str(exc)))
    observations, errors = [], []
    planes = [('explicit-archetype', audit['explicit_archetypes'])]
    planes += [('class-default-candidate', chain) for chain in audit['class_default_candidates']]
    for plane, chain in planes:
        for record in chain['nodes']:
            owner = record['owner']; source = owner['package'], owner['object_index']
            if not record['fields']:
                continue
            try:
                root = graph.one(source, ['PrimaryStyle'])
                if root['type'] != 'StructProperty' or root.get('struct') != 'UIStyleReference':
                    raise FormatError('PrimaryStyle must be UIStyleReference')
            except (ValueError, KeyError) as exc:
                errors.append(dict(plane=plane, owner=owner, reason=str(exc)))
                continue
            for name, catalog in [('AssignedStyleID', by_id), ('DefaultStyleTag', by_tag)]:
                try:
                    path = ['PrimaryStyle', name]
                    if not graph.fields(source, path):
                        continue
                    field = graph.one(source, path)
                    if name == 'AssignedStyleID':
                        if field['type'] != 'StructProperty' or field.get('struct') != 'STYLE_ID':
                            raise FormatError('AssignedStyleID must be STYLE_ID')
                        key = field['style_id']
                        disabled = key == '00000000-00000000-00000000-00000000'
                    else:
                        if field['type'] != 'NameProperty':
                            raise FormatError('DefaultStyleTag must be NameProperty')
                        value = field['value']; key = value['name'].casefold(), value['number']
                        disabled = key == ('none', 0)
                    styles = [] if disabled else catalog.get(key, [])
                    item = dict(plane=plane, owner=owner, field=field,
                        selector_is_zero_or_none=disabled, style_definition_count=len(styles),
                        style_definitions=[graph.describe(s) for s in styles], candidate_paths=[], unresolved=[])
                    if not disabled and not styles:
                        item['unresolved'].append(dict(reason='selector has no supplied UIStyle definition'))
                    for style in styles:
                        paths, failures = style_font_paths(graph, style)
                        item['candidate_paths'].extend(paths); item['unresolved'].extend(failures)
                    observations.append(item)
                except (ValueError, KeyError) as exc:
                    errors.append(dict(plane=plane, owner=owner, field=name, reason=str(exc)))
    return dict(owner=graph.describe(node), prototype_audit=audit,
        selector_observations=observations, unresolved=errors, style_catalog_errors=catalog_errors,
        inherited_values_merged=False, fallback_order_verified=False,
        native_owner_pointer_identity_verified=False, runtime_binding_verified=False,
        interpretation='independent serialized label PrimaryStyle observations; not a proven native getter branch')
