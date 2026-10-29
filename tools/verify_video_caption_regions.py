"""Focused, source-locked all-frame replay of one caption role and protected art.

This supplements whole-frame build replay. A prior plan/candidate may be supplied
as a measurable regression baseline. Coordinates, role and error bounds are
explicit inputs, not embedded locale or game constants. Original art hidden by
source lettering is reconstructed; unmasked pixels are preserved before lossy
encoding, not misrepresented as lossless final video.
"""
import argparse,copy,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from .build_video_captions import load_plan,locked_file,prepare_layers,composite,encoded
from .video_caption import bink_header,decoded_frames,sha


def rectangle(value):
    values=[int(v) for v in value.split(',')]
    if len(values)!=4 or min(values[:2])<0 or min(values[2:])<1:raise ValueError('Explicit rectangle required')
    return values


def intersection(a,b):
    return max(a[0],b[0])<min(a[0]+a[2],b[0]+b[2]) and max(a[1],b[1])<min(a[1]+a[3],b[1]+b[3])


def local_layers(plan,entry,role,root,source_root,ffmpeg,rect):
    chosen=copy.deepcopy(entry);chosen['captions']=[c for c in entry['captions'] if c['role']==role]
    if len(chosen['captions'])!=1:raise ValueError('Unique caption role required')
    source,raw,header,masks,layer,changed,proof=prepare_layers(plan,chosen,root,source_root,ffmpeg)
    x,y,w,h=rect;box=(x,y,x+w,y+h)
    if x+w>header['width'] or y+h>header['height']:raise ValueError('ROI outside movie')
    shifted=[];erase=np.zeros((h,w),bool)
    from .video_native_indicator import NativeIndicator
    for operation in masks:
        area,mask=operation
        xx,yy,ww,hh=area
        if xx<x or yy<y or xx+ww>x+w or yy+hh>y+h:raise ValueError('ROI must contain complete erase mask')
        if isinstance(operation,NativeIndicator):
            moved=copy.copy(operation);moved.rect=(xx-x,yy-y,ww,hh);shifted.append(moved)
        else:shifted.append(([xx-x,yy-y,ww,hh],mask))
        erase[yy-y:yy-y+hh,xx-x:xx-x+ww]|=mask
    # Reject unaccounted-for neighbouring captions in the selected crop.
    for c in entry['captions']:
        if c['role']!=role and intersection(c['style']['rect'],rect):
            raise ValueError('ROI intersects another caption')
    return source,raw,header,shifted,layer.crop(box),changed[y:y+h,x:x+w],erase,proof


