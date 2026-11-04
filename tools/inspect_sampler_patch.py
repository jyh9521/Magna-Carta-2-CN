"""Read-only, hash-locked sampler argument inspection, not a GPU/game emulator.

The plan's independently reviewed context windows bind the caller, consumer and
lookup table. This reports the argument and enum, not observed rendering.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import struct

try:
    from .runtime_patch import apply_image,digest
except ImportError:
    from runtime_patch import apply_image,digest


def inspect(image,plan):
    if digest(image)==plan['image_sha256']:
        original=image
    else:
        # Reject unrelated changes, not just a different instruction at the site.
        original=apply_image(image,plan,reverse=True)
    modified=apply_image(original,plan)
    if image not in (original,modified):raise ValueError('unknown sampler image')
    p=plan['sampler_probe'];base=plan['image_base']
    def word(address):
        if type(address) is not int or address%4 or not 0<=address-base<=len(image)-4:
            raise ValueError('sampler word outside image')
        return struct.unpack_from('>I',image,address-base)[0]
    argument=word(p['argument_address'])
    if argument>>16!=0x38a0:raise ValueError('expected li r5,argument')
    argument&=0xffff
    # This narrow profile only covers the two reviewed values, not arbitrary AF.
    if argument not in (4,16):raise ValueError('unreviewed sampler argument')
    compare=word(p['loop_compare_address'])
    if compare!=0x2f040010:raise ValueError('expected sixteen-sampler comparison')
    count=p['table_entries']
    if type(count) is not int or count!=17:raise ValueError('expected reviewed 17-entry table')
    table=[word(p['table_address']+i*4) for i in range(count)]
    if table[4]!=3 or table[16]!=5:raise ValueError('sampler enum mapping changed')
    # Mask is PPC MB=4..ME=6 (LSB bits 25..27), Xenos fetch dword 3.
    mask=0x0e000000;enum=table[argument]
    cases=0
    for flags in (0,0x400,0x800,0xc00):
        for old in (0,0xffffffff,0xa5a5a5a5,0x12345678):
            for sampler in range(16):
                new=(old&~mask)|(enum<<25) if flags&0xc00 else old
                if (new&~mask)!=(old&~mask):raise ValueError('unrelated fetch bits changed')
                if flags&0xc00 and (new&mask)>>25!=enum:raise ValueError('sampler field mismatch')
                cases+=1
    return dict(argument=argument,aniso_enum=enum,max_ratio=f'{argument}x',
                samplers=16,model_cases=cases,static_only=True,game_started=False)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('image',type=Path);p.add_argument('--plan',required=True,type=Path)
    a=p.parse_args(argv)
    try:
        print(json.dumps(inspect(a.image.read_bytes(),json.loads(a.plan.read_bytes())),sort_keys=True))
        return 0
    except (OSError,ValueError,KeyError,TypeError,struct.error) as e:
        print('ERROR: '+str(e));return 2


if __name__=='__main__':raise SystemExit(main())
