"""Bounded replay of forced-wrap arithmetic/branch instructions, not a game run.

Recognizes only direct non-link branches, single fnmsubs and single fsubs.
Input registers are controlled finite metrics; this is not a general PPC VM,
FPSCR model, UI renderer, string tokenizer, or in-game layout acceptance.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import struct
try:
    from .runtime_patch import apply_image,digest
except ImportError:
    from runtime_patch import apply_image,digest


def single(v):return struct.unpack('>f',struct.pack('>f',v))[0]


def replay(image,base,entry,exit,cave,origin,accumulated,scale,last_advance):
    values=[origin,accumulated,scale,last_advance]
    if not all(math.isfinite(x) and abs(x)<1e7 for x in values):raise ValueError('replay metrics outside finite controlled range')
    f=[single(1000+i) for i in range(32)]
    f[0],f[25],f[29],f[30]=map(single,[scale,origin,last_advance,accumulated])
    pc=entry;trace=[]
    for _ in range(8):
        if pc==exit:return f[26],trace
        if pc not in {entry,cave,cave+4,cave+8} or not 0<=pc-base<=len(image)-4:raise ValueError('replay PC escaped selected window')
        w=int.from_bytes(image[pc-base:pc-base+4],'big');trace.append(pc)
        if w>>26==18 and w&3==0:
            displacement=w&0x3fffffc
            if displacement&0x2000000:displacement-=0x4000000
            pc+=displacement;continue
        op=w>>26;dst=(w>>21)&31;a=(w>>16)&31;b=(w>>11)&31;c=(w>>6)&31;xo=(w>>1)&31
        if op==59 and w&1==0 and xo==30:
            f[dst]=single(f[b]-f[a]*f[c])
        elif op==59 and w&1==0 and xo==20 and c==0:
            f[dst]=single(f[a]-f[b])
        else:raise ValueError('unsupported replay instruction')
        pc+=4
    raise ValueError('replay step limit exceeded')


def check(image,plan):
    p=plan['replay'];cases=0;failures=0;example=None
    # Every input uses exactly representable binary increments so this bounded
    # single-rounding arithmetic does not claim a general FMA implementation.
    for origin in (0,1,193,207,240,640):
        for scale in (.5,1,1.5,2):
            for advance in (8,16,24):
                for count in (1,7,17):
                    width=single(count*advance*scale);accumulated=single(origin+width+advance*scale)
                    got,trace=replay(image,plan['image_base'],p['entry'],p['exit'],p['cave'],origin,accumulated,scale,advance)
                    cases+=1
                    if got!=width:
                        failures+=1
                        if example is None:example=dict(origin=origin,expected_width=width,reported_width=got,center_shift=(width-got)/2)
    return dict(cases=cases,failures=failures,example=example,game_started=False)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('image',type=Path);p.add_argument('--plan',type=Path,required=True);a=p.parse_args(argv)
    try:
        image=a.image.read_bytes();plan_raw=a.plan.read_bytes();plan=json.loads(plan_raw)
        if digest(image)!=plan['image_sha256']:apply_image(image,plan,reverse=True)
        r=check(image,plan)
        if a.image.read_bytes()!=image or a.plan.read_bytes()!=plan_raw:raise ValueError('replay input changed')
        print(json.dumps(r,sort_keys=True));return int(r['failures']>0)
    except (OSError,ValueError,KeyError,TypeError) as e:print('ERROR: '+str(e));return 2


if __name__=='__main__':raise SystemExit(main())
