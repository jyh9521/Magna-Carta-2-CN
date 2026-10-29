"""Hash-locked XDBF/XSTR localization; preserve all non-string entry payloads.

Independent reader based on Xenia's documented structures (see
references/dlc-format-research.lock.json). Supported writing profile: packed
version 0x10000 database, one terminal free record, unique UTF-8 XSTR IDs.
No game, emulator, account, achievement flags or scores are modified here.
"""
from __future__ import annotations

import hashlib
import re
import struct

from .validate_catalog import token_errors

MAX_BYTES = 64 * 1024 * 1024


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_xstr(data):
    if len(data) < 14:
        raise ValueError('truncated XSTR header')
    magic, version, size, count = struct.unpack_from('>4sIIH', data)
    if magic != b'XSTR' or version != 1 or size not in (len(data), len(data)-4):
        raise ValueError('unsupported XSTR size/version')
    rows, seen, pos = [], set(), 14
    for _ in range(count):
        if pos+4 > len(data):
            raise ValueError('truncated XSTR entry')
        identity, length = struct.unpack_from('>HH', data, pos)
        pos += 4
        if identity in seen or pos+length > len(data):
            raise ValueError('duplicate or out-of-range XSTR entry')
        text = data[pos:pos+length].decode('utf8', errors='strict')
        if '\0' in text:
            raise ValueError('embedded NUL in XSTR')
        seen.add(identity)
        rows.append(dict(id=identity, text=text))
        pos += length
    if pos != len(data):
        raise ValueError('unparsed XSTR tail')
    return rows


def write_xstr(original, replacements):
    rows = read_xstr(original)
    if set(replacements)-{r['id'] for r in rows}:
        raise ValueError('unknown XSTR ID')
    blocks = []
    for r in rows:
        text = replacements.get(r['id'], r['text'])
        if not isinstance(text, str) or '\0' in text:
            raise ValueError('invalid XSTR text')
        raw = text.encode('utf8', errors='strict')
        if len(raw) > 0xffff:
            raise ValueError('XSTR UTF-8 length overflow')
        blocks.append(struct.pack('>HH', r['id'], len(raw))+raw)
    payload = b''.join(blocks)
    size_excludes_magic = struct.unpack_from('>I', original, 8)[0] == len(original)-4
    result = struct.pack('>4sIIH', b'XSTR', 1, 14+len(payload)-(4 if size_excludes_magic else 0), len(rows))+payload
    read_xstr(result)
    return result


class Xdbf:
    def __init__(self, data):
        if not isinstance(data, bytes) or not 24 <= len(data) <= MAX_BYTES:
            raise ValueError('invalid XDBF size/type')
        magic, version, capacity, used, free_capacity, free_used = struct.unpack_from('>4s5I', data)
        if (magic != b'XDBF' or version != 0x10000 or not 0 < used <= capacity <= 65535
                or not 1 <= free_capacity <= 65535 or free_used != 1):
            raise ValueError('unsupported XDBF header/free-table profile')
        self.base = 24+capacity*18+free_capacity*8
        if self.base > len(data):
            raise ValueError('XDBF tables outside file')
        self.free_offset = 24+capacity*18
        if data[24+used*18:self.free_offset] != bytes((capacity-used)*18):
            raise ValueError('nonzero unused XDBF entries')
        if data[self.free_offset+8:self.base] != bytes((free_capacity-1)*8):
            raise ValueError('nonzero unused XDBF free records')
        if struct.unpack_from('>II', data, self.free_offset) != (len(data)-self.base, 0):
            raise ValueError('unsupported nonterminal XDBF free record')
        self.data, self.entries, identities = data, [], set()
        for i in range(used):
            section, identity, offset, size = struct.unpack_from('>HQII', data, 24+i*18)
            if section not in (1, 2, 3) or not size or offset+size > len(data)-self.base:
                raise ValueError('invalid XDBF entry range/section')
            key = (section, identity)
            if key in identities:
                raise ValueError('duplicate XDBF entry')
            identities.add(key)
            payload = data[self.base+offset:self.base+offset+size]
            if section == 3:
                read_xstr(payload)
            self.entries.append(dict(section=section, id=identity, offset=offset, size=size,
                                     payload=payload, table_offset=24+i*18))
        end = 0
        for e in sorted(self.entries, key=lambda e:e['offset']):
            if e['offset'] != end:
                raise ValueError('XDBF overlap or unsupported gap')
            end += e['size']
        if end != len(data)-self.base:
            raise ValueError('unparsed XDBF content tail')

    def strings(self):
        return {e['id']:read_xstr(e['payload']) for e in self.entries if e['section']==3}

    def replace_entries(self, replacements):
        keys = {(e['section'],e['id']) for e in self.entries}
        if set(replacements)-keys:
            raise ValueError('unknown XDBF replacement entry')
        header, content = bytearray(self.data[:self.base]), bytearray()
        for e in sorted(self.entries, key=lambda e:e['offset']):
            payload = replacements.get((e['section'],e['id']),e['payload'])
            if not isinstance(payload, bytes) or not payload:
                raise ValueError('invalid XDBF replacement payload')
            struct.pack_into('>II',header,e['table_offset']+10,len(content),len(payload))
            content.extend(payload)
        struct.pack_into('>II',header,self.free_offset,len(content),0)
        output = bytes(header+content)
        Xdbf(output)
        return output


