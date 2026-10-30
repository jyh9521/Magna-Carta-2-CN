"""Offline transactional installer engine shared by the Windows GUI and CLI.

All policy and language data lives in the hash-pinned release manifest. ZAR uses
a virtual XEX tree: unchanged ISO extents plus patched loose files, avoiding an
unnecessary second full-game copy. XEX materializes that exact same tree.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import struct
import subprocess
import threading
import time
import uuid

from .content_bundle import check_no_links, _unique_object
from .disc_inventory import Disc
from .installer_delta import apply_delta, digest, MAX_RESOURCE
from .runtime_envelope import require_raw_envelope
from .stfs_package import StfsPackage


class Cancelled(Exception):
    pass


class InstallError(ValueError):
    pass


def safe_relative(value):
    if not isinstance(value, str) or not value or len(value) > 240:
        raise InstallError('无效的资源路径')
    if any(ord(c) < 32 or ord(c) > 126 or c in '\\:*?"<>|' for c in value):
        raise InstallError('资源路径含非法字符')
    parts = value.split('/')
    for part in parts:
        if (not part or part in ('.', '..') or part.endswith((' ', '.'))
                or re.fullmatch(r'(CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])', part.split('.')[0], re.I)):
            raise InstallError('资源路径越界或包含保留名称')
    return value


def sha_file(path, cancel=lambda: None, progress=lambda x: None):
    result = hashlib.sha256()
    total = 0
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            cancel()
            result.update(block)
            total += len(block)
            progress(total)
    return result.hexdigest()


def hash_value(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise InstallError('无效的 SHA256 摘要')
    return value


def integer(value, low=0, high=1 << 40):
    if type(value) is not int or not low <= value <= high:
        raise InstallError('清单数值超出支持范围')
    return value


def execution_id(data):
    if len(data) < 24 or data[:4] != b'XEX2':
        raise InstallError('文件不是 XEX2 可执行文件')
    count = struct.unpack_from('>I', data, 20)[0]
    if not 1 <= count <= 256 or 24 + count * 8 > len(data):
        raise InstallError('XEX 头结构不完整')
    options = {}
    for i in range(count):
        key, value = struct.unpack_from('>II', data, 24 + i * 8)
        if key in options:
            raise InstallError('XEX 头包含重复字段')
        options[key] = value
    offset = options.get(0x40006, 0)
    if offset < 24 + count * 8 or offset + 24 > len(data):
        raise InstallError('XEX 缺少有效 Execution ID')
    media, version, base, title, platform, kind, disc, total, save = struct.unpack_from('>4I4BI', data, offset)
    return dict(title_id=f'{title:08X}', media_id=f'{media:08X}', disc=disc,
                disc_count=total, version=version, base_version=base,
                platform=platform, executable_type=kind, savegame_id=save)


def validate_manifest(m):
    if (not isinstance(m, dict) or m.get('schema_version') != 1
            or m.get('kind') != 'localization-installer' or not re.fullmatch('[0-9A-F]{8}', m.get('title_id', ''))):
        raise InstallError('不支持的安装器清单')
    safe_relative(m['output_name'])
    if '/' in m['output_name']:
        raise InstallError('输出名称必须是单一目录名')
    if not isinstance(m['discs'], list) or len(m['discs']) != 2:
        raise InstallError('清单必须包含两张独立光盘')
    for n, disc in enumerate(m['discs'], 1):
        if disc['execution_id']['disc'] != n or disc['execution_id']['disc_count'] != 2:
            raise InstallError('清单盘号不匹配')
        if disc['execution_id']['title_id'] != m['title_id']:
            raise InstallError('清单 Title ID 不匹配')
        hash_value(disc['sha256'])
        integer(disc['size'], 1)
        integer(disc['partition_base'])
        entries = disc['files']
        if not isinstance(entries, list) or not 1 <= len(entries) <= 20000:
            raise InstallError('资源数量超限')
        seen = set()
        for entry in entries:
            path = safe_relative(entry['path'])
            if path.casefold() in seen:
                raise InstallError('资源路径重复')
            seen.add(path.casefold())
            integer(entry['size'])
            hash_value(entry['sha256'])
            if 'patch' in entry:
                validate_patch(entry)
                if path.casefold() == 'default.xex':
                    raise InstallError('本安装器不修改可执行文件')
        if 'default.xex' not in seen:
            raise InstallError('清单缺少 default.xex')
        for name in seen:
            if any(str(p).casefold() in seen for p in PurePosixPath(name).parents if str(p) != '.'):
                raise InstallError('文件与目录路径冲突')
    if not isinstance(m['dlc'], list) or len(m['dlc']) > 16:
        raise InstallError('DLC 数量超限')
    seen = set()
    for entry in m['dlc']:
        if not re.fullmatch('[0-9A-F]{40}|[0-9A-F]{42}', entry['name']) or entry['name'] in seen:
            raise InstallError('DLC 文件标识无效或重复')
        seen.add(entry['name'])
        integer(entry['size'], 1, MAX_RESOURCE)
        hash_value(entry['sha256'])
        validate_patch(entry)
        if entry['transform'] != 'identity':
            raise InstallError('DLC 转换方式不受支持')
    for name, entry in m['tools'].items():
        safe_relative(entry['path'])
        hash_value(entry['sha256'])


def validate_patch(entry):
    if entry['transform'] not in ('identity', 'ue3-raw-v1'):
        raise InstallError('不支持的源转换')
    integer(entry['size'], 0, MAX_RESOURCE)
    integer(entry['output_size'], 0, MAX_RESOURCE)
    hash_value(entry['output_sha256'])
    hash_value(entry['patch_sha256'])
    hash_value(entry['base_sha256'])
    safe_relative(entry['patch'])
    if entry['patch'] != 'patches/' + entry['patch_sha256'] + '.mcdelta':
        raise InstallError('差异文件名与摘要不符')


class Bundle:
    def __init__(self, root, expected):
        self.root = check_no_links(root)
        manifest = check_no_links(self.root / 'manifest.json')
        if manifest.stat().st_size > 16 * 1024 * 1024:
            raise InstallError('清单过大')
        raw = manifest.read_bytes()
        if digest(raw) != hash_value(expected):
            raise InstallError('安装数据清单已改变，请重新解压完整安装包')
        self.sha256 = expected
        self.data = json.loads(raw, object_pairs_hook=_unique_object)
        validate_manifest(self.data)

    def member(self, relative, expected):
        path = check_no_links(self.root / safe_relative(relative))
        if not path.is_relative_to(self.root) or not path.is_file() or sha_file(path) != expected:
            raise InstallError('安装数据损坏：' + relative)
        return path

    def tool(self, name):
        entry = self.data['tools'][name]
        return self.member(entry['path'], entry['sha256'])

    def transform(self, source, entry):
        if digest(source) != entry['sha256'] or len(source) != entry['size']:
            raise InstallError('原始资源摘要不匹配')
        if entry['transform'] == 'identity':
            base = source
        else:
            from .decompress_package import decompress_copy
            from .ue3_package import LzxDecoder
            base, _ = decompress_copy(source, entry['sha256'], LzxDecoder(self.tool('lzx')), alignment=1)
        if digest(base) != entry['base_sha256']:
            raise InstallError('规范化原始资源摘要不匹配')
        return base

    def patch(self, source, entry, cancel):
        patch = self.member(entry['patch'], entry['patch_sha256'])
        if patch.stat().st_size > MAX_RESOURCE + 1024 * 1024:
            raise InstallError('差异数据超限')
        result = apply_delta(self.transform(source, entry), patch.read_bytes(), cancel)
        if len(result) != entry['output_size'] or digest(result) != entry['output_sha256']:
            raise InstallError('补丁应用后摘要不符')
        if entry.get('runtime_envelope'):
            require_raw_envelope(result)
        return result


class Installer:
    def __init__(self, bundle, emit=lambda event: None, cancel=None):
        self.bundle = bundle
        self.emit_callback = emit
        self.cancel_event = cancel or threading.Event()
        self.log = None
        self.last_progress = 0.0

    def check_cancel(self):
        if self.cancel_event.is_set():
            raise Cancelled('安装已取消；原版文件保持不变')

    def event(self, stage, message, progress=None, level='info', **fields):
        event = dict(time=time.strftime('%Y-%m-%dT%H:%M:%S'), stage=stage, level=level, message=message, **fields)
        if progress is not None:
            event['progress'] = round(max(self.last_progress, min(1.0, progress)), 5)
            self.last_progress = event['progress']
        if self.log:
            self.log.write(json.dumps(event, ensure_ascii=False) + '\n')
            self.log.flush()
        self.emit_callback(event)

    def inspect(self, images, full=False):
        if len(images) != 2:
            raise InstallError('请选择韩版 Disc 1 和 Disc 2')
        discs = []
        for index, (path, expected) in enumerate(zip(images, self.bundle.data['discs'])):
            self.check_cancel()
            path = check_no_links(path)
            if not path.is_file():
                raise InstallError(f'Disc {index + 1} 文件不存在')
            disc = Disc(path)
            inventory = {x['path']: x for x in disc.inventory() if not x['directory']}
            if 'default.xex' not in inventory:
                raise InstallError('镜像中缺少 default.xex')
            xex = inventory['default.xex']
            if not 1 <= xex['size'] <= 64 * 1024 * 1024:
                raise InstallError('XEX 大小异常')
            identity = execution_id(disc.read(xex['offset'], xex['size']))
            if identity != expected['execution_id']:
                raise InstallError(f'Disc {index + 1} 身份不符：实际盘号 {identity["disc"]}，Title ID {identity["title_id"]} / Media ID {identity["media_id"]}')
            if disc.size != expected['size'] or disc.base != expected['partition_base']:
                raise InstallError(f'Disc {index + 1} 镜像版本或长度不符')
            if set(inventory) != {e['path'] for e in expected['files']}:
                raise InstallError(f'Disc {index + 1} 文件清单不符')
            for entry in expected['files']:
                if inventory[entry['path']]['size'] != entry['size']:
                    raise InstallError('原始文件长度不符：' + entry['path'])
            xex_expected = next(e for e in expected['files'] if e['path'] == 'default.xex')
            if disc.resource_hash(xex) != xex_expected['sha256']:
                raise InstallError('default.xex 摘要不符')
            if full:
                self.event('verify', f'校验 Disc {index + 1} 完整镜像', index * .12)
                last = [0.0]
                def progress(count):
                    now = time.monotonic()
                    if now - last[0] > .25:
                        self.event('verify', f'校验 Disc {index + 1}：{count / disc.size:.0%}', index * .12 + .12 * count / disc.size)
                        last[0] = now
                actual = sha_file(path, self.check_cancel, progress)
                if actual != expected['sha256']:
                    raise InstallError(f'Disc {index + 1} 完整 SHA256 不匹配，仅支持清单中记录的韩版原盘')
            self.event('verify', f'Disc {index + 1} 身份正确 · {identity["media_id"]}', level='success', disc=index + 1, full_hash_verified=full)
            discs.append((disc, inventory))
        if discs[0][0].path.samefile(discs[1][0].path):
            raise InstallError('两张光盘不能使用同一个文件')
        return discs

    def check_dlc(self, root):
        root = check_no_links(root)
        found = []
        for entry in self.bundle.data['dlc']:
            path = check_no_links(root / entry['name'])
            if (not path.is_file() or path.stat().st_size != entry['size']
                    or sha_file(path, self.check_cancel) != entry['sha256']):
                raise InstallError('DLC 原版缺失或版本不匹配：' + entry['name'])
            data = path.read_bytes()
            package = StfsPackage(data, entry['sha256'])
            info = package.inventory()
            if info['title_id'] != self.bundle.data['title_id'] or info['content_type'] != '00000002':
                raise InstallError('DLC Title ID / Content Type 不兼容')
            found.append((path, entry))
        return found

    def required_space(self, format_name, include_dlc):
        totals, scratch = [], 0
        for disc in self.bundle.data['discs']:
            totals.append(sum(e.get('output_size', e['size']) for e in disc['files']))
            scratch = max(scratch, sum(e['output_size'] for e in disc['files'] if 'patch' in e))
        dlc = sum(e['output_size'] for e in self.bundle.data['dlc']) if include_dlc else 0
        # Worst case: ZSTD can be slightly larger than its input. No compression
        # ratio assumption is used when deciding whether an install can start.
        return int(sum(totals) * 1.02) + dlc + (scratch if format_name == 'zar' else 0) + 512 * 1024 * 1024

    def run_native(self, args, progress_start, progress_end):
        self.check_cancel()
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        process = subprocess.Popen([str(self.bundle.tool('zar')), *map(str, args)],
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, encoding='utf-8', errors='replace', creationflags=creationflags)
        lines = []
        def read():
            for line in process.stdout:
                lines.append(line.rstrip())
        reader = threading.Thread(target=read, daemon=True)
        reader.start()
        try:
            cursor = 0
            while process.poll() is None:
                self.check_cancel()
                while cursor < len(lines):
                    line = lines[cursor]
                    cursor += 1
                    if line.startswith('PROGRESS '):
                        fraction = float(line.split()[1])
                        self.event('archive', 'ZArchive：' + line.split(' ', 2)[-1], progress_start + (progress_end-progress_start)*fraction)
                time.sleep(.05)
            reader.join()
            if process.returncode:
                raise InstallError('ZArchive 工具失败：' + '\n'.join(lines[-8:]))
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)
            reader.join(timeout=10)
            process.stdout.close()

    def install(self, images, output, format_name, dlc_root=None):
        if format_name not in ('zar', 'xex'):
            raise InstallError('请选择 ZAR 或 XEX')
        output = check_no_links(output)
        if output.exists() or not output.parent.is_dir():
            raise InstallError('输出目录已存在，或上级目录不存在；请选择一个全新目录')
        if output.is_relative_to(self.bundle.root) or self.bundle.root.is_relative_to(output):
            raise InstallError('输出目录必须与安装数据目录分离')
        for source in [*images, *([dlc_root] if dlc_root else [])]:
            source = check_no_links(source)
            if source == output or source.is_relative_to(output):
                raise InstallError('输出目录不能包含原版输入')
            if source.is_dir() and output.is_relative_to(source):
                raise InstallError('输出目录必须与原版 DLC 目录分离')
        required = self.required_space(format_name, dlc_root is not None)
        free = shutil.disk_usage(output.parent).free
        if free < required:
            raise InstallError(f'空间不足：保守需要 {required / 2**30:.1f} GiB，可用 {free / 2**30:.1f} GiB')
        lock = output.parent / ('.' + output.name + '.install-lock')
        token = uuid.uuid4().hex
        with lock.open('x', encoding='ascii') as stream:
            stream.write(token)
        stage = output.parent / ('.mc2-' + token + '.partial')
        logs = output.parent / 'MC2-Installer-Logs'
        log_path = logs / (token + '.jsonl')
        success = False
        try:
            check_no_links(logs)
            logs.mkdir(exist_ok=True)
            stage.mkdir()
            (stage / '.owner.json').write_text(json.dumps({'token':token, 'output':str(output), 'bundle':self.bundle.sha256, 'pid':os.getpid()}), encoding='utf-8')
            self.log = log_path.open('x', encoding='utf-8')
            self.event('prepare', '开始离线安装；原版文件只读', 0, log_path=str(log_path), required_bytes=required)
            discs = self.inspect(images, full=True)
            dlc = self.check_dlc(dlc_root) if dlc_root else []
            if not dlc_root:
                self.event('dlc', '本次未选择 DLC：仅输出本体', level='warning')
            receipt = dict(schema_version=1, kind='localization-install-receipt', bundle_sha256=self.bundle.sha256,
                           format=format_name, discs=[], dlc=[], game_runtime_tested=False,
                           original_inputs_modified=False, log_path=str(log_path))
            for n, ((disc, inventory), profile) in enumerate(zip(discs, self.bundle.data['discs']), 1):
                work = stage / '.work' / f'Disc{n}'
                tree = stage / f'Disc{n}' if format_name == 'xex' else work
                tree.mkdir(parents=True)
                sources, expected_files = [], []
                start = .25 + (n - 1) * .33
                total = len(profile['files'])
                with disc.path.open('rb') as iso:
                    for i, entry in enumerate(profile['files']):
                        self.check_cancel()
                        name = entry['path']
                        record = inventory[name]
                        offset, size = record['offset'], record['size']
                        out_hash = entry.get('output_sha256', entry['sha256'])
                        out_size = entry.get('output_size', entry['size'])
                        source_path = disc.path
                        if 'patch' in entry:
                            iso.seek(offset)
                            data = iso.read(size)
                            result = self.bundle.patch(data, entry, self.check_cancel)
                            target = tree / name
                            target.parent.mkdir(parents=True, exist_ok=True)
                            with target.open('xb') as stream:
                                stream.write(result)
                            source_path, offset = target, 0
                        elif format_name == 'xex':
                            target = tree / name
                            target.parent.mkdir(parents=True, exist_ok=True)
                            iso.seek(offset)
                            h = hashlib.sha256()
                            remaining = size
                            with target.open('xb') as stream:
                                while remaining:
                                    self.check_cancel()
                                    part = iso.read(min(4*1024*1024, remaining))
                                    if not part:
                                        raise InstallError('ISO 读取意外结束')
                                    stream.write(part)
                                    h.update(part)
                                    remaining -= len(part)
                            if h.hexdigest() != out_hash:
                                raise InstallError('提取后摘要不符：' + name)
                            source_path, offset = target, 0
                        if any(c in str(source_path) for c in '\t\r\n'):
                            raise InstallError('输入路径包含控制字符')
                        sources.append(f'{name}\t{source_path}\t{offset}\t{out_size}')
                        expected_files.append(dict(path=name, size=out_size, sha256=out_hash))
                        if i % 10 == 0 or i + 1 == total:
                            self.event('patch', f'Disc {n} · {i+1}/{total} · {name}', start + .16*(i+1)/total)
                if format_name == 'zar':
                    spec, report = work / '_sources.tsv', work / '_readback.tsv'
                    spec.write_text('\n'.join(sources)+'\n', encoding='utf-8', newline='\n')
                    archive = stage / f'{self.bundle.data["output_name"]}_Disc{n}.zar'
                    self.run_native(['create', spec, archive], start+.16, start+.26)
                    self.run_native(['verify', archive, report], start+.26, start+.32)
                    actual = []
                    for line in report.read_text(encoding='utf-8').splitlines():
                        sha, size, name = line.split('\t')
                        actual.append(dict(path=name, size=int(size), sha256=sha))
                    if sorted(actual, key=lambda e:e['path']) != sorted(expected_files, key=lambda e:e['path']):
                        raise InstallError('ZAR 读回清单或文件摘要不符')
                    archive_hash = sha_file(archive, self.check_cancel)
                    guarded_remove(work, stage)
                    disc_receipt = dict(disc=n, path=archive.name, sha256=archive_hash, files=expected_files)
                else:
                    for i, entry in enumerate(expected_files):
                        path = tree / entry['path']
                        if path.stat().st_size != entry['size'] or sha_file(path, self.check_cancel) != entry['sha256']:
                            raise InstallError('XEX 输出读回校验失败：' + entry['path'])
                        if i % 20 == 0:
                            self.event('readback', f'Disc {n} 读回校验 {i+1}/{total}', start+.16+.16*(i+1)/total)
                    disc_receipt = dict(disc=n, path=tree.name, files=expected_files)
                receipt['discs'].append(disc_receipt)
            for path, entry in dlc:
                self.check_cancel()
                self.event('dlc', '应用并验证 DLC：' + entry['label'], .92)
                result = self.bundle.patch(path.read_bytes(), entry, self.check_cancel)
                package = StfsPackage(result, entry['output_sha256'])
                info = package.inventory()
                if info['title_id'] != self.bundle.data['title_id'] or info['content_type'] != '00000002':
                    raise InstallError('DLC 输出身份不符')
                relative = f'Content/0000000000000000/{self.bundle.data["title_id"]}/00000002/{entry["name"]}'
                target = stage / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open('xb') as stream:
                    stream.write(result)
                if sha_file(target) != entry['output_sha256']:
                    raise InstallError('DLC 写入后摘要不符')
                receipt['dlc'].append(dict(path=relative, sha256=entry['output_sha256'], size=len(result)))
            self.check_cancel()
            if (stage / '.work').exists():
                guarded_remove(stage / '.work', stage)
            receipt['inputs'] = []
            for n, ((disc, _), expected) in enumerate(zip(discs, self.bundle.data['discs']), 1):
                self.event('source-readback', f'最终核对原版 Disc {n} 未变化', .95 + .015*(n-1))
                actual = sha_file(disc.path, self.check_cancel)
                if actual != expected['sha256']:
                    raise InstallError('处理期间原版 ISO 被其他程序更改，输出不予发布')
                receipt['inputs'].append(dict(path=str(disc.path),sha256=actual,size=disc.size))
            for path, entry in dlc:
                if sha_file(path, self.check_cancel) != entry['sha256']:
                    raise InstallError('处理期间原版 DLC 被其他程序更改')
            instructions = self.bundle.member('USAGE.txt', self.bundle.data['usage_sha256'])
            from .installer_usage import render_usage
            guide = render_usage(instructions.read_text(encoding='utf-8'), format_name,
                                 self.bundle.data['output_name'], bool(receipt['dlc']))
            (stage / '使用说明.txt').write_text(guide, encoding='utf-8')
            (stage / '安装结果.json').write_text(json.dumps(receipt, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
            # Atomic no-replace publication: a failed/cancelled run never creates
            # the final output name. No user data is merged or overwritten.
            self.event('publish', '全部输出校验通过，正在发布结果', .99)
            if output.exists():
                raise InstallError('安装过程中出现同名输出，已停止发布')
            publish_no_replace(stage, output)
            success = True
            self.event('complete', '本体与所选 DLC 已完成并通过文件校验', 1, level='success', output=str(output), receipt=receipt)
            return receipt
        except BaseException as error:
            self.event('cancelled' if isinstance(error, Cancelled) else 'failed', str(error), level='warning' if isinstance(error, Cancelled) else 'error', log_path=str(log_path))
            raise
        finally:
            if self.log:
                self.log.close()
                self.log = None
            if not success and stage.exists() and (stage / '.owner.json').is_file():
                guarded_remove(stage, output.parent, expected_token=token)
            if lock.exists() and lock.read_text(encoding='ascii') == token:
                lock.unlink()


def guarded_remove(path, parent, expected_token=None):
    path, parent = check_no_links(path), check_no_links(parent)
    if path == parent or not path.is_relative_to(parent):
        raise InstallError('临时清理路径不在本次工作目录内')
    if expected_token:
        if path.name != '.mc2-' + expected_token + '.partial':
            raise InstallError('临时目录标识不符')
        owner = json.loads((path / '.owner.json').read_text(encoding='utf-8'))
        if owner['token'] != expected_token:
            raise InstallError('临时目录所有权标记不符')
    # Refuse links anywhere before recursive deletion; preserve unexpected paths.
    for member in path.rglob('*'):
        check_no_links(member)
        if not (member.is_file() or member.is_dir()):
            raise InstallError('临时目录含非常规文件')
    shutil.rmtree(path)


def publish_no_replace(source, target):
    if os.name == 'nt':
        os.rename(source, target)  # Win32 MoveFile: never replace an existing path.
    elif os.sys.platform.startswith('linux'):
        libc = ctypes.CDLL(None, use_errno=True)
        result = libc.renameat2(-100, os.fsencode(source), -100, os.fsencode(target), 1)
        if result:
            raise OSError(ctypes.get_errno(), 'no-replace publication failed', str(target))
    else:
        if target.exists():
            raise FileExistsError(target)
        os.rename(source, target)


def process_alive(pid):
    integer(pid, 1, 2**32-1)
    if os.name == 'nt':
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x1000, False, pid)
        if handle:
            kernel.CloseHandle(handle)
            return True
        return ctypes.get_last_error() != 87  # access denied is not proof of exit
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def recover_interrupted(output, bundle_hash):
    """Explicit recovery, never auto-prune arbitrary old directories or saves."""
    output = check_no_links(output)
    if output.exists():
        raise InstallError('最终输出已存在；中断清理不会删除成功结果')
    lock = check_no_links(output.parent / ('.' + output.name + '.install-lock'))
    token = lock.read_text(encoding='ascii')
    if not re.fullmatch('[0-9a-f]{32}', token):
        raise InstallError('中断锁标识无效')
    stage = check_no_links(output.parent / ('.mc2-' + token + '.partial'))
    owner = json.loads((stage / '.owner.json').read_text(encoding='utf-8'))
    if owner['output'] != str(output) or owner['bundle'] != bundle_hash or owner['token'] != token:
        raise InstallError('中断任务清单身份不符')
    if process_alive(owner['pid']):
        raise InstallError('该安装进程仍在运行，请从原窗口取消')
    guarded_remove(stage, output.parent, expected_token=token)
    if lock.read_text(encoding='ascii') != token:
        raise InstallError('中断锁在清理期间变化')
    lock.unlink()
    return dict(stage='recovered',level='success',message='已清理核验过的中断任务；原版文件和日志保留')
