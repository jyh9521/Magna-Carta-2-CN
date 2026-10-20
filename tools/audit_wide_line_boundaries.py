"""Read-only byte-boundary observations; never repair or reinterpret source INI."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from tools.coalesced import parse, serialize, write_json_atomic


def audit(data: bytes) -> dict:
    files = parse(data)
    if serialize(files) != data:
        raise ValueError('source roundtrip mismatch')
    documents = []
    for file in files:
        if file.content.encoding != 'utf-16-le':
            continue
        raw = file.content.text.encode('utf-16-le')
        # This pattern is an observation, not a claim about the original codec.
        # It can also represent legitimate U+0A0D followed by a low zero byte.
        hits = [i for i in range(len(raw) - 2) if raw[i:i + 3] == b'\r\n\0']
        if not hits:
            continue
        documents.append(dict(
            embedded_path=file.path.text,
            content_offset=file.content.offset,
            payload_offset=file.content.offset + 4,
            payload_sha256=hashlib.sha256(raw).hexdigest(),
            payload_bytes=len(raw),
            candidate_offsets=hits,
            candidate_parity=[i % 2 for i in hits],
            container_offsets=[file.content.offset + 4 + i for i in hits],
            policy='observation-only; preserve bytes, identifiers and decoded values',
        ))
    return dict(schema_version=1, input_sha256=hashlib.sha256(data).hexdigest(),
                roundtrip_identical=True, documents=documents,
                candidate_count=sum(len(d['candidate_offsets']) for d in documents))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--expected-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.output.exists() or args.output.is_symlink():
            raise ValueError('output must be new')
        if args.output.resolve() == args.source.resolve():
            raise ValueError('output aliases source')
        data = args.source.read_bytes()
        if hashlib.sha256(data).hexdigest() != args.expected_sha256:
            raise ValueError('source hash mismatch')
        report = audit(data)
        if args.source.read_bytes() != data:
            raise ValueError('source changed during audit')
        write_json_atomic(args.output, report)
        print(f"PASS audit: {len(report['documents'])} wide documents, "
              f"{report['candidate_count']} candidate boundaries; source unchanged; no repair")
        return 0
    except (OSError, ValueError) as error:
        print(f'ERROR: {error}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
