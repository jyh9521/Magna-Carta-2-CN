"""Read-only, hash-locked UI declarations, native stubs and opt-in wrapper scripts."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

try:
    from .inspect_font_references import _tables
    from .ue3_package import FormatError, LzxDecoder, parse_summary, write_report
    from .ue3_ui_styles import StyleGraph
    from .ue3_function_metadata import parse_function_metadata,function_header
except ImportError:
    from inspect_font_references import _tables
    from ue3_package import FormatError, LzxDecoder, parse_summary, write_report
    from ue3_ui_styles import StyleGraph
    from ue3_function_metadata import parse_function_metadata,function_header


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('package',type=Path);p.add_argument('--sha256',required=True)
    scope=p.add_mutually_exclusive_group(required=True)
    scope.add_argument('--object',action='append')
    scope.add_argument('--class',dest='defining_class',help='inventory immediate Function exports of this exact Class')
    p.add_argument('--lzx-library',type=Path)
    p.add_argument('--include-scripted',action='store_true',help='opt in to the bounded UI-wrapper grammar, never execute it')
    p.add_argument('--native-only',action='store_true',help='inventory all immediate Class Function headers and parse only declared-native stubs')
    p.add_argument('--reference-package',nargs=3,action='append',default=[],metavar=('LABEL','PATH','SHA256'))
    p.add_argument('--output',type=Path,required=True);a=p.parse_args(argv)
    try:
        if a.native_only and (not a.defining_class or a.include_scripted):
            raise FormatError('--native-only requires --class and excludes --include-scripted')
        inputs=[a.package]+[Path(row[1]) for row in a.reference_package]+([a.lzx_library] if a.lzx_library else [])
        if a.output.exists() or a.output.is_symlink() or a.output.resolve() in [v.resolve() for v in inputs]:
            raise FormatError('function report must be new and distinct from inputs')
        raw=a.package.read_bytes();summary=parse_summary(raw,len(raw))
        if summary['byte_order']!='big':raise FormatError('function reader requires big-endian 446/25')
        if hashlib.sha256(raw).hexdigest()!=a.sha256:raise FormatError('package SHA256 mismatch')
        reference_inputs=[];labels={a.package.stem.casefold()}
        for key,path,sha in a.reference_package:
            if key.casefold() in labels:raise FormatError('duplicate reference package label')
            labels.add(key.casefold());value=Path(path).read_bytes();s=parse_summary(value,len(value))
            if s['byte_order']!='big':raise FormatError('function references require big-endian 446/25')
            if hashlib.sha256(value).hexdigest()!=sha:raise FormatError('reference package SHA256 mismatch')
            reference_inputs.append((key,Path(path),sha,value))
        decoder=LzxDecoder(a.lzx_library) if a.lzx_library else None
        logical,tables=_tables(raw,a.sha256,decoder);label=a.package.stem.casefold()
        packages={label:dict(logical=logical,tables=tables,sha256=a.sha256)};snapshots=[(a.package,raw)]
        for key,path,sha,value in reference_inputs:
            l,t=_tables(value,sha,decoder)
            packages[key.casefold()]=dict(logical=l,tables=t,sha256=sha);snapshots.append((path,value))
        g=StyleGraph(packages)
        names=a.object
        if a.defining_class:
            owners=g.paths[label].get(a.defining_class.casefold(),[])
            if len(owners)!=1 or g.export(label,owners[0])['class_path']!='Class':
                raise FormatError('missing/ambiguous defining Class')
            names=[e['path'] for e in tables['exports'] if e['outer']==owners[0] and e['class_path']=='Core.Function']
            if not names:raise FormatError('defining Class has no immediate Function exports')
        results,errors,inventory,selected=[],[],[],[]
        for name in names:
            try:
                matches=g.paths[label].get(name.casefold(),[])
                if len(matches)!=1:raise FormatError('missing/ambiguous Function definition')
                if a.native_only:
                    h=function_header(g,(label,matches[0]));native=bool(h['flags']&0x400)
                    inventory.append(dict(owner=g.describe((label,matches[0])),defining_class=g.describe(h['outer']),
                        function_flags_hex=f"{h['flags']:08x}",native_token=h['native_token'],declared_native=native))
                    if not native:continue
                    selected.append(name)
                results.append(parse_function_metadata(g,(label,matches[0]),a.include_scripted))
            except (ValueError,KeyError) as exc:errors.append(dict(object=name,reason=str(exc)))
        report=dict(schema_version=1,source_sha256=a.sha256,profile='446/25-big-retained-editor-fields-and-friendly-name',
                    selected_objects=selected if a.native_only else names,defining_class_scope=a.defining_class,include_scripted=a.include_scripted,
                    reference_sources=[dict(package=key.casefold(),sha256=sha) for key,_,sha,_ in reference_inputs],
                    functions=results,unparsed=errors,native_implementation_verified=False,game_rendering_verified=False)
        if a.native_only:
            report['native_filter']=dict(mode='declared-native-only',class_function_count=len(names),
                omitted_non_native_count=sum(not row['declared_native'] for row in inventory),inventory=inventory,
                omitted_scripts_decoded=False)
        write_report(a.output,report)
        if json.loads(a.output.read_text(encoding='utf8'))!=report:raise FormatError('function report reopening mismatch')
        if any(path.read_bytes()!=value for path,value in snapshots):raise FormatError('original package changed during inspection')
        print(json.dumps(dict(functions=len(results),unparsed=len(errors),game_rendering_verified=False),sort_keys=True))
        return int(bool(errors))
    except (OSError,ValueError,KeyError) as exc:
        print('ERROR: '+str(exc));return 2


if __name__=='__main__':raise SystemExit(main())
