"""Fuse a reconstructed clean plate only inside audited old-lettering support.

The clean plate is not an original-art recovery and never replaces a portrait.
Dirichlet color correction reconciles its texture to exact unmasked source
neighbors; all unowned source bytes remain unchanged before BC encoding.
"""


def reconcile_rgba(source, plate, width, height, mask, iterations=1000,
                   alpha_mode='preserve-source'):
    import numpy as np
    if (type(width) is not int or type(height) is not int
            or not 1 <= width <= 2048 or not 1 <= height <= 2048
            or not isinstance(source,bytes) or not isinstance(plate,bytes)
            or len(source)!=width*height*4 or len(plate)!=len(source)
            or not isinstance(mask,bytes) or len(mask)!=width*height
            or set(mask)-{0,255} or not any(mask) or all(mask)
            or type(iterations) is not int or not 0<=iterations<=2048
            or alpha_mode not in ('preserve-source','guided-source-envelope-v1','interpolate-source-alpha-v1')):
        raise ValueError('bounded source/plate RGBA and sparse binary mask required')
    original=np.frombuffer(source,dtype=np.uint8).reshape(height,width,4)
    guide=np.frombuffer(plate,dtype=np.uint8).reshape(height,width,4).astype(np.float64)
    selected=np.frombuffer(mask,dtype=np.uint8).reshape(height,width)>0
    s=original.astype(np.float64)

    def harmonic(values,inside=0):
        correction=values.copy();correction[selected]=inside
        for _ in range(iterations):
            padded=np.pad(correction,((1,1),(1,1),(0,0)),mode='edge')
            average=(padded[:-2,1:-1]+padded[2:,1:-1]
                     +padded[1:-1,:-2]+padded[1:-1,2:])/4
            correction[selected]=average[selected]
        return correction

    # A generated plate may carry white RGB behind zero/near-zero alpha. Its
    # straight RGB is not visible artwork and must not be exposed by a later
    # reconstruction of the original native fade/alpha field.
    source_premultiplied=s[:,:,:3]*s[:,:,3:]/255
    guide_premultiplied=guide[:,:,:3]*guide[:,:,3:]/255
    correction=harmonic(source_premultiplied-guide_premultiplied)
    result=s.copy();premultiplied=guide_premultiplied+correction
    if alpha_mode=='guided-source-envelope-v1':
        # Outside-mask native alpha supplies the original fade envelope. The
        # text-free guide supplies only silhouette support where old letters
        # themselves made native alpha nonzero outside the character.
        ratio=np.divide(s[:,:,3:],guide[:,:,3:],
                        out=np.ones_like(s[:,:,3:]),where=guide[:,:,3:]>16)
        ratio=np.clip(ratio,0,4)
        envelope=harmonic(ratio,inside=1)
        result[selected,3]=(guide[:,:,3:]*envelope)[selected,0]
    elif alpha_mode=='interpolate-source-alpha-v1':
        result[selected,3]=harmonic(s[:,:,3:])[selected,0]
    alpha=result[:,:,3:]
    reconstructed=np.divide(premultiplied*255,alpha,
                             out=np.zeros_like(premultiplied),where=alpha>0)
    result[selected,:3]=reconstructed[selected]
    result=np.rint(result).clip(0,255).astype(np.uint8)
    result[~selected]=original[~selected]
    if (not np.array_equal(result[~selected],original[~selected])
            or (alpha_mode=='preserve-source'
                and not np.array_equal(result[:,:,3],original[:,:,3]))):
        raise ValueError('unowned source pixels or preserved alpha changed')
    return result.tobytes()
