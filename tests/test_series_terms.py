"""Synthetic and repository-source tests; no game files or network required."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from tools import series_terms as st


class SeriesTermsTests(unittest.TestCase):
    def row(self, source="NAME", target="译名", ref="one", state="approved"):
        return dict(source=source, target=target, reference=ref, commit="a"*40,
                    source_id="name-1", translation_state=state, category="person", relation="pending", context="context")

    def term(self):
        return dict(id="name-1", source="NAME", target="译名", category="person",
                    resource="fixture.bin", source_string_id="fixture:1", review_status="reviewed",
                    relation="unverified", basis="synthetic evidence", form="short-name", series_references=[])

    def database(self, *terms):
        return dict(schema=1, locale="test", terms=list(terms))

    def test_exact_no_substring(self):
        rows = [self.row("NAME LONG"), self.row("NAME")]
        self.assertEqual([r["source"] for r in st.lookup(rows, "NAME")], ["NAME"])
        self.assertEqual(st.lookup(rows, "name"), [])

    def test_variants_only_explicit(self):
        self.assertEqual(len(st.lookup([self.row("Name")], "NAME", ["Name"])), 1)
        self.assertEqual(st.lookup([self.row(" A ")], "A"), [])

    def test_retains_pending_context(self):
        row = self.row()
        self.assertEqual(st.lookup([row], "NAME")[0], row)
        self.assertEqual(st.lookup([row], "NAME")[0]["relation"], "pending")

    def test_markdown_only_glossary(self):
        text = "## 术语表\n| Korean / 源文 | 中文译名 | 分类 | 状态 | 备注 / 参考 |\n|---|---|---|---|---|\n| Name | Name CN | person | draft | A\\|B |\n## 人物性别与第三人称校对基准\n| Other | Male | He | Other | ignored |"
        rows = st.markdown_rows(text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["context"], "A|B")
        self.assertEqual(rows[0]["translation_state"], "draft")

    def test_conflicts_no_implicit_choice(self):
        result = st.audit([self.row(), self.row(target="另译", ref="two")])
        self.assertEqual(len(result["cross_reference_conflicts"]), 1)
        self.assertEqual(len(result["cross_reference_conflicts"][0]["candidates"]), 2)
        self.assertEqual(result["inherited_terms"], 0)

    def test_internal_conflict(self):
        self.assertEqual(len(st.audit([self.row(), self.row(target="另译")])["within_reference_conflicts"]), 1)

    def test_no_match_not_new_concept(self):
        self.assertEqual(st.lookup([self.row()], "UNKNOWN"), [])
        self.assertEqual(st.validate_terms(self.database(self.term())), [])

    def test_missing_provenance_and_status(self):
        t = self.term(); del t["resource"]; del t["review_status"]
        errors = st.validate_terms(self.database(t))
        self.assertTrue(any("missing resource" in e for e in errors))
        self.assertTrue(any("review status" in e for e in errors))

    def test_duplicate_ids(self):
        self.assertTrue(any("duplicate" in e for e in st.validate_terms(self.database(self.term(), self.term()))))

    def test_same_source_requires_disambiguation(self):
        a, b = self.term(), self.term(); b.update(id="name-2", target="另译")
        self.assertTrue(any("disambiguation" in e for e in st.validate_terms(self.database(a, b))))
        a["disambiguation"] = "one concept"; b["disambiguation"] = "another concept"
        self.assertEqual(st.validate_terms(self.database(a, b)), [])

    def test_series_change_requires_explanation(self):
        t = self.term(); row = self.row()
        t.update(target="另译", relation="same-concept", series_references=[row])
        self.assertTrue(any("changed" in e for e in st.validate_terms(self.database(t), [row])))
        t["override_reason"] = "maintainer-approved differentiation"
        self.assertEqual(st.validate_terms(self.database(t), [row]), [])

    def test_pinned_reference_identity(self):
        t = self.term(); row = self.row(); t["series_references"] = [dict(row, commit="b"*40)]
        self.assertTrue(any("identity" in e for e in st.validate_terms(self.database(t), [row])))

    def test_fuzzy_merge_requires_evidence(self):
        t = self.term(); row = self.row(source="NAME LONG"); t["series_references"] = [row]
        self.assertTrue(any("spelling variant" in e for e in st.validate_terms(self.database(t), [row])))

    def test_missing_relation_reference(self):
        t = self.term(); t["relation"] = "same-concept"
        self.assertTrue(any("requires reference" in e for e in st.validate_terms(self.database(t))))

    def test_candidate_translation_signal(self):
        t = self.term(); t["review_status"] = "candidate"
        errors = st.validate_terms(self.database(t), [], [dict(id="s1", target="a译名b", term_ids=["name-1"])])
        self.assertTrue(any("unreviewed candidate" in e for e in errors))
        self.assertTrue(any("candidate wording" in e for e in errors))

    def test_translation_name_form_mismatch(self):
        t = self.term()
        errors = st.validate_terms(self.database(t), [], [dict(id="s1", term_ids=["name-1"], term_forms={"name-1": "full-name"})])
        self.assertTrue(any("name form mismatch" in e for e in errors))

    def test_invalid_name_form(self):
        t = self.term(); t["form"] = "combined"
        self.assertTrue(any("name form" in e for e in st.validate_terms(self.database(t))))

    def test_comparison_preserves_before_after(self):
        a = self.row(); b = dict(a, target="另译", commit="b"*40)
        result = st.compare([a], [b])
        self.assertEqual(result["changed"][0], dict(before=a, after=b))
        self.assertEqual(st.compare([a], [dict(a, commit="b"*40)])["changed"], [])

    def test_lock_paths_and_commit(self):
        for path in ["../escape", "/absolute", "C:/absolute", "a\\b"]:
            lock = dict(schema=1, references=[dict(id="one", repository="owner/repo", commit="a"*40, files=[dict(path=path, sha256="b"*64)])])
            with self.assertRaises(ValueError): st.checked_lock(lock)
        with self.assertRaises(ValueError):
            st.checked_lock(dict(schema=1, references=[dict(id="one", repository="owner/repo", commit="main", files=[])]))

    def test_cache_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/"one"/"a"; p.parent.mkdir(); p.write_bytes(b"changed")
            with self.assertRaises(ValueError):
                st.cached_bytes(tmp, dict(id="one"), dict(path="a", sha256=st.digest(b"original")))

    def test_fetch_existing_does_not_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/"one"/"a"; p.parent.mkdir(); p.write_bytes(b"original")
            lock = dict(schema=1, references=[dict(id="one", repository="owner/repo", commit="a"*40, files=[dict(path="a", sha256=st.digest(b"original"))])])
            self.assertEqual(st.fetch(lock, tmp)["verified_files"], 1)

    def test_generated_glossary_deterministic(self):
        text = st.glossary(self.database())
        self.assertIn("本作词条：0；已继承：0", text)
        self.assertEqual(text, st.glossary(self.database()))


class RepositoryGlossaryTests(unittest.TestCase):
    def test_committed_glossary_matches_current_terms(self):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            status = st.main(["render", "--check"])
        self.assertEqual(
            status, 0,
            errors.getvalue() + "Run python tools/series_terms.py render and commit "
            "GLOSSARY.md together with locales/zh-Hans/terms.json.",
        )
        self.assertEqual(json.loads(output.getvalue()), {"glossary": "current"})


if __name__ == "__main__":
    unittest.main()
