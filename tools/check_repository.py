"""Check versioned content; no game files or credentials required."""
import subprocess
from pathlib import PurePosixPath

BLOCKED = {".iso", ".xex", ".exe", ".dll", ".pdb", ".xxx", ".upk", ".bik", ".xma", ".ttf", ".otf", ".pem", ".key", ".pfx"}
LOCAL = {"build", "dist", "out", "xenia", "original", "extracted", "unpacked"}

def violations(paths):
    errors = []
    for name in paths:
        p = PurePosixPath(name)
        if p.name == "AGENTS.md" or name == "docs/LOCALIZATION_STANDARD.md" or p.suffix.lower() in BLOCKED or any(part in LOCAL for part in p.parts):
            errors.append(name)
    return errors

def main():
    raw = subprocess.check_output(["git", "ls-files", "-z"])
    paths = raw.decode("utf-8").split("\0")
    errors = violations(p for p in paths if p)
    if errors:
        print("FAIL repository hygiene: " + ", ".join(errors))
        return 1
    print("PASS repository hygiene")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
