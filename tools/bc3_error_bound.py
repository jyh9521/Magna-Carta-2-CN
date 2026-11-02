"""Opt-in minimax RGB refinement for mixed lettering/art BC3 blocks."""
import struct

from .ue3_textures import decode_dxt5


def refine(rgba, encoded, limit):
    """Keep alpha fixed; refine only blocks exceeding the stated colour budget."""
    pixels = [tuple(rgba[i:i+4]) for i in range(0,64,4)]
    decoded = decode_dxt5(encoded,4,4)
    alphas = list(decoded[3::4])
    error = max(abs(p[c]*p[3]-decoded[i*4+c]*alphas[i])
                for i,p in enumerate(pixels) for c in range(3))
    if error <= limit*255:
        return encoded

    def unpack(q):
        r,g,b=q>>11,(q>>5)&63,q&31
        return r*8+r//4,g*4+g//16,b*8+b//4

    def evaluate(c0,c1):
        c0,c1=max(c0,c1),min(c0,c1)
        a,b=unpack(c0),unpack(c1)
        palette=[a,b,tuple((2*x+y)//3 for x,y in zip(a,b)),tuple((x+2*y)//3 for x,y in zip(a,b))]
        errors=[[[abs(p[k]*p[3]-q[k]*alpha) for k in range(3)] for q in palette]
                for p,alpha in zip(pixels,alphas,strict=True)]
        indices=[min(range(4),key=lambda j:(max(row[j]),sum(d*d for d in row[j]))) for row in errors]
        score=(max(max(row[j])for row,j in zip(errors,indices,strict=True)),
               sum(d*d for row,j in zip(errors,indices,strict=True)for d in row[j]))
        return score,c0,c1,indices

    best=evaluate(*struct.unpack('<HH',encoded[8:12]))
    colours={((p[0]*31+127)//255<<11)|((p[1]*63+127)//255<<5)|((p[2]*31+127)//255)
             for p in pixels if p[3]}
    colours.update(best[1:3])
    for a in sorted(colours):
        for b in sorted(colours):
            candidate=evaluate(a,b)
            if candidate[0]<best[0]:best=candidate
    for _ in range(8):
        previous=best
        for endpoint in (1,2):
            q=best[endpoint];values=[q>>11,(q>>5)&63,q&31]
            for k,bound in enumerate((31,63,31)):
                for step in (-1,1):
                    v=list(values);v[k]+=step
                    if not 0<=v[k]<=bound:continue
                    cs=list(best[1:3]);cs[endpoint-1]=(v[0]<<11)|(v[1]<<5)|v[2]
                    candidate=evaluate(*cs)
                    if candidate[0]<best[0]:best=candidate
        if best==previous:break
    return encoded[:8]+struct.pack('<HHI',best[1],best[2],sum(j<<(2*i)for i,j in enumerate(best[3])))
