import unittest
from tools.text_line_layout import audit, reflow, atoms
from tools.subtitle_text import rebuild_reversible, digest


RULES = dict(atomic_pairs={'[':']'}, no_line_start='，。！？；：)]',
             no_line_end='([', repeat_pairs='…—', preferred_break_after='，。！？；：',
             natural_break_min_fraction=.5)


class TextLineLayoutTests(unittest.TestCase):
    def table(self, text):
        return {ord(c):10 for c in text}

    def test_closing_punctuation_never_starts_new_line(self):
        text = '甲乙丙丁，戊己。'
        widths = self.table(text)
        self.assertFalse(audit(text, widths, 40, RULES)['passed'])
        out = reflow(text, widths, 40, RULES)
        self.assertEqual(out.replace('\\n', ''), text)
        self.assertTrue(audit(out, widths, 40, RULES)['passed'])
        self.assertNotIn('\\n，', out)
        self.assertNotIn('\\n。', out)

    def test_atomic_bracket_stays_intact(self):
        text = '甲乙[AB]，丙丁。'
        out = reflow(text, self.table(text), 60, RULES)
        self.assertIn('[AB]', out)
        self.assertTrue(audit(out, self.table(text), 60, RULES)['passed'])

    def test_explicit_bad_break_is_moved_without_changing_content(self):
        text = '甲乙[AB\\n]，丙丁。'
        out = reflow(text, self.table(text), 80, RULES)
        self.assertIn('[AB]', out)
        self.assertEqual(text.replace('\\n', ''), out.replace('\\n', ''))

    def test_functional_empty_line_and_whitespace_stay(self):
        text = '甲乙。\\n\\n 丙丁。'
        self.assertEqual(reflow(text, self.table(text), 100, RULES), text)

    def test_unresolved_placeholder_or_lone_separator_rejected(self):
        for text in ('甲%s乙', '甲\\乙', '<Strings:Unknown.X.Y>'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                reflow(text, self.table(text), 100, RULES)

    def test_style_icons_have_actual_advance_and_protected_order(self):
        text = '<Styles:icons>A<Styles:/>甲乙丙丁'
        out = reflow(text, self.table(text), 45, RULES, icon_widths={'icons':{65:25}})
        self.assertTrue(out.startswith('<Styles:icons>A<Styles:/>甲乙'))
        self.assertEqual(out.replace('\\n', ''), text)
        self.assertTrue(audit(out, self.table(text), 45, RULES, icon_widths={'icons':{65:25}})['passed'])

    def test_height_failure_is_visible(self):
        self.assertFalse(audit('甲\\n乙\\n丙', self.table('甲乙丙'), 20, RULES, max_lines=2)['passed'])

    def test_reviewed_soft_break_reflow_keeps_blank_paragraphs(self):
        text = '甲\\n乙\\n\\n丙\\n丁'
        out = reflow(text, self.table(text), 40, RULES, merge_soft_breaks=True)
        self.assertEqual(out, '甲乙\\n\\n丙丁')

    def test_paragraph_leading_pause_is_not_an_orphan(self):
        r = RULES | {'no_line_start': RULES['no_line_start']+'…'}
        text = '甲乙。\\n\\n……丙丁。'
        self.assertTrue(audit(text, self.table(text), 100, r)['passed'])

    def test_oversize_atomic_word_rejected(self):
        with self.assertRaisesRegex(ValueError, 'atomic run'):
            reflow('[ABCDE]', self.table('[ABCDE]'), 40, RULES)

    def test_explicit_timed_break_policy_roundtrips(self):
        raw = b'\xff\xfe'+('1\r\n<SYNC Start=0><P Class=KRCC>甲乙丙丁。'
                              '<SYNC Start=1000><P Class=KRCC>&nbsp;\r\n').encode('utf-16-le')
        plan = dict(schema_version=1, kind='timed-subtitle-text', input_sha256=digest(raw),
                    entries=[dict(start=0, end=1000, source_sha256=digest('甲乙丙丁。'.encode()),
                                  translation='甲乙<br>丙丁。', break_policy=dict(token='<br>', source_count=0, target_count=1))])
        out, proof = rebuild_reversible(raw, plan)
        self.assertNotEqual(out, raw)
        self.assertTrue(proof['inverse_rebuild_byte_identical'])

    def test_timed_break_policy_rejects_other_control_edits(self):
        raw = b'\xff\xfe'+('1\r\n<SYNC Start=0><P Class=KRCC>甲乙<br>丙丁。'
                              '<SYNC Start=1000><P Class=KRCC>&nbsp;\r\n').encode('utf-16-le')
        for policy in (dict(token='<BR>', source_count=1, target_count=0),
                       dict(token='<br>', source_count=0, target_count=0)):
            plan = dict(schema_version=1, kind='timed-subtitle-text', input_sha256=digest(raw),
                    entries=[dict(start=0, end=1000, source_sha256=digest('甲乙<br>丙丁。'.encode()),
                                  translation='甲乙丙丁。', break_policy=policy)])
            with self.assertRaises(ValueError): rebuild_reversible(raw, plan)


if __name__ == '__main__': unittest.main()
