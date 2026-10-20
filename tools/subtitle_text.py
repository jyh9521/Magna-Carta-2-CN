"""Source-locked UTF16LE SAMI-like cue files; preserve BOM, timings, classes and clear events."""
import hashlib
import re
from .validate_catalog import TOKEN

CUE=re.compile(r'(<SYNC Start=(\d+)><P Class=([A-Z]+)>)(.*?)(<SYNC Start=(\d+)><P Class=\3>&nbsp;)',re.S)
def digest(b):return hashlib.sha256(b).hexdigest()
def parse(data):
    if not data.startswith(b'\xff\xfe'):raise ValueError('subtitle requires UTF16LE BOM')
    text=data[2:].decode('utf-16-le');matches=list(CUE.finditer(text))
    if not matches:raise ValueError('empty subtitle cues')
    tail=CUE.sub('',text)
    if tail.replace('1\r\n','',1).replace('\r\n',''):raise ValueError('unsupported subtitle framing')
    if any(int(m[2])>int(m[6]) for m in matches):raise ValueError('subtitle interval reversed')
    return text,matches
def rebuild(data,plan):
    if type(plan.get('schema_version')) is not int or plan.get('schema_version')!=1 or plan.get('kind')!='timed-subtitle-text' or digest(data)!=plan['input_sha256']:
        raise ValueError('subtitle identity mismatch')
    text,cues=parse(data);by_start={m[2]:m for m in cues}
    if len(by_start)!=len(cues):raise ValueError('ambiguous subtitle cue start')
    edits={}
    for e in plan['entries']:
        key=str(e['start']);m=by_start.get(key);t=e['translation']
        if key in edits or m is None or int(m[6])!=e['end'] or digest(m[4].encode('utf8'))!=e['source_sha256']:
            raise ValueError('subtitle cue source/timing mismatch')
        if not t.strip() or any(c in t for c in '\r\n\0') or TOKEN.findall(t)!=TOKEN.findall(m[4]) or '&' in t:
            raise ValueError('subtitle protected markup mismatch')
        edits[key]=t
    out=CUE.sub(lambda m:m[1]+edits.get(m[2],m[4])+m[5],text)
    raw=b'\xff\xfe'+out.encode('utf-16-le');_,after=parse(raw)
    if [(m[1],m[5]) for m in cues]!=[(m[1],m[5]) for m in after]:raise ValueError('subtitle timing drift')
    return raw


def rebuild_reversible(data, plan):
    """Prove a cue-level inverse independently of retained-original backups."""
    output = rebuild(data, plan)
    _, before = parse(data)
    originals = {int(m[2]):m[4] for m in before}
    reverse = dict(schema_version=1, kind='timed-subtitle-text',
                   input_sha256=digest(output), entries=[dict(start=e['start'], end=e['end'],
                       source_sha256=digest(e['translation'].encode('utf8')),
                       translation=originals[int(e['start'])]) for e in plan['entries']])
    if rebuild(output, reverse) != data:
        raise ValueError('subtitle inverse rebuild changed original bytes')
    return output, dict(source_sha256=digest(data), candidate_sha256=digest(output),
                        edited_cues=len(plan['entries']), total_cues=len(before),
                        inverse_rebuild_byte_identical=True,
                        timings_classes_and_clear_events_preserved=True)
