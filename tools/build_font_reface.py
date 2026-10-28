"""Build selected dynamic fonts on resource copies, never an ISO/game tree."""
import argparse
import json
from pathlib import Path
from .reface_font import reface, sha
from .font_binding_plan import confined_path


def build(profile_path, profile_sha, source_root, project_root, output, verify=False):
    profile_path=Path(profile_path);raw=profile_path.read_bytes()
    if sha(raw)!=profile_sha:raise ValueError('profile SHA256 mismatch')
    p=json.loads(raw)
    if p.get('schema_version')!=1 or p.get('kind')!='font-reface-plan':raise ValueError('wrong profile')
    output=Path(output).resolve();source_root=Path(source_root).resolve();project_root=Path(project_root).resolve()
    if (output.exists() != verify or output.is_relative_to(source_root)
            or source_root.is_relative_to(output)):
        raise ValueError('disjoint output with correct build/verify state required')
    font=confined_path(project_root,p['font']['path']);roles={r['id']:r for r in p['roles']}
    if not verify:output.mkdir(parents=True)
    def save(path,data):
        if verify:
            actual = path.read_bytes()
            # Older Windows proof writers used CRLF; resource bytes stay exact.
            if path.suffix == '.json':
                actual = actual.replace(b'\r\n', b'\n')
            if actual!=data:raise ValueError('independent rebuild mismatch: '+str(path))
        else:
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
            if path.read_bytes()!=data:raise ValueError('output reopening mismatch')
    manifest=dict(schema_version=1,kind='font-reface-build',profile_sha256=profile_sha,
                  game_started=False,game_rendering_verified=False,resources=[])
    for s in p['sources']:
        src=confined_path(source_root,s['path']);before=src.read_bytes()
        if sha(before)!=s['before_sha256']:raise ValueError('source package mismatch: '+s['path'])
        after=before;proofs=[]
        for selection in s['fonts']:
            after,proof=reface(after,sha(after),selection['object'],font,p['font']['sha256'],roles[selection['role']])
            proofs.append(proof)
        for phase,data in [('baseline',before),('candidate',after)]:
            path=confined_path(output,phase+'/'+s['path']);save(path,data)
        report=output/(Path(s['path']).stem+'-proof.json')
        save(report,(json.dumps(proofs,ensure_ascii=False,indent=2)+'\n').encode())
        manifest['resources'].append(dict(path=s['path'],before_sha256=sha(before),sha256=sha(after),
                                         size=len(after),font_count=len(proofs),proof=report.name))
        if src.read_bytes()!=before:raise ValueError('source changed during build')
    save(output/'manifest.json',(json.dumps(manifest,indent=2)+'\n').encode())
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile',type=Path,required=True);p.add_argument('--profile-sha256',required=True)
    p.add_argument('--source-root',type=Path,required=True);p.add_argument('--project-root',type=Path,default=Path('.'))
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--output',type=Path);g.add_argument('--verify',type=Path);a=p.parse_args()
    m=build(a.profile,a.profile_sha256,a.source_root,a.project_root,a.output or a.verify,bool(a.verify))
    print(json.dumps(dict(status='PASS',resources=len(m['resources']),fonts=sum(r['font_count'] for r in m['resources']),game_started=False)))


if __name__=='__main__':main()
