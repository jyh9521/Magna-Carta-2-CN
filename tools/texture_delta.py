"""Select complete affected texture packages, never partial consumer atlases."""
from __future__ import annotations

import copy
from .build_texture_overlay import select_sources
from .texture_overlay import layer_ids
from .build_font_route_probe import encoded
from .verify_resource_phase import sha


def select_delta(before, after, disc):
    """Return a normal overlay plan containing only affected package sources.

    All layers of each selected package are retained. This prevents a small
    alignment revision from reverting other localized textures in that package.
    The complete after-plan remains the authoritative clean-build input.
    """
    def labels(plan):
        rows = plan['labels']; result = {r['id']: r for r in rows}
        if len(result) != len(rows): raise ValueError('duplicate label IDs')
        return result
    old = labels(before); new = labels(after)
    changed = {key for key in set(old) | set(new) if old.get(key) != new.get(key)}
    globals_changed = ({k: v for k, v in before.items() if k not in ('labels', 'sources')}
                       != {k: v for k, v in after.items() if k not in ('labels', 'sources')})
    old_sources = select_sources(before['sources'], disc)
    new_sources = select_sources(after['sources'], disc)
    prior = {s['path']: s for s in old_sources}
    current = {s['path']: s for s in new_sources}
    if len(prior) != len(old_sources) or len(current) != len(new_sources):
        raise ValueError('duplicate source paths')
    if set(prior) - set(current):
        raise ValueError('removed packages require an explicit original-resource restore')
    selected = []; needed = set()
    for source in new_sources:
        ids = {lid for edit in source['textures'] for lid in layer_ids(edit)}
        if ids - set(new): raise ValueError('source references missing labels')
        if globals_changed or source != prior.get(source['path']) or changed.intersection(ids):
            selected.append(source); needed.update(ids)
    if not selected: raise ValueError('no changed texture sources for disc')
    result = copy.deepcopy(after)
    result['sources'] = copy.deepcopy(selected)
    result['labels'] = [copy.deepcopy(r) for r in after['labels'] if r['id'] in needed]
    proof = dict(disc=disc, before_plan_canonical_sha256=sha(encoded(before)),
        after_plan_canonical_sha256=sha(encoded(after)), subset_plan_canonical_sha256=sha(encoded(result)),
        changed_labels=sorted(changed), globals_changed=globals_changed,
        selected_packages=[s['path'] for s in selected],
        retained_package_layers=len(needed), unchanged_packages=len(new_sources)-len(selected))
    return result, proof
