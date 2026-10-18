"""Read direct UE3 UIStyle font references; static links are not runtime binding."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct

try:
    from .ue3_package import FormatError, Reader, LzxDecoder, parse_summary, parse_tables, package_header, write_report
    from .ue3_fonts import read_properties
except ImportError:
    from ue3_package import FormatError, Reader, LzxDecoder, parse_summary, parse_tables, package_header, write_report
    from ue3_fonts import read_properties


def inspect_links(logical, tables):
    links, unparsed = [], []
    for index, export in enumerate(tables['exports'], 1):
        if export['class_path'] not in ('Engine.UIStyle_Text', 'Engine.UIStyle_Combo'):
            continue
        try:
            start, size = export['serial_offset'], export['serial_size']
            if start < 0 or size < 4 or start + size > len(logical):
                raise FormatError('style payload outside logical package')
            r = Reader(logical[start:start + size]); r.i32()
            props = read_properties(r, tables['names'])
            font_props = [p for p in props if p['name'] == 'StyleFont']
            if len(font_props) > 1:
                raise FormatError('duplicate StyleFont property')
            for prop in font_props:
                if prop['type'] != 'ObjectProperty' or len(prop['raw']) != 4:
                    raise FormatError('StyleFont is not an object reference')
                ref = struct.unpack('>i', prop['raw'])[0]
                if not -len(tables['imports']) <= ref <= len(tables['exports']):
                    raise FormatError('font reference outside object tables')
                target = tables['exports'][ref - 1] if ref > 0 else tables['imports'][-ref - 1] if ref < 0 else None
                if ref > 0 and target['class_path'] != 'Engine.Font':
                    raise FormatError('local StyleFont has non-Font class')
                if ref < 0 and target['class_name']['name'] != 'Font':
                    raise FormatError('imported StyleFont has non-Font class')
                links.append(dict(object_index=index, object=export['path'], serial_offset=start,
                                  property='StyleFont', font_reference=ref,
                                  font_path=target['path'] if target else None,
                                  binding_kind='direct-serialized-reference'))
        except (ValueError, KeyError) as exc:
            unparsed.append(dict(object=export['path'], reason=str(exc)))
    return dict(font_bindings=links, unparsed=unparsed, runtime_binding_verified=False,
                inheritance_resolved=False)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('package', type=Path); p.add_argument('--sha256', required=True)
    p.add_argument('--lzx-library', type=Path); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--deep', action='store_true', help='Trace component/nested serialized style candidates without executing game')
    p.add_argument('--text-token', help='Match nested StrProperty values (deep mode only)')
    p.add_argument('--reference-package', nargs=3, action='append', default=[], metavar=('LABEL', 'PATH', 'SHA256'))
    p.add_argument('--audit-bindings', action='store_true', help='Audit renderer/label prototypes, PrimaryStyle selectors and supplied Font namespace candidates (requires --deep)')
    p.add_argument('--audit-struct-defaults',action='store_true',help='Bind renderer StructProperty declarations/defaults (requires --deep --audit-bindings)')
    a = p.parse_args(argv)
    try:
        if a.audit_struct_defaults and not (a.deep and a.audit_bindings):
            raise FormatError('--audit-struct-defaults requires --deep --audit-bindings')
        if a.deep:
            if not a.text_token:
                raise FormatError('--deep requires a nonempty --text-token')
            try:
                from .inspect_font_references import _tables
                from .ue3_ui_styles import StyleGraph
            except ImportError:
                from inspect_font_references import _tables
                from ue3_ui_styles import StyleGraph
            packages = {}
            decoder = LzxDecoder(a.lzx_library) if a.lzx_library else None
            inputs = [(a.package.stem, str(a.package), a.sha256)] + a.reference_package
            for label, path, digest in inputs:
                key = label.casefold()
                if key in packages:
                    raise FormatError('duplicate package label')
                raw = Path(path).read_bytes()
                logical, tables = _tables(raw, digest.lower(), decoder)
                packages[key] = dict(logical=logical, tables=tables, sha256=digest.lower())
                if a.audit_bindings:
                    packages[key]['package_guid'] = parse_summary(raw,len(raw))['guid']
            graph = StyleGraph(packages)
            result = graph.trace(a.package.stem, a.text_token)
            if a.audit_bindings:
                try:
                    from .font_binding_audit import audit_font_candidates
                    from .owner_style_audit import audit_owner_primary_style
                except ImportError:
                    from font_binding_audit import audit_font_candidates
                    from owner_style_audit import audit_owner_primary_style
                fonts = set()
                for match in result['text_matches']:
                    owner = match['owner']
                    owner_audit = audit_owner_primary_style(graph, (owner['package'], owner['object_index']))
                    match['owner_primary_style_audit'] = owner_audit
                    for observation in owner_audit['selector_observations']:
                        for candidate in observation['candidate_paths']:
                            f = candidate['font']; fonts.add((f['package'], f['object_index']))
                    if 'renderer' in match:
                        r = match['renderer']
                        match['renderer_prototype_audit'] = graph.archetype_audit((r['package'],r['object_index']))
                    for candidate in match['candidate_paths']:
                        f = candidate['font'];fonts.add((f['package'],f['object_index']))
                result['font_namespace_audit'] = audit_font_candidates(graph,fonts,decoder)
                if a.audit_struct_defaults:
                    try:
                        from .ue3_struct_defaults import audit_struct_property
                    except ImportError:
                        from ue3_struct_defaults import audit_struct_property
                    for match in result['text_matches']:
                        bound,errors=[],[]
                        if 'renderer' in match:
                            r=match['renderer'];node=(r['package'],r['object_index'])
                            fields=sorted({p['property_path'][0]['name'] for p in graph.parse(node)['flattened']
                                           if p['type']=='StructProperty' and len(p['property_path'])==1})
                            for name in fields:
                                try:bound.append(audit_struct_property(graph,node,name))
                                except (ValueError,KeyError) as exc:errors.append(dict(field=name,reason=str(exc)))
                        match['renderer_struct_default_audit']=dict(bindings=bound,unresolved=errors,
                            native_initialization_verified=False,runtime_effective_values_resolved=False)
            write_report(a.output, result)
            if json.loads(a.output.read_text(encoding='utf-8')) != result:
                raise FormatError('output reopening mismatch')
            print(json.dumps(dict(**result['coverage'], text_matches=len(result['text_matches']),
                                  candidate_paths=sum(len(m['candidate_paths']) for m in result['text_matches']),
                                  runtime_binding_verified=False), sort_keys=True))
            return 0
        if a.text_token or a.reference_package or a.audit_bindings:
            raise FormatError('--text-token, --reference-package and --audit-bindings require --deep')
        raw = a.package.read_bytes()
        if hashlib.sha256(raw).hexdigest() != a.sha256.lower():
            raise FormatError('package SHA256 mismatch')
        s = parse_summary(raw, len(raw))
        total = max([len(raw)] + [c['uncompressed_offset'] + c['uncompressed_size'] for c in s['compressed_chunks']])
        logical = package_header(raw, dict(s, header_size=total), LzxDecoder(a.lzx_library) if a.lzx_library else None)
        tables = parse_tables(logical, s, total)
        result = dict(schema_version=1, sha256=a.sha256.lower(), **inspect_links(logical, tables))
        write_report(a.output, result)
        print(json.dumps(dict(font_bindings=len(result['font_bindings']), unparsed=len(result['unparsed']), runtime_binding_verified=False), sort_keys=True))
        return int(bool(result['unparsed']))
    except (OSError, ValueError, KeyError) as exc:
        print('ERROR: ' + str(exc)); return 2


if __name__ == '__main__':
    raise SystemExit(main())
