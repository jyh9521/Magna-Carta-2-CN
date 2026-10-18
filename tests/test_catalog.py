import copy
import unittest
from tools.validate_catalog import validate


class CatalogTests(unittest.TestCase):
    def catalog(self):
        return {"schema_version": 1, "entries": [dict(id="fixture:1", resource="synthetic", context="test", source_locale="en", source="Test {0} %s$n", translation="测试 {0} %s$n", status="draft", reviewer="")]}

    def test_empty(self):
        self.assertEqual(validate({"schema_version": 1, "entries": []}), [])

    def test_valid(self):
        self.assertEqual(validate(self.catalog()), [])

    def test_missing_token(self):
        d = self.catalog(); d["entries"][0]["translation"] = "测试"; self.assertTrue(validate(d))

    def test_duplicate_token(self):
        d = self.catalog(); d["entries"][0]["translation"] += " {0}"; self.assertTrue(validate(d))

    def test_duplicate_id(self):
        d = self.catalog(); d["entries"].append(copy.deepcopy(d["entries"][0])); self.assertTrue(validate(d))

    def test_review_gate(self):
        d = self.catalog(); d["entries"][0]["status"] = "reviewed"; self.assertTrue(validate(d))

    def test_reviewed(self):
        d = self.catalog(); d["entries"][0].update(status="reviewed", reviewer="human"); self.assertEqual(validate(d), [])

    def test_bad_envelope(self):
        for d in ([], {}, {"schema_version": 2, "entries": []}):
            self.assertTrue(validate(d))

    def test_bad_field(self):
        d = self.catalog(); del d["entries"][0]["context"]; self.assertTrue(validate(d))

    def test_untranslated_not_empty(self):
        d = self.catalog(); d["entries"][0]["status"] = "untranslated"; self.assertTrue(validate(d))
