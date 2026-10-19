"""Export hash-locked Coalesced sources to local editable per-document catalogs.

Disc membership remains explicit. Identical containers share translation work,
not inferred runtime binding. Config and opaque documents remain in audit scope.
"""
import argparse
import hashlib
import json
from pathlib import Path, PureWindowsPath

try:
    from .coalesced import parse, serialize, extract_entries
    from .validate_catalog import validate
except ImportError:
    from coalesced import parse, serialize, extract_entries
    from validate_catalog import validate


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf8')
    with path.open('xb') as f:
        f.write(raw)
    if path.read_bytes() != raw:
        raise ValueError('output reopening mismatch')


def export_sources(root, profile, output):
    if output.exists():
        raise ValueError('output must be new')
    prepared, sources, grouped = [], [], {}
    for source in profile['sources']:
        path = root / source['path']
        if not path.resolve().is_relative_to(root.resolve()):
            raise ValueError('source escapes root')
        data = path.read_bytes()
        if digest(data) != source['sha256']:
            raise ValueError('source SHA256 mismatch: ' + source['path'])
        files = parse(data)
        if serialize(files) != data:
            raise ValueError('byte-identical roundtrip failed')
        rows = extract_entries(files, source['resource'], source.get('source_locale', 'und'))
        if validate(dict(schema_version=1, entries=rows)):
            raise ValueError('extracted catalog invalid')
        sources.append(dict(**source, entries=len(rows), roundtrip_equal=True,
                            opaque_documents=sum(f.content.encoding == 'opaque-8bit' for f in files)))
        identity = (source['resource'], source['sha256'])
        if source.get('role') != 'translation':
            continue
        if identity in grouped:
            grouped[identity]['discs'].append(source['disc'])
            continue
        group = dict(resource=source['resource'], sha256=source['sha256'], discs=[source['disc']], catalogs=[])
        grouped[identity] = group
        by_document = {}
        for row in rows:
            row['source_sha256'] = digest(row['source'].encode('utf8'))
            # File domain is only a triage hint, never a visible-text guarantee.
            name = PureWindowsPath(row['embedded_path']).stem
            row['domain_hint'] = profile.get('domains', {}).get(name, 'unclassified')
            row['text_kind'] = 'unclassified'
            by_document.setdefault(row['embedded_path'], []).append(row)
        for embedded, entries in sorted(by_document.items()):
            filename = digest(embedded.encode('utf8'))[:16] + '.json'
            relative = source['sha256'] + '/' + filename
            group['catalogs'].append(dict(path=relative, embedded_path=embedded, entries=len(entries),
                                          domain_hint=entries[0]['domain_hint']))
            prepared.append((relative, dict(schema_version=1, kind='selected-coalesced-catalog',
                resource=source['resource'], input_sha256=source['sha256'], entries=entries)))
    # Validate every input before creating output. No guessed cross-language match.
    for source in profile['sources']:
        if digest((root / source['path']).read_bytes()) != source['sha256']:
            raise ValueError('source changed during extraction')
    for relative, catalog in prepared:
        write_json(output / relative, catalog)
    report = dict(schema_version=1, sources=sources, groups=list(grouped.values()),
                  unique_catalog_entries=sum(len(c['entries']) for _, c in prepared),
                  catalog_count=len(prepared), scope='Coalesced only; not all game text',
                  counts_are='physical INI values, including non-player/editor data')
    write_json(output / 'manifest.json', report)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root', type=Path, required=True)
    p.add_argument('--profile', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    try:
        report = export_sources(a.source_root, json.loads(a.profile.read_text(encoding='utf8')), a.output)
        print(json.dumps(dict(sources=len(report['sources']), catalogs=report['catalog_count'],
                              unique_entries=report['unique_catalog_entries']), sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as e:
        print('ERROR: ' + str(e))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
