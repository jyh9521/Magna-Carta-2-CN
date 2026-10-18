"""Read-only, bounded UE3 446/25 component and serialized UI style graph.

Format reference: EliotVU/Unreal-Library 8236c39b79e30887a487ecf9b018204e430a5ebc,
UObject.cs (component template before NetIndex). Independent implementation;
no tag-start guessing, target execution, resource modification or runtime claims.
"""
from __future__ import annotations

import struct
from collections import defaultdict

try:
    from .ue3_package import FormatError, Reader
    from .ue3_fonts import read_properties
except ImportError:
    from ue3_package import FormatError, Reader
    from ue3_fonts import read_properties


TAGGED_STRUCTS = {'UIStyleReference', 'StyleDataReference', 'STYLE_ID',
                  'UIDataStoreBinding', 'UITextStyleOverride'}
UI_BASES = {'engine.uiobject', 'engine.uicomponent', 'engine.uistyle',
            'engine.uistyle_data', 'engine.uiskin'}


def object_flags(export):
    """The table stores LO u32 then HO u32, not one big-endian uint64."""
    raw = bytes.fromhex(export['object_flags'])
    if len(raw) != 8:
        raise FormatError('object flags must contain LO and HO uint32 words')
    return struct.unpack('>II', raw)


def read_name(reader, names):
    index, number = reader.u32(), reader.u32()
    if index >= len(names):
        raise FormatError('FName index outside names')
    return dict(name=names[index], number=number)


def style_id(properties):
    """STYLE_ID is four tagged IntProperty words, not a raw 16-byte GUID."""
    if len(properties) != 4 or {p['name'] for p in properties} != set('ABCD'):
        raise FormatError('STYLE_ID requires exactly A/B/C/D')
    values = {}
    for p in properties:
        if p['type'] != 'IntProperty' or p['array_index'] or len(p['raw']) != 4:
            raise FormatError('invalid STYLE_ID word')
        values[p['name']] = p['raw'].hex()
    return '-'.join(values[k] for k in 'ABCD')


