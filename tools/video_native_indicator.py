"""Source-screen dematting with explicit opaque-core artwork, not background blur.

High-confidence background pixels are inverted independently in each video frame.
An explicitly supplied RGBA repair covers ill-conditioned or inconsistent pixels.
Temporal light changes, not texture, are sampled from nearby native pixels.
"""
from __future__ import annotations
import hashlib
import math
import numpy as np
from PIL import Image
from .video_screen_underlay import inverse_screen,nearest_known_indices,harmonic_lighting,rectangular_lighting


class NativeIndicator:
    def __init__(self,rect,mask,matte,anchor,patch,layers,frame_count,minimum_transmittance=.12,invalid_mask=None,
                 temporal_lighting='nearest-known-v1',lighting_weight=None):
        x,y,w,h=rect
        if (len(rect)!=4 or any(type(v)is not int for v in rect) or min(x,y)<0 or min(w,h)<1
                or mask.shape!=(h,w) or mask.dtype!=np.bool_ or matte.shape!=(h,w,3)
                or anchor.shape!=(h,w,3) or anchor.dtype!=np.uint8
                or patch.mode!='RGBA' or patch.size!=(w,h)
                or type(frame_count)is not int or not 3<=frame_count<=600 or len(layers)!=3):
            raise ValueError('native indicator geometry/type/frame contract')
        self.rect=tuple(rect);self.mask=mask.copy();self.matte=matte.copy()
        if temporal_lighting not in ('nearest-known-v1','harmonic-feathered-v1'):
            raise ValueError('unsupported temporal lighting method')
        self.temporal_lighting=temporal_lighting
        self.lighting_weight=lighting_weight
        if temporal_lighting=='harmonic-feathered-v1':
            if (not isinstance(lighting_weight,np.ndarray) or lighting_weight.shape!=mask.shape
                    or lighting_weight.dtype!=np.uint8 or not np.all(lighting_weight[mask]==255)):
                raise ValueError('feathered lighting must fully cover old caption support')
            self.lighting_weight=lighting_weight.copy()
            self.mask|=lighting_weight>0
        elif lighting_weight is not None:
            raise ValueError('lighting feather requires its explicit method')
        self.threshold=minimum_transmittance;self.frames=frame_count
        baseline=inverse_screen(anchor,self.matte,minimum_transmittance=minimum_transmittance)
        self.unknown=baseline['unknown'];self.anchor=baseline['clean_rgb'].astype(np.float32)
        if invalid_mask is not None:
            if invalid_mask.dtype!=np.bool_ or invalid_mask.shape!=mask.shape:
                raise ValueError('native validity mask geometry/type mismatch')
            self.unknown|=invalid_mask&mask
        rgba=np.asarray(patch)
        if not np.array_equal(rgba[:,:,3],self.unknown.astype(np.uint8)*255):
            raise ValueError('core repair must cover exactly the non-invertible pixels')
        if np.any(rgba[:,:,:3][~self.unknown]):raise ValueError('core repair has undeclared RGB outside opaque support')
        if np.any(self.unknown&~mask):raise ValueError('opaque core outside explicit caption support')
        self.patch=rgba[:,:,:3].astype(np.float32)
        self.clean_anchor=self.anchor.copy()
        self.clean_anchor[self.unknown]=self.patch[self.unknown]
        if temporal_lighting=='harmonic-feathered-v1' and self.unknown.any():
            # A sparse authored donor has no trustworthy exterior. Extend its
            # edge only to measure the colour discrepancy against the known
            # native perimeter, then harmonically propagate that correction.
            # The donor's texture gradients stay; no scene pixels are averaged.
            py,px=nearest_known_indices(~self.unknown,max_radius=128)
            extended=self.patch[py,px]
            correction=harmonic_lighting(self.anchor-extended,self.unknown,limit=128)
            matched=np.rint(self.patch+correction).clip(0,255)
            self.clean_anchor[self.unknown]=matched[self.unknown]
        self.nearest=nearest_known_indices(self.unknown)
        self.layers=tuple(layers)
        if any(im.mode!='RGBA' or im.size!=(w,h) for im in self.layers):
            raise ValueError('indicator lettering must stay in its bounded canvas')

    def __iter__(self):
        # Inspection helpers may enumerate support; they must not use an old
        # interpolation implementation to replay this restoration.
        return iter((self.rect,self.mask))

    def _lighting_adjustment(self,result):
        # Copy only lighting change; generated texture never spreads to known pixels.
        delta=result.astype(np.float32)-self.anchor
        if self.temporal_lighting=='harmonic-feathered-v1':
            # Estimate a continuous LIGHT CHANGE from outside the entire old
            # caption support. Never copy lightning from nearest-donor Voronoi
            # cells, and never blur the character/cloth artwork in self.patch.
            adjustment=rectangular_lighting(delta,limit=48)
        else:
            yy,xx=self.nearest
            adjustment=np.clip(delta[yy,xx],-48,48)
        return adjustment

    def lighting_adjustment(self,crop):
        """Expose the actual field used by clean(), for all-frame seam audits."""
        return self._lighting_adjustment(inverse_screen(crop,self.matte,
            minimum_transmittance=self.threshold)['clean_rgb'])

    def clean(self,crop):
        result=inverse_screen(crop,self.matte,minimum_transmittance=self.threshold)['clean_rgb']
        adjustment=self._lighting_adjustment(result)
        if self.temporal_lighting=='harmonic-feathered-v1':
            weight=self.lighting_weight[:,:,None].astype(np.float64)/255
            result=np.rint((self.clean_anchor+adjustment)*weight+result*(1-weight)).clip(0,255).astype(np.uint8)
        else:
            result[self.unknown]=np.rint(self.patch+adjustment).clip(0,255).astype(np.uint8)[self.unknown]
        result[~self.mask]=crop[~self.mask]
        return result

    def apply(self,frame,index):
        if type(index)is not int or not 0<=index<self.frames:raise ValueError('indicator frame index outside loop')
        x,y,w,h=self.rect;box=(x,y,x+w,y+h)
        crop=np.asarray(frame.convert('RGB').crop(box));clean=self.clean(crop)
        dots=min(2,index*3//self.frames)
        layer=self.layers[dots].copy()
        alpha=np.asarray(layer.getchannel('A'),dtype=np.float32)
        # Continuous cyclic pulse; the native spinner/lightning remain untouched.
        gain=.96+.04*math.cos(2*math.pi*index/self.frames)
        layer.putalpha(Image.fromarray(np.rint(alpha*gain).astype(np.uint8)))
        rendered=Image.alpha_composite(Image.fromarray(clean).convert('RGBA'),layer).convert('RGB')
        output=frame.copy();output.paste(rendered,(x,y))
        return output

    def proof(self):
        return dict(method='native-screen-matte-with-explicit-opaque-core-v1',
            support_pixels=int(self.mask.sum()),reconstructed_glyph_pixels=int(self.unknown.sum()),
            known_pixels_spatially_filtered=0,minimum_transmittance=self.threshold,
            temporal_lighting=self.temporal_lighting,
            matte_sha256=hashlib.sha256(self.matte.tobytes()).hexdigest(),
            core_rgb_sha256=hashlib.sha256(self.patch.astype(np.uint8).tobytes()).hexdigest(),
            animation_frames=self.frames,dot_states=3,minimum_background_haze_may_be_removed=True,
            hidden_pixels_are_reconstructed=True,original_background_recovery_claimed=False)
