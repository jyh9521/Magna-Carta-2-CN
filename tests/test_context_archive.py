import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_line_context_suite import split
from tools.audit_context_archive import audit_pages, load_pages, main
from tools.audit_line_context import canonical, digest
from tools.audit_line_context_suite import audit_many


def indexed(root):
    data, plan, profile, parts = split()
    refs = []
    for i, part in enumerate(parts):
        path = root / f'profiles/part-{i}.json'
        path.parent.mkdir(exist_ok=True)
        raw = json.dumps(part).encode()
        path.write_bytes(raw)
        refs.append(dict(id=f'page-{i}', profiles=[
            dict(path=path.relative_to(root).as_posix(), sha256=digest(raw))]))
    index = dict(schema_version=1, kind='source-locked-context-archive',
                 resource='fixture', input_sha256=digest(data),
                 plan_canonical_sha256=canonical(plan), human_finalized=False,
                 runtime_layout_approved=False, pages=refs)
    return data, plan, index


class ContextArchiveTests(unittest.TestCase):
    def test_single_page_is_original_suite_plus_explicit_provenance(self):
        data, plan, profile, parts = split()
        original = audit_many(data, plan, parts)
        report = audit_pages(data, plan, [parts])
        report.pop('pages')
        report['kind'] = original['kind']
        self.assertEqual(report, original)

    def test_disjoint_pages_keep_source_order_controls_and_policy_budget(self):
        data, plan, profile, parts = split()
        before = copy.deepcopy(parts)
        one = audit_pages(data, plan, [[parts[0]], [parts[1]]])
        two = audit_pages(data, plan, [[parts[1]], [parts[0]]])
        for key in ('context', 'policies', 'protected_breaks'):
            self.assertEqual(one[key], two[key])
        self.assertEqual(one['context_entries'], 3)
        self.assertEqual(one['pending_runtime_layout_policies'], 1)
        self.assertEqual(one['policy_entries'], 1)
        self.assertEqual(one['translation_edits'], 0)
        self.assertFalse(one['human_finalized'])
        self.assertFalse(one['runtime_layout_approved'])
        self.assertFalse(one['game_rendering_verified'])
        self.assertEqual(parts, before)

    def test_cross_page_overlap_rejected_even_when_identical(self):
        data, plan, profile, parts = split()
        with self.assertRaisesRegex(ValueError, 'overlapping context pages'):
            audit_pages(data, plan, [[parts[0]], [parts[0]]])

    def test_outer_page_and_original_inner_profile_scope_bounds(self):
        data, plan, profile, parts = split()
        for pages in (None, [], (), [[profile]] * 17):
            with self.subTest(pages=type(pages)), self.assertRaisesRegex(ValueError, 'page bound'):
                audit_pages(data, plan, pages)
        with self.assertRaisesRegex(ValueError, 'suite bound'):
            audit_pages(data, plan, [[profile] * 17])
        profile['scopes'] *= 17
        with self.assertRaisesRegex(ValueError, 'scope bound'):
            audit_pages(data, plan, [[profile]])

    def test_original_total_member_budget_is_not_multiplied_by_pages(self):
        data, plan, profile, parts = split()
        original = audit_many(data, plan, parts)
        for count in (16000, 16001):
            report = copy.deepcopy(original)
            report['context'] = [dict(id=f'id-{i}') for i in range(count)]
            report['protected_breaks'] = []
            order = [dict(id=row['id']) for row in report['context']]
            with self.subTest(count=count), patch(
                    'tools.audit_context_archive.audit_many', return_value=report), patch(
                    'tools.audit_context_archive.extract_entries', return_value=order):
                if count == 16000:
                    self.assertEqual(audit_pages(data, plan, [[profile]])['context_entries'], count)
                else:
                    with self.assertRaisesRegex(ValueError, 'total member bound'):
                        audit_pages(data, plan, [[profile]])

    def test_index_loads_exact_hashed_profiles_and_does_not_mutate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data, plan, index = indexed(root)
            before = copy.deepcopy(index)
            pages, snapshots = load_pages(index, root, data, plan)
            self.assertEqual(audit_pages(data, plan, pages)['context_entries'], 3)
            self.assertEqual(len(snapshots), 2)
            self.assertEqual(index, before)

    def test_index_identity_and_approval_drift_rejected(self):
        for key, value in [('schema_version', True), ('kind', 'other'),
                           ('resource', 'other'), ('input_sha256', '0' * 64),
                           ('plan_canonical_sha256', '0' * 64),
                           ('human_finalized', True), ('runtime_layout_approved', True)]:
            with tempfile.TemporaryDirectory() as directory:
                data, plan, index = indexed(Path(directory))
                index[key] = value
                with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'identity or approval'):
                    load_pages(index, directory, data, plan)

    def test_index_rejects_duplicate_page_ids_and_profile_aliases(self):
        with tempfile.TemporaryDirectory() as directory:
            data, plan, index = indexed(Path(directory))
            index['pages'][1]['id'] = index['pages'][0]['id']
            with self.assertRaisesRegex(ValueError, 'page id'):
                load_pages(index, directory, data, plan)
            index['pages'][1]['id'] = 'second'
            index['pages'][1]['profiles'] = copy.deepcopy(index['pages'][0]['profiles'])
            with self.assertRaisesRegex(ValueError, 'duplicate context profile path'):
                load_pages(index, directory, data, plan)

    def test_index_rejects_escape_noncanonical_paths_and_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            data, plan, index = indexed(Path(directory))
            for text in ('', '/outside.json', '../outside.json', 'profiles/../part.json',
                         'C:/outside.json', 'profiles\\part.json', './part.json', 'profiles//part.json'):
                broken = copy.deepcopy(index)
                broken['pages'][0]['profiles'][0]['path'] = text
                with self.subTest(text=text), self.assertRaisesRegex(ValueError, 'profile path'):
                    load_pages(broken, directory, data, plan)
            with patch.object(Path, 'is_symlink', return_value=True):
                with self.assertRaisesRegex(ValueError, 'escapes or aliases'):
                    load_pages(index, directory, data, plan)

    def test_profile_raw_hash_and_member_target_locks_are_both_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data, plan, index = indexed(root)
            path = root / index['pages'][0]['profiles'][0]['path']
            profile = json.loads(path.read_bytes())
            profile['entries'][0]['translation_sha256'] = '0' * 64
            path.write_text(json.dumps(profile))
            with self.assertRaisesRegex(ValueError, 'byte hash'):
                load_pages(index, root, data, plan)
            index['pages'][0]['profiles'][0]['sha256'] = digest(path.read_bytes())
            pages, snapshots = load_pages(index, root, data, plan)
            with self.assertRaisesRegex(ValueError, 'membership/order/hash'):
                audit_pages(data, plan, pages)

    def test_index_rejects_empty_oversized_or_nonobject_pages(self):
        with tempfile.TemporaryDirectory() as directory:
            data, plan, index = indexed(Path(directory))
            for pages in ([], index['pages'] * 9, [None]):
                broken = copy.deepcopy(index)
                broken['pages'] = pages
                with self.assertRaises((ValueError, AttributeError)):
                    load_pages(broken, directory, data, plan)
            for profiles in ([], index['pages'][0]['profiles'] * 17):
                broken = copy.deepcopy(index)
                broken['pages'][0]['profiles'] = profiles
                with self.assertRaisesRegex(ValueError, 'suite bound'):
                    load_pages(broken, directory, data, plan)

    def test_cli_success_existing_output_and_input_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data, plan, index = indexed(root)
            files = [('source', data), ('plan', json.dumps(plan).encode()),
                     ('index', json.dumps(index).encode())]
            for name, raw in files:
                (root / name).write_bytes(raw)
            output = root / 'report'
            args = sum([['--' + name, str(root / name)] for name in ('source', 'plan', 'index')], [])
            args += ['--output', str(output)]
            self.assertEqual(main(args), 0)
            before = output.read_bytes()
            self.assertEqual(main(args), 2)
            self.assertEqual(output.read_bytes(), before)
            original = audit_pages

            def drift(*a):
                result = original(*a)
                (root / index['pages'][0]['profiles'][0]['path']).write_bytes(b'changed')
                return result

            other = root / 'other'
            with patch('tools.audit_context_archive.audit_pages', side_effect=drift):
                self.assertEqual(main(args[:-1] + [str(other)]), 2)
            self.assertFalse(other.exists())
