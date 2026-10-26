"""Publish an offline review from hash-verified, natively decoded bundle previews."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil


def digest(b):return hashlib.sha256(b).hexdigest()


def build(project, inventory, revision, plan, bundles, output):
    from PIL import Image
    from .texture_overlay import image_id
    project=Path(project).resolve();inventory=Path(inventory).resolve();output=Path(output).resolve()
    if output.exists() or not output.is_relative_to(project):raise ValueError('review output must be new and inside project')
    source=json.loads(inventory.read_bytes());decisions=json.loads(Path(revision).read_bytes());p=json.loads(Path(plan).read_bytes())
    if decisions['review_plan_sha256']!=digest(Path(plan).read_bytes()):raise ValueError('review plan identity mismatch')
    review_round=decisions.get('review_round',2)
    if type(review_round) is not int or not 2<=review_round<=99:raise ValueError('invalid review round')
    notes={x['image_id']:x for x in decisions['entries']};mapping={};snapshots=[]
    for root in bundles:
        root=Path(root).resolve();manifest_bytes=(root/'manifest.json').read_bytes();manifest=json.loads(manifest_bytes)
        if manifest['plan_canonical_sha256']!=digest((json.dumps(p,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode()):
            # The project canonical encoder is authoritative, not file whitespace.
            from .build_font_route_probe import encoded
            if manifest['plan_canonical_sha256']!=digest(encoded(p)):raise ValueError('preview bundle plan mismatch')
        disc=manifest['disc'];selected=[s for s in p['sources'] if disc in s.get('discs',[1,2])]
        for n,s in enumerate(selected,1):
            for i,e in enumerate(s['textures']):
                key=image_id(e);path=f'previews/after-{n:02d}-{i:02d}.png';b=(root/path).read_bytes()
                if digest(b)!=manifest['member_sha256'][path]:raise ValueError('native preview file hash mismatch')
                with Image.open(root/path) as im:rgba=im.convert('RGBA').tobytes()
                if digest(rgba)!=manifest['alias_rgba_sha256']['after:'+key]:raise ValueError('native preview RGBA mismatch')
                if key in mapping and digest(rgba)!=mapping[key][1]:raise ValueError('cross-disc native alias mismatch')
                mapping.setdefault(key,(root/path,digest(rgba)))
        snapshots.append((root/'manifest.json',digest(manifest_bytes)))
    output.mkdir();(output/'images').mkdir();items=[]
    for item in source['items']:
        item=dict(item);key=item['id'];note=notes[key];original=inventory.parent/item['original_image'];previous=inventory.parent/item['chinese_image']
        for f,expected in [(original,item['before_hash']),(previous,item['after_hash'])]:
            with Image.open(f) as im:
                if digest(im.convert('RGBA').tobytes())!=expected:raise ValueError('prior review input RGBA mismatch')
        if key not in mapping:raise ValueError('image missing from final native bundles: '+key)
        revised,after=mapping[key]
        if note['action']=='unchanged' and after!=item['after_hash']:raise ValueError('unrequested image changed: '+key)
        if note['action']=='restore-original' and after!=item['before_hash']:raise ValueError('original restoration not exact: '+key)
        stem=f"{item['number']:04d}"
        for suffix,f in [('original',original),('previous',previous),('revised',revised)]:
            destination=output/'images'/f'{stem}_{suffix}.png';shutil.copyfile(f,destination)
            if destination.read_bytes()!=f.read_bytes():raise ValueError('review publication mismatch')
        item.update(original_image=f'images/{stem}_original.png',previous_image=f'images/{stem}_previous.png',
                    chinese_image=f'images/{stem}_revised.png',after_hash=after,
                    previous_feedback=note['previous_feedback'],action=note['action'],
                    native_review_focus_note=note.get('native_review_focus',''))
        if decisions.get('retained_semantic_hold',{}).get('image_id')==key:
            item['retained_note']='待证地图名 원수의 언덕 仍保留原文，未把酋长之丘当作确认译名。'
        items.append(item)
    templates=Path(__file__).parent/'review_page';payload=json.dumps(items,ensure_ascii=False).replace('<','\\u003c')
    revision_id=decisions['review_plan_sha256'];html=(templates/'review.html').read_text('utf-8')
    html=html.replace('__REVISION__',revision_id).replace('__ROUND__',str(review_round)).replace('__SCRIPT__',(templates/'review.js').read_text('utf-8')).replace('__ITEMS__',payload)
    (output/'index.html').write_bytes(html.encode())
    manifest=dict(schema_version=2,count=len(items),revision=revision_id,native_decoded=True,items=items,
                  bundle_manifests=[dict(path=str(f),sha256=h) for f,h in snapshots])
    (output/'manifest.json').write_bytes((json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode())
    (output/'README.txt').write_text('打开 index.html。左右键在任何输入框中均只翻页；翻页自动聚焦反馈框。\n上轮反馈只读展示；本轮反馈独立自动保存，可导出 CSV。\n图片均来自原生 BC 编码后解码的最终候选，非绘制草稿。\n',encoding='utf-8')
    for f,h in snapshots:
        if digest(f.read_bytes())!=h:raise ValueError('bundle changed during review publication')
    if (output/'index.html').read_text('utf-8')!=html:raise ValueError('review HTML reopening mismatch')
    return dict(images=len(items),native_decoded=True,output=str(output/'index.html'))


def main(argv=None):
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--project-root',type=Path,default=Path('.'));a.add_argument('--inventory',type=Path,required=True)
    a.add_argument('--revision',type=Path,required=True);a.add_argument('--plan',type=Path,required=True)
    a.add_argument('--bundle',type=Path,action='append',required=True);a.add_argument('--output',type=Path,required=True)
    args=a.parse_args(argv)
    try:print(json.dumps(build(args.project_root,args.inventory,args.revision,args.plan,args.bundle,args.output)));return 0
    except (OSError,ValueError,KeyError) as e:print('ERROR: '+str(e));return 2


if __name__=='__main__':raise SystemExit(main())
