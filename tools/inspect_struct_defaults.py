"""Read-only, hash-locked UI ScriptStruct declaration/default inspection."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

try:
    from .inspect_font_references import _tables
    from .ue3_package import FormatError,LzxDecoder,parse_summary,write_report
    from .ue3_ui_styles import StyleGraph
    from .ue3_struct_defaults import parse_struct_defaults
except ImportError:
    from inspect_font_references import _tables
    from ue3_package import FormatError,LzxDecoder,parse_summary,write_report
    from ue3_ui_styles import StyleGraph
    from ue3_struct_defaults import parse_struct_defaults


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('package',type=Path);p.add_argument('--sha256',required=True)
    p.add_argument('--object',action='append',required=True);p.add_argument('--lzx-library',type=Path)
    p.add_argument('--reference-package',nargs=3,action='append',default=[],metavar=('LABEL','PATH','SHA256'))
    p.add_argument('--output',type=Path,required=True);a=p.parse_args(argv)
    try:
        inputs=[a.package]+[Path(row[1]) for row in a.reference_package]+([a.lzx_library] if a.lzx_library else [])
        if a.output.exists() or a.output.is_symlink() or a.output.resolve() in [v.resolve() for v in inputs]:
            raise FormatError('struct report must be new and distinct from inputs')
        raw=a.package.read_bytes();summary=parse_summary(raw,len(raw))
        if summary['byte_order']!='big':raise FormatError('struct reader requires big-endian 446/25')
        decoder=LzxDecoder(a.lzx_library) if a.lzx_library else None
        logical,tables=_tables(raw,a.sha256,decoder)
        label=a.package.stem.casefold();packages={label:dict(logical=logical,tables=tables,sha256=a.sha256)}
        snapshots=[(a.package,raw)]
        for key,path,sha in a.reference_package:
            if key.casefold() in packages:raise FormatError('duplicate reference package label')
            value=Path(path).read_bytes();s=parse_summary(value,len(value))
            if s['byte_order']!='big':raise FormatError('struct references require big-endian 446/25')
            l,t=_tables(value,sha,decoder);packages[key.casefold()]=dict(logical=l,tables=t,sha256=sha);snapshots.append((Path(path),value))
        g=StyleGraph(packages)
        results,errors=[],[]
        for name in a.object:
            try:
                matches=g.paths[label].get(name.casefold(),[])
                if len(matches)!=1:raise FormatError('missing/ambiguous ScriptStruct definition')
                results.append(parse_struct_defaults(g,(label,matches[0])))
            except (ValueError,KeyError) as exc:errors.append(dict(object=name,reason=str(exc)))
        report=dict(schema_version=1,source_sha256=a.sha256,profile='446/25-big',structs=results,unparsed=errors,
                    native_initialization_verified=False,game_rendering_verified=False)
        write_report(a.output,report)
        if json.loads(a.output.read_text(encoding='utf8'))!=report:raise FormatError('struct report reopening mismatch')
        if any(path.read_bytes()!=value for path,value in snapshots):raise FormatError('original package changed during inspection')
        print(json.dumps(dict(structs=len(results),unparsed=len(errors),game_rendering_verified=False),sort_keys=True))
        return int(bool(errors))
    except (OSError,ValueError,KeyError) as exc:
        print('ERROR: '+str(exc));return 2


if __name__=='__main__':raise SystemExit(main())
