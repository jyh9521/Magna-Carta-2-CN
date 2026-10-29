"""Launch from an exact user config; optional keyboard-test deviations are explicit."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tomllib

KEYBOARD_TEST_OVERRIDES = ["--hid=keyboard", "--keyboard_mode=1",
                           "--keybind_start=0x0D", "--keybind_a=0x20",
                           "--keybind_b=0x08", "--keybind_guide=0x87"]


def file_hash(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def prepare(exe, config, game, run_dir, expected_config=None, keyboard_test_input=False,
            patch_bundle=None, patch_manifest_sha256=None,
            content_bundle=None, content_manifest_sha256=None):
    content_manifest = content_payloads = None
    if (content_bundle is None) != (content_manifest_sha256 is None):
        raise ValueError('content bundle and trusted manifest SHA256 must be supplied together')
    if content_bundle is not None:
        try:
            from .content_bundle import read_bundle as read_content_bundle, check_no_links
        except ImportError:
            from content_bundle import read_bundle as read_content_bundle, check_no_links
        check_no_links(run_dir)
        content_manifest, content_payloads = read_content_bundle(content_bundle, content_manifest_sha256)
        source_root = Path(content_bundle).resolve()
        resolved_run = Path(run_dir).resolve()
        if resolved_run == source_root or source_root in resolved_run.parents:
            raise ValueError('run directory must be outside content bundle')
    exe, config, game, run_dir = (Path(p).resolve() for p in (exe, config, game, run_dir))
    for p in (exe, config, game):
        if not p.is_file():
            raise ValueError(f"missing input: {p}")
    raw = config.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    tomllib.loads(raw.decode("utf-8-sig"))
    if expected_config is not None and expected_config != digest:
        raise ValueError("config SHA256 mismatch")
    payloads=None
    if (patch_bundle is None)!=(patch_manifest_sha256 is None):
        raise ValueError('runtime patch bundle and trusted manifest SHA256 must be supplied together')
    if patch_bundle is not None:
        try:
            from .runtime_patch import read_bundle
        except ImportError:
            from runtime_patch import read_bundle
        _,payloads=read_bundle(patch_bundle,patch_manifest_sha256,game,exe,raw)
    # The run must not add experiment state inside the game input tree.
    if run_dir == game.parent or game.parent in run_dir.parents:
        raise ValueError("run directory must be outside game tree")
    run_dir.mkdir(parents=True, exist_ok=False)
    snapshot = run_dir / "config.snapshot.toml"
    snapshot.write_bytes(raw)
    args = [str(exe), str(game), f"--config={snapshot}"]
    for name in ("storage", "content", "cache"):
        args.append(f"--{name}_root={run_dir / name}")
    args.append(f"--log_file={run_dir / 'runtime.log'}")
    overrides = list(KEYBOARD_TEST_OVERRIDES) if keyboard_test_input else []
    args.extend(overrides)
    record = dict(schema_version=1, status="prepared", config_source=str(config),
                  config_sha256=digest, config_snapshot=str(snapshot),
                  exe_sha256=file_hash(exe), game_sha256=file_hash(game),
                  command=args, cwd=str(exe.parent), tuning_overrides=overrides,
                  game_rendering_verified=False)
    if payloads is not None:
        patch_root=run_dir/'storage/patches';patch_root.mkdir(parents=True,exist_ok=False)
        for name,data in payloads.items():
            target=patch_root/name
            with target.open('xb') as f:f.write(data)
            if target.read_bytes()!=data:raise ValueError('runtime patch copy reopening mismatch')
        record['runtime_patch']=dict(bundle=str(Path(patch_bundle).resolve()),manifest_sha256=patch_manifest_sha256,
            files={str(patch_root/name):hashlib.sha256(data).hexdigest() for name,data in payloads.items()})
    if content_payloads is not None:
        try:
            from .content_bundle import install_bundle
        except ImportError:
            from content_bundle import install_bundle
        installed = install_bundle(run_dir / 'content', content_manifest, content_payloads)
        record['content_bundle'] = dict(bundle=str(Path(content_bundle).resolve()),
            manifest_sha256=content_manifest_sha256, title_id=content_manifest['title_id'],
            files=installed, profiles_copied=False, saves_copied=False)
    save(run_dir, record)
    return record


def save(run_dir, record):
    (Path(run_dir) / "run.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def launch(run_dir, record):
    if 'content_bundle' in record:
        try:
            from .content_bundle import check_no_links
        except ImportError:
            from content_bundle import check_no_links
        check_no_links(run_dir)
    run_dir=Path(run_dir).resolve()
    if record["status"] != "prepared":
        raise ValueError("run is not prepared")
    for p in (record["config_source"], record["config_snapshot"]):
        if file_hash(p) != record["config_sha256"]:
            raise ValueError("config changed before launch")
    for p, digest in ((record["command"][0], record["exe_sha256"]),
                      (record["command"][1], record["game_sha256"])):
        if file_hash(p) != digest:
            raise ValueError("launch input changed")
    if 'runtime_patch' in record:
        r=record['runtime_patch']
        if file_hash(Path(r['bundle'])/'manifest.json')!=r['manifest_sha256']:
            raise ValueError('runtime patch manifest changed before launch')
        patch_root=Path(run_dir)/'storage/patches'
        if set(patch_root.iterdir())!={Path(p) for p in r['files']}:
            raise ValueError('runtime patch inventory changed before launch')
        for p,h in r['files'].items():
            if Path(p).is_symlink() or file_hash(p)!=h:raise ValueError('runtime patch copy changed before launch')
    if 'content_bundle' in record:
        try:
            from .content_bundle import read_bundle as read_content_bundle, verify_installed
        except ImportError:
            from content_bundle import read_bundle as read_content_bundle, verify_installed
        r = record['content_bundle']
        content_options = [arg for arg in record['command'] if arg.startswith('--content_root=')]
        if content_options != [f"--content_root={run_dir / 'content'}"]:
            raise ValueError('content command root changed')
        manifest, _ = read_content_bundle(r['bundle'], r['manifest_sha256'])
        expected_files = {str(run_dir / 'content' / entry['path']): entry['sha256']
                          for entry in manifest['files']}
        if r['files'] != expected_files or r['title_id'] != manifest['title_id']:
            raise ValueError('content run record changed')
        verify_installed(run_dir / 'content', manifest)
    process = subprocess.Popen(record["command"], cwd=record["cwd"])
    record.update(status="started", pid=process.pid)
    save(run_dir, record)
    return process


def verify_config(run_dir):
    run_dir = Path(run_dir)
    record = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    source = Path(record["config_source"])
    snapshot = Path(record["config_snapshot"])
    if any(file_hash(p) != record["config_sha256"] for p in (source, snapshot)):
        raise ValueError("source or snapshot config changed")
    expected = tomllib.loads(snapshot.read_text(encoding="utf-8-sig"))
    log = (run_dir / "runtime.log").read_text(encoding="utf-8", errors="strict")
    begin, end = "----------- CONFIG DUMP -----------", "----------- END OF CONFIG DUMP ----"
    if log.count(begin) != 1 or log.count(end) != 1:
        raise ValueError("expected exactly one complete config dump; check game overrides")
    dump = log.split(begin, 1)[1].split(end, 1)[0].strip()
    if tomllib.loads(dump) != expected:
        raise ValueError("loaded config dump differs from snapshot")
    return dict(status="config-dump-matches", config_sha256=record["config_sha256"],
                source_unchanged=True, tuning_overrides=record["tuning_overrides"],
                game_rendering_verified=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", type=Path, metavar="RUN_DIR")
    parser.add_argument("--exe", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--game", type=Path)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--config-sha256")
    parser.add_argument("--launch", action="store_true")
    parser.add_argument('--patch-bundle',type=Path)
    parser.add_argument('--patch-manifest-sha256')
    parser.add_argument('--content-bundle', type=Path)
    parser.add_argument('--content-manifest-sha256')
    parser.add_argument("--keyboard-test-input", action="store_true",
                        help="Explicit temporary keyboard-controller CLI override; source TOML unchanged")
    args = parser.parse_args(argv)
    try:
        if args.verify:
            if any((args.exe, args.config, args.game, args.run_dir, args.launch,
                    args.config_sha256, args.keyboard_test_input,args.patch_bundle,args.patch_manifest_sha256,
                    args.content_bundle,args.content_manifest_sha256)):
                raise ValueError("verify cannot be combined with launch arguments")
            result = verify_config(args.verify)
        else:
            if not all((args.exe, args.config, args.game, args.run_dir)):
                raise ValueError("exe, config, game and run-dir are required")
            result = prepare(args.exe, args.config, args.game, args.run_dir,
                             args.config_sha256, args.keyboard_test_input,args.patch_bundle,args.patch_manifest_sha256,
                             args.content_bundle,args.content_manifest_sha256)
            if args.launch:
                launch(args.run_dir, result)
        print(json.dumps(result, ensure_ascii=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
