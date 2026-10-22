"""Explicit source/target-locked atomic fragment groups, not global empty-text permission."""
import hashlib
H=lambda s:hashlib.sha256(s.encode()).hexdigest()
def whitespace_suffixes(plan,review):
    edits={e['id']:e for e in plan['entries']};kinds={e['id']:e['text_kind'] for e in review['entries']};allowed=set();seen=set()
    groups=review.get('fragment_groups',[])
    if not isinstance(groups,list) or len(groups)>64:raise ValueError('fragment group bound')
    for g in groups:
        if g.get('kind')!='source-locked-atomic-fragments' or not isinstance(g.get('reason'),str) or not g['reason'].strip():raise ValueError('fragment group classification required')
        members=g.get('members');joins=g.get('joins');evidence=g.get('evidence')
        if not isinstance(members,list) or not 2<=len(members)<=256 or not isinstance(joins,list) or not 1<=len(joins)<=256 or not isinstance(evidence,list) or not evidence:raise ValueError('fragment group members/joins/evidence required')
        roles={}
        for m in members:
            i=m['id'];e=edits.get(i)
            if i in seen or e is None or kinds.get(i)!='fragment' or m.get('role') not in ['prefix','suffix'] or m.get('source_sha256')!=e['source_sha256'] or m.get('translation_sha256')!=H(e['translation']):raise ValueError('fragment member lock/role mismatch')
            seen.add(i);roles[i]=m['role']
            if not e['translation'].strip():
                if e['translation']!=' ' or m['role']!='suffix':raise ValueError('only an explicit single-space suffix is supported')
                allowed.add(i)
        used=set()
        for j in joins:
            if set(j)!=set(['prefix','suffix']) or roles.get(j['prefix'])!='prefix' or roles.get(j['suffix'])!='suffix':raise ValueError('fragment join role mismatch')
            used.update(j.values())
        if used!=set(roles):raise ValueError('fragment group includes unjoined member')
    return allowed
