"""Opt-in deterministic RGB565 cluster fit for small BC3 lettering regions.

The legacy farthest-pair encoder remains the initial candidate and default.
Minimize alpha-squared weighted RGB error, keeping the alpha block untouched.
This is lossy encoding, not a change to the font mask or the source palette.
"""
import struct


def encode_fitted_rgba_block(rgba):
    from .texture_overlay import encode_rgba_block
    original=encode_rgba_block(rgba)  # also validates the bounded input
    pixels=[tuple(rgba[i:i+4]) for i in range(0,64,4)]
    weights=[p[3]**2 for p in pixels]
    if not any(weights):return original

    def unpack(q):
        r,g,b=q>>11,(q>>5)&63,q&31
        return r*8+r//4,g*4+g//16,b*8+b//4

    def pack(rgb):
        v=[max(0,min(255,round(c))) for c in rgb]
        return ((v[0]*31+127)//255<<11)|((v[1]*63+127)//255<<5)|((v[2]*31+127)//255)

    def evaluate(c0,c1):
        c0,c1=max(c0,c1),min(c0,c1)
        a,b=unpack(c0),unpack(c1)
        palette=[a,b,tuple((2*x+y)//3 for x,y in zip(a,b)),
                 tuple((x+2*y)//3 for x,y in zip(a,b))]
        distances=[[sum((p[k]-q[k])**2 for k in range(3)) for q in palette] for p in pixels]
        indices=[min(range(4),key=row.__getitem__) for row in distances]
        error=sum(w*row[j] for w,row,j in zip(weights,distances,indices))
        return error,c0,c1,indices

    best=evaluate(*struct.unpack('<HH',original[8:12])); current=best
    factors=[(1,0),(0,1),(2/3,1/3),(1/3,2/3)]
    for _ in range(8):
        aa=ab=bb=0; av=[0.]*3; bv=[0.]*3
        for pixel,weight,index in zip(pixels,weights,current[3]):
            a,b=factors[index]; aa+=weight*a*a; ab+=weight*a*b; bb+=weight*b*b
            for k in range(3):
                av[k]+=weight*a*pixel[k]; bv[k]+=weight*b*pixel[k]
        determinant=aa*bb-ab*ab
        if determinant<1e-8:break
        current=evaluate(pack([(av[k]*bb-bv[k]*ab)/determinant for k in range(3)]),
                         pack([(bv[k]*aa-av[k]*ab)/determinant for k in range(3)]))
        if current[0]<best[0]:best=current
    # Bounded, deterministic local search around quantized endpoints. Strict
    # improvements only: ties retain the earlier result across platforms.
    for _ in range(4):
        previous=best
        for endpoint in (1,2):
            q=best[endpoint]; values=[q>>11,(q>>5)&63,q&31]
            for k,limit in enumerate((31,63,31)):
                for step in (-1,1):
                    v=list(values); v[k]+=step
                    if not 0<=v[k]<=limit:continue
                    cs=[best[1],best[2]]; cs[endpoint-1]=(v[0]<<11)|(v[1]<<5)|v[2]
                    candidate=evaluate(*cs)
                    if candidate[0]<best[0]:best=candidate
        if best==previous:break
    return original[:8]+struct.pack('<HHI',best[1],best[2],
                                    sum(j<<(2*i) for i,j in enumerate(best[3])))
