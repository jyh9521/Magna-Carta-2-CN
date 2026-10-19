"""Audit actual sample glyph advances through the bounded native width replay.

Controlled layout model only: kerning/bias assumptions are explicit;
tokenization, live font selection, actual UI coordinates and pixels are not
observed. Wide no-wrap cases must remain unchanged, not just narrow cases.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
try:
    from .runtime_patch import apply_image,digest
    from .replay_wrap_width import replay
    from .build_coalesced import rebuild
    from .build_font_supplement import context
    from .ue3_fonts import parse_font_payload
    from .verify_resource_phase import inspect,confined,stable
except ImportError:
    from runtime_patch import apply_image,digest
    from replay_wrap_width import replay
    from build_coalesced import rebuild
    from build_font_supplement import context
    from ue3_fonts import parse_font_payload
    from verify_resource_phase import inspect,confined,stable


def sample_paragraph(sample,entry_id=None):
    selected=sample['entries'][0] if entry_id is None else next((e for e in sample['entries'] if e['id']==entry_id),None)
    if selected is None:raise ValueError('layout audit entry ID absent from sample')
    text=selected['translation'].split('\\n')[-1]
    if not text or any(c.isspace() for c in text):raise ValueError('audit requires an unspaced final paragraph')
    return selected['id'],text


def audit(image,plan,sample,packet,manifest_sha,fonts,entry_id=None):
    packet=Path(packet).resolve()
    if digest(image)==plan['image_sha256']:variant='baseline'
    else:
        apply_image(image,plan,reverse=True);variant='modified'
    checked,snapshots=inspect(packet,manifest_sha,packet/'candidate','candidate')
    if not checked['all_resources_match']:raise ValueError('sample packet bytes mismatch')
    original=confined(packet/'controls',sample['resource']).read_bytes()
    candidate=confined(packet/'candidate',sample['resource']).read_bytes()
    if rebuild(original,sample)!=candidate:raise ValueError('candidate sample text differs from exact plan')
    selected_id,text=sample_paragraph(sample,entry_id)
    profile=plan['replay'];cases=[]
    for spec in fonts:
        path,obj=spec.split('::',1);ctx=context(confined(packet/'candidate',path).read_bytes(),None)
        e=next(e for e in ctx['tables']['exports'] if e['path']==obj)
        font=parse_font_payload(ctx['logical'][e['serial_offset']:e['serial_offset']+e['serial_size']],ctx['tables']['names'])
        mapping={r['codepoint']:r['glyph_index'] for r in font['remap']}
        advances=[font['characters'][mapping[ord(c)]]['USize'] for c in text]
        for origin in (0,193,640):
            for width in (128,380,396,800,1200):
                for scale in (.5,1,1.5,2):
                    lines=[];cursor=0
                    while cursor<len(text):
                        start=cursor;actual=0
                        while cursor<len(text) and actual+advances[cursor]*scale<=width:
                            actual+=advances[cursor]*scale;cursor+=1
                        if cursor==start:raise ValueError('audit cell wider than model box')
                        if cursor==len(text):reported=actual
                        else:
                            reported,_=replay(image,plan['image_base'],profile['entry'],profile['exit'],profile['cave'],
                                origin,origin+actual+advances[cursor]*scale,scale,advances[cursor])
                        x=origin+(width-reported)/2
                        lines.append(dict(text=text[start:cursor],actual_width=actual,reported_width=reported,x=x,
                            center_error=x-(origin+(width-actual)/2),inside=origin<=x and x+actual<=origin+width))
                    cases.append(dict(font=obj,origin=origin,width=width,scale=scale,lines=lines,
                        passed=all(l['center_error']==0 and l['inside'] for l in lines)))
    stable(snapshots)
    return dict(variant=variant,cases=len(cases),failed_cases=sum(not c['passed'] for c in cases),
        no_wrap_cases=sum(len(c['lines'])==1 for c in cases),
        no_wrap_failures=sum(len(c['lines'])==1 and not c['passed'] for c in cases),
        text_resource_sha256=digest(candidate),entry_id=selected_id,manual_newlines_added=0,game_started=False,
        assumptions='glyph USize advance; zero additional runtime bias/kerning; controlled box widths and scale; final paragraph only',
        rows=cases)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('image','plan','sample','packet-root','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--manifest-sha256',required=True);p.add_argument('--font',action='append',required=True)
    p.add_argument('--entry-id',help='Audit the final original-break-delimited paragraph of this sample entry')
    a=p.parse_args(argv)
    try:
        roots=[a.image.resolve(),a.plan.resolve(),a.sample.resolve(),a.packet_root.resolve()]
        if a.output.exists() or any(a.output.resolve().is_relative_to(r) for r in roots):raise ValueError('audit output must be new and outside inputs')
        r=audit(a.image.read_bytes(),json.loads(a.plan.read_bytes()),json.loads(a.sample.read_bytes()),a.packet_root,a.manifest_sha256,a.font,a.entry_id)
        raw=(json.dumps(r,ensure_ascii=True,indent=2)+'\n').encode();a.output.parent.mkdir(parents=True,exist_ok=True)
        with a.output.open('xb') as f:f.write(raw)
        if a.output.read_bytes()!=raw:raise ValueError('layout audit reopening mismatch')
        print(json.dumps({k:r[k] for k in ('variant','cases','failed_cases','no_wrap_cases','no_wrap_failures','manual_newlines_added','game_started')},sort_keys=True))
        return int(r['failed_cases']>0)
    except (OSError,ValueError,KeyError,TypeError,StopIteration) as e:print('ERROR: '+str(e));return 2


if __name__=='__main__':raise SystemExit(main())
