"""Build a bounded, offline raw-original comparison phase for one locale disc.

No installation, launcher changes or runtime claims. The full composition is
independently replayed first; raw package bytes are derived from original bytes,
not from translated packages. Each disc retains its own original TOC.
"""
from pathlib import Path
import argparse
import json
from tools.font_binding_plan import read_locked_json,parse_json_object,digest,confined_path
from tools.build_font_route_probe import encoded
from tools.compose_locale_resources import verify as verify_composition,check_inputs
from tools.decompress_package import decompress_copy
from tools.ue3_package import parse_summary,LzxDecoder
from tools.update_resource_sizes import update_sizes_reversible
from tools.verify_locale_candidate import scan_tree
from tools.build_font_supplement import restore_copy
from tools.verify_resource_phase import relative,MAX_PACKET_RESOURCES

KIND='offline-disc-locale-raw-comparison'


def raw_phase(originals,font_paths,toc_path,decoder=None):
    """Normalize only explicitly declared font packages; update original TOC once."""
    if not isinstance(originals,dict) or not 1<=len(originals)<=MAX_PACKET_RESOURCES:raise ValueError('raw resource count outside bound')
    for p in originals:relative(p)
    if len({p.casefold() for p in originals})!=len(originals):raise ValueError('aliased raw resource paths')
    if not font_paths or len(font_paths)>8 or len(set(font_paths))!=len(font_paths):raise ValueError('invalid raw font set')
    if toc_path not in originals or toc_path in font_paths or not set(font_paths)<=set(originals):
        raise ValueError('raw roles do not match originals')
    raw=dict(originals);proofs=[]
    for path in sorted(font_paths):
        source=originals[path];summary=parse_summary(source,len(source))
        if summary['compression_flags']:
            raw[path],proof=decompress_copy(source,digest(source),decoder)
        else:
            proof=dict(input_sha256=digest(source),output_sha256=digest(source),
                       logical_payload_preserved=True,unchanged_uncompressed=True,game_rendering_verified=False)
        if parse_summary(raw[path],len(raw[path]))['compression_flags']!=0:
            raise ValueError('raw phase contains compressed font package')
        proofs.append(dict(path=path,**proof))
    changes=[dict(path=p,expected_size=len(originals[p]),new_size=len(b)) for p,b in raw.items()
             if p!=toc_path and len(b)!=len(originals[p])]
    raw[toc_path],toc=update_sizes_reversible(originals[toc_path],digest(originals[toc_path]),changes)
    return raw,dict(font_packages=proofs,toc=toc,toc_changes=changes,
                    untranslated_text_retained=True,game_rendering_verified=False)


def prepare(plan,project,decoder=None):
    project=Path(project).resolve();snapshots=[]
    if (type(plan.get('schema_version')) is not int or plan['schema_version']!=1 or plan.get('kind')!=KIND
            or plan.get('game_rendering_verified') is not False):raise ValueError('invalid offline comparison plan')
    def locked(ref):
        obj,path,raw=read_locked_json(project,ref);snapshots.append((path,digest(raw)));return obj,path.parent
    cp,_=locked(plan['composition_plan']);cm,source=locked(plan['composition_manifest'])
    if type(plan.get('disc')) is not int or plan['disc'] not in (1,2) or cp['disc']!=plan['disc'] or cm['disc']!=plan['disc']:
        raise ValueError('comparison disc identity mismatch')
    if encoded(verify_composition(cp,project,source,decoder))!=encoded(cm):raise ValueError('composition replay mismatch')
    # Lock every upstream output as well as its manifest throughout this build.
    for name,h in cm['member_sha256'].items():snapshots.append((confined_path(source,name),h))
    fm,font_root=locked(cp['font_component'])
    families=[]
    route,_=locked(cp['font_route_plan'])
    for ref in route['font_plans']:
        fp,_=locked(ref);families.extend(s['path'] for s in fp['sources'])
    fonts=sorted(set(families));toc_plan,_=locked(cp['subtitle_plan']);toc=toc_plan['toc']['path']
    originals={r['path']:confined_path(source,'controls/'+r['path']).read_bytes() for r in cm['resources']}
    raw,proof=raw_phase(originals,fonts,toc,decoder)
    for path in fonts:
        name='raw-controls/'+path;member=confined_path(font_root,name);data=member.read_bytes()
        if digest(data)!=fm['member_sha256'][name] or raw[path]!=data:
            raise ValueError('raw original font component mismatch')
        snapshots.append((member,digest(data)))
    files={name:confined_path(source,name).read_bytes() for name in cm['member_sha256']}
    rows=[]
    for r in cm['resources']:
        p=r['path'];files['raw-controls/'+p]=raw[p];files['raw-rollback-check/'+p]=originals[p]
        rows.append(dict(r,raw_sha256=digest(raw[p]),raw_size=len(raw[p])))
    files['reports/raw-originals.json']=encoded(proof)
    manifest=dict(cm,kind=KIND,composition_manifest_sha256=plan['composition_manifest']['sha256'],
                  comparison_plan_canonical_sha256=digest(encoded(plan)),raw_package_outputs=True,resources=rows,
                  raw_control_method='source-derived-uncompressed-fonts-original-text-disc-toc',
                  member_sha256={p:digest(b) for p,b in files.items()})
    files['manifest.json']=encoded(manifest);check_inputs(snapshots)
    return files,manifest,snapshots


