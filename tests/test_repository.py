import unittest
from tools.check_repository import violations

class RepositoryTests(unittest.TestCase):
    def test_proprietary_and_local(self):
        names = ["disc.iso", "game/default.xex", "AGENTS.md", "docs/LOCALIZATION_STANDARD.md", "build/source.json", "xenia/LICENSE", "font.TTF", "key.pem"]
        self.assertEqual(violations(names), names)

    def test_public_source(self):
        self.assertEqual(violations(["tools/coalesced.py", "tests/test_disc_inventory.py", ".github/workflows/validate.yml", "LICENSE"]), [])
