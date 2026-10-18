"""Launch an isolated experiment from an exact user-config snapshot, without tuning overrides."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tomllib


def file_hash(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def prepare(exe, config, game, run_dir, expected_config=None):
    exe, config, game, run_dir = (Path(p).resolve() for p in (exe, config, game, run_dir))
    for p in (exe, config, game):
        if not p.is_file():
            raise ValueError(f"missing input: {p}")
    raw = config.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    tomllib.loads(raw.decode("utf-8-sig"))
    if expected_config is not None and expected_config != digest:
        raise ValueError("config SHA256 mismatch")
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
    record = dict(schema_version=1, status="prepared", config_source=str(config),
                  config_sha256=digest, config_snapshot=str(snapshot),
                  exe_sha256=file_hash(exe), game_sha256=file_hash(game),
                  command=args, cwd=str(exe.parent), tuning_overrides=[],
                  game_rendering_verified=False)
    save(run_dir, record)
    return record


def save(run_dir, record):
    (Path(run_dir) / "run.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def launch(run_dir, record):
    if record["status"] != "prepared":
        raise ValueError("run is not prepared")
    for p in (record["config_source"], record["config_snapshot"]):
        if file_hash(p) != record["config_sha256"]:
            raise ValueError("config changed before launch")
    for p, digest in ((record["command"][0], record["exe_sha256"]),
                      (record["command"][1], record["game_sha256"])):
        if file_hash(p) != digest:
            raise ValueError("launch input changed")
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
                source_unchanged=True, tuning_overrides=[], game_rendering_verified=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", type=Path, metavar="RUN_DIR")
    parser.add_argument("--exe", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--game", type=Path)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--config-sha256")
    parser.add_argument("--launch", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.verify:
            if any((args.exe, args.config, args.game, args.run_dir, args.launch, args.config_sha256)):
                raise ValueError("verify cannot be combined with launch arguments")
            result = verify_config(args.verify)
        else:
            if not all((args.exe, args.config, args.game, args.run_dir)):
                raise ValueError("exe, config, game and run-dir are required")
            result = prepare(args.exe, args.config, args.game, args.run_dir, args.config_sha256)
            if args.launch:
                launch(args.run_dir, result)
        print(json.dumps(result, ensure_ascii=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
