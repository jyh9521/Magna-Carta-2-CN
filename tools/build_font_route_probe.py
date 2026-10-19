"""Compose explicitly planned font families into one undeployed warning probe.

Overlapping packages are edited sequentially and every font is checked again
after the last edit. Verification replays from retained original controls.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
try:
    from .font_binding_plan import digest,read_locked_json,_read,_relative,parse_json_object
    from .build_font_supplement import validate_plan,context,select_font,restore_copy
    from .font_binding_audit import fingerprint
    from .supplement_font import validate_plan as glyph_plan,rasterize_plan,supplement_package
    from .build_coalesced import rebuild
    from .audit_text_font_coverage import audit
    from .ue3_ui_styles import StyleGraph
    from .update_resource_sizes import update_sizes
    from .ue3_package import FormatError,LzxDecoder,parse_summary
    from .decompress_package import decompress_copy
except ImportError:
    from font_binding_plan import digest,read_locked_json,_read,_relative,parse_json_object
    from build_font_supplement import validate_plan,context,select_font,restore_copy
    from font_binding_audit import fingerprint
    from supplement_font import validate_plan as glyph_plan,rasterize_plan,supplement_package
    from build_coalesced import rebuild
    from audit_text_font_coverage import audit
    from ue3_ui_styles import StyleGraph
    from update_resource_sizes import update_sizes
    from ue3_package import FormatError,LzxDecoder,parse_summary
    from decompress_package import decompress_copy


def encoded(value):return (json.dumps(value,ensure_ascii=True,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()


def prepare(plan,game_root,project_root,font_file,decoder=None):
    if (type(plan.get('schema_version')) is not int or plan['schema_version']!=1 or plan.get('kind')!='offline-font-route-probe'
            or plan.get('game_rendering_verified') is not False):raise FormatError('unsupported font route probe plan')
    groups=plan.get('font_plans')
    if not isinstance(groups,list) or not 1<=len(groups)<=8:raise FormatError('font route family count outside bound')
    raw_mode=plan.get('raw_packages',False)
    if type(raw_mode) is not bool:raise FormatError('raw_packages must be an explicit boolean')
    if type(plan.get('verify_glyph_ink',False)) is not bool:raise FormatError('verify_glyph_ink must be boolean')
    if not isinstance(plan.get('additional_text_plans',[]),list) or len(plan.get('additional_text_plans',[]))>16:raise FormatError('additional text plan count outside bound')
    originals={};current={};raw_controls={};inputs=[];plans=[];reports=[];seen_fonts=set();identities=set();toc_spec=None
    def locked(spec):
        obj,path,raw=read_locked_json(project_root,spec);inputs.append((path,digest(raw)));return obj
    for spec in groups:
        fp=locked(spec);sources=validate_plan(fp);gp=locked(fp['supplement']);glyph_plan(gp)
        if fp['canonical_font_path'] in identities:raise FormatError('duplicate font route family')
        identities.add(fp['canonical_font_path'])
        if toc_spec is not None and fp['toc']!=toc_spec:raise FormatError('font route TOC inputs disagree')
        toc_spec=fp['toc']
        for source in sources:
            path=source['path'];key=(path,source['font_object'])
            if key in seen_fonts:raise FormatError('duplicate font route source object')
            seen_fonts.add(key);raw,physical=_read(game_root,path,source['sha256']);inputs.append((physical,source['sha256']))
            if path in originals and originals[path]!=raw:raise FormatError('shared package original mismatch')
            originals[path]=raw
            if path not in current:
                compressed=parse_summary(raw,len(raw))['compression_flags']
                current[path]=decompress_copy(raw,digest(raw),decoder)[0] if raw_mode and compressed else raw
                raw_controls[path]=current[path]
        plans.append((fp,gp,sources))
    font_file=Path(font_file);font_hash=digest(font_file.read_bytes());inputs.append((font_file,font_hash))
    if any(fp['font_source_sha256']!=font_hash for fp,_,_ in plans):raise FormatError('font route raster source mismatch')
    toc,toc_path=_read(game_root,toc_spec['path'],toc_spec['sha256']);inputs.append((toc_path,digest(toc)))
    tp=locked(plan['text_plan']);resource=_relative(plan['text_resource'])
    if tp.get('resource')!=resource or resource in originals or resource==toc_spec['path'] or toc_spec['path'] in originals:
        raise FormatError('font route resource roles conflict')
    text,text_path=_read(game_root,resource,tp['input_sha256']);inputs.append((text_path,digest(text)))
    # Use current in-memory package bytes; never deploy or edit originals.
    for fp,gp,sources in plans:
        alphas,_=rasterize_plan(font_file,font_hash,gp)
        for source in sources:
            label=source['label'].casefold();path=source['path'];ctx=context(current[path],decoder);g=StyleGraph({label:ctx})
            before=fingerprint(g,select_font(g,source,fp),decoder)
            if before['semantic_sha256']!=fp['expected_semantic_sha256']:raise FormatError('font route original semantic mismatch')
            changed,report=supplement_package(current[path],digest(current[path]),source['font_object'],gp,alphas,decoder,raw_atlas=raw_mode)
            current[path]=changed;reports.append(dict(family=fp['canonical_font_path'],resource=path,report=report))
    extra_texts=[]
    for ref in plan.get('additional_text_plans',[]):
        ep=locked(ref);path=_relative(ep['resource'])
        if path in originals or path in {resource,toc_spec['path']}:raise FormatError('duplicate additional resource role')
        original,physical=_read(game_root,path,ep['input_sha256']);inputs.append((physical,digest(original)))
        from tools.subtitle_text import rebuild as rebuild_subtitle
        originals[path]=original;current[path]=rebuild_subtitle(original,ep);raw_controls[path]=original
        extra_texts.extend(e['translation'] for e in ep['entries'])
    final=[];coverage_fonts=[];ink_reports=[]
    for fp,gp,sources in plans:
        for source in sources:
            label=source['label'].casefold();raw=current[source['path']];g=StyleGraph({label:context(raw,decoder)})
            result=fingerprint(g,select_font(g,source,fp),decoder)
            if result['semantic_sha256']!=fp['expected_supplement_semantic_sha256']:raise FormatError('font route final semantic mismatch')
            final.append(dict(family=fp['canonical_font_path'],resource=source['path'],fingerprint=result))
            coverage_fonts.append(dict(label='route'+str(len(coverage_fonts)),data=raw,sha256=digest(raw),font_object=source['font_object']))
            if plan.get('verify_glyph_ink'):
                from tools.font_ink import ink_records
                from tools.audit_text_font_coverage import literal_codepoints
                from tools.ue3_fonts import parse_font_payload
                ctx=g.packages[label];ex=g.export(*select_font(g,source,fp))
                font=parse_font_payload(ctx['logical'][ex['serial_offset']:ex['serial_offset']+ex['serial_size']],ctx['tables']['names'])
                texts=[e['translation'] for e in tp['entries']]+extra_texts
                cps={cp for t in texts for cp in literal_codepoints(t)}
                records=ink_records(ctx,font,cps,decoder)
                if any(r['status']!='ink' for r in records):raise FormatError('mapped glyph has no ink or is missing')
                ink_reports.append(dict(family=fp['canonical_font_path'],resource=source['path'],codepoints=records))
    coverage=audit(text,tp,coverage_fonts,decoder)
    if not coverage['all_supplied_fonts_cover_literals']:raise FormatError('font route full probe text lacks coverage')
    changed_text=rebuild(text,tp)
    if digest(changed_text)!=plan['expected_text_sha256']:raise FormatError('font route text output mismatch')
    originals[resource]=text;current[resource]=changed_text
    changes=[dict(path=p,expected_size=len(originals[p]),new_size=len(raw)) for p,raw in current.items() if len(raw)!=len(originals[p])]
    new_toc=update_sizes(toc,toc_spec['sha256'],changes) if changes else toc
    reverse=[dict(path=r['path'],expected_size=r['new_size'],new_size=r['expected_size']) for r in changes]
    if (update_sizes(new_toc,digest(new_toc),reverse) if reverse else new_toc)!=toc:raise FormatError('font route TOC inverse mismatch')
    originals[toc_spec['path']]=toc;current[toc_spec['path']]=new_toc
    files={};rows=[]
    if raw_mode:
        raw_changes=[dict(path=p,expected_size=len(originals[p]),new_size=len(raw)) for p,raw in raw_controls.items() if len(raw)!=len(originals[p])]
        raw_controls[resource]=text;raw_controls[toc_spec['path']]=update_sizes(toc,digest(toc),raw_changes) if raw_changes else toc
        files.update({'raw-controls/'+p:raw for p,raw in raw_controls.items()})
    for path in sorted(originals):
        for kind,raw in [('controls',originals[path]),('candidate',current[path]),('rollback-check',originals[path])]:files[kind+'/'+path]=raw
        rows.append(dict(path=path,original_sha256=digest(originals[path]),candidate_sha256=digest(current[path]),original_size=len(originals[path]),candidate_size=len(current[path])))
    files['reports/fonts.json']=encoded(final);files['reports/coverage.json']=encoded(coverage);files['reports/operations.json']=encoded(reports)
    if plan.get('verify_glyph_ink'):files['reports/ink.json']=encoded(ink_reports)
    manifest=dict(schema_version=1,kind=plan['kind'],plan_canonical_sha256=digest(encoded(plan)),font_family_count=len(plans),font_object_count=len(final),
        resources=rows,toc_changes=changes,member_sha256={p:digest(raw) for p,raw in files.items()},
        rollback_method='hash-guarded-retained-original-backup',game_rendering_verified=False,deployment_performed=False)
    if raw_mode:manifest['raw_package_outputs']=True
    files['manifest.json']=encoded(manifest)
    check_inputs(inputs)
    return files,inputs,manifest


def check_inputs(inputs):
    if any(digest(Path(p).read_bytes())!=h for p,h in inputs):raise FormatError('font route input changed')


def build(plan,game_root,project_root,font_file,output_root,decoder=None):
    output=Path(output_root).resolve();game=Path(game_root).resolve()
    if output.exists() or Path(output_root).is_symlink() or output.is_relative_to(game):raise FormatError('font route output must be new and outside originals')
    files,inputs,manifest=prepare(plan,game,project_root,font_file,decoder)
    output.mkdir(parents=True,exist_ok=False)
    for path,raw in files.items():
        target=output/path
        if path.startswith('rollback-check/'):
            relative=path[len('rollback-check/'):]
            restore_copy(output/'candidate'/relative,output/'controls'/relative,target,digest(files['candidate/'+relative]),digest(raw))
        else:
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as stream:stream.write(raw)
        if target.read_bytes()!=raw:raise FormatError('font route output reopening mismatch')
    check_inputs(inputs)
    return manifest


def verify(plan,root,project_root,font_file,decoder=None):
    try:
        from .verify_locale_candidate import scan_tree
    except ImportError:
        from verify_locale_candidate import scan_tree
    root=Path(root).resolve();files,inputs,manifest=prepare(plan,root/'controls',project_root,font_file,decoder)
    scan_tree(root,set(files))
    for path,expected in files.items():
        if (root/path).read_bytes()!=expected:raise FormatError('font route independent replay mismatch: '+path)
    check_inputs(inputs);return manifest


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',type=Path,required=True);p.add_argument('--project-root',type=Path,default=Path('.'))
    p.add_argument('--font-file',type=Path,required=True);p.add_argument('--game-root',type=Path)
    mode=p.add_mutually_exclusive_group(required=True);mode.add_argument('--output-dir',type=Path);mode.add_argument('--verify-root',type=Path)
    p.add_argument('--lzx-library',type=Path);a=p.parse_args(argv)
    try:
        raw=a.plan.read_bytes();plan=parse_json_object(raw)
        decoder=LzxDecoder(a.lzx_library) if a.lzx_library else None
        if a.output_dir:
            if a.game_root is None:raise FormatError('font route build requires game root')
            r=build(plan,a.game_root,a.project_root,a.font_file,a.output_dir,decoder)
        else:r=verify(plan,a.verify_root,a.project_root,a.font_file,decoder)
        if a.plan.read_bytes()!=raw:raise FormatError('font route plan changed')
        print(json.dumps(dict(font_objects=r['font_object_count'],resources=len(r['resources']),verified=bool(a.verify_root),deployment_performed=False),sort_keys=True));return 0
    except (OSError,ValueError,KeyError,TypeError,ImportError) as exc:
        print('ERROR: '+str(exc));return 2


if __name__=='__main__':raise SystemExit(main())