class StyleGraph:
    def __init__(self, packages):
        """packages: label -> {logical, tables, sha256}; identities checked by CLI."""
        self.packages, self.paths = {}, {}
        self._classes, self._parsed = {}, {}
        for label, package in packages.items():
            key = label.casefold()
            if not label or key in self.packages:
                raise FormatError('duplicate or empty package label')
            self.packages[key] = package
            paths = defaultdict(list)
            for index, export in enumerate(package['tables']['exports'], 1):
                paths[export['path'].casefold()].append(index)
            self.paths[key] = paths

    def export(self, package, index):
        p = self.packages[package.casefold()]
        if not 1 <= index <= len(p['tables']['exports']):
            raise FormatError('export reference outside object tables')
        return p['tables']['exports'][index - 1]

    def describe(self, node):
        package, index = node
        e = self.export(*node)
        return dict(package=package, object_index=index, path=e['path'], class_path=e['class_path'],
                    object_flags=e['object_flags'], export_flags=e.get('export_flags'),
                    source_sha256=self.packages[package]['sha256'],
                    logical_serial_offset=e['serial_offset'], serial_size=e['serial_size'])

    def reference(self, package, ref):
        package = package.casefold()
        if not ref:
            return None
        if ref > 0:
            self.export(package, ref)
            return package, ref
        imports = self.packages[package]['tables']['imports']
        if -ref > len(imports):
            raise FormatError('import reference outside object tables')
        imp = imports[-ref - 1]
        label, sep, path = imp['path'].partition('.')
        label = label.casefold()
        if not sep or label not in self.packages:
            raise FormatError('unresolved imported object: ' + imp['path'])
        candidates = self.paths[label].get(path.casefold(), [])
        if len(candidates) != 1:
            raise FormatError('missing or ambiguous imported object: ' + imp['path'])
        node = label, candidates[0]
        expected = imp['class_name']['name']
        if self.export(*node)['class_path'].rsplit('.', 1)[-1].casefold() != expected.casefold():
            raise FormatError('import/export class mismatch: ' + imp['path'])
        return node

    def symbolic_reference(self, package, ref):
        if ref < 0:
            imports = self.packages[package]['tables']['imports']
            if -ref > len(imports):
                raise FormatError('import reference outside object tables')
            return imports[-ref - 1]['path'].casefold()
        e = self.export(package, ref)
        return package + '.' + e['path'].casefold()

    def class_chain(self, node):
        e = self.export(*node)
        key = node[0], e['class']
        if key in self._classes:
            return self._classes[key]
        package, ref = key
        seen, chain = set(), []
        while ref:
            if (package, ref) in seen or len(seen) >= 256:
                raise FormatError('cyclic or overlong class hierarchy')
            seen.add((package, ref))
            path = self.symbolic_reference(package, ref)
            chain.append(path)
            if path in ('core.component', 'core.object'):
                break
            definition = self.reference(package, ref)
            if definition is None:
                raise FormatError('null class definition')
            package, index = definition
            c = self.export(package, index)
            if c['class_path'] != 'Class':
                raise FormatError('class chain points to non-Class export')
            ref = c['super']
        self._classes[key] = chain
        return chain

    def cdo_outer(self, node):
        seen = set()
        while node:
            if node in seen or len(seen) >= 256:
                raise FormatError('cyclic or overlong component outer chain')
            seen.add(node)
            e = self.export(*node)
            if object_flags(e)[1] & 0x200:
                return True
            node = self.reference(node[0], e['outer'])
        return False

    def parse(self, node):
        if node in self._parsed:
            return self._parsed[node]
        package, index = node
        context = self.packages[package]
        e = self.export(package, index)
        start, size = e['serial_offset'], e['serial_size']
        if start < 0 or size < 4 or start + size > len(context['logical']):
            raise FormatError('object payload outside logical package')
        r = Reader(context['logical'][start:start + size])
        lo, ho = object_flags(e)
        prefix = dict(class_default=bool(ho & 0x200), component=False)
        if not prefix['class_default']:
            if lo & 0x02000000:
                raise FormatError('HasStack object prefix is not supported')
            prefix['component'] = 'core.component' in self.class_chain(node)
            if prefix['component']:
                owner = r.i32()
                if owner:
                    target = self.reference(package, owner)
                    if not target or self.export(*target)['class_path'] != 'Class':
                        raise FormatError('TemplateOwnerClass must reference Class or null')
                prefix['template_owner_class'] = owner
                if self.cdo_outer(node):
                    prefix['template_name'] = read_name(r, context['tables']['names'])
        prefix['net_index'] = r.i32()
        prefix['tagged_offset'] = r.pos
        props = read_properties(r, context['tables']['names'])
        # Known nested structures are validated completely, before caching any result.
        flat, opaque = [], []

        def walk(properties, base, path, depth):
            if depth > 8:
                raise FormatError('nested UI property depth exceeds limit')
            for prop in properties:
                if len(flat) >= 8192:
                    raise FormatError('nested UI property count exceeds limit')
                location = path + [dict(name=prop['name'], array_index=prop['array_index'])]
                record = dict(property_path=location, type=prop['type'],
                              logical_package_offset=base + prop['value_offset'])
                raw = Reader(prop['raw'])
                if prop['type'] == 'StructProperty':
                    record['struct'] = prop['struct']
                    if prop['struct'] in TAGGED_STRUCTS:
                        children = read_properties(raw, context['tables']['names'])
                        if raw.pos != len(raw.data):
                            raise FormatError('nested UI struct trailing bytes')
                        if prop['struct'] == 'STYLE_ID':
                            record['style_id'] = style_id(children)
                        flat.append(record)
                        walk(children, record['logical_package_offset'], location, depth + 1)
                        continue
                    opaque.append(dict(**record, size=len(prop['raw'])))
                elif prop['type'] in ('ObjectProperty', 'ComponentProperty'):
                    record['reference'] = raw.i32()
                    ref = record['reference']
                    if not -len(context['tables']['imports']) <= ref <= len(context['tables']['exports']):
                        raise FormatError('nested object reference outside tables')
                elif prop['type'] == 'StrProperty':
                    record['value'] = raw.string()
                elif prop['type'] == 'NameProperty':
                    record['value'] = read_name(raw, context['tables']['names'])
                elif prop['type'] == 'BoolProperty':
                    record['value'] = prop['bool']
                else:
                    flat.append(record)
                    continue
                if prop['type'] != 'StructProperty' and raw.pos != len(raw.data):
                    raise FormatError('UI scalar property size mismatch')
                flat.append(record)
        walk(props, start, [], 0)
        result = dict(prefix=prefix, properties=props, flattened=flat, opaque=opaque,
                      tagged_end=r.pos, native_tail_size=size - r.pos)
        self._parsed[node] = result
        return result

    def fields(self, node, path):
        return [p for p in self.parse(node)['flattened']
                if [q['name'] for q in p['property_path']] == path]

    def one(self, node, path):
        props = self.fields(node, path)
        if len(props) != 1 or any(p['array_index'] for p in props[0]['property_path']):
            raise FormatError('missing, duplicate or indexed UI field: ' + '.'.join(path))
        return props[0]

    def state_map(self, node):
        if 'engine.uistyle' not in self.class_chain(node):
            raise FormatError('StateMap requires UIStyle class')
        p = self.parse(node);e = self.export(*node);ctx = self.packages[node[0]]
        r = Reader(ctx['logical'][e['serial_offset']:e['serial_offset'] + e['serial_size']])
        r.seek(p['tagged_end'])
        entries, seen = [], set()
        for _ in range(r.count(4096)):
            offset = e['serial_offset'] + r.pos
            state, data = r.i32(), r.i32()
            if not state or not data or state in seen:
                raise FormatError('invalid or duplicate style state')
            seen.add(state)
            # State imports may remain symbolic; style data must resolve.
            self.symbolic_reference(node[0], state)
            target = self.reference(node[0], data)
            if target is None or not any(c in self.class_chain(target) for c in
                                         ('engine.uistyle_data', 'engine.uistyle_text', 'engine.uistyle_combo', 'engine.uistyle_image')):
                raise FormatError('StateMap data has wrong class')
            entries.append(dict(state=self.symbolic_reference(node[0], state), data=target,
                                logical_package_offset=offset))
        if r.pos != len(r.data):
            raise FormatError('UIStyle StateMap trailing bytes')
        return entries

    def trace(self, package, token):
        """Return every serialized candidate; never pick active skin/state/font."""
        package = package.casefold()
        selected, unparsed, classification_errors, matches, prefixes = 0, [], [], [], defaultdict(int)
        for index, e in enumerate(self.packages[package]['tables']['exports'], 1):
            node = package, index
            leaf = e['class_path'].rsplit('.', 1)[-1]
            if (not e['class'] or not e['serial_size'] or leaf.endswith('Property')
                    or leaf in ('Function', 'State', 'ScriptStruct', 'Enum', 'Const', 'Package', 'Font', 'MultiFont', 'Texture2D')):
                continue
            selected_node = False
            try:
                chain = self.class_chain(node)
                if not UI_BASES.intersection(chain):
                    continue
                selected += 1
                selected_node = True
                parsed = self.parse(node)
                prefixes[str(parsed['prefix']['tagged_offset'])] += 1
                for prop in parsed['flattened']:
                    if prop['type'] == 'StrProperty' and token in prop['value']:
                        matches.append(dict(owner=self.describe(node), property=prop, node=node))
            except (ValueError, KeyError) as exc:
                (unparsed if selected_node else classification_errors).append(
                    dict(object_index=index, object_path=e['path'], reason=str(exc)))
        ids, style_errors = defaultdict(list), []
        for label, context in self.packages.items():
            for index, e in enumerate(context['tables']['exports'], 1):
                if (not e['class'] or e['class_path'].rsplit('.', 1)[-1] != 'UIStyle'
                        or object_flags(e)[1] & 0x200):
                    continue
                node = label, index
                try:
                    sid = self.one(node, ['StyleID'])['style_id']
                    ids[sid].append(node)
                except (ValueError, KeyError) as exc:
                    style_errors.append(dict(owner=self.describe(node), reason=str(exc)))
        traces = []
        for match in matches:
            node = match.pop('node')
            item = dict(**match, candidate_paths=[], unresolved=[])
            try:
                renderer_field = self.one(node, ['StringRenderComponent'])
                renderer = self.reference(node[0], renderer_field['reference'])
                if renderer is None or 'engine.uicomp_drawstring' not in self.class_chain(renderer):
                    raise FormatError('StringRenderComponent is not UIComp_DrawString')
                assigned = self.one(renderer, ['StringStyle', 'AssignedStyleID'])
                candidates = ids.get(assigned['style_id'], [])
                if not candidates:
                    raise FormatError('AssignedStyleID has no supplied UIStyle definition')
                item.update(renderer=self.describe(renderer), renderer_prefix=self.parse(renderer)['prefix'],
                            assigned_style_id=assigned['style_id'], assigned_id_offset=assigned['logical_package_offset'],
                            style_definition_count=len(candidates),
                            explicit_text_overrides=[p for p in self.parse(renderer)['flattened']
                                                    if p['property_path'][0]['name'] == 'TextStyleCustomization'])
                for style in candidates:
                    try:
                        for state in self.state_map(style):
                            data = state['data']
                            hops = [self.describe(style), self.describe(data)]
                            if 'engine.uistyle_combo' in self.class_chain(data):
                                field = self.one(data, ['TextStyle', 'CustomStyleData'])
                                data = self.reference(data[0], field['reference'])
                                if data is None:
                                    raise FormatError('null CustomStyleData; inherited/source-style resolution pending')
                                hops.append(self.describe(data))
                            if 'engine.uistyle_text' not in self.class_chain(data):
                                raise FormatError('text style data has wrong class')
                            font_field = self.one(data, ['StyleFont'])
                            font = self.reference(data[0], font_field['reference'])
                            if font is None or self.export(*font)['class_path'].rsplit('.', 1)[-1] not in ('Font', 'MultiFont'):
                                raise FormatError('StyleFont is not a resolved Font/MultiFont')
                            item['candidate_paths'].append(dict(state=state['state'], state_map_offset=state['logical_package_offset'],
                                hops=hops, font=self.describe(font), font_reference_offset=font_field['logical_package_offset'],
                                status='serialized-font-candidate-not-runtime-selection'))
                    except (ValueError, KeyError) as exc:
                        item['unresolved'].append(dict(style=self.describe(style), reason=str(exc)))
            except (ValueError, KeyError) as exc:
                item['unresolved'].append(dict(reason=str(exc)))
            traces.append(item)
        return dict(schema_version=1, text_token=token, primary_package=package,
                    sources={k:v['sha256'] for k,v in self.packages.items()},
                    coverage=dict(selected_ui_exports=selected, parsed_ui_exports=sum(prefixes.values()),
                                  tagged_prefix_offsets=dict(prefixes), unparsed_exports=len(unparsed)),
                    text_matches=traces, unparsed=unparsed, classification_errors=classification_errors,
                    style_errors=style_errors,
                    runtime_binding_verified=False, inherited_values_resolved=False,
                    interpretation='serialized candidate paths only; active widget/skin/state, overrides and linker precedence unverified')
