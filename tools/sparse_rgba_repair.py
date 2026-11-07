"""Deterministic reconstruction confined to an explicit, audited RGBA ink mask.

This estimates pixels hidden by baked lettering. It does not recover the
original artwork. Unselected pixels remain exact before native BC encoding.
"""


def interpolate_rgba(pixels, width, height, mask, iterations=64):
    import numpy as np

    if (type(width) is not int or type(height) is not int
            or not 1 <= width <= 2048 or not 1 <= height <= 2048
            or not isinstance(pixels, bytes) or len(pixels) != width*height*4
            or not isinstance(mask, bytes) or len(mask) != width*height
            or set(mask)-{0, 255} or not any(mask) or all(mask)
            or type(iterations) is not int or not 0 <= iterations <= 256):
        raise ValueError('explicit bounded sparse RGBA mask required')
    original = np.frombuffer(pixels, dtype=np.uint8).reshape(height, width, 4)
    selected = np.frombuffer(mask, dtype=np.uint8).reshape(height, width) > 0
    # Premultiplication prevents hidden RGB in transparent pixels bleeding into
    # the reconstructed character contour. The unselected bytes are copied back.
    values = original.astype(np.float64)
    values[:, :, :3] *= values[:, :, 3:] / 255
    known = ~selected
    pending = selected.copy()
    for _ in range(width+height):
        if not pending.any():
            break
        total = np.zeros_like(values)
        count = np.zeros((height, width), dtype=np.float64)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            source = (slice(max(0, dy), min(height, height+dy)),
                      slice(max(0, dx), min(width, width+dx)))
            target = (slice(max(0, -dy), min(height, height-dy)),
                      slice(max(0, -dx), min(width, width-dx)))
            weight = known[source]
            count[target] += weight
            total[target] += values[source] * weight[:, :, None]
        ready = pending & (count > 0)
        if not ready.any():
            raise ValueError('sparse RGBA mask has no exterior samples')
        values[ready] = total[ready] / count[ready, None]
        known[ready] = True
        pending[ready] = False
    if pending.any():
        raise ValueError('sparse RGBA front did not converge')
    for _ in range(iterations):
        padded = np.pad(values, ((1, 1), (1, 1), (0, 0)), mode='edge')
        average = (padded[:-2, 1:-1] + padded[2:, 1:-1]
                   + padded[1:-1, :-2] + padded[1:-1, 2:]) / 4
        values[selected] = average[selected]
    alpha = values[:, :, 3:]
    values[:, :, :3] = np.divide(values[:, :, :3]*255, alpha,
                                 out=np.zeros_like(values[:, :, :3]), where=alpha > 0)
    result = np.rint(values).clip(0, 255).astype(np.uint8)
    result[~selected] = original[~selected]
    if not np.array_equal(result[~selected], original[~selected]):
        raise ValueError('unmasked RGBA artwork changed')
    return result.tobytes()


def exemplar_rgba(pixels, width, height, mask, patch_radius=3, search_radius=48):
    """Fill traced lettering from bounded nearby unmasked texture exemplars.

    Source patches are always wholly outside the original mask. Synthesized
    pixels help match continuation, but never become source exemplars. This
    avoids averaging a bright original glow into a uniform horizontal smear.
    """
    import numpy as np
    if (type(width) is not int or type(height) is not int
            or not 1 <= width <= 2048 or not 1 <= height <= 2048
            or not isinstance(pixels, bytes) or len(pixels) != width*height*4
            or not isinstance(mask, bytes) or len(mask) != width*height
            or set(mask)-{0, 255} or not any(mask) or all(mask)
            or type(patch_radius) is not int or not 1 <= patch_radius <= 5
            or type(search_radius) is not int or not 8 <= search_radius <= 96):
        raise ValueError('explicit bounded exemplar RGBA mask required')
    radius=patch_radius;size=radius*2+1
    original=np.frombuffer(pixels,dtype=np.uint8).reshape(height,width,4)
    holes=np.frombuffer(mask,dtype=np.uint8).reshape(height,width)>0
    padded=np.pad(original,((radius,radius),(radius,radius),(0,0)),mode='edge')
    source=padded.astype(np.float32)
    source[:,:,:3]*=source[:,:,3:]/255
    current=source.copy()
    unavailable=np.pad(holes,((radius,radius),(radius,radius)),constant_values=True)
    # A candidate never samples even one old lettering/glow pixel.
    valid=np.ones((height,width),dtype=bool)
    for dy in range(size):
        for dx in range(size):
            valid &= ~unavailable[dy:dy+height,dx:dx+width]
    candidates=np.argwhere(valid)
    if not len(candidates):
        raise ValueError('exemplar repair has no unmasked source patch')
    pending=holes.copy()
    known=~unavailable
    while pending.any():
        # Choose a boundary with the most known context. Stable row-major ties
        # make the selection reproducible and favour narrow holes/corners.
        confidence=np.zeros((height,width),dtype=np.uint16)
        for dy in range(size):
            for dx in range(size):
                confidence += known[dy:dy+height,dx:dx+width]
        confidence[~pending]=0
        if not confidence.max():
            raise ValueError('exemplar repair has no known boundary')
        yy,xx=np.unravel_index(confidence.argmax(),confidence.shape)
        target=current[yy:yy+size,xx:xx+size]
        weights=known[yy:yy+size,xx:xx+size]
        local=candidates[(np.abs(candidates[:,0]-yy)<=search_radius)
                         &(np.abs(candidates[:,1]-xx)<=search_radius)]
        if not len(local):
            local=candidates
        # Gather one bounded neighborhood at a time rather than materializing
        # every image patch. At radius<=96 this remains finite and small.
        sampled=np.stack([source[y:y+size,x:x+size] for y,x in local])
        delta=sampled[:,weights,:]-target[weights,:]
        score=np.mean(delta*delta,axis=(1,2))
        score+=np.sum((local-np.array([yy,xx]))**2,axis=1)*0.015
        by,bx=local[score.argmin()]
        donor=source[by:by+size,bx:bx+size]
        target_holes=~weights
        # Only the original selected mask is mutable, including when a target
        # patch reaches the context border or another synthesized patch.
        target_selected=np.pad(pending,((radius,radius),(radius,radius)),constant_values=False)[yy:yy+size,xx:xx+size]
        target[target_selected]=donor[target_selected]
        known[yy:yy+size,xx:xx+size][target_selected]=True
        pending=~known[radius:radius+height,radius:radius+width]&holes
    result=current[radius:radius+height,radius:radius+width].copy()
    alpha=result[:,:,3:]
    result[:,:,:3]=np.divide(result[:,:,:3]*255,alpha,
                             out=np.zeros_like(result[:,:,:3]),where=alpha>0)
    result=np.rint(result).clip(0,255).astype(np.uint8)
    result[~holes]=original[~holes]
    return result.tobytes()
