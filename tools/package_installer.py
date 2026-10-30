"""Build the pinned offline Windows GUI/backend and verify a portable ZIP.

Requires an already validated delta bundle, pinned source checkouts and MSVC.
Never downloads game files or includes complete game resources in the package.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import zipfile

from tools.installer_core import Bundle, sha_file

ROOT = Path(__file__).resolve().parents[1]


def archive_path(output):
    return output.with_name(output.name + '.zip')


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def run(command, log, cwd=ROOT):
    print('BUILD ' + log.stem, flush=True)
    with log.open('wb') as stream:
        result = subprocess.run([str(x) for x in command], cwd=cwd, stdout=stream,
                                stderr=subprocess.STDOUT, timeout=3600)
    if result.returncode:
        raise RuntimeError(f'{log.name}: exit {result.returncode}\n' + log.read_text(encoding='utf-8', errors='replace')[-8000:])


def pinned_checkout(path, commit):
    if subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip() != commit:
        raise ValueError('upstream revision mismatch: ' + str(path))
    if subprocess.check_output(['git', '-C', str(path), 'status', '--porcelain', '--untracked-files=no']):
        raise ValueError('upstream source has local edits: ' + str(path))


def single_file(payload, work, output):
    """Embed the byte-verified portable tree without altering its DLLs/data."""
    output = output.resolve()
    if output.exists() or output.suffix.lower() != '.exe':
        raise ValueError('single-file output must be a new EXE')
    expected = sha_file(payload / 'release-files.json')
    (work / 'singlefile_release.py').write_text(f'PAYLOAD_SHA256 = {expected!r}\n', encoding='utf-8')
    version = work / 'singlefile-version.txt'
    version.write_text('''VSVersionInfo(ffi=FixedFileInfo(filevers=(1,0,0,1), prodvers=(1,0,0,1),
mask=0x3f, flags=0, OS=0x40004, fileType=1, subtype=0, date=(0,0)),
kids=[StringFileInfo([StringTable('080404B0', [
StringStruct('FileDescription','《真名法典2》简体中文汉化补丁'),
StringStruct('ProductName','《真名法典2》简体中文汉化补丁'),
StringStruct('ProductVersion','v1.0'), StringStruct('FileVersion','1.0.0.1'),
StringStruct('OriginalFilename','MC2-CN-v1.0.exe')])]),
VarFileInfo([VarStruct('Translation',[2052,1200])])])''', encoding='utf-8')
    run([sys.executable, '-m', 'PyInstaller', '--clean', '--noconfirm', '--onefile',
         '--windowed', '--noupx', '--name', output.stem, '--paths', work,
         '--hidden-import', 'singlefile_release', '--version-file', version,
         '--icon', ROOT / 'src/installer/windows/runner/resources/app_icon.ico',
         '--add-data', str(payload) + os.pathsep + 'payload',
         '--distpath', work / 'singlefile', '--workpath', work / 'singlefile-build',
         '--specpath', work, ROOT / 'tools/installer_singlefile.py'], work / 'singlefile-build.log')
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(work / 'singlefile' / output.name, output)
    report = work / 'singlefile-check.json'
    run([output, '--verify-only', '--report', report], work / 'singlefile-check.log')
    result = json.loads(report.read_bytes())
    if result['status'] != 'PASS' or Path(result['temporary_root']).exists():
        raise ValueError('single-file self-test or temporary cleanup failed')
    result.update(exe=str(output), sha256=sha_file(output), bytes=output.stat().st_size,
                  temporary_cleanup_verified=True)
    return result


def package(args):
    lock_path = ROOT / 'references/installer-toolchain.lock.json'
    lock = json.loads(lock_path.read_bytes())
    if platform.python_version() != lock['python'] or importlib.metadata.version('pyinstaller') != lock['pyinstaller']:
        raise ValueError('use the pinned Python and PyInstaller versions')
    flutter = args.flutter.resolve()
    libmspack = args.libmspack.resolve()
    zarchive = args.zarchive.resolve()
    zstd = args.zstd.resolve()
    for name, path in [('flutter', flutter), ('libmspack', libmspack), ('zarchive', zarchive), ('zstd', zstd)]:
        pinned_checkout(path, lock[name]['commit'])
    bundle = Bundle(args.bundle, args.manifest_sha256)
    for name in bundle.data['tools']:
        bundle.tool(name)
    logo = ROOT / 'src/installer/assets/logo.png'
    if sha_file(logo) != lock['logo_sha256']:
        raise ValueError('logo differs from supplied final artwork')
    out, work = args.output.resolve(), args.work.resolve()
    archive = archive_path(out)
    if out.exists() or archive.exists() or work.exists():
        raise ValueError('output, ZIP and build work directories must all be new')
    work.mkdir(parents=True)
    gui = ROOT / 'src/installer'
    flutter_bin = flutter / 'bin/flutter.bat'
    run([flutter_bin, 'pub', 'get', '--enforce-lockfile'], work / 'flutter-pub.log', gui)
    run([flutter_bin, 'analyze'], work / 'flutter-analyze.log', gui)
    run([flutter_bin, 'test'], work / 'flutter-test.log', gui)
    run([flutter_bin, 'build', 'windows', '--release'], work / 'flutter-build.log', gui)
    (work / 'installer_release.py').write_text(f'MANIFEST_SHA256 = {bundle.sha256!r}\n', encoding='utf-8')
    run([sys.executable, '-m', 'PyInstaller', '--clean', '--noconfirm', '--onedir', '--console',
         '--name', 'mc2-patch', '--paths', ROOT, '--paths', work, '--hidden-import', 'installer_release',
         '--distpath', work / 'frozen', '--workpath', work / 'pyinstaller', '--specpath', work,
         ROOT / 'tools/installer_cli.py'], work / 'backend-build.log')
    built = gui / 'build/windows/x64/runner/Release'
    shutil.copytree(built, out, ignore=shutil.ignore_patterns('*.pdb', '*.lib', '*.exp'))
    shutil.copytree(work / 'frozen/mc2-patch', out / 'backend')
    shutil.copytree(bundle.root, out / 'patch')
    (out / '使用说明.txt').write_text(
        '《真名法典2》简体中文汉化补丁 v1.0\n\n'
        '运行补丁程序，依次选择原版两盘 ISO、可选 DLC 和输出格式，再指定一个新输出目录。\n'
        '完成后请打开输出目录中的“使用说明.txt”，其中包含对应格式的启动、换碟和 DLC 步骤。\n'
        '程序已内置所需组件，无需另装 Python、Flutter 或 VC++ 运行库。\n', encoding='utf-8')
    finder = Path(os.environ['ProgramFiles(x86)']) / 'Microsoft Visual Studio/Installer/vswhere.exe'
    vs = Path(subprocess.check_output([str(finder), '-latest', '-products', '*', '-requires',
              'Microsoft.VisualStudio.Component.VC.Tools.x86.x64', '-property', 'installationPath'], text=True).strip())
    redist = vs / f'VC/Redist/MSVC/{lock["redistributable"]}/x64/Microsoft.VC143.CRT'
    for name in ('msvcp140.dll', 'vcruntime140.dll', 'vcruntime140_1.dll'):
        shutil.copy2(redist / name, out / name)
    third = out / 'THIRD-PARTY'
    third.mkdir()
    copies = [(ROOT / 'LICENSE', 'Project-MIT.txt'),
              (ROOT / 'LICENSE-translations.md', 'Translations.md'),
              (ROOT / 'NOTICE.md', 'Project-NOTICE.md'),
              (flutter / 'LICENSE', 'Flutter-BSD.txt'),
              (flutter / 'bin/cache/artifacts/engine/windows-x64-release/license.windows_flutter.md', 'Flutter-Engine-NOTICES.md'),
              (flutter / 'bin/cache/artifacts/material_fonts/materialicons_license.txt', 'Material-Icons.txt'),
              (flutter / 'bin/cache/dart-sdk/LICENSE', 'Dart-LICENSE.txt'),
              (Path(sys.base_prefix) / 'LICENSE.txt', 'Python-LICENSE.txt'),
              (zarchive / 'LICENSE', 'ZArchive-MIT-0.txt'),
              (zarchive / 'src/sha_256.h', 'ZArchive-SHA256-Public-Domain.h'),
              (zstd / 'LICENSE', 'Zstandard-BSD.txt'),
              (libmspack / 'libmspack/COPYING.LIB', 'libmspack-LGPL-2.1.txt'),
              (ROOT / 'tools/lzx_bridge.c', 'lzx_bridge.c'),
              (lock_path, 'toolchain.lock.json'),
              (ROOT / 'src/installer/THIRD-PARTY.md', 'README.md')]
    for path in (ROOT / 'licenses').glob('*'):
        if path.is_file(): copies.append((path, 'project-' + path.name))
    for path in importlib.metadata.files('pyinstaller'):
        if str(path).endswith('licenses/COPYING.txt'):
            copies.append((Path(path.locate()), 'PyInstaller-LICENSE.txt'))
    for source, name in copies:
        shutil.copy2(source, third / name)
    subprocess.run(['git', '-C', str(libmspack), 'archive', '--format=zip',
                    '--output=' + str(third / 'libmspack-source.zip'), lock['libmspack']['commit']], check=True)
    info = subprocess.check_output([str(out / 'backend/mc2-patch.exe'), '--info'], text=True, encoding='utf-8')
    if json.loads(info)['manifest_sha256'] != bundle.sha256:
        raise ValueError('frozen backend identity differs from packaged bundle')
    (work / 'backend-info.json').write_text(info, encoding='utf-8')
    identities = {p.relative_to(out).as_posix(): dict(size=p.stat().st_size, sha256=sha_file(p))
                  for p in sorted(out.rglob('*')) if p.is_file()}
    write_json(out / 'release-files.json', dict(schema=1, manifest_sha256=bundle.sha256,
               files=identities, logo_sha256=sha_file(logo), version=bundle.data['version']))
    if args.single_file:
        result = single_file(out, work, args.single_file)
        write_json(work / 'package-result.json', result)
        print(json.dumps(result), flush=True)
        return
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in sorted(out.rglob('*')):
            if path.is_file():
                info = zipfile.ZipInfo(out.name + '/' + path.relative_to(out).as_posix(), (2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                with path.open('rb') as source, z.open(info, 'w', force_zip64=True) as dest:
                    shutil.copyfileobj(source, dest)
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None: raise ValueError('ZIP readback failed')
        for name, expected in identities.items():
            with z.open(out.name + '/' + name) as member:
                digest = hashlib.file_digest(member, 'sha256').hexdigest()
            if digest != expected['sha256']: raise ValueError('ZIP hash mismatch: ' + name)
    result = dict(output=str(out), zip=str(archive), bytes=archive.stat().st_size,
                  sha256=sha_file(archive), files=len(identities) + 1, manifest_sha256=bundle.sha256)
    write_json(work / 'package-result.json', result)
    print(json.dumps(result), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('bundle', 'flutter', 'libmspack', 'zarchive', 'zstd', 'output', 'work'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--single-file', type=Path, help='deliver only this EXE; output is internal staging')
    package(parser.parse_args())


if __name__ == '__main__': main()
