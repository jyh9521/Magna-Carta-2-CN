"""Source-locked property/container declaration audit; no runtime or mutation."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
try:
    from .inspect_font_references import _tables
    from .ue3_package import FormatError,LzxDecoder,parse_summary
    from .ue3_ui_styles import StyleGraph
    from .font_binding_plan import digest,parse_json_object
    from .property_declaration_audit import class_properties,property_tree
except ImportError:
    from inspect_font_references import _tables
    from ue3_package import FormatError,LzxDecoder,parse_summary
    from ue3_ui_styles import StyleGraph
    from font_binding_plan import digest,parse_json_object
    from property_declaration_audit import class_properties,property_tree


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('package',type=Path);p.add_argument('--sha256',required=True)
    scope=p.add_mutually_exclusive_group(required=True);scope.add_argument('--class',dest='class_name');scope.add_argument('--object',action='append')
    p.add_argument('--bind-structs',action='store_true');p.add_argument('--lzx-library',type=Path)
    p.add_argument('--reference-package',nargs=3,action='append',default=[],metavar=('LABEL','PATH','SHA256'))
    p.add_argument('--output',type=Path,required=True);a=p.parse_args(argv);created=False;encoded=None
    try:
        inputs=[a.package]+[Path(row[1]) for row in a.reference_package]+([a.lzx_library] if a.lzx_library else [])
        if a.output.exists() or a.output.is_symlink() or a.output.resolve() in [v.resolve() for v in inputs]:
            raise FormatError('declaration report must be new and distinct from inputs')
        if len(inputs)>34 or any(v.stat().st_size>512*1024*1024 for v in inputs):raise FormatError('declaration input count/size outside bound')
        snapshots=[(v,v.read_bytes()) for v in inputs];raw=snapshots[0][1]
        packages={};sources=[];verified=[];labels=set()
        for label,value,sha in [(a.package.stem,raw,a.sha256)]+[(label,snapshots[i+1][1],sha) for i,(label,_,sha) in enumerate(a.reference_package)]:
            key=label.casefold()
            if not key or key in labels:raise FormatError('duplicate/empty declaration package label')
            labels.add(key)
            if digest(value)!=sha:raise FormatError('declaration package SHA256 mismatch')
            s=parse_summary(value,len(value))
            if s['byte_order']!='big':raise FormatError('declaration audit requires big-endian 446/25')
            verified.append((key,value,sha))
            sources.append(dict(package=key,sha256=sha))
        decoder=LzxDecoder(a.lzx_library) if a.lzx_library else None
        for key,value,sha in verified:
            logical,tables=_tables(value,sha,decoder);packages[key]=dict(logical=logical,tables=tables,sha256=sha)
        graph=StyleGraph(packages);label=a.package.stem.casefold();names=[a.class_name] if a.class_name else a.object
        if not 1<=len(names)<=4096 or len({n.casefold() for n in names})!=len(names):raise FormatError('declaration selection count/uniqueness invalid')
        results,errors=[],[]
        for name in names:
            try:
                matches=graph.paths[label].get(name.casefold(),[])
                if len(matches)!=1:raise FormatError('missing/ambiguous declaration selection')
                node=label,matches[0]
                results.append(class_properties(graph,node,a.bind_structs) if a.class_name else property_tree(graph,node,a.bind_structs))
            except (ValueError,KeyError) as exc:errors.append(dict(object=name,reason=str(exc)))
        report=dict(schema_version=1,profile='446/25-property-container-identities',sources=sources,decoder_sha256=digest(snapshots[-1][1]) if a.lzx_library else None,
            class_scope=a.class_name,bind_structs=a.bind_structs,declarations=results,unparsed=errors,
            container_values_decoded=False,native_layout_verified=False,game_rendering_verified=False)
        if any(path.read_bytes()!=value for path,value in snapshots):raise FormatError('declaration input changed')
        encoded=(json.dumps(report,sort_keys=True,ensure_ascii=False,allow_nan=False,indent=2)+'\n').encode('utf-8')
        a.output.parent.mkdir(parents=True,exist_ok=True)
        with a.output.open('xb') as stream:created=True;stream.write(encoded)
        if a.output.read_bytes()!=encoded or parse_json_object(a.output.read_bytes())!=report:raise FormatError('declaration report reopening mismatch')
        if any(path.read_bytes()!=value for path,value in snapshots):raise FormatError('declaration input changed after writing')
        print(json.dumps(dict(selections=len(results),unparsed=len(errors),native_layout_verified=False),sort_keys=True));return int(bool(errors))
    except (OSError,ValueError,KeyError,TypeError) as exc:
        if created:
            try:
                if not a.output.is_symlink() and a.output.read_bytes()==encoded:a.output.unlink()
            except OSError:pass
        print('ERROR: '+str(exc));return 2


if __name__=='__main__':raise SystemExit(main())
