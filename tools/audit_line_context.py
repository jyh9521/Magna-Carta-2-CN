"""Source/draft-locked context observations, never runtime layout approval."""
from pathlib import Path
import argparse,json,hashlib,re
from .build_coalesced import rebuild,resolve_changes
from .coalesced import parse,extract_entries
from .font_binding_plan import parse_json_object
from .validate_catalog import TOKEN


def digest(b):return hashlib.sha256(b).hexdigest()
def canonical(p):return digest(json.dumps(p,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode())
def atoms(text):
    # Escaped line breaks and style markers are already protected by rebuild;
    # their Latin bytes must not hide an immediately following button literal.
    text=TOKEN.sub(' ',text)
    return re.findall(r'(?<![A-Za-z0-9_])(?:LT|RT|LB|RB|A|B|X|Y)(?![A-Za-z0-9_])|[0-9]+(?:\.[0-9]+)?',text)
def lock(row,translation):
    return dict(id=row['id'],document=row['embedded_path'],section=row['section'],key=row['key'],occurrence=row['occurrence'],
                source_sha256=digest(row['source'].encode()),translation_sha256=digest(translation.encode()))


def audit(data,plan,profile=None):
    rebuild(data,plan);resolved=resolve_changes(data,plan)
    rows=extract_entries(parse(data),plan['resource']);by_id={r['id']:r for r in rows}
    changes={e['id']:e for e in resolved['entries']};selected={};protected=[]
    if profile is not None:
        if (type(profile.get('schema_version')) is not int or profile['schema_version']!=1
                or profile.get('kind')!='source-locked-context-observations' or profile.get('resource')!=plan['resource']
                or profile.get('input_sha256')!=digest(data) or profile.get('plan_canonical_sha256')!=canonical(plan)
                or profile.get('human_finalized') is not False or profile.get('runtime_layout_approved') is not False):
            raise ValueError('context profile identity or approval state mismatch')
        scopes=profile.get('scopes')
        if not isinstance(scopes,list) or not 1<=len(scopes)<=32:raise ValueError('context scope bound')
        for scope in scopes:
            if (not isinstance(scope.get('reason'),str) or not scope['reason'].strip()
                    or type(scope.get('complete_section')) is not bool):raise ValueError('invalid context scope')
            keys=scope.get('keys')
            if scope['complete_section']:
                if keys is not None:raise ValueError('complete section cannot have filtered keys')
            elif not isinstance(keys,list) or not keys or len(set(keys))!=len(keys):raise ValueError('invalid context key set')
            hits=[r for r in rows if (r['embedded_path'],r['section'])==(scope['document'],scope['section'])
                  and (keys is None or r['key'] in keys)]
            if not hits or (keys is not None and set(keys)!={r['key'] for r in hits}):raise ValueError('empty or stale context scope')
            for r in hits:
                if r['id'] in selected:raise ValueError('overlapping context scopes')
                if r['id'] not in changes:raise ValueError('context scope includes unplanned original value')
                selected[r['id']]=scope['reason']
        if not 1<=len(selected)<=1000:raise ValueError('context cohort bound')
        actual=[lock(r,changes[r['id']]['translation']) for r in rows if r['id'] in selected]
        expected=profile.get('entries')
        if not isinstance(expected,list) or expected!=actual:raise ValueError('context cohort membership/order/hash mismatch')
        protected=profile.get('protected_breaks')
        if not isinstance(protected,list):raise ValueError('protected break evidence missing')
        seen=set()
        for p in protected:
            i=p['id']
            if i in seen or i not in selected or not isinstance(p.get('reason'),str) or not p['reason'].strip():raise ValueError('invalid protected break evidence')
            seen.add(i);e=changes[i];a=TOKEN.findall(e['source']);b=TOKEN.findall(e['translation'])
            if not a.count('\\n') or a!=b:raise ValueError('protected functional break not preserved')
    context=[];policy_rows=[];groups={}
    for r in rows:groups.setdefault((r['embedded_path'],r['section']),[]).append(r['id'])
    neighbors={i:(ids[n-1] if n else None,ids[n+1] if n+1<len(ids) else None)
               for ids in groups.values() for n,i in enumerate(ids)}
    for r in rows:
        i=r['id'];e=changes.get(i)
        if e is None:continue
        if i in selected:
            if atoms(e['source'])!=atoms(e['translation']):raise ValueError('selected context key/numeric atom mismatch')
            context.append(dict(**lock(r,e['translation']),previous_id=neighbors[i][0],next_id=neighbors[i][1],
                                reason=selected[i],disposition='context-observed-draft-retained'))
        if 'line_break_policy' in e:
            policy_rows.append(dict(**lock(r,e['translation']),line_break_policy=e['line_break_policy'],
                                    context_observed=i in selected,runtime_layout_approved=False))
    observed=sum(p['context_observed'] for p in policy_rows)
    return dict(schema_version=1,kind='read-only-line-context-audit',input_sha256=digest(data),plan_canonical_sha256=canonical(plan),
                translated_entries=len(changes),policy_entries=len(policy_rows),context_observed_policies=observed,
                pending_context_policies=len(policy_rows)-observed,pending_runtime_layout_policies=len(policy_rows),
                context_entries=len(context),context=context,policies=policy_rows,protected_breaks=protected,
                translation_edits=0,human_finalized=False,runtime_layout_approved=False,game_rendering_verified=False)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('source','plan','output'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--profile',type=Path);a=p.parse_args(argv)
    try:
        if a.output.exists() or a.output.is_symlink():raise ValueError('context output must be new')
        paths=[a.source,a.plan]+([a.profile] if a.profile else []);before=[x.read_bytes() for x in paths]
        result=audit(before[0],parse_json_object(before[1]),parse_json_object(before[2]) if a.profile else None)
        if any(x.read_bytes()!=b for x,b in zip(paths,before)):raise ValueError('context input changed')
        data=(json.dumps(result,ensure_ascii=True,sort_keys=True,indent=2)+'\n').encode();a.output.parent.mkdir(parents=True,exist_ok=True)
        with a.output.open('xb') as f:f.write(data)
        if a.output.read_bytes()!=data:raise ValueError('context output reopening mismatch')
        print(json.dumps({k:result[k] for k in ('context_entries','context_observed_policies','pending_context_policies','pending_runtime_layout_policies','translation_edits')},sort_keys=True));return 0
    except (OSError,ValueError,KeyError,TypeError) as e:print('ERROR: '+str(e));return 2


if __name__=='__main__':raise SystemExit(main())
