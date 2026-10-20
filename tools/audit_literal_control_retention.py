"""Source-locked control retention report; not a font coverage or deployment gate."""
import argparse
import json
from pathlib import Path
from tools.audit_text_font_coverage import audit_control_retention
from tools.font_binding_plan import digest, parse_json_object
from tools.coalesced import MAX_BYTES


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('coalesced', 'plan', 'ledger', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args(argv)
    try:
        inputs = [a.coalesced, a.plan, a.ledger]
        if a.output.exists() or a.output.is_symlink() or a.output.resolve() in [v.resolve() for v in inputs]:
            raise ValueError('control report must be new and distinct from inputs')
        if any(v.stat().st_size > MAX_BYTES for v in inputs):
            raise ValueError('control audit input size limit')
        raw = [v.read_bytes() for v in inputs]
        report = audit_control_retention(raw[0], parse_json_object(raw[1]), parse_json_object(raw[2]))
        if any(p.read_bytes() != b for p,b in zip(inputs, raw)):
            raise ValueError('control audit input changed')
        report['ledger_sha256'] = digest(raw[2])
        a.output.parent.mkdir(parents=True, exist_ok=True)
        with a.output.open('xb') as f:
            f.write((json.dumps(report, ensure_ascii=True, indent=2)+'\n').encode())
        if json.loads(a.output.read_bytes()) != report or any(p.read_bytes() != b for p,b in zip(inputs, raw)):
            raise ValueError('control audit publication verification failed')
        print(json.dumps(dict(retained_entries=len(report['entries']),
            retained_literal_codepoints=report['retained_literal_codepoints'],
            font_coverage_verified=False, game_rendering_verified=False), sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as e:
        print('ERROR: '+str(e)); return 2


if __name__ == '__main__':
    raise SystemExit(main())