def metrics(delta,mask):
    values=delta[mask].mean(axis=1)
    if not len(values):raise ValueError('Focused comparison mask empty')
    return dict(mean=float(values.mean()),p99=float(np.quantile(values,.99)),maximum=float(values.max()))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('plan','prior-plan','source-root','candidate-root','baseline-root','ffmpeg','output-dir'):
        p.add_argument('--'+name,required=True,type=Path)
    for name in ('plan-sha256','prior-plan-sha256','ffmpeg-sha256','role'):p.add_argument('--'+name,required=True)
    p.add_argument('--project-root',type=Path,default=Path('.'));p.add_argument('--region',type=rectangle,required=True)
    p.add_argument('--reference-caption-x',type=int)
    p.add_argument('--measurement',choices=('new-erase-halo','owned-text-support'),default='new-erase-halo')
    p.add_argument('--protect',type=rectangle,action='append',default=[])
    p.add_argument('--max-mean',type=float,default=5);p.add_argument('--max-p99',type=float,default=20)
    a=p.parse_args()
    if not a.protect or not 0<a.max_mean<=255 or not 0<a.max_p99<=255:raise ValueError('Explicit protected regions and finite error bounds required')
    plan,_=load_plan(a.plan,a.plan_sha256);prior,_=load_plan(a.prior_plan,a.prior_plan_sha256)
    locked_file(a.ffmpeg,a.ffmpeg_sha256,256*1024*1024)
    old={e['id']:e for e in prior['entries']};out=a.output_dir;out.mkdir(exist_ok=True,parents=True)
    all_rows=[];contact=Image.new('RGB',(a.region[2]*4,len(plan['entries'])*a.region[3]),(20,24,26))
    for index,e in enumerate(plan['entries']):
        shift=0 if a.reference_caption_x is None else next(c['style']['rect'][0] for c in e['captions'] if c['role']==a.role)-a.reference_caption_x
        region=[a.region[0]+shift,*a.region[1:]]
        guards=[[r[0]+shift,*r[1:]] for r in a.protect]
        args=(a.role,a.project_root,a.source_root,a.ffmpeg,region)
        source,source_raw,header,masks,layer,changed,erase,proof=local_layers(plan,e,*args)
        _,_,_,old_masks,old_layer,old_changed,old_erase,_=local_layers(prior,old[e['id']],*args)
        halo=changed if a.measurement=='owned-text-support' else erase&~old_erase&~(np.asarray(layer.getchannel('A'))>0)
        if not halo.any():raise ValueError('Selected measurement support is empty')
        protected=np.zeros_like(changed);x,y,w,h=region
        for px,py,pw,ph in guards:
            if px<x or py<y or px+pw>x+w or py+ph>y+h:raise ValueError('Protected region outside ROI')
            protected[py-y:py-y+ph,px-x:px-x+pw]=True
        if (changed&protected).any():raise ValueError('Caption touches protected artwork')
        candidate=a.candidate_root/(e['id']+'.bik');candidate_raw=candidate.read_bytes()
        baseline=a.baseline_root/e['source']['member'];baseline_raw=baseline.read_bytes()
        if bink_header(candidate_raw)!=header or bink_header(baseline_raw)!=header:raise ValueError('Video timeline differs')
        streams=[decoded_frames(a.ffmpeg,p,header) for p in (source,candidate,baseline)]
        rows=[];box=(x,y,x+w,y+h)
        try:
            for frame_no,(s,c,b) in enumerate(zip(*streams,strict=True)):
                images=[Image.frombytes('RGB',(header['width'],header['height']),raw).crop(box) for raw in (s,c,b)]
                expected=composite(images[0],masks,layer,changed,frame_no)
                delta=np.abs(np.array(expected).astype('int16')-np.array(images[1]).astype('int16'))
                old_delta=np.abs(np.array(expected).astype('int16')-np.array(images[2]).astype('int16'))
                old_expected=composite(images[0],old_masks,old_layer,old_changed,frame_no)
                if not np.array_equal(np.array(expected)[protected],np.array(images[0])[protected]):raise ValueError('Protected preencode pixels changed')
                if not np.array_equal(np.array(expected)[~(changed|old_changed)],np.array(old_expected)[~(changed|old_changed)]):raise ValueError('Caption change escaped mask union')
                row=dict(frame=frame_no,modified_halo=metrics(delta,halo),baseline_halo=metrics(old_delta,halo),
                    protected_decode_mean=float(delta[protected].mean()),protected_preencode_changed_pixels=0,
                    outside_mask_union_changed_pixels=0)
                row['passed']=row['modified_halo']['mean']<=a.max_mean and row['modified_halo']['p99']<=a.max_p99
                rows.append(row)
                for column,at in ((1,0),(2,header['frames']//2),(3,header['frames']-1)):
                    if frame_no==at:contact.paste(images[1],(column*w,index*h))
                if frame_no==header['frames']//2:contact.paste(images[2],(0,index*h))
        finally:
            for stream in streams:stream.close()
        if len(rows)!=header['frames'] or not all(r['passed'] for r in rows):raise ValueError('Focused caption decode regression: '+e['id'])
        for path,content in ((source,source_raw),(candidate,candidate_raw),(baseline,baseline_raw)):
            if sha(path.read_bytes())!=sha(content):raise ValueError('Movie changed during focused replay: '+str(path))
        report=dict(id=e['id'],source_sha256=sha(source_raw),baseline_sha256=sha(baseline_raw),output_sha256=sha(candidate_raw),
            role=a.role,region=region,protect=guards,measurement=a.measurement,
            new_halo_pixels=int(halo.sum()) if a.measurement=='new-erase-halo' else 0,
            measured_pixels=int(halo.sum()),mask=proof,frames=rows,passed=True)
        (out/(e['id']+'.json')).write_bytes(encoded(report));all_rows.append(report)
        print('PASS',e['id'],'frames',len(rows),'halo_max_mean',round(max(r['modified_halo']['mean'] for r in rows),4),flush=True)
    contact.save(out/'baseline-mid__modified-first-mid-last.png')
    summary=dict(passed=True,movies=len(all_rows),frames=sum(len(r['frames']) for r in all_rows),
        protected_preencode_changed_pixels=0,outside_mask_union_changed_pixels=0,
        max_halo_mean=max(f['modified_halo']['mean'] for r in all_rows for f in r['frames']),
        max_halo_p99=max(f['modified_halo']['p99'] for r in all_rows for f in r['frames']),
        baseline_failing_frames=sum(f['baseline_halo']['mean']>a.max_mean or f['baseline_halo']['p99']>a.max_p99 for r in all_rows for f in r['frames']),
        limits=dict(mean=a.max_mean,p99=a.max_p99),game_rendering_verified=False)
    (out/'summary.json').write_bytes(encoded(summary));print(json.dumps(summary))
    return 0


if __name__=='__main__':raise SystemExit(main())