def build(plan,project,output,decoder=None):
    output=Path(output);project=Path(project).resolve()
    if output.is_symlink() or output.exists():raise ValueError('comparison output must be new')
    output=output.resolve()
    if not output.is_relative_to(project) or output==project:raise ValueError('comparison output must be inside project')
    cp,_,_=read_locked_json(project,plan['composition_plan'])
    for ref in (plan['composition_manifest'],cp['font_component'],cp['subtitle_component']):
        parent=confined_path(project,ref['path']).parent
        if output.is_relative_to(parent) or parent.is_relative_to(output):raise ValueError('comparison output overlaps component')
    files,manifest,snapshots=prepare(plan,project,decoder);output.mkdir(parents=True,exist_ok=False)
    for name,data in files.items():
        p=confined_path(output,name)
        if name.startswith('raw-rollback-check/'):
            rel=name[len('raw-rollback-check/'):]
            restore_copy(output/'raw-controls'/rel,output/'controls'/rel,p,
                         digest(files['raw-controls/'+rel]),digest(data))
        else:
            p.parent.mkdir(parents=True,exist_ok=True)
            with p.open('xb') as f:f.write(data)
        if p.read_bytes()!=data:raise ValueError('comparison output reopening mismatch')
    check_inputs(snapshots);return manifest


def verify(plan,project,output,decoder=None):
    if Path(output).is_symlink():raise ValueError('comparison root cannot be linked')
    output=Path(output).resolve();files,m,snapshots=prepare(plan,project,decoder)
    scan_tree(output,set(files))
    for name,data in files.items():
        if confined_path(output,name).read_bytes()!=data:raise ValueError('comparison replay mismatch: '+name)
    check_inputs(snapshots);return m


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',type=Path,required=True)
    p.add_argument('--project-root',type=Path,default=Path('.'));p.add_argument('--lzx-library',type=Path,required=True)
    g=p.add_mutually_exclusive_group(required=True);g.add_argument('--output-dir',type=Path);g.add_argument('--verify-root',type=Path)
    a=p.parse_args(argv)
    try:
        before=a.plan.read_bytes();plan=parse_json_object(before);decoder=LzxDecoder(a.lzx_library)
        m=build(plan,a.project_root,a.output_dir,decoder) if a.output_dir else verify(plan,a.project_root,a.verify_root,decoder)
        if a.plan.read_bytes()!=before:raise ValueError('comparison plan changed')
        print(json.dumps(dict(disc=m['disc'],resources=len(m['resources']),raw_controls=True,
                             literal_coverage_verified=m['all_literal_coverage_verified'],deployment_performed=False),sort_keys=True));return 0
    except (OSError,ValueError,KeyError,TypeError,ImportError) as e:print('ERROR: '+str(e));return 2


if __name__=='__main__':raise SystemExit(main())
