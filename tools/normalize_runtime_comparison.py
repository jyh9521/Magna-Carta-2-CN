"""Audit/build a new raw 32-KiB runtime view of a hash-locked comparison packet.

Only modified UE3 .xxx candidates are normalized. Original-identical compressed
packages, raw controls, opaque resources, configuration and live copies stay
unchanged. Existing stored-LZX conversion is reused; artwork is not reencoded.
This is offline format validation, never a successful-boot assertion.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath

from . import compose_incremental_comparison as compose
from .build_disc_image import TOC_LIMIT, toc_rows
from .runtime_envelope import ALIGNMENT, MAGICS, PROFILE, require_raw_envelope
from .runtime_package import normalize_package
from .ue3_package import LzxDecoder, parse_summary
from .verify_resource_phase import MAX_FILE, PHASES, inspect, relative, sha, stable

REPORT_LIMIT = 32 * 1024 * 1024


def _encoded(value):
    data = (json.dumps(value, sort_keys=True, ensure_ascii=True, indent=2,
                       allow_nan=False)+'\n').encode('utf8')
    if len(data) > REPORT_LIMIT:
        raise ValueError('normalization report exceeds bounded size')
    return data


def _output_path(output, packet):
    out = Path(output).absolute()
    compose.unlinked(out, Path(out.anchor))
    if (out.parent.resolve() != out.parent or not out.parent.is_dir()
            or out.exists() or out.is_relative_to(packet) or packet.is_relative_to(out)):
        raise ValueError('normalization output must be new, canonical and disjoint from packet')
    return out


def _read_locked(path, expected):
    if not 0 < expected['size'] <= MAX_FILE:
        raise ValueError('normalization input size outside bounded profile')
    with path.open('rb') as stream:
        data = stream.read(expected['size'])
        if stream.read(1):
            raise ValueError('normalization input grew beyond its locked size')
    if len(data) != expected['size'] or sha(data) != expected['sha256']:
        raise ValueError('normalization source SHA256/size mismatch')
    return data


def _preflight(packet_root, manifest_sha256, toc_path):
    packet = Path(packet_root).absolute()
    compose.unlinked(packet, Path(packet.anchor))
    if packet.resolve() != packet or not packet.is_dir():
        raise ValueError('packet must be a canonical directory')
    manifest, manifest_raw = compose.locked_json(packet/'manifest.json', manifest_sha256)
    if not isinstance(manifest, dict) or manifest.get('kind') != compose.PACKET_KIND:
        raise ValueError('normalization requires an explicit disc comparison packet')
    snapshots = {}
    for phase in PHASES:
        # Byte guards deliberately accept an old noncanonical envelope, since
        # repairing that envelope is the purpose of this separate tool.
        result, checked = inspect(packet, manifest_sha256, packet/phase, phase)
        if not result['all_resources_match']:
            raise ValueError('packet phase mismatch')
        for path, state in checked:
            compose.unlinked(path, packet)
            snapshots[path] = state
    rows = {row['path']:row for row in manifest['resources']}
    toc = relative(toc_path)
    if toc not in rows:
        raise ValueError('TOC must be a declared packet resource')
    for phase in PHASES:
        expected = snapshots[packet/phase/toc]
        if expected['size'] > TOC_LIMIT:
            raise ValueError('TOC exceeds size bound')
        parsed = {row['path']:row for row in toc_rows(_read_locked(packet/phase/toc,expected))}
        key = {'controls':'original','raw-controls':'raw','candidate':'candidate'}[phase]
        for name,row in rows.items():
            size = 0 if name == toc else row[key+'_size']
            if name not in parsed or parsed[name]['size'] != size:
                raise ValueError('predecessor '+phase+' TOC resource size mismatch: '+name)
    stable(snapshots.items())
    return dict(packet=packet, manifest=manifest, manifest_raw=manifest_raw,
                toc=toc, snapshots=snapshots)


def _normalize(data, expected_sha256, decoder):
    normalized, proof = normalize_package(data, expected_sha256, decoder)
    summary = parse_summary(normalized, len(normalized))
    if (summary['byte_order'] != 'big' or summary['compression_flags']
            or summary['compressed_chunks'] or summary['package_flags'] & 0x02000000):
        raise ValueError('modified package has residual outer compression or unsupported byte order')
    padding = (-len(normalized)) % ALIGNMENT
    if len(normalized)+padding > MAX_FILE:
        raise ValueError('normalized output exceeds size bound')
    result = normalized+bytes(padding)
    if result[:len(normalized)] != normalized or any(result[len(normalized):]):
        raise ValueError('raw package zero-padding prefix proof failed')
    envelope = require_raw_envelope(result)
    pad_proof = dict(alignment=ALIGNMENT,added_bytes=padding,
        source_size=len(normalized),source_sha256=sha(normalized),
        prefix_sha256=sha(result[:len(normalized)]),prefix_identical=True,
        suffix_all_zero=True,output_size=len(result),output_sha256=sha(result))
    return result, proof, pad_proof, envelope


def _scan(prepared, decoder):
    packet, manifest = prepared['packet'], prepared['manifest']
    records = []
    for row in sorted(manifest['resources'],key=lambda r:r['path']):
        name = row['path']; source = packet/'candidate'/name
        expected = prepared['snapshots'][source]
        record = dict(path=name,source_sha256=expected['sha256'],source_size=expected['size'],
                      original_sha256=row['original_sha256'],changed=False)
        if expected['sha256'] == row['original_sha256']:
            record['action'] = 'preserve-original'
        elif not name.casefold().endswith('.xxx'):
            record['action'] = 'preserve-non-package'
        else:
            data = _read_locked(source,expected)
            with (packet/'controls'/name).open('rb') as stream:
                original_magic = stream.read(4)
            if data[:4] not in MAGICS and original_magic not in MAGICS:
                record['action'] = 'preserve-non-package'
            else:
                if data[:4] not in MAGICS:
                    raise ValueError('modified UE3 candidate lost its package magic: '+name)
                output, proof, padding, envelope = _normalize(data,expected['sha256'],decoder)
                record.update(action='normalize' if output != data else 'canonical',
                    changed=output != data,output_size=len(output),output_sha256=sha(output),
                    normalization=proof,padding=padding,envelope=envelope)
        records.append(record)
    stable(prepared['snapshots'].items())
    report = dict(schema_version=1,kind='offline-runtime-comparison-normalization-audit',
        profile=PROFILE,byte_order='big',serialization_version=446,licensee_version=25,
        alignment=ALIGNMENT,disc=manifest['disc'],toc_path=prepared['toc'],
        packet_root=str(packet),packet_manifest_sha256=sha(prepared['manifest_raw']),
        resource_count=len(records),modified_ue3_count=sum('normalization' in r for r in records),
        changes_needed=sum(r['changed'] for r in records),resources=records,
        original_and_raw_controls_preserved=True,asset_reencoding_performed=False,
        resource_writes_performed=False,deployment_performed=False,
        game_started=False,game_rendering_verified=False)
    _encoded(report)  # Bound proofs even when an API caller does not write them.
    return report


def audit(packet_root, manifest_sha256, toc_path, decoder=None):
    """Return bounded evidence without creating or changing any resource file."""
    return _scan(_preflight(packet_root,manifest_sha256,toc_path),decoder)


def _write(root, name, data, files, directories):
    compose.create_member(root/name,dict(method='bytes',data=data,
        expected=dict(size=len(data),sha256=sha(data))),root,files,directories)


def _check_owned(root, files):
    for path, identity in files:
        compose.unlinked(path,root)
        if compose.identity(path) != identity:
            raise ValueError('normalization output identity changed')


def _check_tree(root, expected):
    expected_dirs = {p.as_posix() for name in expected for p in PurePosixPath(name).parents
                     if p.as_posix() != '.'}
    found=set();pending=[root]
    while pending:
        parent=pending.pop();compose.unlinked(parent,root)
        for path in parent.iterdir():
            compose.unlinked(path,root);name=path.relative_to(root).as_posix()
            if path.is_dir():
                if name not in expected_dirs:
                    raise ValueError('unexpected normalization output directory')
                pending.append(path)
            elif path.is_file():
                if name not in expected:
                    raise ValueError('unexpected normalization output file')
                found.add(name)
            else:
                raise ValueError('non-file normalization output')
    if found != expected:
        raise ValueError('missing normalization output file')


def build(packet_root, manifest_sha256, output_dir, toc_path, decoder=None):
    """Write only a new derived view; all old phases remain immutable inputs."""
    prepared = _preflight(packet_root,manifest_sha256,toc_path)
    out = _output_path(output_dir,prepared['packet'])
    report = _scan(prepared,decoder)
    out.mkdir(); files=[]; directories=[(out,compose.identity(out))]
    packet_published = False
    expected_outputs = {}
    packet_members = set()
    try:
        audit_raw = _encoded(report)
        _write(out,'audit.json',audit_raw,files,directories)
        expected_outputs[out/'audit.json'] = dict(size=len(audit_raw),sha256=sha(audit_raw))
        result = dict(report)
        if not report['changes_needed']:
            result.update(status='ALREADY_CANONICAL',resource_writes_performed=False)
        else:
            selected = []
            for row in report['resources']:
                if not row['changed']:
                    continue
                name = row['path']; source = prepared['packet']/'candidate'/name
                data = _read_locked(source,prepared['snapshots'][source])
                normalized, proof, padding, envelope = _normalize(data,row['source_sha256'],decoder)
                if (sha(normalized) != row['output_sha256'] or len(normalized) != row['output_size']
                        or proof != row['normalization'] or padding != row['padding']
                        or envelope != row['envelope']):
                    raise ValueError('normalization replay differs from audited output')
                member = 'normalized/candidate/'+name
                _write(out,member,normalized,files,directories)
                expected_outputs[out/member] = dict(size=len(normalized),sha256=sha(normalized))
                selected.append(dict(path=name,before_sha256=row['source_sha256'],file=member,
                                     size=len(normalized),sha256=sha(normalized)))
            replacements = dict(schema_version=1,kind=compose.KIND,disc=report['disc'],
                                toc_path=prepared['toc'],resources=selected)
            encoded = _encoded(replacements)
            if len(encoded) > compose.JSON_LIMIT:
                raise ValueError('replacement manifest exceeds size bound')
            _write(out,'replacements.json',encoded,files,directories)
            expected_outputs[out/'replacements.json'] = dict(size=len(encoded),sha256=sha(encoded))
            stable(prepared['snapshots'].items())
            manifest = compose.build(prepared['packet'],manifest_sha256,out/'replacements.json',
                                     sha(encoded),out/'packet')
            packet_published = True
            packet_members = {'packet/'+name for name in manifest['member_sha256']}
            packet_members.add('packet/manifest.json')
            checked = compose.verify(prepared['packet'],manifest_sha256,out/'replacements.json',
                                     sha(encoded),out/'packet')
            mh = checked['manifest_sha256']
            # Reopen the complete output through the same all-phase byte gates.
            for phase in PHASES:
                check, snapshots = inspect(out/'packet',mh,out/'packet'/phase,phase)
                if not check['all_resources_match']:
                    raise ValueError('normalized view phase mismatch')
                stable(snapshots)
            if sha((out/'packet/manifest.json').read_bytes()) != mh:
                raise ValueError('normalized view manifest reopening mismatch')
            for row in selected:
                data = _read_locked(out/'packet/candidate'/row['path'],
                                    dict(size=row['size'],sha256=row['sha256']))
                require_raw_envelope(data)
            result.update(status='BUILT',resource_writes_performed=True,
                packet_root=str(out/'packet'),packet_manifest_sha256=mh,
                source_packet_root=str(prepared['packet']),source_packet_manifest_sha256=manifest_sha256,
                replacement_manifest_sha256=sha(encoded),unchanged_method='same-volume-hardlink',
                resource_count=len(manifest['resources']))
        raw = _encoded(result)
        _write(out,'result.json',raw,files,directories)
        expected_outputs[out/'result.json'] = dict(size=len(raw),sha256=sha(raw))
        _check_owned(out,files)
        _check_tree(out,{p.relative_to(out).as_posix() for p in expected_outputs} | packet_members)
        stable(expected_outputs.items())
        stable(prepared['snapshots'].items())
        return result
    except BaseException:
        # compose.build cleans its own incomplete creations. After a complete
        # packet has been published, retain it and its dependency proofs on a
        # later verification error rather than guessing ownership recursively.
        if not packet_published:
            compose.cleanup_owned(out,files,directories)
        raise


def _write_audit(packet_root, manifest_sha256, output_dir, toc_path, decoder=None):
    prepared = _preflight(packet_root,manifest_sha256,toc_path)
    out = _output_path(output_dir,prepared['packet'])
    report = _scan(prepared,decoder);data=_encoded(report)
    out.mkdir();files=[];directories=[(out,compose.identity(out))]
    try:
        _write(out,'audit.json',data,files,directories)
        if (out/'audit.json').read_bytes() != data:
            raise ValueError('audit report reopening mismatch')
        _check_tree(out,{'audit.json'})
        stable(prepared['snapshots'].items())
    except BaseException:
        compose.cleanup_owned(out,files,directories)
        raise
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('audit','build'))
    parser.add_argument('--packet-root',type=Path,required=True)
    parser.add_argument('--manifest-sha256',required=True)
    parser.add_argument('--toc-path',required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--lzx-dll',type=Path)
    a = parser.parse_args(argv)
    # Load the supplied native decoder only on first needed decode, after all
    # packet phases and source hashes have passed preflight.
    loaded = []
    def decode(data,size):
        if not loaded:
            loaded.append(LzxDecoder(a.lzx_dll))
        return loaded[0](data,size)
    decoder = decode if a.lzx_dll is not None else None
    try:
        function = _write_audit if a.action == 'audit' else build
        result = function(a.packet_root,a.manifest_sha256,a.output_dir,a.toc_path,decoder)
        print(json.dumps(dict(action=a.action,profile=PROFILE,changes_needed=result['changes_needed'],
            status=result.get('status','NEEDS_NORMALIZATION' if result['changes_needed'] else 'CANONICAL'),
            game_started=False),sort_keys=True))
        return int(a.action == 'audit' and bool(result['changes_needed']))
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print('ERROR: '+str(exc))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