def rebuild(data, plan):
    if (not isinstance(plan,dict) or set(plan)!={'schema_version','kind','input_sha256','entries'}
            or type(plan.get('schema_version')) is not int or plan.get('schema_version')!=1
            or plan.get('kind')!='xdbf-string-localization'
            or plan.get('input_sha256') != sha(data) or not isinstance(plan.get('entries'),list)):
        raise ValueError('XDBF localization identity/schema mismatch')
    db = Xdbf(data)
    tables = {(language,r['id']):r['text'] for language,rows in db.strings().items() for r in rows}
    replacements, seen = {}, set()
    for e in plan['entries']:
        if (not isinstance(e,dict) or set(e)!={'language','id','source_sha256','translation'}
                or type(e['language']) is not int or type(e['id']) is not int
                or not isinstance(e['source_sha256'],str)
                or re.fullmatch('[0-9a-f]{64}',e['source_sha256']) is None
                or not isinstance(e['translation'],str)):
            raise ValueError('invalid XDBF localization entry')
        key = (e['language'],e['id'])
        if key in seen or key not in tables:
            raise ValueError('duplicate or unknown XDBF string')
        source, target = tables[key], e['translation']
        if sha(source.encode()) != e['source_sha256']:
            raise ValueError('XDBF source string SHA256 mismatch')
        if not source.strip() or not target.strip() or any(c in target for c in '\0\r\n') or token_errors(source,target):
            raise ValueError('XDBF blank text or protected tokens changed')
        seen.add(key)
        replacements.setdefault(e['language'],{})[e['id']] = target
    payloads = {(3,e['id']):write_xstr(e['payload'],replacements[e['id']])
                for e in db.entries if e['section']==3 and e['id'] in replacements}
    output = db.replace_entries(payloads)
    check = Xdbf(output)
    before = {(e['section'],e['id']):e['payload'] for e in db.entries}
    after = {(e['section'],e['id']):e['payload'] for e in check.entries}
    if before.keys()!=after.keys() or any(after[k]!=payloads.get(k,v) for k,v in before.items()):
        raise ValueError('XDBF re-extraction mismatch')
    inverse = dict(plan,input_sha256=sha(output),entries=[dict(e,
        source_sha256=sha(e['translation'].encode()),translation=tables[(e['language'],e['id'])])
        for e in plan['entries']])
    # Inverse is a structural rebuild, not a retained-original copy.
    inverse_payloads = {(3,e['id']):write_xstr(e['payload'],
        {r['id']:tables[(r['language'],r['id'])] for r in plan['entries'] if r['language']==e['id']})
        for e in check.entries if (3,e['id']) in payloads and e['section']==3}
    if check.replace_entries(inverse_payloads) != data:
        raise ValueError('XDBF exact inverse reconstruction failed')
    return output, dict(source_sha256=sha(data),candidate_sha256=sha(output),
        total_strings=len(tables),changed_strings=len(seen),
        preserved_entry_payloads=len(before)-len(payloads),inverse_byte_identical=True,
        inverse_plan=inverse)
