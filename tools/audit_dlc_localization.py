"""Offline DLC string, subtitle-binding and base-resource coverage audit."""
import argparse
import json
from pathlib import Path
import re

from .build_dlc_localization import read_json,json_bytes
from .build_font_supplement import context
from .build_text_layout_revision import font_metrics
from .coalesced import parse,extract_entries
from .stfs_package import StfsPackage
from .text_line_layout import audit as layout_audit
from .ue3_fonts import read_properties
from .ue3_package import Reader,LzxDecoder
from .ue3_subtitle_refs import read_fields,sha
from .xdbf_strings import Xdbf


def layout_with_font_metrics(layout_path,metrics_path=None):
    raw=Path(layout_path).read_bytes();layout=json.loads(raw)
    if metrics_path is None:return layout
    overlay=read_json(metrics_path)
    if (overlay.get('kind')!='font-metrics-overlay' or overlay.get('schema_version')!=1
            or overlay.get('base_layout_sha256')!=sha(raw)
            or set(overlay['fonts'])!=set(layout['fonts'])):
        raise ValueError('font metric overlay source/schema mismatch')
    for role,updated in overlay['fonts'].items():
        before=layout['fonts'][role]
        if ({k:v for k,v in updated.items() if k!='advances_sha256'}
                !={k:v for k,v in before.items() if k!='advances_sha256'}):
            raise ValueError('font metric overlay may change advances only')
    layout['fonts']=overlay['fonts']
    return layout


def audit(packages,project,game,decoder,profile_path,layout_path,font_metrics_path=None):
    p=read_json(profile_path)
    shared=read_json(project/p['strings']);assets=read_json(project/p['assets'])
    layout=layout_with_font_metrics(layout_path,font_metrics_path)
    metrics=font_metrics(game,layout['fonts'])
    coal_path=game/layout['coalesced']['resource'];coal=coal_path.read_bytes()
    rows=extract_entries(parse(coal),layout['coalesced']['resource']);lookup={}
    for row in rows:
        doc=row['embedded_path'].replace('\\','/').rsplit('/',1)[-1].rsplit('.',1)[0]
        key=f'<Strings:{doc}.{row["section"]}.{row["key"]}>'
        lookup.setdefault(key,[]).append(row)
    families={entry:family for family in layout['families'] for entry in family['entry_ids']}
    counters=dict(strings_mismatch=0,metadata_mismatch=0,subtitle_ref_mismatch=0,missing_references=0,
        subtitle_fields=0,subtitle_layout_checked=0,layout_errors=0,weapon_markers=0,weapon_fields=0,missing_glyphs=0)
    detail=dict(packages=[],subtitles=[],weapons=[],problems=[])
    def bind(ref,kind):
        found=lookup.get(ref,[])
        if len(found)!=1:
            counters['missing_references']+=1;detail['problems'].append(dict(kind=kind,reference=ref,issue='missing/ambiguous text key'));return None
        row=found[0];value=row['source'];family=families.get(row['id'])
        if kind=='subtitle' and family:
            result=layout_audit(value,metrics[family['fonts'][0]],family['width'],layout['rules'],max_lines=family['max_lines'])
            counters['subtitle_layout_checked']+=1
            if not result['passed']:
                counters['layout_errors']+=1;detail['problems'].append(dict(reference=ref,issue=result))
        visible=re.sub('<[^>]*>','',value).replace('\\n','').replace('\\','')
        missing=sorted({c for c in visible if not c.isspace() and ord(c) not in metrics['general']})
        if missing:
            counters['missing_glyphs']+=len(missing);detail['problems'].append(dict(reference=ref,missing=missing))
        return dict(reference=ref,entry_id=row['id'],text=value,sha256=sha(value.encode()),layout_family=family['id']if family else None)
    for spec in p['packages']:
        raw=(packages/spec['name']).read_bytes();container=StfsPackage(raw)
        strings={r['id']:r['text']for r in Xdbf(container.read_member('spa.bin')).strings()[shared['source_language_id']]}
        for edit in shared['entries']:counters['strings_mismatch']+=strings.get(edit['id'])!=edit['translation']
        for key,value in spec['metadata'].items():counters['metadata_mismatch']+=container.metadata()[key]!=value
        detail['packages'].append(dict(name=spec['name'],sha256=sha(raw),size=len(raw),integrity=container.integrity))
        if spec['name']==assets['container']:
            for revision in assets['packages']:
                ctx=context(container.read_member(revision['member']),decoder);fields={}
                for obj in ctx['tables']['exports']:
                    if obj['class_path'] not in ('MC2Game.MC2SeqAct_ShowCSMBSubtitle','Engine.SoundNodeWave'):continue
                    data=ctx['logical'][obj['serial_offset']:obj['serial_offset']+obj['serial_size']]
                    for field in read_fields(data,ctx['tables']['names'],obj['class_path']):
                        fields[(obj['path'],field.get('wrap'),field['item'])]=field['text'];counters['subtitle_fields']+=1
                        bound=bind(field['text'],'subtitle')
                        detail['subtitles'].append(dict(member=revision['member'],object=obj['path'],**field,binding=bound))
                for change in revision['entries']:
                    counters['subtitle_ref_mismatch']+=fields[(change['object'],change['wrap'],change['item'])]!=change['after']
        else:
            ctx=context((game/'MC2Game/CookedXenon/data_weapon.xxx').read_bytes(),decoder)
            exports={e['path'].lower():e for e in ctx['tables']['exports']}
            for entry in container.entries:
                if not entry.path.endswith('.DLC'):continue
                if container.read_member(entry.path)!=b' '*(1024*1024):raise ValueError('weapon unlock marker payload differs')
                obj=exports[entry.path[:-4].lower()];payload=ctx['logical'][obj['serial_offset']:obj['serial_offset']+obj['serial_size']]
                r=Reader(payload);r.seek(4);props=read_properties(r,ctx['tables']['names']);fields=[]
                for prop in props:
                    if prop['name'] in ('ItemName','Description','ShortDescription'):
                        value=Reader(prop['raw'],unicode_endian='<').string();fields.append(dict(field=prop['name'],binding=bind(value,'weapon')))
                        counters['weapon_fields']+=1
                if len(fields)!=3:raise ValueError('weapon text field inventory differs')
                counters['weapon_markers']+=1;detail['weapons'].append(dict(marker=entry.path,object=obj['path'],fields=fields))
    passed=not any(v for k,v in counters.items()if k.endswith('mismatch')or k in ('missing_references','layout_errors','missing_glyphs'))
    return dict(kind='offline-dlc-localization-audit',summary=dict(**counters,passed=passed),details=detail,
                coalesced_sha256=sha(coal),game_launched=False,in_game_verified=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('packages','project','game','profile','layout-profile','lzx-library','output'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--font-metrics-profile',type=Path)
    a=p.parse_args()
    try:
        r=audit(a.packages,a.project,a.game,LzxDecoder(a.lzx_library),a.profile,a.layout_profile,a.font_metrics_profile)
        a.output.parent.mkdir(parents=True,exist_ok=True)
        with a.output.open('xb')as f:f.write(json_bytes(r))
        if read_json(a.output)!=r:raise ValueError('audit output readback mismatch')
        print(json.dumps(r['summary']));return 0 if r['summary']['passed']else 1
    except (ValueError,OSError,KeyError,TypeError)as e:print('ERROR: '+str(e));return 2

if __name__=='__main__':raise SystemExit(main())
