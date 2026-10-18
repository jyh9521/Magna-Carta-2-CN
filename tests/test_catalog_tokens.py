import unittest
from tools.validate_catalog import validate

class ProtectedTokenTests(unittest.TestCase):
    def row(self, source, target):
        return {"schema_version":1,"entries":[dict(id="synthetic",resource="test",context="test",source_locale="und",source=source,translation=target,status="draft",reviewer="")]}

    def test_extended_tokens(self):
        for token in ("{name}", "{0:02d}", "%02d", "%s", "^0A", r"\t", "<tag>", "</tag>"):
            with self.subTest(token=token):
                self.assertTrue(validate(self.row("source "+token, "target")))
                self.assertEqual(validate(self.row("source "+token, "target "+token)), [])

    def test_order_is_protected(self):
        self.assertTrue(validate(self.row("%s %d", "%d %s")))
