"""Build/replay complete affected packages from two SHA-locked overlay plans."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from . import build_texture_overlay as overlay
from .build_font_route_probe import encoded
from .texture_delta import select_delta
from .ue3_package import LzxDecoder
from .verify_resource_phase import hash_value, sha, unique


def locked_plan(path, expected):
    path = Path(path).resolve()
    if path.stat().st_size > 16*1024*1024: raise ValueError('overlay plan exceeds bound')
    raw = path.read_bytes()
    if sha(raw) != hash_value(expected): raise ValueError('overlay plan SHA256 mismatch')
    return json.loads(raw, object_pairs_hook=unique), raw


def run(before_path, before_sha, after_path, after_sha, root, output, decoder, disc, verify=False):
    root = Path(root).resolve(); output = Path(output).resolve()
    if not output.is_relative_to(root) or output == root:
        raise ValueError('delta output must stay inside project')
    before, before_raw = locked_plan(before_path, before_sha)
    after, after_raw = locked_plan(after_path, after_sha)
    subset, proof = select_delta(before, after, disc)
    proof['before_plan_file_sha256'] = before_sha
    proof['after_plan_file_sha256'] = after_sha
    if verify:
        if (output/'plan.json').read_bytes() != encoded(subset):
            raise ValueError('selected plan changed')
        if (output/'selection.json').read_bytes() != encoded(proof):
            raise ValueError('selection proof changed')
        manifest = overlay.verify(subset, root, output/'bundle', decoder, disc)
    else:
        output.mkdir(parents=False, exist_ok=False)
        manifest = overlay.build(subset, root, output/'bundle', decoder, disc)
        (output/'plan.json').write_bytes(encoded(subset))
        (output/'selection.json').write_bytes(encoded(proof))
        if (output/'plan.json').read_bytes() != encoded(subset): raise ValueError('plan reopening mismatch')
        if (output/'selection.json').read_bytes() != encoded(proof): raise ValueError('proof reopening mismatch')
    if Path(before_path).read_bytes() != before_raw or Path(after_path).read_bytes() != after_raw:
        raise ValueError('overlay plan changed during operation')
    return dict(status='PASS', disc=disc, resources=len(manifest['resources']),
                labels=manifest['labels'], independently_replayed=verify,
                game_rendering_verified=False)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--previous-plan', type=Path, required=True)
    p.add_argument('--previous-plan-sha256', required=True)
    p.add_argument('--plan', type=Path, required=True)
    p.add_argument('--plan-sha256', required=True)
    p.add_argument('--project-root', type=Path, default=Path('.'))
    p.add_argument('--disc', type=int, choices=(1, 2), required=True)
    p.add_argument('--lzx-library', type=Path, required=True)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--output-dir', type=Path)
    g.add_argument('--verify-root', type=Path)
    a = p.parse_args(argv)
    try:
        result = run(a.previous_plan, a.previous_plan_sha256, a.plan, a.plan_sha256,
            a.project_root, a.output_dir or a.verify_root, LzxDecoder(a.lzx_library),
            a.disc, bool(a.verify_root))
        print(json.dumps(result, sort_keys=True)); return 0
    except (ValueError, OSError, KeyError, TypeError, ImportError) as error:
        print('ERROR: '+str(error)); return 2


if __name__ == '__main__': raise SystemExit(main())
