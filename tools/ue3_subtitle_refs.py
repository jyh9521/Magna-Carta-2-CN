"""Read and repair exact UE3 subtitle references, preserving cue timing and audio.

The source package, export, field index and corroborating subtitle export are
all explicit. No inferred numeric rename or unbounded binary replacement occurs.
"""
from __future__ import annotations

import hashlib
import struct

from .build_font_supplement import context
from .decompress_package import decompress_copy
from .ue3_fonts import read_properties
from .ue3_package import Reader


def sha(data):
    return hashlib.sha256(data).hexdigest()


def string(prop):
    if prop['type'] != 'StrProperty':
        raise ValueError('expected subtitle StrProperty')
    r=Reader(prop['raw']);value=r.string()
    if r.pos!=len(r.data):
        raise ValueError('subtitle string tail')
    return value


def unique(props,name):
    found=[p for p in props if p['name']==name and p['array_index']==0]
    if len(found)!=1:
        raise ValueError('missing or duplicate subtitle field: '+name)
    return found[0]


def read_subtitles(prop,names,base=0):
    if prop['type']!='ArrayProperty':
        raise ValueError('expected subtitle array')
    r=Reader(prop['raw']);result=[]
    for index in range(r.count(1024)):
        props=read_properties(r,names)
        text=unique(props,'Text')
        result.append(dict(item=index,text=string(text),offset=base+prop['value_offset']+text['value_offset'],
                           size=text['size']))
    if r.pos!=len(r.data):
        raise ValueError('subtitle array tail')
    return result


def read_fields(payload,names,class_path):
    r=Reader(payload);r.seek(4);props=read_properties(r,names)
    if class_path=='Engine.SoundNodeWave':
        candidates=[p for p in props if p['name']=='Subtitles']
        return [] if not candidates else read_subtitles(unique(props,'Subtitles'),names)
    if class_path!='MC2Game.MC2SeqAct_ShowCSMBSubtitle':
        raise ValueError('unsupported subtitle consumer class')
    wrap=unique(props,'SubTitleWrap')
    if wrap['type']!='ArrayProperty':
        raise ValueError('expected subtitle wrapper array')
    reader=Reader(wrap['raw']);result=[]
    for index in range(reader.count(1024)):
        fields=read_properties(reader,names)
        face=string(unique(fields,'FaceFXSeqName'))
        for row in read_subtitles(unique(fields,'Subtitles'),names,wrap['value_offset']):
            row.update(wrap=index,face=face);result.append(row)
    if reader.pos!=len(reader.data):
        raise ValueError('subtitle wrapper tail')
    return result


def patch_package(data,plan,decoder):
    if (not isinstance(plan,dict) or set(plan)!={'source_sha256','entries'}
            or plan['source_sha256']!=sha(data) or not isinstance(plan['entries'],list)):
        raise ValueError('subtitle package identity/schema mismatch')
    normalized,norm_report=decompress_copy(data,plan['source_sha256'],decoder)
    ctx=context(normalized,None);exports={e['path']:e for e in ctx['tables']['exports']}
    if len(exports)!=len(ctx['tables']['exports']):
        raise ValueError('ambiguous export path')
    result=bytearray(normalized);seen=set();edits=[]
    for change in plan['entries']:
        if set(change)!={'object','object_sha256','wrap','item','face','before','after','evidence_object','evidence_sha256'}:
            raise ValueError('invalid subtitle edit fields')
        if type(change['wrap']) is not int or type(change['item']) is not int:
            raise ValueError('subtitle field indices must be integers')
        obj=exports.get(change['object']);evidence=exports.get(change['evidence_object'])
        if obj is None or evidence is None or obj['path']==evidence['path']:
            raise ValueError('subtitle or independent evidence export missing')
        payload=normalized[obj['serial_offset']:obj['serial_offset']+obj['serial_size']]
        donor=normalized[evidence['serial_offset']:evidence['serial_offset']+evidence['serial_size']]
        if sha(payload)!=change['object_sha256'] or sha(donor)!=change['evidence_sha256']:
            raise ValueError('subtitle export SHA256 mismatch')
        rows=read_fields(payload,ctx['tables']['names'],obj['class_path'])
        selected=[r for r in rows if r.get('wrap')==change['wrap'] and r['item']==change['item']]
        if len(selected)!=1 or selected[0]['text']!=change['before'] or selected[0]['face']!=change['face']:
            raise ValueError('subtitle reference/FaceFX field mismatch')
        corroborated=read_fields(donor,ctx['tables']['names'],evidence['class_path'])
        if evidence['class_path']=='Engine.SoundNodeWave' and evidence['path'].rsplit('.',1)[-1]!=change['face']:
            raise ValueError('sound-wave identity differs from FaceFX cue')
        if not any(r['text']==change['after'] and r.get('face',change['face'])==change['face'] for r in corroborated):
            raise ValueError('independent subtitle binding does not corroborate replacement')
        row=selected[0];offset=obj['serial_offset']+row['offset']
        before=struct.pack('>i',len(change['before'])+1)+change['before'].encode('ascii')+b'\0'
        after=struct.pack('>i',len(change['after'])+1)+change['after'].encode('ascii')+b'\0'
        if len(before)!=len(after) or before==after or before!=normalized[offset:offset+row['size']]:
            raise ValueError('subtitle edit must match an equal-size ASCII FString')
        span=set(range(offset,offset+len(before)))
        if seen&span:
            raise ValueError('overlapping subtitle field edits')
        seen.update(span);result[offset:offset+len(after)]=after
        edits.append(dict(object=obj['path'],offset=offset,before=change['before'],after=change['after'],
                          evidence_object=evidence['path']))
    output=bytes(result);check=context(output,None)
    if check['tables']!=ctx['tables']:
        raise ValueError('subtitle patch changed object tables')
    reverse=bytearray(output)
    for e in edits:
        before=struct.pack('>i',len(e['before'])+1)+e['before'].encode()+b'\0'
        reverse[e['offset']:e['offset']+len(before)]=before
        obj=exports[e['object']];rows=read_fields(output[obj['serial_offset']:obj['serial_offset']+obj['serial_size']],
                                                ctx['tables']['names'],obj['class_path'])
        if not any(r['text']==e['after'] for r in rows):
            raise ValueError('subtitle patch readback mismatch')
    if bytes(reverse)!=normalized:
        raise ValueError('subtitle inverse changed unrelated logical bytes')
    return output,dict(source_sha256=sha(data),sha256=sha(output),size=len(output),edits=edits,
        normalization=norm_report,logical_inverse_byte_identical=True,
        audio_animations_textures_and_cue_times_unchanged=True)
