"""Independent negative-space, Latin-ink and native artifact audit.

The negative-space test uses only glyph coverage plus a fixed distance budget;
it never treats a generated shadow bitmap or original dark pixels as evidence.
"""
import argparse
import json
from pathlib import Path
from PIL import Image,ImageChops,ImageFilter
from .font_binding_plan import confined_path
from .patch_tagged_fields import digest
from .rebuild_texture_titles import load_inputs,compose_island
from .replace_texture_regions import selected
from .texture_layout import decode_texture
from .ue3_package import LzxDecoder


def negative_space(actual,background,inks,radius=3,split_supports=()):
    allowed=background.getchannel('A').point(lambda a:255 if a else 0)
    glyph=Image.new('L',actual.size)
    for ink in inks:glyph=ImageChops.lighter(glyph,ink.getchannel('A'))
    glyph=glyph.point(lambda a:255 if a else 0)
    allowed=ImageChops.lighter(allowed,glyph.filter(ImageFilter.MaxFilter(radius*2+1)))
    for support in split_supports:allowed=ImageChops.lighter(allowed,support)
    return sum(a>0 and not ok for a,ok in zip(actual.getchannel('A').get_flattened_data(),allowed.get_flattened_data(),strict=True))


def audit(plan,project,baseline,actual_root,reference,decoder):
    assets,inputs=load_inputs(plan,Path(project).resolve(),Path(baseline).resolve(),decoder)
    identities={(p['resource'],p['object'],i['id']):i['decoded_rgba_sha256'] for p in reference['proofs']for i in p['islands']}
    groups=[];failures=[]
    for r,base,textures in inputs:
        data=confined_path(Path(actual_root).resolve(),r['path']).read_bytes()
        for t,current,original in textures:
            tx=selected(data,t['object'],None)[3];size=tx['width'],tx['height']
            source=Image.frombytes('RGBA',size,decode_texture(original))
            actual=Image.frombytes('RGBA',size,decode_texture(tx))
            for s in t['islands']:
                x,y,w,h=s['rect'];cut=actual.crop((x,y,x+w,y+h))
                _,background,layers=compose_island(source,s,assets)
                split_supports=[]
                for layer in layers:
                    if layer['crop']:
                        cx,cy,cw,ch=layer['crop']
                        # Neighbouring glyph strokes across a texture seam count;
                        # effect bitmaps are still never used as the audit mask.
                        support=layer['full_ink'].getchannel('A').point(lambda a:255 if a else 0)
                        split_supports.append(support.filter(ImageFilter.MaxFilter(7)).crop((cx,cy,cx+cw,cy+ch)))
                residue=negative_space(cut,background,[l['parts']['ink']for l in layers],split_supports=split_supports)
                identity=digest(cut.tobytes())==identities[r['path'],t['object'],s['id']]
                latin_error=0;latin_lost=0;latin_pixels=0
                for l in s['layers']:
                    if l['kind']!='source-ink':continue
                    cx,cy,cw,ch=l['core']
                    for yy in range(cy,cy+ch):
                        for xx in range(cx,cx+cw):
                            p=source.getpixel((xx,yy));q=actual.getpixel((xx,yy))
                            if p[3]>=80 and max(p[:3])>=48:
                                latin_pixels+=1
                                delta=max(abs(p[c]*p[3]-q[c]*q[3])/255 for c in range(3))
                                latin_error=max(latin_error,delta)
                                latin_lost+=delta>s['max_premultiplied_delta']
                passed=identity and residue==0 and latin_lost==0
                row=dict(id=s['id'],name=s['name'],passed=passed,native_identity=identity,
                         negative_space_residue_pixels=residue,latin_pixels=latin_pixels,
                         latin_premultiplied_max_delta=latin_error,latin_failed_pixels=latin_lost)
                groups.append(row)
                if not passed:failures.append(s['id'])
    return dict(schema_version=1,passed=not failures,groups=groups,failures=failures,
                game_started=False,game_rendering_verified=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('profile','project-root','baseline','actual-root','reference','lzx-library','report'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();result=audit(json.loads(a.profile.read_bytes()),a.project_root,a.baseline,a.actual_root,
                                json.loads(a.reference.read_bytes()),LzxDecoder(a.lzx_library))
    a.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    g=result['groups'];print(f"ISLANDS={len(g)} NEGATIVE_SPACE_RESIDUE={sum(r['negative_space_residue_pixels']for r in g)} "
                           f"LATIN_FAILED_PIXELS={sum(r['latin_failed_pixels']for r in g)} FAILURES={len(result['failures'])} "
                           f"RESULT={'PASS'if result['passed']else'FAIL'}")
    return 0 if result['passed']else 1


if __name__=='__main__':raise SystemExit(main())
