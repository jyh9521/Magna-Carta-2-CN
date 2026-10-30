"""Replay every native loading frame and measure temporal-light donor seams.

Measures the real pre-clipping lighting field used by the restoration, not
background texture edges or the Chinese lettering. Optional encoded-video checks
compare the actual published Bink ROI to the independently rendered recipe.
"""
import argparse
import copy
import json
from pathlib import Path
import numpy as np
from PIL import Image

from .build_video_captions import load_plan, locked_file, prepare_layers, composite
from .video_caption import decoded_frames, bink_header


def neighbor_jump(field,mask):
    if field.shape[:2]!=mask.shape or field.ndim!=3 or mask.dtype!=np.bool_:
        raise ValueError('lighting measurement geometry/type mismatch')
    samples=[]
    for axis in (0,1):
        if axis==0:selected=mask[1:]&mask[:-1]
        else:selected=mask[:,1:]&mask[:,:-1]
        samples.append(np.abs(np.diff(field,axis=axis))[selected].ravel())
    values=np.concatenate(samples)
    if not values.size:raise ValueError('empty measured lighting support')
    return float(values.max())


def lighting_curvature(field,mask):
    """A steep legitimate light gradient is not a seam; donor facets are.

    Measure the discrete harmonic residual only where all five samples belong
    to the reconstructed, uncovered old-glyph core. This excludes native art
    texture, clipping, new lettering and Dirichlet boundary samples.
    """
    if field.shape[:2]!=mask.shape or field.ndim!=3 or mask.dtype!=np.bool_:
        raise ValueError('lighting curvature geometry/type mismatch')
    selected=mask[1:-1,1:-1]&mask[:-2,1:-1]&mask[2:,1:-1]&mask[1:-1,:-2]&mask[1:-1,2:]
    if not selected.any():raise ValueError('empty lighting curvature support')
    residual=(field[:-2,1:-1]+field[2:,1:-1]+field[1:-1,:-2]+field[1:-1,2:]
              -4*field[1:-1,1:-1])
    return float(np.abs(residual[selected]).max())


