import json
import hashlib
from pathlib import Path
import tempfile
import unittest

from tools.audit_terminal_punctuation import classifications, corrected

ROOT = Path(__file__).resolve().parents[1]


class QuestNotificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base = ROOT / 'locales/zh-Hans'
        cls.contract = json.loads((base/'terminal-punctuation-v27.json').read_bytes())
        cls.plan = json.loads((base/'quest-notifications-v27.json').read_bytes())
        cls.review = json.loads((base/'candidate-decisions/quest-notifications-20261103.json').read_bytes())

    def test_status_and_counter_messages_remove_only_terminal_stop(self):
        for text in ['任务: %s 开始。', '任务 : %s 完成。', '任务 : %s 失败。',
                     '任务%s: 消灭克洛普斯 (%s / %s)。', 'Quest: 护送完成。']:
            with self.subTest(text=text):
                self.assertEqual(corrected(text, 'quest_notification', self.contract['rules']), text[:-1])

    def test_trailing_whitespace_and_internal_punctuation_are_preserved(self):
        text = '任务%s：取得物品，返回城镇。 \t'
        self.assertEqual(corrected(text, 'quest_notification', self.contract['rules']),
                         '任务%s：取得物品，返回城镇 \t')

    def test_exclamations_ellipsis_tokens_and_already_clean_labels_are_preserved(self):
        for text in ['任务%s: 营救人质！', '任务: 等待……', '任务: %s 开始',
                     '任务: %s 完成\\n', '任务: %s 完成{0}', '任务: 奖励1.5倍']:
            self.assertEqual(corrected(text, 'quest_notification', self.contract['rules']), text)

    def test_narrative_and_quest_descriptions_keep_existing_rules(self):
        rules = self.contract['rules']
        text = '为了让村民能安全地工作，\\n请消灭海边的3只克洛普斯'
        self.assertEqual(corrected(text, 'quest_description', rules), text+'。')
        for text, kind in [('任务必须完成。', 'dialogue'), ('存档点', 'menu_name'),
                           ('护送途中，若前往其他地区，该任务将失败。', 'system_message')]:
            self.assertEqual(corrected(text, kind, rules), text)

    def test_all_reviewed_ids_are_classified_and_only_91_need_changes(self):
        kinds = classifications(self.contract, ROOT)
        reviewed = {row['id']: row for row in self.review['entries']}
        edits = {row['id']: row for row in self.plan['entries']}
        self.assertEqual(len(reviewed), 95)
        self.assertEqual(len(edits), 91)
        self.assertEqual(set(edits), {k for k, v in reviewed.items() if v['changed']})
        self.assertEqual({k for k, v in kinds.items() if v == 'quest_notification'}, set(reviewed))
        for identity, row in reviewed.items():
            self.assertEqual(corrected(row['translation'], kinds[identity], self.contract['rules']), row['translation'])
            if identity in edits:
                self.assertEqual(edits[identity]['source_sha256'], row['before_sha256'])
                self.assertEqual(edits[identity]['translation'], row['translation'])

    def test_canonical_review_locks_accept_lf_and_crlf_without_rewriting_files(self):
        raw = b'{\n  "entries": [{"id": "a", "text_kind": "system_message"}]\n}\n'
        contract = dict(classification_hash_mode='canonical-lf', classification_overrides=[],
                        classification_sources=[dict(path='review.json', sha256=hashlib.sha256(raw).hexdigest())])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for data in [raw, raw.replace(b'\n', b'\r\n')]:
                (root/'review.json').write_bytes(data)
                self.assertEqual(classifications(contract, root), {'a': 'system_message'})
                self.assertEqual((root/'review.json').read_bytes(), data)

    def test_canonical_hash_does_not_accept_changed_classification_content(self):
        raw = b'{\n"entries": []\n}\n'
        contract = dict(classification_hash_mode='canonical-lf', classification_overrides=[],
                        classification_sources=[dict(path='review.json', sha256=hashlib.sha256(raw).hexdigest())])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'review.json').write_bytes(raw.replace(b'[]', b'[{}]').replace(b'\n', b'\r\n'))
            with self.assertRaisesRegex(ValueError, 'SHA256 mismatch'):
                classifications(contract, root)

    def test_legacy_raw_and_unknown_hash_modes_are_not_relaxed(self):
        raw = b'{\n"entries": []\n}\n'
        contract = dict(classification_overrides=[],
                        classification_sources=[dict(path='review.json', sha256=hashlib.sha256(raw).hexdigest())])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root/'review.json').write_bytes(raw.replace(b'\n', b'\r\n'))
            with self.assertRaisesRegex(ValueError, 'SHA256 mismatch'):
                classifications(contract, root)
            contract['classification_hash_mode'] = 'unknown'
            with self.assertRaisesRegex(ValueError, 'unsupported'):
                classifications(contract, root)


if __name__ == '__main__':
    unittest.main()
