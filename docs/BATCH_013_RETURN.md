# 第十三批：营救归来、休整、胡安送信与早期字幕补缺

日期：2026-10-19。新增INT151条draft，累计2,397条；165项candidate术语。
另补齐csm00-40/01-10/01-20三份独立字幕18cue，累计111/315cue，剩余204cue。

## 范围

- CSMB03_104/110/115/120四场95条：归村、释疑、休整与湿地遇袭。
- NPC 02_oldfox全部14条及Ch03_KotaMare初始section全部27条，共41条。
- Ch02_290_00胡安送信任务13条；胡安的信、爱情魔药2条关联物品名称。
- 分类147 dialogue、3 name、1 quest_description。

KotaMare_01/02/03为不同状态的独立section，当前仍待后续；不按相同key合并，也不宣称全村NPC完成。
已提取csm00四份39cue在本轮补缺后均有draft；csm01还有其他独立字幕，仍按清单推进。

## 术语与格式

新增胡安的信、爱情魔药、路障、治愈连环术4项candidate。
胡安送信任务说明保留1个功能换行，任务名与信件物品名分开；旧“给库布的信”UI标签未覆盖。
族长与尼尔提的母子关系，依据本场明确对白翻译；不向早先未标说话人的句子追加身份。
100/200份香保留原数字，78条对白仅按显式计数策略移除继承硬换行。
爱情魔药仅为游戏内虚构道具名与喜剧情节，不添加原文没有的配方、材料或效果。
峡谷/马雷NPC的立场与猜测保留为对白；不会据村民的说法升级为已证实世界观。
字幕8/9/1cue独立按源值hash及时序翻译，保留3处br、BOM、class和清屏事件；不套用Coalesced行号。

## 重建与验证

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/return-batch013/workspace
python -m tools.export_subtitle_catalogs --source-root . --profile locales/zh-Hans/subtitle-profile.json --output build/batch-013-verification/subtitle-catalogs
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python -m unittest discover -s tests -q
python tools/check_repository.py
```

输出须全新。workflow十三份不重叠INT计划，字幕profile十三份计划；两盘完整ISO及44份字幕hash重新核验。
Verified / offline：双盘INT结果一致，旧2,246条逐ID不变，原18,176条中15,779条保持原文。
字幕旧93cue不变，18cue回填且结构不变；独立副本回滚恢复原三份字幕，修改输出保留新译。
INT独立回滚恢复2,246条基线，MODIFIED_FILE.int仍保留2,397条；旧未知转义、两条纯标记及重复key保持。
另核对02_oldfox 14/14、KotaMare初始27/27、csm00 39/39、干净源码测试、依赖hash和164文件重建一致性。
四份主证据及字幕差异/基线/回滚副本保存在本地build/batch-013-verification。

仅清理核实可再生成的验证缓存，保留原盘、配置、存档、runs、入口依赖及必要基线/回滚/研究证据。
本批不启动游戏、不生成ISO/整盘副本、不更新字库/TOC/可玩包；草稿和候选仍待人工/游戏内验收。
推送核对后从CSMB03_121继续，接KotaMare_01状态NPC、后续任务和剩余字幕。
