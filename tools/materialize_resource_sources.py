"""Materialize only hash-locked original resource inputs from supplied inventories."""
from pathlib import Path
import argparse
import hashlib
import json
from .disc_inventory import Disc
from .font_binding_plan import confined_path, _relative, _hash


def materialize(descriptor, root, inventories, reader_factory=Disc):
    if (descriptor.get('schema_version') != 1
            or descriptor.get('kind') != 'locked-resource-source-subset'):
        raise ValueError('unsupported source subset descriptor')
    rows = descriptor.get('resources')
    if not isinstance(rows, list) or not 1 <= len(rows) <= 1024:
        raise ValueError('source resource count bound')
    root = Path(root).resolve()
    readers, indexes, seen, results = {}, {}, set(), []
    for disc, inventory in inventories.items():
        if type(disc) is not int or not 1 <= disc <= 256:
            raise ValueError('invalid source disc identity')
        index = {}
        for entry in inventory['entries']:
            if entry['directory']:
                continue
            key = _relative(entry['path']).casefold()
            if key in index:
                raise ValueError('ambiguous inventory resource path')
            index[key] = entry
        indexes[disc] = index
    for row in rows:
        resource = _relative(row['resource'])
        relative = _relative(row['destination'])
        expected = row['expected_sha256']
        _hash(expected)
        discs = row['discs']
        if (not isinstance(discs, list) or not discs
                or any(type(d) is not int or not 1 <= d <= 256 for d in discs)
                or len(set(discs)) != len(discs)):
            raise ValueError('invalid declared source discs')
        if relative.casefold() in seen:
            raise ValueError('duplicate source destination')
        seen.add(relative.casefold())
        matches = []
        for disc in discs:
            if disc not in indexes:
                continue
            entry = indexes[disc].get(resource.casefold())
            if entry is None or entry.get('sha256') != expected:
                raise ValueError('declared disc resource identity mismatch')
            matches.append((disc, entry))
        if not matches:
            raise ValueError('no inventory for declared source disc;no cross-disc substitution')
        target = confined_path(root, relative)
        if target.exists():
            if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != expected:
                raise ValueError('existing original differs;never overwrite')
            results.append(dict(destination=relative, sha256=expected, action='verified-existing'))
            continue
        disc, entry = matches[0]
        if disc not in readers:
            image = Path(inventories[disc]['image'])
            readers[disc] = reader_factory(image if image.is_absolute() else root / image)
        raw = readers[disc].read(entry['offset'], entry['size'])
        if len(raw) != entry['size'] or hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError('actual original resource size/SHA mismatch')
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(raw)
        if target.read_bytes() != raw:
            raise ValueError('original resource reopening mismatch')
        results.append(dict(destination=relative, sha256=expected, disc=disc, action='materialized'))
    return dict(kind='locked-resource-source-subset-result', resources=results,
                materialized=sum(r['action'] == 'materialized' for r in results),
                verified_existing=sum(r['action'] == 'verified-existing' for r in results),
                existing_files_overwritten=False, full_game_copy_created=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--descriptor', type=Path, required=True)
    parser.add_argument('--project-root', type=Path, default=Path('.'))
    parser.add_argument('--inventory', action='append', required=True, metavar='DISC=JSON')
    args = parser.parse_args(argv)
    try:
        snapshot = args.descriptor.read_bytes()
        inventories, snapshots = {}, []
        for item in args.inventory:
            disc, name = item.split('=', 1)
            disc = int(disc)
            if disc in inventories:
                raise ValueError('duplicate disc inventory')
            path = Path(name)
            raw = path.read_bytes()
            inventories[disc] = json.loads(raw)
            snapshots.append((path, raw))
        report = materialize(json.loads(snapshot), args.project_root, inventories)
        if args.descriptor.read_bytes() != snapshot or any(p.read_bytes() != raw for p, raw in snapshots):
            raise ValueError('source descriptor/inventory changed')
        print(json.dumps(report))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('ERROR: ' + str(exc))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
