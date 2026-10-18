"""Read-only, hash-locked native UI function declarations and parameter stubs."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

try:
    from .inspect_font_references import _tables
    from .ue3_package import FormatError, LzxDecoder, parse_summary, write_report
    from .ue3_ui_styles import StyleGraph
    from .ue3_function_metadata import parse_function_metadata
except ImportError:
    from inspect_font_references import _tables
    from ue3_package import FormatError, LzxDecoder, parse_summary, write_report
    from ue3_ui_styles import StyleGraph
    from ue3_function_metadata import parse_function_metadata


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('package',type=Path);p.add_argument('--sha256',required=True)
    scope=p.add_mutually_exclusive_group(required=True)
    scope.add_argument('--object',action='append')
    scope.add_argument('--class',dest='defining_class',help='inventory immediate Function exports of this exact Class')
    p.add_argument('--lzx-library',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args(argv)
    try:
        inputs=[a.package]+([a.lzx_library] if a.lzx_library else [])
        if a.output.exists() or a.output.is_symlink() or a.output.resolve() in [v.resolve() for v in inputs]:
            raise FormatError('function report must be new and distinct from inputs')
        raw=a.package.read_bytes();summary=parse_summary(raw,len(raw))
        if summary['byte_order']!='big':raise FormatError('function reader requires big-endian 446/25')
        decoder=LzxDecoder(a.lzx_library) if a.lzx_library else None
        logical,tables=_tables(raw,a.sha256,decoder);label=a.package.stem.casefold()
        g=StyleGraph({label:dict(logical=logical,tables=tables,sha256=a.sha256)})
        names=a.object
        if a.defining_class:
            owners=g.paths[label].get(a.defining_class.casefold(),[])
            if len(owners)!=1 or g.export(label,owners[0])['class_path']!='Class':
                raise FormatError('missing/ambiguous defining Class')
            names=[e['path'] for e in tables['exports'] if e['outer']==owners[0] and e['class_path']=='Core.Function']
            if not names:raise FormatError('defining Class has no immediate Function exports')
        results,errors=[],[]
        for name in names:
            try:
                matches=g.paths[label].get(name.casefold(),[])
                if len(matches)!=1:raise FormatError('missing/ambiguous Function definition')
                results.append(parse_function_metadata(g,(label,matches[0])))
            except (ValueError,KeyError) as exc:errors.append(dict(object=name,reason=str(exc)))
        report=dict(schema_version=1,source_sha256=a.sha256,profile='446/25-big-retained-editor-fields-and-friendly-name',
                    selected_objects=names,defining_class_scope=a.defining_class,
                    functions=results,unparsed=errors,native_implementation_verified=False,game_rendering_verified=False)
        write_report(a.output,report)
        if json.loads(a.output.read_text(encoding='utf8'))!=report:raise FormatError('function report reopening mismatch')
        if a.package.read_bytes()!=raw:raise FormatError('original package changed during inspection')
        print(json.dumps(dict(functions=len(results),unparsed=len(errors),game_rendering_verified=False),sort_keys=True))
        return int(bool(errors))
    except (OSError,ValueError,KeyError) as exc:
        print('ERROR: '+str(exc));return 2


if __name__=='__main__':raise SystemExit(main())
