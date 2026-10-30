"""Audit complete locale item-name banks, resident bindings and native glyph gaps.

No regular-expression search for one reported weapon is used as the inventory.
Name/description banks and expected counts are locale data; DLC unlock markers
are independently bound to the real item exports and then to those same banks.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import unicodedata

from .audit_font_optical_size import Sampler, ink_box
from .build_font_supplement import context
from .coalesced import parse, extract_entries
from .stfs_package import StfsPackage
from .ue3_package import Reader, LzxDecoder
from .font_binding_plan import confined_path
from .disc_inventory import Disc, sha256_file


def sha(data):
    return hashlib.sha256(data).hexdigest()


def is_wide_letter(char):
    return unicodedata.category(char).startswith('L') and unicodedata.east_asian_width(char) in ('W', 'F')


def names_from_banks(rows, banks):
    names=[];total=0
    for bank in banks:
        fields=[r for r in rows if r['embedded_path'].replace('\\','/').rsplit('/',1)[-1]==bank['file']
                and (bank['sections'] is None or r['section'] in bank['sections'])]
        selected=[r for r in fields if not r['key'].lower().endswith(tuple(bank['description_suffixes']))]
        if len(fields)!=bank['expected_fields'] or len(selected)!=bank['expected_names']:
            raise ValueError('complete item bank inventory changed: '+bank['file'])
        total+=len(fields);names.extend(selected)
    keys=[r['id'] for r in names]
    if len(set(keys))!=len(keys):raise ValueError('overlapping item banks')
    return names,total


def item_name(payload,names):
    """Bounded tagged-property scan; numbered unrelated FNames are valid.

    Two native quest items carry RelatedQuestID_2 after ItemName. The generic
    font-specific property reader forbids numbered names, so do not use it to
    silently exclude those item instances from this audit.
    """
    r=Reader(payload);r.seek(4);found=[]
    def name():
        index,number=r.u32(),r.u32()
        if index>=len(names) or number>65536:raise ValueError('invalid item property FName')
        return names[index]+('_'+str(number-1) if number else '')
    for _ in range(4096):
        key=name()
        if key=='None':break
        kind=name();size,index=r.u32(),r.u32()
        if kind=='StructProperty':name()
        if kind=='BoolProperty':
            if size or r.u32() not in (0,1):raise ValueError('invalid item boolean')
        raw=r.read(size)
        if key=='ItemName':
            if kind!='StrProperty' or index:raise ValueError('invalid item-name field')
            value=Reader(raw,unicode_endian='<');text=value.string()
            if value.pos!=len(raw):raise ValueError('item-name trailing data')
            found.append(text)
    else:raise ValueError('item property limit exceeded')
    if len(found)>1:raise ValueError('duplicate item-name field')
    return found[0] if found else None


def installer_item_sources(recipe_path, expected_sha256, disc_number):
    """Stream the actual installed view without extracting a second full game."""
    recipe_path=Path(recipe_path)
    raw=recipe_path.read_bytes()
    if sha(raw)!=expected_sha256:raise ValueError('installer recipe identity mismatch')
    recipe=json.loads(raw)
    if disc_number not in (1,2) or len(recipe['discs'])!=2:raise ValueError('invalid disc selection')
    disc=recipe['discs'][disc_number-1]
    image_path=Path(disc['iso'])
    if sha256_file(image_path)!=disc['sha256']:raise ValueError('original disc identity mismatch')
    image=Disc(image_path)
    records={r['path']:r for r in image.inventory() if not r['directory']}
    overlays={r['path']:r for r in disc['resources']}
    if len(overlays)!=len(disc['resources']) or not set(overlays)<=set(records):
        raise ValueError('invalid installer resource inventory')
    for name,r in sorted(records.items()):
        if not name.startswith('MC2Game/CookedXenon/') or not name.endswith('.xxx'):continue
        if name in overlays:
            entry=overlays[name];data=Path(entry['file']).read_bytes()
            if sha(data)!=entry['sha256']:raise ValueError('installer resource identity mismatch: '+name)
        else:data=image.read(r['offset'],r['size'])
        yield name,data


def resident_bindings(root, decoder, sources=None):
    rows=[];packages=[]
    if sources is None:
        sources=((path.relative_to(root).as_posix(),path.read_bytes())
                 for path in sorted((root/'MC2Game/CookedXenon').glob('*.xxx')))
    for name,raw in sources:
        ctx=context(raw,decoder)
        matched=[]
        for e in ctx['tables']['exports']:
            if not e['class_path'].startswith('MC2Game.MC2Item'):continue
            value=item_name(ctx['logical'][e['serial_offset']:e['serial_offset']+e['serial_size']],ctx['tables']['names'])
            if value is not None:
                matched.append(dict(resource=name,object=e['path'],
                                    class_path=e['class_path'],value=value))
        if matched:
            packages.append(dict(path=name,sha256=sha(raw),names=len(matched)))
            rows.extend(matched)
    if not packages:raise ValueError('empty resident item inventory')
    return rows,packages


def audit(game,fonts,profile,dlc,decoder,original_text,resident_sources=None,disc_number=1):
    game,fonts=Path(game).resolve(),Path(fonts).resolve()
    p=json.loads(Path(profile).read_bytes())
    if p.get('schema_version')!=1 or p.get('kind')!='native-item-spacing-audit':raise ValueError('wrong item audit profile')
    data=confined_path(game,p['coalesced']['resource']).read_bytes()
    if sha(data)!=p['coalesced']['sha256']:raise ValueError('item text source SHA256 mismatch')
    allrows=extract_entries(parse(data),p['coalesced']['resource'])
    names,total=names_from_banks(allrows,p['banks'])
    lookup={}
    for r in names:
        key='<Strings:'+r['embedded_path'].replace('\\','/').rsplit('/',1)[-1].rsplit('.',1)[0]+'.'+r['section']+'.'+r['key']+'>'
        lookup.setdefault(key.casefold(),[]).append(r)
    # The original table contains a duplicated quest-key record. Audit every
    # occurrence; do not guess which one the runtime lookup selects.
    duplicates={key:[r['id'] for r in rs] for key,rs in lookup.items() if len(rs)>1}
    if duplicates!=p.get('duplicate_references',{}):raise ValueError('duplicate item-name inventory changed')
    bindings,packages=resident_bindings(game,decoder,resident_sources)
    literals=[];unbound=[]
    for r in bindings:
        if r['value'].startswith('<Strings:'):
            matches=lookup.get(r['value'].casefold(),[])
            if not matches:
                unbound.append(r.copy());continue
            r['entry_ids']=[m['id'] for m in matches]
            if len(matches)==1:r['entry_id']=matches[0]['id']
        else:literals.append(r)
    signature=sha(json.dumps(unbound,sort_keys=True,separators=(',',':')).encode())
    expected=p.get('retained_unbound_sha256_by_disc',{}).get(str(disc_number),p['retained_unbound_sha256'])
    if signature!=expected:raise ValueError('unbound original-name inventory changed: '+signature)
    original=Path(original_text).read_bytes()
    if sha(original)!=p['coalesced']['original_sha256']:raise ValueError('original text identity mismatch')
    original_keys=set()
    for r in extract_entries(parse(original),p['coalesced']['resource']):
        original_keys.add(('<Strings:'+r['embedded_path'].replace('\\','/').rsplit('/',1)[-1].rsplit('.',1)[0]
                           +'.'+r['section']+'.'+r['key']+'>').casefold())
    if any(r['value'].casefold() in original_keys for r in unbound):
        raise ValueError('translation lost an original item-name binding')
    dlcraw=Path(dlc).read_bytes()
    if sha(dlcraw)!=p['dlc']['sha256']:raise ValueError('DLC identity mismatch')
    container=StfsPackage(dlcraw)
    weapons={r['object'].casefold():r for r in bindings if r['resource']==p['dlc']['resource']}
    unlocked=[]
    for entry in container.entries:
        if not entry.path.endswith('.DLC'):continue
        if container.read_member(entry.path)!=b' '*(1024*1024):raise ValueError('weapon unlock marker changed')
        r=weapons.get(entry.path[:-4].casefold())
        if r is None or 'entry_id' not in r:raise ValueError('unbound DLC weapon marker')
        unlocked.append(dict(marker=entry.path,entry_id=r['entry_id'],reference=r['value']))
    if len(unlocked)!=p['dlc']['expected_names']:raise ValueError('DLC name coverage changed')
    issues=[];whitespace=[]
    for r in names:
        value=r['source']
        if not value.strip() or any(unicodedata.category(c).startswith('C') for c in value):
            issues.append(dict(entry_id=r['id'],issue='empty-or-control-name'))
        if re.search(r'[\u3400-\u9fff]\s+[\u3400-\u9fff]',value):
            issues.append(dict(entry_id=r['id'],issue='space-between-ideographs'))
        if any(c.isspace() for c in value):
            whitespace.append(dict(entry_id=r['id'],text=value,codepoints=[ord(c) for c in value if c.isspace()]))
    font_rows=[];role_metrics={};previews=[]
    for spec in p['fonts']:
        sample=Sampler(confined_path(fonts,spec['resource']).read_bytes(),spec['object'])
        characters=sorted({c for r in names for c in r['source'] if not c.isspace()})
        cells={}
        for char in characters:
            if ord(char) not in sample.mapping:raise ValueError('item glyph absent: U+%04X'%ord(char))
            cell=sample.glyph(ord(char));box=ink_box(cell)
            if box is None:raise ValueError('item glyph has no visible ink: '+char)
            cells[char]=(cell.width,box)
        pairs=[]
        for r in names:
            for at,(a,b) in enumerate(zip(r['source'],r['source'][1:])):
                if not is_wide_letter(a) or not is_wide_letter(b):continue
                aw,ab=cells[a];_,bb=cells[b];gap=aw-ab[2]+bb[0]
                pairs.append(dict(entry_id=r['id'],at=at,pair=a+b,gap=gap))
                if not p['minimum_gap']<=gap<=p['maximum_gap']:
                    issues.append(dict(font=spec['object'],resource=spec['resource'],entry_id=r['id'],pair=a+b,gap=gap))
        signature={c:(a,tuple(b)) for c,(a,b) in cells.items()}
        if spec['role'] in role_metrics and role_metrics[spec['role']]!=signature:
            raise ValueError('font aliases have different native metrics/ink')
        role_metrics[spec['role']]=signature
        font_rows.append(dict(**spec,name_count=len(names),pairs=pairs,gap_counts=dict(sorted(Counter(r['gap'] for r in pairs).items()))))
    summary=dict(passed=not issues,disc=disc_number,banks=len(p['banks']),fields=total,names=len(names),dlc_names=len(unlocked),
                 fonts=len(font_rows),pair_checks=sum(len(f['pairs']) for f in font_rows),failures=len(issues),
                 resident_packages=len(packages),resident_names=len(bindings),literal_names_unchanged=len(literals),
                 duplicate_name_keys=len(duplicates),new_missing_bindings=0,original_unbound_names=len(unbound),
                 source_text_unchanged=True,
                 game_started=False,game_rendering_verified=False)
    return dict(summary=summary,fonts=font_rows,issues=issues,names=names,whitespace=whitespace,
                packages=packages,bindings=bindings,literal_names=literals,original_unbound_names=unbound,
                original_unbound_reachability_verified=False,dlc=unlocked)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('game','font-root','profile','dlc','lzx-library','original-coalesced','output'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--resident-installer-recipe',type=Path)
    p.add_argument('--resident-recipe-sha256')
    p.add_argument('--disc',type=int,choices=(1,2),default=1)
    a=p.parse_args()
    if a.output.exists():raise ValueError('new audit output required')
    if bool(a.resident_installer_recipe)!=bool(a.resident_recipe_sha256):
        raise ValueError('resident recipe and SHA256 must be supplied together')
    if a.disc!=1 and a.resident_installer_recipe is None:
        raise ValueError('a second-disc audit requires the complete installer view')
    sources=(installer_item_sources(a.resident_installer_recipe,a.resident_recipe_sha256,a.disc)
             if a.resident_installer_recipe else None)
    report=audit(a.game,a.font_root,a.profile,a.dlc,LzxDecoder(a.lzx_library),a.original_coalesced,sources,a.disc)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    raw=(json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode();a.output.write_bytes(raw)
    if a.output.read_bytes()!=raw:raise ValueError('audit report readback mismatch')
    print(json.dumps(report['summary'],ensure_ascii=False))
    return int(not report['summary']['passed'])


if __name__=='__main__':raise SystemExit(main())
