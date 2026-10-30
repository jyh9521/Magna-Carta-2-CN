"""Compose source-locked font metrics, scalar UI fields and text-value revisions."""
import argparse
import json
from pathlib import Path

from .build_coalesced import rebuild
from .build_font_supplement import context
from .fit_font_padding import build as build_fonts
from .font_binding_plan import confined_path
from .patch_tagged_fields import digest, patch


def build(profile, profile_sha, project, source, output):
    project, source, output = [Path(p).resolve() for p in (project, source, output)]
    raw = Path(profile).read_bytes()
    if digest(raw) != profile_sha:
        raise ValueError('revision plan SHA256 mismatch')
    p = json.loads(raw)
    if p.get('schema_version') != 1 or p.get('kind') != 'native-metric-revision':
        raise ValueError('unsupported metric revision')
    if output.exists() or output.is_relative_to(source) or source.is_relative_to(output):
        raise ValueError('new disjoint output required')
    plans = {}

    def plan(relative):
        data = confined_path(project, relative).read_bytes()
        plans[relative] = digest(data)
        return json.loads(data)

    font_plan = confined_path(project, p['font_plan'])
    plan(p['font_plan'])
    font_result = build_fonts(font_plan, plans[p['font_plan']], source, output / 'fonts')
    files = {r['path']: confined_path(output / 'fonts/candidate', r['path']).read_bytes()
             for r in font_result['resources']}
    originals = {r['path']: confined_path(source, r['path']).read_bytes() for r in font_result['resources']}
    if any(digest(originals[r['path']]) != r['before_sha256'] for r in font_result['resources']):
        raise ValueError('font source changed during composition')
    proofs = []
    for spec in p['field_plans']:
        fields = plan(spec['plan'])
        original = confined_path(source, spec['resource']).read_bytes()
        if digest(original) != fields['source_package_sha256']:
            raise ValueError('field source identity mismatch')
        originals[spec['resource']] = original
        before = files.get(spec['resource'], original)
        after, proof = patch(before, context(before, None), fields)
        restored, _ = patch(after, context(after, None), fields, reverse=True)
        if restored != before:
            raise ValueError('scalar inverse mismatch')
        files[spec['resource']] = after
        proofs.append(dict(resource=spec['resource'], proof=proof))
    text_proofs = []
    for name in p['text_plans']:
        text_plan = plan(name)
        resource = text_plan['resource']
        if resource in files:
            raise ValueError('duplicate text resource')
        originals[resource] = confined_path(source, resource).read_bytes()
        files[resource] = rebuild(originals[resource], text_plan)
        text_proofs.append(dict(resource=resource, entries=len(text_plan['entries'])))
    resources = []
    for relative, after in sorted(files.items()):
        before = originals[relative]
        for state, data in (('baseline', before), ('candidate', after)):
            path = confined_path(output / state, relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            if path.read_bytes() != data:
                raise ValueError('resource readback mismatch')
        resources.append(dict(path=relative, file='candidate/' + relative,
                              before_sha256=digest(before), sha256=digest(after), size=len(after)))
    manifest = dict(schema_version=1, kind='incremental-comparison-replacements',
                    disc=p['disc'], resources=resources, toc_path=p['toc_path'])
    proof = dict(schema_version=1, profile_sha256=profile_sha, plans=plans, fonts=font_result,
                 fields=proofs, text=text_proofs, game_started=False)
    for name, value in (('replacements.json', manifest), ('manifest.json', proof)):
        raw_out = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
        (output / name).write_bytes(raw_out)
        if (output / name).read_bytes() != raw_out:
            raise ValueError('manifest readback mismatch')
    for relative, expected in plans.items():
        if digest(confined_path(project, relative).read_bytes()) != expected:
            raise ValueError('plan changed during build')
    if Path(profile).read_bytes() != raw or any(confined_path(source, r).read_bytes() != data for r, data in originals.items()):
        raise ValueError('source changed during build')
    return dict(resources=len(resources), font_aliases=sum(len(r['fonts']) for r in font_result['resources']),
                fields=sum(r['proof']['fields'] for r in proofs), text_edits=sum(r['entries'] for r in text_proofs),
                inverse_byte_identical=True, game_started=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('profile', 'project-root', 'source-root', 'output'):
        p.add_argument('--' + key, required=True, type=Path)
    p.add_argument('--profile-sha256', required=True)
    a = p.parse_args()
    print(json.dumps(build(a.profile, a.profile_sha256, a.project_root, a.source_root, a.output)))


if __name__ == '__main__':
    main()
