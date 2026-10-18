"""Locale-neutral version/namespace guards shared by font bundle builders."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
try:
    from .ue3_package import FormatError
except ImportError:
    from ue3_package import FormatError


def digest(data):
    return hashlib.sha256(data).hexdigest()


def validate_binding_plan(plan):
    if not isinstance(plan,dict) or type(plan.get('schema_version')) is not int or plan.get('schema_version') != 1 or plan.get('game_rendering_verified') is not False:
        raise FormatError('binding plan requires schema1 and game_rendering_verified=false')
    sources = plan.get('sources')
    count = plan.get('required_source_count')
    if type(count) is not int or not 1 <= count <= 32 or not isinstance(sources,list) or len(sources) != count:
        raise FormatError('binding source count mismatch')
    labels, paths = set(), set()
    for source in sources:
        if not isinstance(source,dict):
            raise FormatError('source must be an object')
        label = source.get('label','')
        if (not isinstance(label,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,47}',label)
                or label.casefold() in {'con','prn','aux','nul',*(f'com{i}' for i in range(1,10)),*(f'lpt{i}' for i in range(1,10))}
                or label.casefold() in labels):
            raise FormatError('duplicate or invalid binding source label')
        labels.add(label.casefold())
        path = source.get('path','')
        _relative(path)
        if path.casefold() in paths:
            raise FormatError('duplicate binding source path')
        paths.add(path.casefold())
        _hash(source.get('sha256'))
        if not isinstance(source.get('font_object'),str) or not source['font_object']:
            raise FormatError('font object path required')
    toc = plan.get('toc',{})
    if not isinstance(toc,dict):
        raise FormatError('TOC must be an object')
    _relative(toc.get('path',''));_hash(toc.get('sha256'))
    if toc['path'].casefold() in paths:
        raise FormatError('TOC cannot alias a source package')
    _hash(plan.get('expected_semantic_sha256'))
    if not isinstance(plan.get('expected_namespace_guid'),str) or not re.fullmatch('[0-9a-f]{32}',plan.get('expected_namespace_guid','')) or plan['expected_namespace_guid'] == '0'*32:
        raise FormatError('nonzero namespace GUID required')
    if not isinstance(plan.get('canonical_font_path'),str) or not plan['canonical_font_path']:
        raise FormatError('canonical font identity required')
    return sources


def _hash(value):
    if not isinstance(value,str) or not re.fullmatch('[0-9a-f]{64}',value):
        raise FormatError('expected lowercase SHA256')


def _relative(value):
    if (not isinstance(value,str) or not value or '\\' in value or ':' in value
            or value.startswith('/') or any(p in ('','.','..') for p in value.split('/'))):
        raise FormatError('expected confined slash-separated relative resource path')
    return value


def confined_path(root, relative):
    """Resolve a relative input path without escaping its explicit root."""
    root = Path(root).resolve()
    target = (root / _relative(relative)).resolve()
    if not target.is_relative_to(root):
        raise FormatError('resource path escapes selected input root')
    return target


def _read(root, relative, expected):
    target = confined_path(root,relative)
    data = target.read_bytes()
    if digest(data) != expected:
        raise FormatError('source SHA256 mismatch: '+relative)
    return data, target


def parse_json_object(raw):
    """Reject ambiguous duplicate keys and non-finite constants in metadata."""
    def unique(pairs):
        result = {}
        for key,value in pairs:
            if key in result: raise FormatError('duplicate JSON key: '+key)
            result[key] = value
        return result
    def invalid_constant(value):
        raise FormatError('non-finite JSON constant: '+value)
    value = json.loads(raw.decode('utf-8-sig'),object_pairs_hook=unique,parse_constant=invalid_constant)
    if not isinstance(value,dict): raise FormatError('JSON payload must be an object')
    return value


def read_locked_json(root, reference):
    """Read a confined, exact-hash JSON object and retain its actual bytes/path."""
    if not isinstance(reference, dict):
        raise FormatError('locked JSON reference must be an object')
    _relative(reference.get('path')); _hash(reference.get('sha256'))
    raw, path = _read(Path(root).resolve(),reference['path'],reference['sha256'])
    value = parse_json_object(raw)
    return value, path, raw
