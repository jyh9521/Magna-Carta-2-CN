"""Locate every selected UI consumer in a complete streamed installer disc view."""
import argparse
import json
from pathlib import Path
import re

from .audit_item_spacing import installer_item_sources
from .build_font_supplement import context
from .patch_tagged_fields import digest
from .ue3_package import LzxDecoder


def scan(sources, decoder, spec):
    pattern = re.compile(spec['pattern'], re.IGNORECASE)
    found = {}
    seen = set()
    packages = 0
    for name, raw in sources:
        if name in seen:
            raise ValueError('duplicate resident package')
        seen.add(name)
        packages += 1
        c = context(raw, decoder)
        matches = [e['path'] for e in c['tables']['exports'] if pattern.search(e['path'])]
        if matches:
            found[name] = dict(sha256=digest(raw), objects=matches)
    counts = {p: len(r['objects']) for p, r in found.items()}
    return dict(passed=counts == spec['expected'], native_packages=packages,
                matched_counts=counts, packages=found, game_started=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('recipe', 'plan', 'lzx-library', 'output'):
        p.add_argument('--' + key, type=Path, required=True)
    p.add_argument('--recipe-sha256', required=True)
    p.add_argument('--disc', type=int, choices=(1, 2), required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError('new output required')
    raw_plan = a.plan.read_bytes()
    spec = json.loads(raw_plan)['resident_ui']
    result = scan(installer_item_sources(a.recipe, a.recipe_sha256, a.disc), LzxDecoder(a.lzx_library), spec)
    result['passed'] = result['passed'] and result['native_packages'] == spec['native_counts'][str(a.disc)]
    result.update(disc=a.disc, plan_sha256=digest(raw_plan), recipe_sha256=a.recipe_sha256)
    raw = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode()
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_bytes(raw)
    if a.output.read_bytes() != raw or a.plan.read_bytes() != raw_plan:
        raise ValueError('readback mismatch')
    print(json.dumps({k: v for k, v in result.items() if k != 'packages'}))
    return int(not result['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
