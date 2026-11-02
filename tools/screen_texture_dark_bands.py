"""Read-only screening of all active generated lettering in a locked recipe.

Suspects require visual review; this command never writes game resources.
Authored/preserved artwork is counted separately, not automatically smoothed.
"""
import argparse
from collections import defaultdict
from functools import lru_cache
import json
from pathlib import Path

from .build_font_supplement import context
from .repair_texture_dark_bands import load_labels
from .repair_texture_labels import locked, revise
from .reface_font import sha
from .texture_dark_bands import core_mask, narrow_gradient_positions, quantization_rows
from .texture_layout import read_texture, decode_texture
from .texture_overlay import render_label, rgba_crop, select_texture_export


def screen(profile, recipe, project, apply_revision=False):
    project=Path(project).resolve(); labels=load_labels(profile,project); mappings=defaultdict(list)
    for ref in profile['label_plans']:
        plan=json.loads(locked(project,ref))
        for source in plan['sources']:
            for t in source['textures']:
                for lid in t.get('regions',[t.get('label')]):
                    mappings[lid].append((source['path'],t['object'],t.get('profile',
                                         dict(kind='xbox-inline-bc-v1',format=7))))
    # Disc-specific TOCs and unrelated packages need not match. Only compare
    # candidates that can supply one of the active image mappings.
    mapped_paths={relative for choices in mappings.values() for relative,_,_ in choices}
    paths={}
    for disc in reversed(recipe['discs']):
        for r in disc['resources']:
            if r['path'] not in mapped_paths:
                continue
            if r['path'] in paths and paths[r['path']]['sha256']!=r['sha256']:
                raise ValueError('same path has different disc candidates; screen discs separately')
            paths[r['path']]=r
    if apply_revision:
        for request in profile['requests']:
            lid=request['id'];labels[lid]=revise(labels[lid],request['remove_gradient_positions'])
    @lru_cache(maxsize=3)
    def package(relative):
        ref=paths[relative];data=Path(ref['file']).read_bytes()
        if sha(data)!=ref['sha256']:raise ValueError('screen source SHA256 mismatch')
        return context(data,None)
    @lru_cache(maxsize=8)
    def texture(relative,obj,fmt):
        c=package(relative);e=select_texture_export(c['tables'],obj);at=e['serial_offset']
        t=read_texture(c['logical'][at:at+e['serial_size']],c['tables']['names'],at,
                       dict(kind='xbox-inline-bc-v1',format=fmt),None)
        return t,decode_texture(t)
    @lru_cache(maxsize=8)
    def font(path,digest):return locked(project,dict(path=path,sha256=digest))
    rows=[];excluded=[]
    for lid,label in labels.items():
        if label.get('appearance',{}).get('kind')!='source-style-v1' or 'glyph_mask' in label:
            excluded.append(lid);continue
        choices=[m for m in mappings[lid] if m[0] in paths]
        if not choices:raise ValueError('generated label missing from resource index: '+lid)
        relative,obj,fmt=choices[0];t,pixels=texture(relative,obj,fmt['format'])
        ref=label['font'];f=font(ref['path'],ref['sha256']);mask=core_mask(f,label)
        native=rgba_crop(pixels,t['width'],label['rect'])
        rows.append(dict(id=lid,resource=relative,object=obj,
            gradient_positions=narrow_gradient_positions(label),
            quantization_rows=quantization_rows(native,render_label(f,label),mask,label['rect'][2])))
    return dict(total=len(labels),screened=len(rows),excluded_artwork=excluded,rows=rows,
                game_started=False,screening_is_not_visual_acceptance=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('profile','recipe','report'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--recipe-sha256',required=True);p.add_argument('--project-root',type=Path,default=Path('.'))
    p.add_argument('--apply-revision',action='store_true');a=p.parse_args()
    raw=a.recipe.read_bytes()
    if sha(raw)!=a.recipe_sha256:raise ValueError('resource recipe SHA256 mismatch')
    result=screen(json.loads(a.profile.read_bytes()),json.loads(raw),a.project_root,a.apply_revision)
    with a.report.open('x',encoding='utf8')as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(f'LABELS={result["total"]} SCREENED={result["screened"]} '
          f'GRADIENT_SUSPECTS={sum(bool(r["gradient_positions"]) for r in result["rows"])} '
          f'QUANTIZATION_SUSPECTS={sum(bool(r["quantization_rows"]) for r in result["rows"])}')


if __name__=='__main__':main()
