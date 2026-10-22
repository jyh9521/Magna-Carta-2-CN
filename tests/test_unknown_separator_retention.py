import unittest
import hashlib
from tools.coalesced import EmbeddedFile, SerializedString, serialize, parse, extract_entries
from tools.build_coalesced import rebuild
from tools.validate_catalog import token_errors
from tools.audit_text_font_coverage import literal_codepoints


class UnknownSeparatorRetentionTests(unittest.TestCase):
    def test_unknown_separator_is_retained_without_locking_following_language(self):
        self.assertEqual(token_errors('앞\\뒤', '前\\后'), [])

    def test_retained_unknown_separator_still_demands_a_visible_glyph(self):
        self.assertIn(92, literal_codepoints('前\\后'))
        self.assertNotIn(92, literal_codepoints('前\\n后'))

    def test_deletion_and_insertion_are_rejected(self):
        self.assertIn('protected token mismatch', token_errors('앞\\뒤', '前后'))
        self.assertIn('protected token mismatch', token_errors('앞뒤', '前\\后'))

    def test_unknown_separator_does_not_become_known_escape(self):
        self.assertIn('protected token mismatch', token_errors('앞\\뒤', '前\\n后'))

    def test_known_escape_order_is_not_hidden_by_lone_separator(self):
        self.assertEqual(token_errors('앞\\뒤\\n끝', '前\\后\\n尾'), [])
        self.assertIn('protected token order changed (not yet verified)', token_errors('앞\\뒤\\n끝', '前\\n后\\尾'))

    def test_explicit_layout_break_policy_cannot_waive_unknown_separator(self):
        policy = dict(source_count=1, target_count=0)
        self.assertEqual(token_errors('앞\\뒤\\n끝', '前\\后尾', policy), [])
        self.assertIn('protected token mismatch', token_errors('앞\\뒤\\n끝', '前后尾', policy))

    def test_rebuild_preserves_separator_and_rejects_its_deletion(self):
        data = serialize([EmbeddedFile(SerializedString('demo.int', 'ascii', 0),
                         SerializedString('[Demo]\nText=前\\后\n', 'utf-16-le', 0))])
        row = extract_entries(parse(data), 'demo.int')[0]
        plan = dict(schema_version=1, resource='demo.int',
                    input_sha256=hashlib.sha256(data).hexdigest(),
                    entries=[dict(id=row['id'], source=row['source'], translation='左\\右')])
        result = rebuild(data, plan)
        self.assertEqual(extract_entries(parse(result), 'demo.int')[0]['source'], '左\\右')
        self.assertEqual(extract_entries(parse(data), 'demo.int')[0]['source'], '前\\后')
        plan['entries'][0]['translation'] = '左右'
        with self.assertRaises(ValueError):
            rebuild(data, plan)

    def test_markup_is_still_one_protected_token(self):
        self.assertEqual(token_errors('<path:A\\B>앞', '<path:A\\B>前'), [])
        self.assertIn('protected token mismatch', token_errors('<path:A\\B>앞', '<path:A/B>前'))


if __name__ == '__main__':
    unittest.main()
