"""Hash-locked, bounded PPC graphics-fragment replay, not game/GPU execution."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import struct

try:
    from .runtime_patch import apply_image,digest,patch_toml
    from .ppc_fragment import MemorySegment,run_fragment
except ImportError:
    from runtime_patch import apply_image,digest,patch_toml
    from ppc_fragment import MemorySegment,run_fragment


def recover_original(image,plan):
    """Accept only complete, independently toggled sections of this exact image."""
    patch_toml(plan)  # Validate the complete, non-overlapping section partition.
    out=bytearray(image);states={}
    for w in plan['writes']:
        at=w['address']-plan['image_base'];old=bytes.fromhex(w['expected']);new=bytes.fromhex(w['replacement'])
        if not 0<=at<=len(image)-len(old):raise ValueError('graphics write outside image')
        value=image[at:at+len(old)]
        if value not in (old,new):raise ValueError('unknown graphics instruction/data')
        states[w['address']]=value==new
        out[at:at+len(old)]=old
    original=bytes(out)
    if digest(original)!=plan['image_sha256']:raise ValueError('graphics image SHA256 mismatch')
    apply_image(original,plan)  # Verify all source windows and expected bytes.
    for s in plan['patch_sections']:
        if len({states[a] for a in s['write_addresses']})!=1:
            raise ValueError('partial graphics patch section')
    return original


def check(image,plan):
    original=recover_original(image,plan);base=plan['image_base'];p=plan['graphics_probe'];cases=[]
    def word(a):
        if type(a) is not int or a%4 or not 0<=a-base<=len(image)-4:raise ValueError('graphics word outside image')
        return struct.unpack_from('>I',image,a-base)[0]
    def replay(label,spec,registers,memory=()):
        r=run_fragment(image,base,(spec['entry'],spec['end']),spec['entry'],set(spec['stops']),registers,memory)
        inputs=[]
        for s in memory:
            fill=Counter(s.data).most_common(1)[0][0]
            inputs.append(dict(start=f'0x{s.start:08X}',size=len(s.data),fill=fill,writable=s.writable,
                               bytes={str(i):v for i,v in enumerate(s.data) if v!=fill},sha256=digest(s.data)))
        cases.append(dict(label=label,stop=f'0x{r.stop_pc:08X}',steps=r.steps,
                          fetch_window=dict(start=spec['entry'],end=spec['end'],stops=spec['stops']),
                          initial_registers={str(k):v for k,v in registers.items()},synthetic_memory=inputs,
                          trace=[f'0x{a:08X}' for a in r.trace]))
        return r
    def segment_word(r,address):
        for s in r.segments:
            if s.start<=address<=s.start+len(s.data)-4:
                return struct.unpack_from('>I',s.data,address-s.start)[0]
        raise ValueError('missing synthetic result word')
    def device(**fields):
        data=bytearray(0x6000)
        for k,v in fields.items():struct.pack_into('>I',data,int(k[1:],16),v)
        return MemorySegment(0x100000,bytes(data),True)
    def require(condition,message):
        if not condition:raise ValueError(message)

    fps=p['frame'];value=word(fps['write_address'])
    require(value>>16==0x3960 and value&0xffff in (1,2),'unexpected interval instruction')
    two_interval=value&0xffff
    nominal_flags=None
    for request in (0,1,2,3,4,8,0x80000000,0xffffffff):
        interval=1 if request in (0,1) else two_interval if request==2 else 3 if request==4 else 0
        for other in (0,1,0x80000000,0x12345678):
            for flags in (0,1,0x40,0x10000):
                d=device(f351c=request,f2e54=other,f0030=0x300000,f0038=0x300100)
                r=replay('interval-encoding',fps['encode'],{31:0x100000,29:flags},[d])
                rotated=((other<<9)|(other>>23))&0xffffffff
                require(r.registers[30]==((interval<<8)|(rotated&0x7f)|flags),'interval encoding mismatch')
                if (request,other,flags)==(2,0,0):nominal_flags=r.registers[30]

    # Real guest instructions advance and schedule against the vblank counter.
    for tick in (0,1,100,0xffffffff):
        r=replay('vblank-increment',fps['increment'],{31:0x100000,3:0},[device(f40a4=tick)])
        require(segment_word(r,0x1040a4)==(tick+1)&0xffffffff,'vblank counter mismatch')
    for previous in (0,10,100):
        for current in (0,10,100,1000):
            for fraction in (0,50):
                for threshold in (0,100):
                    r=replay('vblank-target',fps['target'],
                             {31:0x100000,29:two_interval,7:fraction,27:threshold},
                             [device(f40ac=previous,f40a4=current)])
                    wanted=previous+two_interval
                    if wanted<=current:wanted=current+int(fraction>threshold)
                    require(r.registers[11]==wanted,'vblank target mismatch')

    # The setup fragment actually emits SCRATCH_ADDR and UMSK (bits 4/5).
    ring=MemorySegment(0x300000,bytes(256),True)
    r=replay('scratch-initialization',fps['scratch_init'],{3:0x300000,31:0x100000},
             [device(f2a94=0x200000),ring])
    require(segment_word(r,0x300020)==0x1dd and segment_word(r,0x300024)==0x200000,
            'scratch address binding mismatch')
    require(segment_word(r,0x300028)==0x1dc and segment_word(r,0x30002c)&0x30==0x30,
            'scratch callback mask mismatch')
    r=replay('scratch-callback-packet',fps['packet'],
             {28:fps['callback'],27:nominal_flags,29:0x300000,31:0},[ring])
    require([segment_word(r,0x300000+i) for i in (4,8,12)]==[0x1057c,fps['callback'],nominal_flags],
            'scratch packet payload mismatch')
    # Source-pinned Xenia maps scratch4/5 into +0x10/+0x14. This explicit
    # synthetic bridge models that contract; it is not a running GPU/interrupt.
    shared=bytearray(64);struct.pack_into('>II',shared,0x10,fps['callback'],nominal_flags)
    r=replay('source1-callback-arguments',fps['dispatch'],{3:1,4:0x100000},
             [device(f2a94=0x200000),MemorySegment(0x200000,bytes(shared))])
    require(r.stop_pc==fps['dispatch']['callback_stop'] and r.registers[10]==fps['callback']
            and r.registers[3]==nominal_flags,'source1 callback argument mismatch')
    r=replay('callback-interval-decoding',fps['decode'],{30:nominal_flags})
    require(r.registers[29]==two_interval,'callback interval decoding mismatch')
    for mmio in (0,1):
        r=replay('source0-vblank-gate',fps['dispatch'],{3:0,4:0x100000},
                 [device(),MemorySegment(0x7fc86544,struct.pack('>I',mmio))])
        wanted=fps['dispatch']['vblank_stop'] if mmio else fps['dispatch']['return_stop']
        require(r.stop_pc==wanted,'source0 vblank gate mismatch')

    tiling=p['tiling'];enabled=word(tiling['flag_address']);mode=word(tiling['mode_address'])
    require(enabled in (0,1) and mode in (0,1),'unreviewed tiling values')
    for render_pass in (0,1,3):
        r=replay('scene-tiling-gate',tiling['scene'],{15:render_pass})
        wanted=tiling['scene']['body'] if enabled and render_pass else tiling['scene']['skip']
        require(r.stop_pc==wanted,'scene tiling gate mismatch')
    for view in (0,1):
        for active in (0,1,2):
            r=replay('view-offset-gate',tiling['view'],{29:view,28:active})
            wanted=tiling['view']['body'] if enabled and view and active else tiling['view']['skip']
            require(r.stop_pc==wanted,'view tiling gate mismatch')
    r=replay('tiling-surface-index',tiling['index'],{})
    require(r.registers[9]==mode*4,'tiling surface index mismatch')

    post=p['post'];bypassed=word(post['write_address'])!=struct.unpack_from('>I',original,post['write_address']-base)[0]
    for chain,count in ((0,0),(0,3),(0x200000,0),(0x200000,1),(0x200000,3),(0x200000,0xffffffff)):
        view=bytearray(b'\xcc'*0x700);struct.pack_into('>I',view,0x10,chain)
        r=replay('empty-proxy-array-initialization',post['initialize'],{30:0x100000,29:0},
                 [MemorySegment(0x100000,bytes(view),True)])
        require([segment_word(r,0x100000+i) for i in (0x6d4,0x6d8,0x6dc)]==[0,0,0],
                'proxy array not initialized empty')
        chain_data=bytearray(0x48);struct.pack_into('>I',chain_data,0x40,count)
        memory=[*r.segments,MemorySegment(0x200000,bytes(chain_data))]
        r=replay('post-process-chain-gate',post['gate'],{30:0x100000,29:0},memory)
        wanted=(post['gate']['returned'] if bypassed or not chain else
                post['gate']['empty'] if count==0 or count&0x80000000 else post['gate']['body'])
        require(r.stop_pc==wanted,'post-process branch mismatch')
        # We do not execute factories for the body path; all initialized empty
        # arrays are independently checked against the existing empty consumer.
        r=replay('empty-proxy-consumer',post['consumer'],{31:0x100000},memory)
        require(r.stop_pc==post['consumer']['empty'],'empty proxy consumer dereference')

    summary=dict(frame_interval=two_interval,nominal_fps_at_60hz=60//two_interval,
                 tiling_enabled=enabled,tiling_mode=mode,
                 postprocess_chain='bypassed' if bypassed else 'original',
                 replay_fragments=len(cases),static_only=True,game_started=False)
    return dict(summary=summary,cases=cases)


def summary_line(summary):
    s=summary
    return (f"interval={s['frame_interval']}; tiling={s['tiling_enabled']}/{s['tiling_mode']}; "
            f"post={s['postprocess_chain']}; fragments={s['replay_fragments']}; static_only=true")


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('image',type=Path);p.add_argument('--plan',required=True,type=Path)
    p.add_argument('--brief',action='store_true')
    a=p.parse_args(argv)
    try:
        result=check(a.image.read_bytes(),json.loads(a.plan.read_bytes()))
        print(summary_line(result['summary']) if a.brief else json.dumps(result['summary'],sort_keys=True));return 0
    except (OSError,ValueError,KeyError,TypeError,struct.error) as e:
        print('ERROR: '+str(e));return 2


if __name__=='__main__':raise SystemExit(main())