def run(args):
    plan,_=load_plan(args.plan,args.plan_sha256);prior,_=load_plan(args.prior_plan,args.prior_plan_sha256)
    locked_file(args.ffmpeg,args.ffmpeg_sha256,256*1024*1024)
    old={e['id']:e for e in prior['entries']};out=args.output_dir
    if out.exists():raise ValueError('new lighting audit directory required')
    out.mkdir(parents=True);reports=[]
    for entry in plan['entries']:
        operations=[]
        for p,e in ((prior,old[entry['id']]),(plan,entry)):
            chosen=copy.deepcopy(e);chosen['captions']=[c for c in e['captions'] if c['role']=='indicator']
            result=prepare_layers(p,chosen,args.project_root,args.source_root,args.ffmpeg)
            if len(result[3])!=1:raise ValueError('one native indicator operation required')
            operations.append((result[3][0],result))
        before,after=[r[0] for r in operations];source,_,header=operations[1][1][:3]
        ox,oy,w,h=before.rect;nx,ny,nw,nh=after.rect
        offset_x,offset_y=ox-nx,oy-ny
        if min(offset_x,offset_y)<0 or offset_x+w>nw or offset_y+h>nh:
            raise ValueError('new indicator does not contain old support')
        letters=np.zeros((nh,nw),bool)
        for layer in after.layers:letters|=np.asarray(layer.getchannel('A'))>0
        measured=before.unknown&~letters[offset_y:offset_y+h,offset_x:offset_x+w]
        rows=[];old_zero=new_zero=None;encoded=None
        if args.candidate_root:
            video=args.candidate_root/(entry['id']+'.bik')
            if bink_header(video.read_bytes())!=header:raise ValueError('encoded loop timing changed')
            encoded=decoded_frames(args.ffmpeg,video,header)
        try:
            for i,raw in enumerate(decoded_frames(args.ffmpeg,source,header)):
                frame=Image.frombytes('RGB',(header['width'],header['height']),raw)
                a=before.lighting_adjustment(np.asarray(frame.crop((ox,oy,ox+w,oy+h))))
                b=after.lighting_adjustment(np.asarray(frame.crop((nx,ny,nx+nw,ny+nh))))
                b=b[offset_y:offset_y+h,offset_x:offset_x+w]
                if i==0:old_zero=a.copy();new_zero=b.copy()
                old_jump=neighbor_jump(a-old_zero,measured);new_jump=neighbor_jump(b-new_zero,measured)
                old_curve=lighting_curvature(a-old_zero,measured)
                new_curve=lighting_curvature(b-new_zero,measured)
                row=dict(frame=i,baseline_step=old_jump,modified_step=new_jump,
                         baseline_curvature=old_curve,modified_curvature=new_curve,
                         passed=new_curve<=args.max_curvature)
                if encoded:
                    actual=Image.frombytes('RGB',(header['width'],header['height']),next(encoded))
                    expected=after.apply(frame,i)
                    box=(nx,ny,nx+nw,ny+nh)
                    error=np.abs(np.asarray(actual.crop(box)).astype(int)-np.asarray(expected.crop(box)).astype(int))
                    support=after.mask.copy()
                    for layer in after.layers:support|=np.asarray(layer.getchannel('A'))>0
                    values=error[support].mean(1)
                    row.update(decode_mean=float(values.mean()),decode_p99=float(np.quantile(values,.99)))
                    row['passed'] &= row['decode_mean']<=5 and row['decode_p99']<=24
                    # The native spinner is left of the operation; artwork
                    # outside its exact support stays identical before encoding.
                    changed=np.any(np.asarray(expected)!=np.asarray(frame),axis=2)
                    allowed=np.zeros(changed.shape,bool);allowed[ny:ny+nh,nx:nx+nw]=support
                    if np.any(changed&~allowed):raise ValueError('indicator changed protected source pixels')
                rows.append(row)
        finally:
            if encoded:encoded.close()
        if len(rows)!=header['frames']:raise ValueError('all-frame lighting coverage differs')
        report=dict(id=entry['id'],frames=rows,measured_pixels=int(measured.sum()),
                    baseline_max_step=max(r['baseline_step'] for r in rows),
                    modified_max_step=max(r['modified_step'] for r in rows),
                    baseline_max_curvature=max(r['baseline_curvature'] for r in rows),
                    modified_max_curvature=max(r['modified_curvature'] for r in rows),
                    max_curvature=args.max_curvature,passed=all(r['passed'] for r in rows))
        (out/(entry['id']+'.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
        reports.append(report)
        print(entry['id'],'baseline_curvature',round(report['baseline_max_curvature'],6),
              'modified_curvature',round(report['modified_max_curvature'],6),'PASS' if report['passed'] else 'FAIL',flush=True)
    result=dict(movies=len(reports),frames=sum(len(r['frames']) for r in reports),
                baseline_failing_frames=sum(f['baseline_curvature']>args.max_curvature for r in reports for f in r['frames']),
                modified_failing_frames=sum(not f['passed'] for r in reports for f in r['frames']),
                baseline_max_step=max(r['baseline_max_step'] for r in reports),
                modified_max_step=max(r['modified_max_step'] for r in reports),
                baseline_max_curvature=max(r['baseline_max_curvature'] for r in reports),
                modified_max_curvature=max(r['modified_max_curvature'] for r in reports),
                encoded_checked=bool(args.candidate_root),game_started=False,game_rendering_verified=False)
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result));return int(result['modified_failing_frames']>0)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('plan','prior-plan','source-root','ffmpeg','output-dir'):
        p.add_argument('--'+name,type=Path,required=True)
    for name in ('plan-sha256','prior-plan-sha256','ffmpeg-sha256'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--project-root',type=Path,default=Path('.'))
    p.add_argument('--candidate-root',type=Path)
    p.add_argument('--max-curvature',type=float,default=.01)
    a=p.parse_args()
    if not 0<a.max_curvature<=1:raise ValueError('finite bounded lighting curvature limit required')
    return run(a)


if __name__=='__main__':raise SystemExit(main())
