"""Build an independent, UI-only Flutter preview without touching the installer.

Only source files are staged; no backend, patch bundle, ISO or game copy is used.
Both output and work must be new. The original source and release stay in place.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ENTRY = 'src/installer/lib/expressive_preview.dart'
EXE = 'MC2ExpressivePreview.exe'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def replace_once(path, old, new):
    text = path.read_text(encoding='utf-8')
    if text.count(old) != 1:
        raise ValueError('unexpected runner source: ' + str(path))
    path.write_text(text.replace(old, new), encoding='utf-8', newline='\n')


def stage_sources(root, destination, names=None):
    """Copy only a source inventory, rejecting links and path traversal."""
    root, destination = Path(root).resolve(), Path(destination).resolve()
    if destination.exists():
        raise ValueError('preview work must be new')
    if names is None:
        names = subprocess.check_output(
            ['git', '-C', str(root), 'ls-files', '-z', '--', 'src/installer']).decode('utf-8').split('\0')
        names = sorted(set(filter(None, names)) | {ENTRY, 'src/installer/test/expressive_preview_test.dart'})
    rows = []
    for name in names:
        rel = PurePosixPath(name)
        if (rel.is_absolute() or '..' in rel.parts or '\\' in name or ':' in name
                or rel.parts[:2] != ('src', 'installer')):
            raise ValueError('invalid source member: ' + name)
        source = root.joinpath(*rel.parts)
        if source.is_symlink() or not source.resolve().is_relative_to(root / 'src/installer'):
            raise ValueError('source link escaped installer: ' + name)
        rows.append((source, destination.joinpath(*rel.parts[2:])))
    destination.mkdir(parents=True)
    for source, target in rows:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return {str(source.relative_to(root)).replace('\\', '/'): sha(source) for source, _ in rows}


def prepare_runner(project):
    replace_once(project / 'windows/CMakeLists.txt', 'set(BINARY_NAME "MC2Installer")',
                 'set(BINARY_NAME "MC2ExpressivePreview")')
    path = project / 'windows/runner/main.cpp'
    replace_once(path, 'Win32Window::Size size(1080, 870);', 'Win32Window::Size size(1120, 820);')
    replace_once(path, 'L"《真名法典2》简体中文汉化补丁"', 'L"真名法典2 · Material 3 Expressive 预览"')
    path = project / 'windows/runner/Runner.rc'
    text = path.read_text(encoding='utf-8')
    if '"v1.0"' not in text or 'MC2Installer.exe' not in text:
        raise ValueError('unexpected preview version source')
    path.write_text(text.replace('"v1.0"', '"0.1.0-preview"')
                    .replace('MC2Installer', 'MC2ExpressivePreview')
                    .replace('《真名法典2》简体中文汉化补丁', '真名法典2 · Expressive UI 预览'),
                    encoding='utf-8', newline='\n')


def run(command, cwd, log):
    with log.open('wb') as stream:
        result = subprocess.run([str(v) for v in command], cwd=cwd,
                                stdout=stream, stderr=subprocess.STDOUT, timeout=1200)
    if result.returncode:
        raise RuntimeError(log.read_text(encoding='utf-8', errors='replace')[-10000:])


def build(args):
    work, output, flutter = args.work.resolve(), args.output.resolve(), args.flutter.resolve()
    archive = output.with_suffix('.zip')
    if work.exists() or output.exists() or archive.exists():
        raise ValueError('work, output and ZIP must all be new')
    lock = json.loads((ROOT / 'references/installer-toolchain.lock.json').read_bytes())
    revision = subprocess.check_output(['git', '-C', str(flutter), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != lock['flutter']['commit']:
        raise ValueError('Flutter revision differs from pinned toolchain')
    original = ROOT / 'dist/MC2-CN-v1.0.exe'
    before = sha(original) if original.exists() else None
    work.mkdir(parents=True)
    project = work / 'project'
    sources = stage_sources(ROOT, project)
    prepare_runner(project)
    binary = flutter / 'bin/flutter.bat'
    run([binary, 'pub', 'get', '--enforce-lockfile'], project, work / 'pub.log')
    run([binary, 'analyze'], project, work / 'analyze.log')
    run([binary, 'test'], project, work / 'tests.log')
    run([binary, 'build', 'windows', '--release', '--target', 'lib/expressive_preview.dart',
         '--build-name=0.1.0', '--build-number=0'], project, work / 'build.log')
    built = project / 'build/windows/x64/runner/Release'
    shutil.copytree(built, output, ignore=shutil.ignore_patterns('*.pdb', '*.lib', '*.exp'))
    finder = Path(os.environ['ProgramFiles(x86)']) / 'Microsoft Visual Studio/Installer/vswhere.exe'
    vs = subprocess.check_output([str(finder), '-latest', '-products', '*', '-requires',
        'Microsoft.VisualStudio.Component.VC.Tools.x86.x64', '-property', 'installationPath'], text=True).strip()
    redist = Path(vs) / f'VC/Redist/MSVC/{lock["redistributable"]}/x64/Microsoft.VC143.CRT'
    for name in ('msvcp140.dll', 'vcruntime140.dll', 'vcruntime140_1.dll'):
        shutil.copy2(redist / name, output / name)
    third = output / 'THIRD-PARTY'
    third.mkdir()
    for source, name in [
        (ROOT / 'LICENSE', 'Project-MIT.txt'), (ROOT / 'NOTICE.md', 'Project-NOTICE.md'),
        (flutter / 'LICENSE', 'Flutter-BSD.txt'),
        (flutter / 'bin/cache/artifacts/engine/windows-x64-release/license.windows_flutter.md', 'Flutter-Engine-NOTICES.md'),
        (flutter / 'bin/cache/artifacts/material_fonts/materialicons_license.txt', 'Material-Icons.txt'),
        (flutter / 'bin/cache/dart-sdk/LICENSE', 'Dart-LICENSE.txt')]:
        shutil.copy2(source, third / name)
    (output / '使用说明.txt').write_text(
        'Material 3 Expressive UI 独立预览\n\n运行 MC2ExpressivePreview.exe。\n'
        '底部箭头或键盘左右键切换 A 紫藤分栏 / B 赤陶向导 / C 青瓷工作台。右上角切换主题。\n'
        '点击“填入演示文件”再继续，可体验设置、进度、取消、错误重试和完成页面。\n'
        '所有安装行为都是演示，没有安装后端，不读写游戏资源。原安装器不受影响。\n'
        '请保留同目录的 DLL 和 data。--variant=B 或 --variant=C 选择启动布局；--dark 启动深色主题。\n'
        '品牌 LOGO 沿用原安装器原文件；其授权不自动改为 MIT。\n', encoding='utf-8', newline='\n')
    files = {p.relative_to(output).as_posix(): {'size': p.stat().st_size, 'sha256': sha(p)}
             for p in sorted(output.rglob('*')) if p.is_file()}
    manifest = dict(schema=1, kind='ui-only-preview', entrypoint='lib/expressive_preview.dart',
                    files=files, sources=sources, flutter_revision=revision, original_installer_sha256=before)
    (output / 'preview-files.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(output.rglob('*')):
            if p.is_file():
                info = zipfile.ZipInfo(output.name + '/' + p.relative_to(output).as_posix(), (2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, p.read_bytes())
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise ValueError('preview ZIP readback failed')
        for name, identity in files.items():
            if hashlib.sha256(z.read(output.name + '/' + name)).hexdigest() != identity['sha256']:
                raise ValueError('preview ZIP member hash mismatch')
    if before is not None and sha(original) != before:
        raise ValueError('original installer identity changed')
    result = dict(status='PASS', exe=str(output / EXE), zip=str(archive), zip_sha256=sha(archive),
                  original_unchanged=True, file_count=len(files))
    (work / 'build-result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--flutter', type=Path, default=ROOT / 'build/toolchain/flutter')
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    build(parser.parse_args(argv))


if __name__ == '__main__':
    main()
