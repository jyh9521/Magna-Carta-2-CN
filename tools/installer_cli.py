"""JSON-lines backend. Frozen builds embed the trusted release manifest hash."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import threading
import traceback
import tempfile
import uuid

from tools.installer_core import Bundle, Installer, Cancelled, recover_interrupted


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stdin.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path)
    parser.add_argument('--manifest-sha256')
    parser.add_argument('--request', type=Path)
    parser.add_argument('--info', action='store_true')
    args = parser.parse_args(argv)
    frozen = bool(getattr(sys, 'frozen', False))
    if frozen:
        from installer_release import MANIFEST_SHA256
        expected = MANIFEST_SHA256
        root = Path(sys.executable).parent.parent / 'patch'
    else:
        expected, root = args.manifest_sha256, args.bundle
    diagnostic = None
    def emit(event):
        nonlocal diagnostic
        event = dict(event)
        if not args.info or event.get('stage') == 'failed':
            if diagnostic is None:
                directory = Path(os.environ.get('LOCALAPPDATA', tempfile.gettempdir())) / 'MC2Installer' / 'logs'
                directory.mkdir(parents=True, exist_ok=True)
                diagnostic = directory / (uuid.uuid4().hex + '.jsonl')
            event.setdefault('log_path', str(diagnostic))
            with diagnostic.open('a', encoding='utf-8') as log:
                log.write(json.dumps(event, ensure_ascii=False) + '\n')
        print(json.dumps(event, ensure_ascii=False), flush=True)
    try:
        if not root or not expected:
            raise ValueError('源码运行需提供 --bundle 和 --manifest-sha256')
        bundle = Bundle(root, expected)
        engine = Installer(bundle, emit)
        if args.info:
            emit(dict(stage='info', version=bundle.data['version'], title_id=bundle.data['title_id'],
                      required_xex=engine.required_space('xex', True), required_zar=engine.required_space('zar', True),
                      dlc=bundle.data['dlc'], manifest_sha256=expected))
            return 0
        request_path = args.request
        if not request_path or request_path.stat().st_size > 32768:
            raise ValueError('需要有效的安装请求文件')
        request = json.loads(request_path.read_text(encoding='utf-8'))
        def listen():
            try:
                for line in sys.stdin:
                    if line.strip() == 'cancel':
                        engine.cancel_event.set()
            except (OSError, ValueError):
                pass
        threading.Thread(target=listen, daemon=True).start()
        if request['operation'] == 'recover':
            emit(recover_interrupted(request['output'], expected))
            return 0
        images = [Path(request['disc1']), Path(request['disc2'])]
        if request['operation'] == 'inspect':
            engine.inspect(images, full=False)
            if request.get('include_dlc', True):
                engine.check_dlc(Path(request['dlc']))
            emit(dict(stage='inspected', level='success', message='两张光盘及所选 DLC 身份检查通过；安装时将校验完整 ISO'))
        elif request['operation'] == 'install':
            engine.install(images, Path(request['output']), request['format'],
                           Path(request['dlc']) if request.get('include_dlc', True) else None)
        else:
            raise ValueError('未知操作')
        return 0
    except Cancelled as error:
        emit(dict(stage='cancelled', level='warning', message=str(error)))
        return 130
    except Exception as error:
        emit(dict(stage='failed', level='error', message=str(error), detail=traceback.format_exc()))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
