"""Read-only, source-locked script/prefix screening of effective text resources.

Classification is not translation or runtime acceptance. Locale ranges, literal
rules and dated field-level dispositions are supplied separately from this tool.
The optional resolution gate covers findings in the selected text views only.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

from .coalesced import extract_entries, parse, serialize
from .font_binding_plan import confined_path
from .subtitle_text import parse as subtitle_parse
from .verify_resource_phase import unique


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def locked(path, expected, limit=64*1024*1024):
    if not isinstance(expected, str) or not re.fullmatch('[0-9a-f]{64}', expected):
        raise ValueError('Expected lowercase SHA256')
    with Path(path).open('rb') as stream:
        raw = stream.read(limit+1)
    if not raw or len(raw)>limit or digest(raw)!=expected:
        raise ValueError('Input size/SHA256 mismatch: '+str(path))
    return raw


def observation_metadata(value):
    """Validate a human observation reference, not its image or asserted meaning.

    External captures may have moved since review. Their path and digest remain
    checkable provenance; this reader neither opens them nor interprets pixels.
    """
    if (not isinstance(value,dict)
            or set(value)!={'kind','source_path','sha256'}
            or value.get('kind')!='user-supplied-screenshot'
            or not isinstance(value.get('source_path'),str)
            or not value['source_path'].strip() or len(value['source_path'])>4096
            or any(ord(c)<32 for c in value['source_path'])
            or not isinstance(value.get('sha256'),str)
            or not re.fullmatch('[0-9a-f]{64}',value['sha256'])):
        raise ValueError('Invalid runtime observation metadata')
    return value


def policy_tables(policy):
    if not isinstance(policy,dict) or type(policy.get('schema_version')) is not int or policy['schema_version']!=1 or policy.get('kind')!='text-residual-screen-policy':
        raise ValueError('Unsupported screening policy')
    ranges = policy.get('script_ranges')
    if not isinstance(ranges, dict) or not 1<=len(ranges)<=16:
        raise ValueError('Bounded script ranges required')
    for name, spans in ranges.items():
        if not isinstance(name,str) or not isinstance(spans,list) or not 1<=len(spans)<=16:
            raise ValueError('Invalid script range')
        for span in spans:
            if (not isinstance(span,list) or len(span)!=2
                    or any(type(n) is not int for n in span)
                    or not 0<=span[0]<=span[1]<=0x10ffff):
                raise ValueError('Invalid Unicode interval')
    decisions = {}
    known = policy.get('known_dispositions', [])
    rules = policy.get('prefix_rules', [])
    if not isinstance(known,list) or len(known)>4096 or not isinstance(rules,list) or len(rules)>32:
        raise ValueError('Policy count bound')
    for row in known:
        discs=row.get('discs')
        if (not isinstance(discs,list) or not discs or len(set(discs))!=len(discs)
                or any(type(d) is not int or not 1<=d<=256 for d in discs)
                or not re.fullmatch('[0-9a-f]{64}',row['value_sha256'])
                or row['status'] not in ('excluded','pending','confirmed-player-gap')
                or not row.get('classification') or not row.get('evidence')):
            raise ValueError('Duplicate/incomplete field disposition')
        if 'runtime_observation' in row:
            observation_metadata(row['runtime_observation'])
        elif row['status']=='confirmed-player-gap':
            raise ValueError('Confirmed player gap requires runtime observation metadata')
        if 'runtime_display_observed' in row:
            if (type(row['runtime_display_observed']) is not bool
                    or row['runtime_display_observed']!=bool(row.get('runtime_observation'))):
                raise ValueError('Runtime display flag conflicts with observation metadata')
        for disc in discs:
            key=(row['resource'],row['id'],disc)
            if key in decisions:raise ValueError('Duplicate field/disc disposition')
            decisions[key]=row
    rule_ids = set()
    for rule in rules:
        if (not isinstance(rule,dict) or not isinstance(rule.get('literal'),str)
                or not 1<=len(rule['literal'])<=80 or rule.get('id') in rule_ids
                or not rule.get('id') or not rule.get('document_suffix')
                or type(rule.get('case_sensitive')) is not bool):
            raise ValueError('Invalid/duplicate prefix rule')
        rule_ids.add(rule['id'])
    return ranges, decisions, rules


def prefix_matches(value, rule):
    value=value.lstrip();literal=rule['literal']
    if not rule['case_sensitive']:
        value=value.casefold();literal=literal.casefold()
    if not value.startswith(literal):return False
    rest=value[len(literal):]
    # A plain sentence/prompt prefix, never a longer machine identifier.
    return not rest or not (rest[0].isascii() and (rest[0].isalnum() or rest[0]=='_'))


def paired_rows(before, after, resource, kind):
    if kind=='coalesced':
        old,new=parse(before),parse(after)
        if serialize(old)!=before or serialize(new)!=after:
            raise ValueError('Text container roundtrip failed')
        a,b=extract_entries(old,resource),extract_entries(new,resource)
        if [r['id'] for r in a]!=[r['id'] for r in b]:
            raise ValueError('Text field identities changed')
        return [(x,y['source']) for x,y in zip(a,b,strict=True)],sum(f.content.encoding=='opaque-8bit' for f in new)
    if kind=='timed-cues':
        _,old=subtitle_parse(before);_,new=subtitle_parse(after)
        if [(m[2],m[6],m[3]) for m in old]!=[(m[2],m[6],m[3]) for m in new]:
            raise ValueError('Cue timing/class identities changed')
        return [(dict(id=resource+':'+x[2]+':'+x[6],source=x[4],
                      context=resource+' ['+x[2]+','+x[6]+']',embedded_path=''),y[4])
                for x,y in zip(old,new,strict=True)],0
    raise ValueError('Unsupported text resource kind')


def screen(inputs, policy, project_root):
    ranges,decisions,rules=policy_tables(policy)
    if not isinstance(inputs,dict):raise ValueError('Expected effective text input object')
    definitions=inputs.get('resources')
    if (type(inputs.get('schema_version')) is not int or inputs['schema_version']!=1 or inputs.get('kind')!='effective-text-screen-inputs'
            or not isinstance(definitions,list) or not 1<=len(definitions)<=256):
        raise ValueError('Expected bounded effective text inputs')
    root=Path(project_root).resolve();snapshots={};seen=set();used=set();resources=[];findings=[];total_bytes=0;total_fields=0
    for definition in definitions:
        resource=definition['resource'];role=definition['role'];discs=definition['discs']
        if (role not in ('primary','alternate-locale','configuration')
                or not isinstance(discs,list) or not discs or len(set(discs))!=len(discs)
                or any(type(d) is not int or not 1<=d<=256 for d in discs)):
            raise ValueError('Duplicate/invalid resource identity or role')
        memberships={(resource,d) for d in discs}
        if seen & memberships:raise ValueError('Duplicate resource/disc membership')
        seen.update(memberships);data=[]
        for phase in ('original','effective'):
            ref=definition[phase];path=confined_path(root,ref['file']);raw=locked(path,ref['sha256'])
            if path in snapshots and snapshots[path]!=ref['sha256']:
                raise ValueError('Conflicting input identity')
            snapshots[path]=ref['sha256'];data.append(raw)
        total_bytes+=sum(map(len,data))
        if total_bytes>256*1024*1024:raise ValueError('Total text byte bound')
        rows,opaque=paired_rows(*data,resource,definition['kind']);total_fields+=len(rows)
        if len(rows)>100000 or total_fields>256000:
            raise ValueError('Resource screening bound')
        counts=Counter();changed=0
        for original,value in rows:
            changed+=original['source']!=value
            hits=[name for name,spans in ranges.items()
                  if any(lo<=ord(c)<=hi for c in value for lo,hi in spans)]
            counts.update(hits)
            if role!='primary':continue
            identities=[(resource,original['id'],disc) for disc in discs]
            matches=[decisions[key] for key in identities if key in decisions]
            if matches and len(matches)!=len(identities):
                raise ValueError('Partially classified membership; split the disc view')
            decision=matches[0] if matches else None;value_sha=digest(value.encode('utf8'))
            if decision:
                if any(value_sha!=row['value_sha256'] for row in matches):
                    raise ValueError('Field disposition source drift: '+original['id'])
                if any((row['classification'],row['status'],row['evidence'],row.get('runtime_observation'))!=
                       (decision['classification'],decision['status'],decision['evidence'],decision.get('runtime_observation')) for row in matches):
                    raise ValueError('Conflicting grouped dispositions; split the disc view')
                used.update(identities)
            matched=[r['id'] for r in rules
                     if original.get('embedded_path','').endswith(r['document_suffix']) and prefix_matches(value,r)]
            observation=decision.get('runtime_observation') if decision else None
            player_gap=bool(decision and decision['status']=='confirmed-player-gap')
            if hits or matched or decision is not None:
                findings.append(dict(resource=resource,id=original['id'],discs=discs,
                    context=original.get('context',''),value_sha256=value_sha,
                    original_value_sha256=digest(original['source'].encode('utf8')),
                    value_excerpt=value[:120],script_hits=hits,prefix_rules=matched,
                    disposition=decision,status='confirmed-player-gap' if player_gap else 'confirmed-resource-gap' if matched else decision['status'] if decision else 'unclassified',
                    runtime_display_observed=bool(observation),runtime_observation=observation,
                    runtime_observation_semantics_verified=False))
        resources.append(dict(resource=resource,kind=definition['kind'],role=role,discs=discs,
            original_sha256=digest(data[0]),effective_sha256=digest(data[1]),entries=len(rows),
            changed_fields=changed,script_fields=dict(counts),opaque_documents=opaque))
    if set(decisions)!=used:
        raise ValueError('Disposition field absent from current primary view')
    for path,expected in snapshots.items():locked(path,expected)
    summary=dict(primary_fields=sum(r['entries'] for r in resources if r['role']=='primary' and r['kind']=='coalesced'),
        subtitle_cues=sum(r['entries'] for r in resources if r['role']=='primary' and r['kind']=='timed-cues'),
        script_residuals=sum(bool(r['script_hits']) for r in findings),
        classified_residuals=sum(bool(r['script_hits']) and r['status']!='unclassified' for r in findings),
        prefix_gaps=sum(bool(r['prefix_rules']) for r in findings),
        unclassified=sum(r['status']=='unclassified' for r in findings),
        pending=sum(r['status']=='pending' for r in findings),
        excluded=sum(r['status']=='excluded' for r in findings),
        confirmed_player_gaps=sum(r['status']=='confirmed-player-gap' for r in findings),
        unresolved=sum(r['status']!='excluded' for r in findings),
        opaque_primary_documents=sum(r['opaque_documents'] for r in resources if r['role']=='primary'))
    return dict(schema_version=1,kind='effective-text-residual-screen',summary=summary,
        resources=resources,findings=findings,source_files_unchanged=True,
        complete_language_coverage_claimed=False,game_started=False,game_rendering_verified=False)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('inputs','policy','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--inputs-sha256',required=True);parser.add_argument('--policy-sha256',required=True)
    parser.add_argument('--project-root',type=Path,default=Path('.'));parser.add_argument('--require-classified',action='store_true')
    parser.add_argument('--require-resolved',action='store_true',
        help='Fail for unresolved findings or opaque primary documents in the selected text views')
    args=parser.parse_args(argv)
    try:
        if args.output.exists() or args.output.resolve() in (args.inputs.resolve(),args.policy.resolve()):
            raise ValueError('New disjoint output required')
        a=locked(args.inputs,args.inputs_sha256,4*1024*1024);b=locked(args.policy,args.policy_sha256,4*1024*1024)
        result=screen(json.loads(a,object_pairs_hook=unique),json.loads(b,object_pairs_hook=unique),args.project_root)
        locked(args.inputs,args.inputs_sha256,4*1024*1024);locked(args.policy,args.policy_sha256,4*1024*1024)
        result.update(inputs_sha256=args.inputs_sha256,policy_sha256=args.policy_sha256)
        raw=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode();args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open('xb') as f:f.write(raw)
        if args.output.read_bytes()!=raw:raise ValueError('Report reopening mismatch')
        s=result['summary']
        unresolved=bool(s['unresolved'] or s['opaque_primary_documents'])
        verdict=('UNRESOLVED' if unresolved else 'RESOLVED') if args.require_resolved else ('UNCLASSIFIED' if s['unclassified'] else 'CLASSIFIED')
        print(' '.join(k.upper()+'='+str(v) for k,v in s.items())+' RESULT='+verdict)
        return int((args.require_classified and bool(s['unclassified']))
                   or (args.require_resolved and unresolved))
    except (ValueError,OSError,KeyError,TypeError,UnicodeError) as error:
        print('ERROR: '+str(error),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
