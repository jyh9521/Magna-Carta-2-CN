"""Compose source-locked UI ink, scalar and text changes into a sparse copy.

No deployment, ISO generation or game execution. Donors only supply declared
native texture blocks; they never replace a current package wholesale.
"""
import argparse
import json
from pathlib import Path

from .build_font_supplement import context
from .build_texture_overlay import prepare
from .build_texture_region_update import transfer
from .build_coalesced import rebuild, resolve_changes
from .font_binding_plan import confined_path
from .patch_tagged_fields import digest, patch
from .runtime_envelope import ALIGNMENT, require_raw_envelope
from .ue3_package import LzxDecoder
from .ui_ink_revision import clean_alpha, fit_right_ink


def build(profile, expected_sha, project, source, output, decoder):
    project, source, output = map(lambda p: Path(p).resolve(), (project, source, output))
    profile = Path(profile).resolve()
    raw = profile.read_bytes()
    if digest(raw) != expected_sha:
        raise ValueError('revision profile SHA256 mismatch')
    plan = json.loads(raw)
    if plan.get('schema_version') != 1 or plan.get('kind') != 'ui-ink-revision':
        raise ValueError('unsupported ink revision')
    if type(plan.get('disc')) is not int or plan['disc'] not in (1, 2):
        raise ValueError('explicit supported disc required')
    if not isinstance(plan.get('sources'), list) or not 1 <= len(plan['sources']) <= 128:
        raise ValueError('bounded sparse source set required')
    if output.exists() or output.is_relative_to(source) or source.is_relative_to(output):
        raise ValueError('new disjoint output required')
    originals, files, snapshots = {}, {}, []
    seen = set()
    for row in plan['sources']:
        relative = row['resource']
        if relative.casefold() in seen or not relative.lower().endswith(('.xxx', '.int')):
            raise ValueError('duplicate or unsupported source resource')
        seen.add(relative.casefold())
        data = confined_path(source, relative).read_bytes()
        if digest(data) != row['sha256']:
            raise ValueError('source resource SHA256 mismatch: ' + relative)
        originals[relative] = files[relative] = data
    for group in ('transfers', 'alpha_filters', 'font_metrics', 'field_plans'):
        if not isinstance(plan.get(group), list) or len(plan[group]) > 256:
            raise ValueError('bounded operation list required')
        if any(item['resource'] not in files for item in plan[group]):
            raise ValueError('operation references an undeclared source')
    enrollments = plan.get('enrollments', [])
    if len(enrollments) != len(set(enrollments)) or any(r not in files for r in enrollments):
        raise ValueError('invalid original enrollment')

    def load(ref):
        path = confined_path(project, ref['path'])
        data = path.read_bytes()
        if digest(data) != ref['sha256']:
            raise ValueError('dependency SHA256 mismatch')
        snapshots.append((path, data))
        return json.loads(data)

    overlay = load(plan['overlay'])
    donors, donor_manifest, donor_inputs = prepare(overlay, project, decoder, plan['disc'])
    proofs = []
    for item in plan['transfers']:
        r = item['resource']
        files[r], proof, _ = transfer(files[r], digest(files[r]), item['object'],
            donors['candidate/' + r], item['object'], item['rectangles'], decoder)
        proofs.append(dict(kind='native-texture-transfer', resource=r, **proof))
    for item in plan['alpha_filters']:
        r = item['resource']
        files[r], proof = clean_alpha(files[r], item['object'], item['rectangles'],
                                      item['rgb_ceiling'], item['max_retained_delta'])
        proofs.append(dict(kind='native-alpha-cleanup', resource=r, object_path=item['object'], **proof))
    for item in plan['font_metrics']:
        r = item['resource']
        files[r], proof = fit_right_ink(files[r], item['object'], originals[item['reference_resource']],
            item['reference_object'], item['codepoints'], item['right_padding'], item['shadow_alpha'])
        proofs.append(dict(kind='native-optical-metrics', resource=r, **proof))
    for item in plan['field_plans']:
        r = item['resource']
        fields = load(item['plan'])
        before = files[r]
        files[r], proof = patch(before, context(before, None), fields)
        restored, _ = patch(files[r], context(files[r], None), fields, reverse=True)
        if restored != before:
            raise ValueError('scalar inverse mismatch')
        proofs.append(dict(kind='scalar-fields', resource=r, **proof))
    for ref in plan['text_plans']:
        text = load(ref)
        r = text['resource']
        files[r] = rebuild(files[r], resolve_changes(files[r], text))
    resources = []
    for relative, data in sorted(files.items()):
        if data == originals[relative]:
            continue
        if relative.lower().endswith('.xxx'):
            data += bytes((-len(data)) % ALIGNMENT)
            require_raw_envelope(data)
        files[relative] = data
        resources.append(dict(path=relative, file='candidate/' + relative,
                              before_sha256=digest(originals[relative]), sha256=digest(data), size=len(data)))
        if relative in plan.get('enrollments', []):
            resources[-1]['original'] = dict(file='baseline/' + relative,
                size=len(originals[relative]), sha256=digest(originals[relative]))
    if not resources:
        raise ValueError('empty revision')
    for path, data in snapshots:
        if path.read_bytes() != data:
            raise ValueError('dependency changed during build')
    for path, expected in donor_inputs:
        if digest(path.read_bytes()) != expected:
            raise ValueError('donor input changed during build')
    for relative, data in originals.items():
        if confined_path(source, relative).read_bytes() != data:
            raise ValueError('source changed during build')
    if profile.read_bytes() != raw:
        raise ValueError('profile changed during build')
    output.mkdir(parents=True)
    for row in resources:
        for state, data in [('baseline', originals[row['path']]), ('candidate', files[row['path']])]:
            path = confined_path(output, state + '/' + row['path'])
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as stream:
                stream.write(data)
            if path.read_bytes() != data:
                raise ValueError('published resource readback mismatch')
    manifest = dict(schema_version=1, profile_sha256=expected_sha, resources=resources, proofs=proofs,
                    overlay_sha256=donor_manifest['plan_canonical_sha256'], game_started=False,
                    game_rendering_verified=False)
    replacements = dict(schema_version=1, kind='incremental-comparison-replacements',
                        disc=plan['disc'], toc_path=plan['toc_path'], resources=resources)
    for name, obj in [('manifest.json', manifest), ('replacements.json', replacements)]:
        path = output / name
        data = (json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode()
        path.write_bytes(data)
        if path.read_bytes() != data:
            raise ValueError('manifest readback mismatch')
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('profile', 'source-root', 'output', 'lzx-library'):
        p.add_argument('--' + key, required=True, type=Path)
    p.add_argument('--project-root', type=Path, default=Path('.'))
    p.add_argument('--profile-sha256', required=True)
    a = p.parse_args()
    result = build(a.profile, a.profile_sha256, a.project_root, a.source_root, a.output,
                   LzxDecoder(a.lzx_library))
    print(json.dumps(dict(resources=len(result['resources']), operations=len(result['proofs']),
                          game_started=False, game_rendering_verified=False)))


if __name__ == '__main__':
    main()
