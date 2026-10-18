"""Build an optional, pinned libmspack LZX adapter in ignored local build/ only."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

COMMIT = "55d501976171397ccd5d5a7a1ca7da065b1d9a06"
URL = "https://github.com/kyz/libmspack.git"
ROOT = Path(__file__).resolve().parents[1]


def command(argv, **kwargs):
    return subprocess.run(argv, check=True, text=True, encoding="utf-8", errors="replace", capture_output=True, **kwargs).stdout.strip()


def build_path(path: Path, root: Path = ROOT):
    """Reject paths outside this checkout's ignored build directory, including links."""
    resolved = path.resolve()
    allowed = (root / "build").resolve()
    if resolved == allowed or not resolved.is_relative_to(allowed):
        raise ValueError("build path must be strictly inside repository build/")
    return resolved


def validate_checkout(path: Path):
    """Existing checkouts are verified read-only; they are never reset or fetched."""
    if not (path / ".git").is_dir():
        raise ValueError("existing source is not a Git checkout")
    if command(["git", "-C", str(path), "remote", "get-url", "origin"]) != URL:
        raise ValueError("libmspack origin mismatch")
    if command(["git", "-C", str(path), "rev-parse", "HEAD"]) != COMMIT:
        raise ValueError("libmspack commit mismatch")
    if command(["git", "-C", str(path), "status", "--porcelain", "--untracked-files=all"]):
        raise ValueError("libmspack checkout is modified")
    source = path / "libmspack" / "mspack"
    for name in ("lzxd.c", "lzx.h", "mspack.h"):
        if not (source / name).is_file():
            raise ValueError(f"missing libmspack source: {name}")
    return source


def obtain_checkout(path: Path):
    if path.exists():
        return validate_checkout(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive mkdir: no mutation of a pre-existing foreign directory.
    path.mkdir()
    command(["git", "init", str(path)])
    command(["git", "-C", str(path), "remote", "add", "origin", URL])
    command(["git", "-C", str(path), "fetch", "--depth", "1", "origin", COMMIT])
    command(["git", "-C", str(path), "checkout", "--detach", "FETCH_HEAD"])
    return validate_checkout(path)


def quote_batch_path(path: Path):
    value = str(path)
    if any(c in value for c in '\r\n"%!&|<>^'):
        raise ValueError("unsupported batch metacharacter in build path")
    return '"' + value + '"'


def msvc_batch(setup: Path, source: Path, bridge: Path, output: Path):
    q = quote_batch_path
    return ("@echo off\r\nsetlocal\r\n"
            f"chcp 65001 >nul\r\ncall {q(setup)} >nul\r\nif errorlevel 1 exit /b 1\r\n"
            f"cl /nologo /LD /O2 /I{q(source)} {q(bridge)} {q(source / 'lzxd.c')} "
            f"/link /OUT:{q(output)}\r\nexit /b %errorlevel%\r\n")


def posix_command(cc: str, source: Path, bridge: Path, output: Path):
    return [cc, "-shared", "-fPIC", "-O2", "-I", str(source), str(bridge),
            str(source / "lzxd.c"), "-o", str(output)]


def build(output_dir: Path, cc="cc"):
    output_dir = build_path(output_dir)
    if output_dir.exists():
        raise ValueError("output directory already exists; choose a new build directory")
    source = obtain_checkout(build_path(ROOT / "build" / "upstream" / ("libmspack-" + COMMIT)))
    output_dir.mkdir(parents=True)
    bridge = ROOT / "tools" / "lzx_bridge.c"
    if sys.platform == "win32":
        finder = Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
        install = command([str(finder), "-latest", "-products", "*", "-requires",
                           "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"])
        setup = Path(install) / "VC/Auxiliary/Build/vcvars64.bat"
        if not install or not setup.is_file():
            raise ValueError("MSVC x64 build tools not found")
        output = output_dir / "ue3_lzx.dll"
        batch = output_dir / "build-lzx.cmd"
        batch.write_text(msvc_batch(setup, source, bridge, output), encoding="utf-8", newline="")
        log = command(["cmd.exe", "/d", "/c", str(batch)], cwd=output_dir)
    else:
        output = output_dir / ("libue3_lzx.dylib" if sys.platform == "darwin" else "libue3_lzx.so")
        log = command(posix_command(cc, source, bridge, output), cwd=output_dir)
    if not output.is_file() or not output.stat().st_size:
        raise ValueError("compiler produced no library")
    (output_dir / "compiler.log").write_text(log + "\n", encoding="utf-8")
    # Preserve license/source in the local build; none of these binaries enter Git.
    checkout = source.parents[1]
    license_files = list((checkout / "libmspack").glob("COPYING*"))
    if not license_files:
        raise ValueError("upstream license file missing")
    for license_file in license_files:
        shutil.copyfile(license_file, output_dir / license_file.name)
    manifest = {"schema_version": 1, "library": str(output), "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "upstream": URL, "commit": COMMIT, "source_checkout": str(checkout),
                "license": "libmspack LGPL-2.1; bridge MIT; linked adapter subject to LGPL terms",
                "bridge_sha256": hashlib.sha256(bridge.read_bytes()).hexdigest()}
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "build/lzx/native")
    parser.add_argument("--cc", default="cc")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(build(args.output_dir, args.cc), sort_keys=True))
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}")
        if isinstance(exc, subprocess.CalledProcessError):
            print(exc.stdout or "")
            print(exc.stderr or "")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
