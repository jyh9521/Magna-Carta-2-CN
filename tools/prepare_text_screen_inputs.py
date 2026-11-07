"""Materialize only selected, verified text resources from a recipe and originals."""
import argparse
import fnmatch
import json
from pathlib import Path
import sys

from .audit_text_residuals import digest, locked, paired_rows
from .disc_inventory import Disc, sha256_file
from .font_binding_plan import _relative
from .verify_resource_phase import unique


def prepare(recipe, selectors, inventories, root, output, disc_factory=Disc):
    root=Path(root).resolve();output=Path(output).resolve()
    if output.exists() or not output.is_relative_to(root) or output==root:
        raise ValueError('New output inside project required')
    if not isinstance(selectors,dict) or not isinstance(recipe,dict):
        raise ValueError('Recipe and selectors must be objects')
    definitions=selectors.get('selectors')
    if (type(selectors.get('schema_version')) is not int or selectors['schema_version']!=1 or selectors.get('kind')!='text-screen-resource-selectors'
            or not isinstance(definitions,list) or not 1<=len(definitions)<=32
            or not isinstance(recipe.get('discs'),list) or not 1<=len(recipe['discs'])<=8
            or set(inventories)!=set(range(1,len(recipe['discs'])+1))):
        raise ValueError('Selector/disc inventory contract mismatch')
    for selector in definitions:
        if (not isinstance(selector,dict) or not isinstance(selector.get('pattern'),str)
                or not 1<=len(selector['pattern'])<=256
                or selector.get('kind') not in ('coalesced','timed-cues')
                or ('role' in selector)==('role_by_suffix' in selector)):
            raise ValueError('Invalid text selector')
        roles=selector.get('role_by_suffix',{'':selector.get('role')})
        if (not isinstance(roles,dict) or not 1<=len(roles)<=16
                or any(not isinstance(k,str) or value not in ('primary','alternate-locale','configuration')
                       for k,value in roles.items())):
            raise ValueError('Invalid text selector role')
    prepared=[];groups={};snapshots={};images=[];total=0;memberships=0
    for disc_no,view in enumerate(recipe['discs'],1):
        image=Path(view['iso']);image=image if image.is_absolute() else root/image
        inv=inventories[disc_no];disc=disc_factory(image)
        if (image.stat().st_size!=inv['image_size'] or sha256_file(image)!=view['sha256']
                or inv['sha256']!=view['sha256']):
            raise ValueError('Original image identity mismatch')
        images.append((image,view['sha256']))
        actual={(r['path'],r.get('offset'),r.get('size')) for r in disc.inventory() if not r['directory']}
        declared={(r['path'],r.get('offset'),r.get('size')) for r in inv['entries'] if not r['directory']}
        if actual!=declared:raise ValueError('Actual disc directory/inventory mismatch')
        updates={r['path']:r for r in view['resources']}
        if len(updates)!=len(view['resources']):raise ValueError('Duplicate recipe resource')
        for row in inv['entries']:
            if row['directory']:continue
            name=_relative(row['path']);matches=[s for s in definitions if fnmatch.fnmatchcase(name,s['pattern'])]
            if not matches:continue
            if len(matches)!=1:raise ValueError('Overlapping text selectors')
            selector=matches[0];role=selector.get('role')
            if role is None:role=selector.get('role_by_suffix',{}).get(Path(name).suffix.lower())
            if role not in ('primary','alternate-locale','configuration'):
                raise ValueError('Selected text resource has no explicit role')
            if type(row['size']) is not int or not 0<row['size']<=64*1024*1024:
                raise ValueError('Selected text resource size bound')
            before=disc.read(row['offset'],row['size'])
            if digest(before)!=row['sha256']:raise ValueError('Original text resource hash mismatch')
            ref=updates.get(name);after=before
            if ref:
                path=Path(ref['file']);path=path if path.is_absolute() else root/path
                path=path.resolve()
                if path in snapshots and snapshots[path]!=ref['sha256']:
                    raise ValueError('Conflicting effective file identities')
                after=locked(path,ref['sha256']);snapshots[path]=ref['sha256']
            total+=len(before)+len(after);memberships+=1
            if total>256*1024*1024 or memberships>256:raise ValueError('Total selected text bound')
            paired_rows(before,after,name,selector['kind'])
            key=(name,selector['kind'],role,digest(before),digest(after))
            if key in groups:
                groups[key]['discs'].append(disc_no);continue
            definition=dict(resource=name,kind=selector['kind'],role=role,discs=[disc_no],
                original=dict(file=f'originals/disc{disc_no}/'+name,sha256=digest(before)),
                effective=dict(file=f'effective/disc{disc_no}/'+name,sha256=digest(after)))
            if before==after:definition['effective']=dict(definition['original'])
            groups[key]=definition;prepared.append((definition,before,after))
    if not prepared:raise ValueError('No text resources matched explicit selectors')
    output.mkdir(parents=True)
    rows=[]
    for row,before,after in prepared:
        for phase,raw in [('original',before),('effective',after)]:
            target=output/row[phase]['file']
            if target.exists():
                if target.read_bytes()!=raw:raise ValueError('Output alias mismatch')
            else:
                target.parent.mkdir(parents=True,exist_ok=True)
                with target.open('xb') as f:f.write(raw)
            locked(target,row[phase]['sha256'])
            row[phase]['file']=target.relative_to(root).as_posix()
        rows.append(row)
    for path,sha in snapshots.items():locked(path,sha)
    for image,sha in images:
        if sha256_file(image)!=sha:raise ValueError('Original image changed during audit preparation')
    return dict(schema_version=1,kind='effective-text-screen-inputs',resources=rows,
        resource_memberships=memberships,original_image_hashes_verified=True,
        game_resources_written=0,full_game_copy_created=False)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('recipe','selectors'):p.add_argument('--'+name,type=Path,required=True);p.add_argument('--'+name+'-sha256',required=True)
    p.add_argument('--inventory',action='append',required=True,metavar='DISC=JSON=SHA256')
    p.add_argument('--project-root',type=Path,default=Path('.'));p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args(argv)
    try:
        snapshots=[(a.recipe,a.recipe_sha256),(a.selectors,a.selectors_sha256)]
        recipe=json.loads(locked(*snapshots[0],4*1024*1024),object_pairs_hook=unique)
        selectors=json.loads(locked(*snapshots[1],1024*1024),object_pairs_hook=unique);inventories={}
        for ref in a.inventory:
            disc,file,sha=ref.split('=',2);disc=int(disc)
            if disc in inventories:raise ValueError('Duplicate inventory disc')
            snapshots.append((Path(file),sha));inventories[disc]=json.loads(locked(file,sha,32*1024*1024),object_pairs_hook=unique)
        result=prepare(recipe,selectors,inventories,a.project_root,a.output_dir)
        for path,sha in snapshots:locked(path,sha)
        result.update(recipe_sha256=a.recipe_sha256,selectors_sha256=a.selectors_sha256)
        raw=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode();target=a.output_dir/'inputs.json'
        with target.open('xb') as f:f.write(raw)
        if target.read_bytes()!=raw:raise ValueError('Input manifest reopening mismatch')
        print(f'TEXT_RESOURCES={len(result["resources"])} MEMBERSHIPS={result["resource_memberships"]} ORIGINAL_IMAGE_HASHES=PASS GAME_RESOURCES_WRITTEN=0')
        return 0
    except (ValueError,OSError,KeyError,TypeError,UnicodeError) as e:
        print('ERROR: '+str(e),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
