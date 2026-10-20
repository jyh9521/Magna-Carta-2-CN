"""Compose one disc's verified font/subtitle components and full INT offline.

Retained literal controls remain explicitly unverified for runtime/coverage.
Partial TOCs are never copied: one table is rebuilt from this disc's original.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import unicodedata
from tools.font_binding_plan import digest,read_locked_json,confined_path,_relative,parse_json_object
from tools.build_font_supplement import context,select_font,validate_plan as validate_font_plan,restore_copy
from tools.build_font_route_probe import encoded
from tools.build_subtitle_bundle import load_inputs as subtitle_inputs,select_inputs,verify as verify_subtitles
from tools.verify_locale_candidate import scan_tree
from tools.disc_inventory import Disc,sha256_file
from tools.build_coalesced import rebuild,resolve_changes
from tools.audit_text_font_coverage import (audit,audit_control_retention,literal_control_shape,
    literal_codepoints,font_coverage)
from tools.font_binding_audit import fingerprint
from tools.ue3_ui_styles import StyleGraph
from tools.ue3_fonts import parse_font_payload
from tools.ue3_package import LzxDecoder
from tools.supplement_font import parse_atlas_payload,atlas_tiles,METRIC_KEYS
from tools.ue3_textures import untile_dxt5,decode_dxt5
from tools.subtitle_text import parse as parse_subtitles
from tools.update_resource_sizes import update_sizes_reversible


def merge_resources(originals,font_updates,subtitle_updates,text_plan,ledger,toc_spec):
    """Pure byte composition; component identity/Font checks are performed by prepare."""
    text_path=text_plan['resource'];toc_path=toc_spec['path']
    roles=list(font_updates)+list(subtitle_updates)+[text_path,toc_path]
    for path in roles:_relative(path)
    if len(set(p.casefold() for p in roles))!=len(roles) or set(originals)!=set(roles):
        raise ValueError('composition roles overlap or originals do not match this disc')
    resolved=resolve_changes(originals[text_path],text_plan)
    if ledger is not None:
        retention=audit_control_retention(originals[text_path],text_plan,ledger)
    else:
        if any(literal_control_shape(e[k])[0] for e in resolved['entries'] for k in ('source','translation')):
            raise ValueError('literal controls require explicit source retention evidence')
        retention=dict(entries=[],retained_literal_codepoints=[],font_coverage_verified=False,
                       unknown_control_syntax_resolved=False,game_rendering_verified=False)
    current={**font_updates,**subtitle_updates,text_path:rebuild(originals[text_path],text_plan)}
    changes=[dict(path=p,expected_size=len(originals[p]),new_size=len(b))
             for p,b in current.items() if len(b)!=len(originals[p])]
    current[toc_path],toc_report=update_sizes_reversible(originals[toc_path],toc_spec['sha256'],changes)
    return current,retention,toc_report,changes


def pixel_proof(ctx,font,wanted,decoder):
    mapping={r['codepoint']:r['glyph_index'] for r in font['remap']};cache={};ink=0;blanks=[]
    for cp in sorted(wanted):
        if unicodedata.category(chr(cp)).startswith('C'):continue
        g=font['characters'][mapping[cp]];ti=g['TextureIndex']
        if ti not in cache:
            if not 0<=ti<len(font['textures']):raise ValueError('glyph texture index outside font')
            ref=font['textures'][ti]
            if not 1<=ref<=len(ctx['tables']['exports']):raise ValueError('glyph atlas is not local')
            ex=ctx['tables']['exports'][ref-1];raw=ctx['logical'][ex['serial_offset']:ex['serial_offset']+ex['serial_size']]
            t=parse_atlas_payload(raw,ctx['tables']['names'],ex['serial_offset'])
            cache[ti]=(t['width'],t['height'],decode_dxt5(untile_dxt5(atlas_tiles(raw,t,decoder),t['width'],t['height']),t['width'],t['height']))
        w,h,rgba=cache[ti];x,y,gw,gh=[g[k] for k in ('StartU','StartV','USize','VSize')]
        if min(x,y)<0 or min(gw,gh)<=0 or x+gw>w or y+gh>h:raise ValueError('glyph rectangle outside atlas')
        visible=sum(rgba[((y+iy)*w+x+ix)*4+3]>0 for iy in range(gh) for ix in range(gw))
        if chr(cp).isspace():
            if unicodedata.category(chr(cp))!='Zs' or visible:raise ValueError('unsupported or visible layout literal')
            blanks.append(cp)
        elif not visible:raise ValueError('mapped non-layout glyph has no ink')
        else:ink+=1
    return dict(ink_glyphs=ink,blank_layout_codepoints=blanks,blank_alpha_zero=True)


def prepare(plan,root,originals=None,decoder=None):
    root=Path(root).resolve();snapshots=[]
    def locked(ref):
        obj,path,raw=read_locked_json(root,ref);snapshots.append((path,digest(raw)));return obj
    if (type(plan.get('schema_version')) is not int or plan['schema_version']!=1
            or plan.get('kind')!='offline-disc-locale-composition' or type(plan.get('disc')) is not int
            or plan.get('game_rendering_verified') is not False):raise ValueError('invalid offline disc composition plan')
    subplan=locked(plan['subtitle_plan']);text_plan=locked(plan['text_plan'])
    ledger=locked(plan['control_ledger']) if 'control_ledger' in plan else None
    route=locked(plan['font_route_plan'])
    if (type(route.get('schema_version')) is not int or route['schema_version']!=1
            or route.get('kind')!='offline-font-route-probe' or route.get('raw_packages') is not True
            or route.get('game_rendering_verified') is not False):
        raise ValueError('composition requires explicit raw font component')
    profile,subplans,subsnapshots=subtitle_inputs(subplan,root)
    snapshots.extend((p,digest(raw)) for p,raw in subsnapshots)
    source,_=select_inputs(subplan,profile,subplans)
    if source['disc']!=plan['disc']:raise ValueError('subtitle disc identity mismatch')
    def component(ref,kind):
        m=locked(ref);parent=confined_path(root,ref['path']).parent
        if (type(m.get('schema_version')) is not int or m['schema_version']!=1 or m.get('kind')!=kind
                or m.get('game_rendering_verified') is not False or m.get('deployment_performed') is not False):
            raise ValueError('composition component kind or verification state mismatch')
        names=set(m['member_sha256'])|{'manifest.json'}
        for p in names:_relative(p)
        scan_tree(parent,names)
        for name,h in m['member_sha256'].items():
            p=confined_path(parent,name)
            if digest(p.read_bytes())!=h:raise ValueError('component member SHA256 mismatch')
            snapshots.append((p,h))
        return m,parent
    fonts,font_root=component(plan['font_component'],'offline-font-route-probe')
    subtitles,sub_root=component(plan['subtitle_component'],'offline-disc-subtitle-bundle')
    if (fonts.get('raw_package_outputs') is not True or fonts['plan_canonical_sha256']!=digest(encoded(route))
            or subtitles['plan_canonical_sha256']!=digest(encoded(subplan))
            or subtitles['disc']!=plan['disc']):raise ValueError('component plan or disc mismatch')
    if encoded(verify_subtitles(subplan,root,sub_root))!=encoded(subtitles):raise ValueError('subtitle replay mismatch')
    if not isinstance(route.get('font_plans'),list) or not 1<=len(route['font_plans'])<=8:
        raise ValueError('composition font family count outside bound')
    families=[];font_paths={};objects=set()
    for ref in route['font_plans']:
        fp=locked(ref);sources=validate_font_plan(fp)
        for s in sources:
            key=(s['path'],s['font_object'])
            if key in objects:raise ValueError('duplicate composition font object')
            objects.add(key)
            if s['path'] in font_paths and font_paths[s['path']]!=s['sha256']:raise ValueError('font original identity conflict')
            font_paths[s['path']]=s['sha256']
        families.append((fp,locked(fp['supplement']),sources))
    if (type(fonts.get('font_object_count')) is not int or fonts['font_object_count']!=len(objects)
            or type(fonts.get('font_family_count')) is not int or fonts['font_family_count']!=len(families)):
        raise ValueError('font object or family count mismatch')
    text_path=text_plan['resource'];toc=subplan['toc']
    if text_path!=route['text_resource']:raise ValueError('composition text resource mismatch')
    sub_paths={m['resource'] for m in source['members']}
    roles=list(font_paths)+list(sub_paths)+[text_path,toc['path']]
    if len({p.casefold() for p in roles})!=len(roles):raise ValueError('composition resource role conflict')
    for path in roles:_relative(path)
    image_guard=None
    if originals is None:
        image=confined_path(root,source['path']);stat=image.stat()
        if stat.st_size!=source['size'] or sha256_file(image)!=source['sha256']:raise ValueError('composition source ISO identity mismatch')
        disc=Disc(image);inventory={e['path']:e for e in disc.inventory() if not e['directory']};originals={}
        for path in roles:
            e=inventory.get(path)
            if e is None or not 1<=e['size']<=128*1024*1024:raise ValueError('composition resource absent or oversized')
            originals[path]=disc.read(e['offset'],e['size'])
        image_guard=(image,stat.st_size,stat.st_mtime_ns)
    if set(originals)!=set(roles):raise ValueError('composition original member set mismatch')
    def original(path,expected):
        if digest(originals[path])!=expected:raise ValueError('composition original hash mismatch: '+path)
    original(text_path,text_plan['input_sha256']);original(toc['path'],toc['sha256'])
    font_updates={}
    font_rows={r['path']:r for r in fonts['resources']}
    for path,h in font_paths.items():
        original(path,h)
        if font_rows[path]['original_sha256']!=h:raise ValueError('font component provenance mismatch')
        font_updates[path]=confined_path(font_root,'candidate/'+path).read_bytes()
        if digest(font_updates[path])!=font_rows[path]['candidate_sha256']:raise ValueError('font component candidate hash mismatch')
    subtitle_updates={}
    subtitle_rows={r['path']:r for r in subtitles['resources']}
    for member in source['members']:
        path=member['resource'];original(path,member['sha256'])
        if originals[path]!=confined_path(sub_root,'controls/'+path).read_bytes():raise ValueError('subtitle component source mismatch')
        subtitle_updates[path]=confined_path(sub_root,'candidate/'+path).read_bytes()
        if digest(subtitle_updates[path])!=subtitle_rows[path]['candidate_sha256']:raise ValueError('subtitle component candidate hash mismatch')
    current,retention,toc_report,changes=merge_resources(originals,font_updates,subtitle_updates,text_plan,ledger,toc)
    resolved=resolve_changes(originals[text_path],text_plan)
    wanted={cp for e in resolved['entries'] for cp in literal_codepoints(e['translation'])}
    for raw in subtitle_updates.values():
        for cue in parse_subtitles(raw)[1]:
            if literal_control_shape(cue[4])[0]:raise ValueError('subtitle literal controls need separate explicit evidence')
            wanted.update(literal_codepoints(cue[4]))
    retained=set(retention['retained_literal_codepoints']);coverage_fonts=[];font_proofs=[]
    for fp,gp,sources in families:
        for s in sources:
            label=s['label'].casefold();path=s['path'];ctx=context(current[path],decoder);graph=StyleGraph({label:ctx})
            ex=graph.export(*select_font(graph,s,fp))
            if fingerprint(graph,select_font(graph,s,fp),decoder)['semantic_sha256']!=fp['expected_supplement_semantic_sha256']:
                raise ValueError('composed font semantic mismatch')
            font=parse_font_payload(ctx['logical'][ex['serial_offset']:ex['serial_offset']+ex['serial_size']],ctx['tables']['names'])
            failures=[r for r in font_coverage(font,sorted(wanted)) if r['status']!='mapped']
            if any(r['status']!='control-or-format-literal-unverified' or r['codepoint'] not in retained for r in failures):
                raise ValueError('non-retained font coverage failure')
            before_ctx=context(originals[path],decoder);before_graph=StyleGraph({label:before_ctx});node=select_font(before_graph,s,fp)
            if fingerprint(before_graph,node,decoder)['semantic_sha256']!=fp['expected_semantic_sha256']:
                raise ValueError('original font semantic mismatch')
            be=before_graph.export(*node);bf=parse_font_payload(before_ctx['logical'][be['serial_offset']:be['serial_offset']+be['serial_size']],before_ctx['tables']['names'])
            bm={r['codepoint']:r['glyph_index'] for r in bf['remap']}
            if not bf['is_remapped']:
                if gp.get('remap_conversion')!='identity-256' or len(bf['characters'])!=256:raise ValueError('unverified original direct-index font mode')
                bm=dict(zip(range(256),range(256)))
            cm={r['codepoint']:r['glyph_index'] for r in font['remap']}
            for cp in retained:
                if cp not in bm or cm.get(cp)!=bm[cp] or any(bf['characters'][bm[cp]][k]!=font['characters'][cm[cp]][k] for k in METRIC_KEYS):
                    raise ValueError('retained control original glyph mapping/metrics changed')
            proof=pixel_proof(ctx,font,wanted,decoder)
            font_proofs.append(dict(family=fp['canonical_font_path'],resource=path,**proof,
                retained_control_glyph_mappings_and_metrics_preserved=True,unverified_literals=failures))
            coverage_fonts.append(dict(label='route'+str(len(coverage_fonts)),data=current[path],sha256=digest(current[path]),font_object=s['font_object']))
    coverage=audit(originals[text_path],text_plan,coverage_fonts,decoder)
    if coverage['rebuilt_sha256']!=digest(current[text_path]):raise ValueError('composition INT output mismatch')
    files={};rows=[]
    for path in sorted(originals):
        for kind,raw in [('controls',originals[path]),('candidate',current[path]),('rollback-check',originals[path])]:files[kind+'/'+path]=raw
        rows.append(dict(path=path,original_sha256=digest(originals[path]),candidate_sha256=digest(current[path]),original_size=len(originals[path]),candidate_size=len(current[path])))
    for name,obj in [('font-proofs',font_proofs),('text-font-coverage',coverage),('control-retention',retention),('combined-toc',toc_report)]:
        files['reports/'+name+'.json']=encoded(obj)
    manifest=dict(schema_version=1,kind=plan['kind'],disc=plan['disc'],source_image_sha256=source['sha256'],
        plan_canonical_sha256=digest(encoded(plan)),INT_entries=len(resolved['entries']),subtitle_resources=len(sub_paths),
        subtitle_cues=subtitles['translated_cues'],font_objects=len(font_proofs),resources=rows,toc_changes=changes,
        all_noncontrol_literals_covered=True,all_literal_coverage_verified=coverage['all_supplied_fonts_cover_literals'],
        retained_control_literals=sorted(retained),unknown_control_syntax_resolved=False,
        game_rendering_verified=False,deployment_performed=False,member_sha256={p:digest(raw) for p,raw in files.items()})
    files['manifest.json']=encoded(manifest)
    check_inputs(snapshots,image_guard)
    return files,manifest,snapshots,image_guard


def check_inputs(snapshots,image_guard=None):
    if any(digest(p.read_bytes())!=h for p,h in snapshots):raise ValueError('composition input changed')
    if image_guard:
        image,size,mtime=image_guard;now=image.stat()
        if (now.st_size,now.st_mtime_ns)!=(size,mtime):raise ValueError('composition ISO changed')


def build(plan,root,output,decoder=None):
    if Path(output).is_symlink():raise ValueError('composition output cannot be linked')
    root,output=Path(root).resolve(),Path(output).resolve()
    if output.exists() or not output.is_relative_to(root) or output==root:raise ValueError('composition output must be new and inside project')
    files,manifest,snapshots,guard=prepare(plan,root,decoder=decoder);output.mkdir(parents=True,exist_ok=False)
    for path,raw in files.items():
        target=confined_path(output,path)
        if path.startswith('rollback-check/'):
            relative=path[len('rollback-check/'):]
            restore_copy(output/'candidate'/relative,output/'controls'/relative,target,digest(files['candidate/'+relative]),digest(raw))
        else:
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as f:f.write(raw)
        if target.read_bytes()!=raw:raise ValueError('composition output reopening mismatch')
    check_inputs(snapshots,guard);return manifest


def verify(plan,root,output,decoder=None):
    if Path(output).is_symlink():raise ValueError('composition verify root cannot be linked')
    output=Path(output).resolve();m=json.loads((output/'manifest.json').read_bytes())
    originals={r['path']:confined_path(output,'controls/'+r['path']).read_bytes() for r in m['resources']}
    files,manifest,snapshots,_=prepare(plan,root,originals=originals,decoder=decoder)
    scan_tree(output,set(files))
    for path,raw in files.items():
        if confined_path(output,path).read_bytes()!=raw:raise ValueError('composition independent replay mismatch: '+path)
    check_inputs(snapshots);return manifest


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',type=Path,required=True)
    p.add_argument('--project-root',type=Path,default=Path('.'));p.add_argument('--lzx-library',type=Path,required=True)
    g=p.add_mutually_exclusive_group(required=True);g.add_argument('--output-dir',type=Path);g.add_argument('--verify-root',type=Path)
    a=p.parse_args(argv)
    try:
        raw=a.plan.read_bytes();plan=parse_json_object(raw);decoder=LzxDecoder(a.lzx_library)
        m=build(plan,a.project_root,a.output_dir,decoder) if a.output_dir else verify(plan,a.project_root,a.verify_root,decoder)
        if a.plan.read_bytes()!=raw:raise ValueError('composition plan changed')
        print(json.dumps(dict(disc=m['disc'],INT_entries=m['INT_entries'],subtitle_cues=m['subtitle_cues'],resources=len(m['resources']),verified=bool(a.verify_root),literal_coverage_verified=m['all_literal_coverage_verified'],deployment_performed=False),sort_keys=True));return 0
    except (OSError,ValueError,KeyError,TypeError,ImportError) as e:
        print('ERROR: '+str(e));return 2


if __name__=='__main__':raise SystemExit(main())
