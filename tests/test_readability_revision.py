"""Current text revisions do not rewrite historical font/style experiments."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

from tools.audit_line_context import atoms
from tools.audit_text_font_coverage import literal_codepoints
from tools.validate_catalog import TOKEN

ROOT = Path(__file__).resolve().parents[1]
BASELINE = 'locales/zh-Hans/readability-fix.json'
CURRENT = 'locales/zh-Hans/readability-revised.json'
TERM = 'coalesced:72eff463a7ab0592d9c4f9af4a5916dc27732b3815a5eafdfb56a048464c4d96'
TCR_REVISIONS = {'coalesced:a2e7b4458d009f37d4db6cba294a6193ad8c7293c7e15fb0a4ca4a46b6a1263e': ('《真名法典2》的游戏数据\\n已经损坏。\\n可以在Xbox主界面中\\n删除损坏的数据。', '《玛格纳卡尔塔2》的游戏数据\\n已经损坏。\\n可以在Xbox主界面中\\n删除损坏的数据。'), 'coalesced:3af35a7a348f273db2f5aa3c266273cc4d768eb71cf74bbda4cc5dc33a4d2831': ('没有《真名法典2》的\\n游戏数据。', '没有《玛格纳卡尔塔2》的\\n游戏数据。'), 'coalesced:79d8893a78d11934d1455bec265dc73086de281e740f3c73cf909c448bafbb2d': ('请通关《真名法典2》，\\n或从XboxLIVE卖场\\n下载语音剧。', '请通关《玛格纳卡尔塔2》，\\n或从XboxLIVE卖场\\n下载短剧。'), 'coalesced:0ae46bc6646a61cc38d28f7519fd007ce5f2a43f56d8a50ecff0179cda989615': ('通关《真名法典2》后，\\n即可欣赏影片。', '通关《玛格纳卡尔塔2》后，\\n即可欣赏影片。'), 'coalesced:fc1f38914f271bc1f9f9f8f32c81445f1333170a267b4282f0b1029999742cae': ('拥有对应的下载内容后，\\n即可欣赏语音剧。', '拥有对应的下载内容后，\\n即可欣赏短剧。'), 'coalesced:2693289e1f5d6fb085435e2c81092523b6de91c7caca4ee8ed10577ec016d01d': ('发现下载内容中的语音剧。退出附加内容菜单后重新进入，即可欣赏语音剧。', '发现下载内容中的短剧。退出附加内容菜单后重新进入，即可欣赏短剧。'), 'coalesced:d8dc80fbe4bf315d1312bdcf13b85a99da41ef14c84a157e25cd95c7f1d37363': ('光盘不正确。请放入《真名法典2》光盘1。', '光盘不正确。请放入《玛格纳卡尔塔2》光盘1。'), 'coalesced:14041db170daccf7265d06899bf27d52d918f58698dea25d1042757512ac7883': ('光盘不正确。请放入《真名法典2》光盘2。', '光盘不正确。请放入《玛格纳卡尔塔2》光盘2。')}
NUMBER = 'coalesced:97cee44222d2dbfa70581cccc02656f6da6cb366b411c31a751e671ee7cb7642'


def load(name):
    return json.loads((ROOT/name).read_bytes())


class ReadabilityRevisionTests(unittest.TestCase):
    def test_exact_scalars_in_single_existing_workflow_slot(self):
        old = load(BASELINE)
        current = load(CURRENT)
        expected = copy.deepcopy(old)
        for entry in expected['entries']:
            if entry['id'] == TERM:
                self.assertIn('尖刺蠕虫', entry['translation'])
                entry['translation'] = entry['translation'].replace('尖刺蠕虫', '穿刺蠕虫')
            elif entry['id'] == NUMBER:
                self.assertIn('第三年', entry['translation'])
                entry['translation'] = entry['translation'].replace('第三年', '第3年')
        for entry in expected['entries']:
            if entry['id'] in TCR_REVISIONS:
                before, after = TCR_REVISIONS[entry['id']]
                self.assertEqual(entry['translation'], before)
                entry['translation'] = after
        self.assertEqual(current, expected)
        self.assertEqual(len(current['entries']), 262)
        refs = [batch['plan'] for batch in load('locales/zh-Hans/translation-workflow.json')['batches']]
        self.assertEqual(sum(ref['path'] == CURRENT for ref in refs), 1)
        self.assertFalse(any(ref['path'] == BASELINE for ref in refs))
        ref = next(ref for ref in refs if ref['path'] == CURRENT)
        self.assertEqual(hashlib.sha256((ROOT/CURRENT).read_bytes()).hexdigest(), ref['sha256'])

    def test_eight_draft_consistency_repairs_keep_metadata_and_candidate_anchors(self):
        old = {e['id']: e for e in load(BASELINE)['entries']}
        current = {e['id']: e for e in load(CURRENT)['entries']}
        self.assertEqual(len(TCR_REVISIONS), 8)
        for identity, (before, after) in TCR_REVISIONS.items():
            self.assertEqual(old[identity]['translation'], before)
            self.assertEqual(current[identity]['translation'], after)
            self.assertEqual({k:v for k,v in old[identity].items() if k!='translation'},
                             {k:v for k,v in current[identity].items() if k!='translation'})
        anchors = {t['source']:t for t in load('locales/zh-Hans/terms.json')['terms']}
        for source, target in [('마그나카르타', '玛格纳卡尔塔'), ('라이브 드라마', '短剧')]:
            self.assertEqual(anchors[source]['target'], target)
            self.assertEqual(anchors[source]['review_status'], 'candidate')
            self.assertEqual(anchors[source]['relation'], 'unverified')

    def test_strict_atoms_controls_and_full_demand_subset(self):
        old = {entry['id']: entry for entry in load(BASELINE)['entries']}
        current = {entry['id']: entry for entry in load(CURRENT)['entries']}
        self.assertNotEqual(atoms(old[NUMBER]['translation']), atoms('3'))
        self.assertEqual(atoms(current[NUMBER]['translation']), atoms('3'))
        for identity in [TERM, NUMBER, *TCR_REVISIONS]:
            self.assertEqual(TOKEN.findall(old[identity]['translation']), TOKEN.findall(current[identity]['translation']))
        before = set()
        after = set()
        seen = set()
        for batch in load('locales/zh-Hans/translation-workflow.json')['batches']:
            path = batch['plan']['path']
            entries = load(path)['entries']
            for entry in entries:
                self.assertNotIn(entry['id'], seen)
                seen.add(entry['id'])
                before_entry = old[entry['id']] if path == CURRENT else entry
                before.update(literal_codepoints(before_entry['translation']))
                after.update(literal_codepoints(entry['translation']))
        self.assertEqual(len(seen), 14082)
        self.assertEqual(len(before), 2446)
        self.assertEqual(len(after), 2445)
        self.assertEqual(before-after, {ord('尖')})
        self.assertFalse(after-before)


if __name__ == '__main__':
    unittest.main()
