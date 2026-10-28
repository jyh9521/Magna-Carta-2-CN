"""Run an owned Windows GUI batch tool on a private, never-displayed desktop.

This is window isolation, not a security sandbox. No elevation or desktop switch
is performed. A kill-on-close job owns the suspended child before it can run.
"""
from __future__ import annotations

import ctypes as C
from ctypes import wintypes as W
import os
from pathlib import Path
import subprocess
import time
import uuid


def run(argv, *, timeout=120, cwd=None):
    if os.name != 'nt':
        raise OSError('Private GUI desktops require Windows')
    if not argv or not 0 < timeout <= 3600:
        raise ValueError('Explicit command and bounded timeout required')
    executable = Path(argv[0]).resolve(strict=True)
    if not executable.is_file():
        raise ValueError('Executable must be a file')
    k = C.WinDLL('kernel32', use_last_error=True)
    u = C.WinDLL('user32', use_last_error=True)
    H = W.HANDLE
    S = C.c_size_t
    class SI(C.Structure):
        _fields_ = [('cb', W.DWORD), ('reserved', W.LPWSTR), ('desktop', W.LPWSTR),
            ('title', W.LPWSTR), ('x', W.DWORD), ('y', W.DWORD), ('cx', W.DWORD),
            ('cy', W.DWORD), ('xc', W.DWORD), ('yc', W.DWORD), ('fill', W.DWORD),
            ('flags', W.DWORD), ('show', W.WORD), ('reserved2size', W.WORD),
            ('reserved2', C.POINTER(W.BYTE)), ('stdin', H), ('stdout', H), ('stderr', H)]
    class PI(C.Structure):
        _fields_ = [('process', H), ('thread', H), ('pid', W.DWORD), ('tid', W.DWORD)]
    class BL(C.Structure):
        _fields_ = [('process_time', C.c_longlong), ('job_time', C.c_longlong),
            ('flags', W.DWORD), ('minws', S), ('maxws', S), ('active', W.DWORD),
            ('affinity', S), ('priority', W.DWORD), ('scheduling', W.DWORD)]
    class EL(C.Structure):
        _fields_ = [('basic', BL), ('io', C.c_ulonglong * 6), ('processmem', S),
            ('jobmem', S), ('peakprocessmem', S), ('peakjobmem', S)]
    callback = C.WINFUNCTYPE(W.BOOL, H, W.LPARAM)
    def signature(dll, name, args, result):
        fn = getattr(dll, name); fn.argtypes = args; fn.restype = result; return fn
    create = signature(u, 'CreateDesktopW', [W.LPCWSTR, W.LPCWSTR, C.c_void_p, W.DWORD, W.DWORD, C.c_void_p], H)
    close_desktop = signature(u, 'CloseDesktop', [H], W.BOOL)
    input_desktop = signature(u, 'OpenInputDesktop', [W.DWORD, W.BOOL, W.DWORD], H)
    info = signature(u, 'GetUserObjectInformationW', [H, C.c_int, C.c_void_p, W.DWORD, C.POINTER(W.DWORD)], W.BOOL)
    station = signature(u, 'GetProcessWindowStation', [], H)
    enum = signature(u, 'EnumDesktopWindows', [H, callback, W.LPARAM], W.BOOL)
    caption = signature(u, 'GetWindowTextW', [H, W.LPWSTR, C.c_int], C.c_int)
    create_job = signature(k, 'CreateJobObjectW', [C.c_void_p, W.LPCWSTR], H)
    set_job = signature(k, 'SetInformationJobObject', [H, C.c_int, C.c_void_p, W.DWORD], W.BOOL)
    assign = signature(k, 'AssignProcessToJobObject', [H, H], W.BOOL)
    terminate_job = signature(k, 'TerminateJobObject', [H, W.UINT], W.BOOL)
    close = signature(k, 'CloseHandle', [H], W.BOOL)
    launch = signature(k, 'CreateProcessW', [W.LPCWSTR, W.LPWSTR, C.c_void_p, C.c_void_p,
        W.BOOL, W.DWORD, C.c_void_p, W.LPCWSTR, C.POINTER(SI), C.POINTER(PI)], W.BOOL)
    resume = signature(k, 'ResumeThread', [H], W.DWORD)
    wait = signature(k, 'WaitForSingleObject', [H, W.DWORD], W.DWORD)
    exit_code = signature(k, 'GetExitCodeProcess', [H, C.POINTER(W.DWORD)], W.BOOL)
    terminate = signature(k, 'TerminateProcess', [H, W.UINT], W.BOOL)
    def checked(value):
        if not value: raise C.WinError(C.get_last_error())
        return value
    def name(handle):
        buffer = C.create_unicode_buffer(512); size = W.DWORD()
        checked(info(handle, 2, buffer, C.sizeof(buffer), C.byref(size)))
        return buffer.value
    def current():
        handle = checked(input_desktop(0, False, 1))
        try: return name(handle)
        finally: close_desktop(handle)
    before = current()
    desktop_name = 'localization-batch-' + uuid.uuid4().hex
    desktop = checked(create(desktop_name, None, None, 0, 0x00ff, None))
    job = None; process = PI(); started = time.monotonic(); titles = set()
    try:
        job = checked(create_job(None, None))
        limits = EL(); limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        checked(set_job(job, 9, C.byref(limits), C.sizeof(limits)))
        startup = SI(); startup.cb = C.sizeof(SI)
        startup.desktop = name(station()) + '\\' + desktop_name
        startup.flags = 1; startup.show = 0  # STARTF_USESHOWWINDOW / SW_HIDE
        command = C.create_unicode_buffer(subprocess.list2cmdline([str(executable), *map(str, argv[1:])]))
        checked(launch(str(executable), command, None, None, False, 0x08000004,
            None, str(Path(cwd).resolve()) if cwd else None, C.byref(startup), C.byref(process)))
        checked(assign(job, process.process))
        if resume(process.thread) == 0xffffffff: raise C.WinError(C.get_last_error())
        @callback
        def record(window, parameter):
            buffer = C.create_unicode_buffer(2048)
            if caption(window, buffer, len(buffer)): titles.add(buffer.value)
            return True
        timed_out = False
        while True:
            enum(desktop, record, 0)
            result = wait(process.process, 100)
            if result == 0: break
            if result != 258: raise C.WinError(C.get_last_error())
            if time.monotonic() - started >= timeout:
                timed_out = True
                checked(terminate_job(job, 124)); checked(wait(process.process, 10000) == 0)
                break
        code = W.DWORD(); checked(exit_code(process.process, C.byref(code)))
        after = current()
        return dict(exit_code=code.value, timed_out=timed_out, pid=process.pid,
            private_desktop=desktop_name, input_desktop_before=before,
            input_desktop_after=after, input_desktop_unchanged=before == after,
            desktop_switched=False, window_titles=sorted(titles),
            elapsed_seconds=round(time.monotonic()-started, 3), child_tree_closed=True)
    finally:
        if process.process:
            # Also handles assignment/resume failures while the child is suspended.
            if wait(process.process, 0) == 258: terminate(process.process, 124)
        if job: close(job)
        if process.thread: close(process.thread)
        if process.process: wait(process.process, 10000); close(process.process)
        close_desktop(desktop)
