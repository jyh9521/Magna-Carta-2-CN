"""Check versioned content; no game files or credentials required."""
import subprocess
import struct
from pathlib import PurePosixPath,Path

BLOCKED = {".iso", ".xex", ".exe", ".dll", ".pdb", ".xxx", ".upk", ".bik", ".xma", ".ttf", ".otf", ".pem", ".key", ".pfx"}
LOCAL = {"build", "dist", "out", "xenia", "original", "extracted", "unpacked"}

def executable_signature(path):
    """Catch complete ELF/PE images even when a forced Git add disguises suffixes."""
    with path.open('rb') as f:
        head=f.read(64)
        if head.startswith(b'\x7fELF'):return True
        if len(head)==64 and head[:2]==b'MZ':
            offset=struct.unpack_from('<I',head,0x3c)[0]
            if 64<=offset<=16*1024*1024:
                f.seek(offset)
                return f.read(4)==b'PE\0\0'
    return False

def violations(paths,root=None):
    errors = []
    for name in paths:
        p = PurePosixPath(name)
        if p.name == "AGENTS.md" or name == "docs/LOCALIZATION_STANDARD.md" or p.suffix.lower() in BLOCKED or any(part in LOCAL for part in p.parts):
            errors.append(name)
        elif root is not None and (Path(root)/name).is_file() and executable_signature(Path(root)/name):
            errors.append(name)
    return errors

def main():
    raw = subprocess.check_output(["git", "ls-files", "-z"])
    paths = raw.decode("utf-8").split("\0")
    errors = violations((p for p in paths if p),Path.cwd())
    if errors:
        print("FAIL repository hygiene: " + ", ".join(errors))
        return 1
    print("PASS repository hygiene")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
