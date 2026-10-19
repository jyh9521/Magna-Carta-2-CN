# 第二十九批：第五章主线收尾与比尔特治疗任务

日期：2026-10-19。新增INT116条，累计4,461条draft；209项candidate，0项人工reviewed。
字幕新增csm05-90两条，累计154/315cue，profile22份计划。

## 范围与限定覆盖

- CSMB05_089/089_1/089_2/100/110分别17/8/11/10/18，共64条。
- MC2Quest/05_105_0/1/2分别30/15/5，共50条，比尔特治疗和两组守备队联络。
- MC2Item/Valuables/fantastic_roots与fantastic_roots_D两个关联字段。
- 分类103 dialogue、3 narrative、1 quest_progress、1 quest_objective、4 name、3 quest_description、1 item_description。

Verified / source/offline：CSMB05前缀433条中432条有draft，仅070_27疑似编辑占位保留；
Compose/Chapter05共75字段、NpcTalk的05_前缀46字段及四份csm05字幕13cue均有draft。
上述为明确资源/前缀覆盖，不是全章全部可见文字完成，也不是玩家游戏验收。
第五章任务05_前缀共157字段，本批后57个已有draft，余六组100字段待补齐；E05邮件16字段仍待核读。

089_1回忆、村长证词、朱特向爷爷隐瞒真相和末三条内心叙述分别保留。
北部军场景的威胁、目的及角色对朱特记忆的判断仍是发言者立场，不改成额外旁白结论。
治疗与两组联络任务发生于更早状态，本批作为同章缺口补齐，保持原状态与key，不将其改成战后现况。
幻之根新增candidate，比尔特/杰巴萨等复用候选；物品“死人复生”保留传说属性，并非现实疗效说明。

67条普通对白/叙述去源硬换行有显式line_break_policy；治疗DES保留1个功能换行。
QUEST%s空格/冒号及源单个%s、标题ASCII括号、fantastic_roots尾随1空格保持。
两条新字幕保留各4次喘息、时间轴、KRCC/BOM和1个br；按profile实际来源Disc2读取，不强行在Disc1查找缺失资源。
旧152cue逐字段保持；第五章13cue已全draft，其他章节161cue仍未译。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/chapter05-close-batch029/workspace
python -m tools.export_subtitle_catalogs --source-root . --profile locales/zh-Hans/subtitle-profile.json --output build/batch-029-verification/subtitle-catalogs
python build/batch-029-verification/verify_resources.py baseline
python build/batch-029-verification/verify_resources.py modified
python build/batch-029-verification/verify_resources.py rollback
python build/batch-029-verification/verify_subtitles.py
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

输出须全新。双盘INT源hash不变，116条新值回填一致；旧4,345条保留，13,715条仍为源值。
独立回滚恢复4,345条基线，主MODIFIED_FILE.int保持4,461条；错误hash输入拒绝且不变。
字幕导出重新核验双盘ISO完整hash及44份文本成员，不输出整盘副本；字幕独立回滚恢复，修改副本保留。
干净Git index源码测试、83项依赖锁、164文件重建一致性及推送后四组GitHub CI分别核对。
完整原文/资源与本机验证脚本只在build/batch-029-verification，不进入Git。

仅清理已核实可再生成且无入口依赖的验证缓存；保留原盘、配置、存档、runs、当前包及必要基线/回滚/研究证据。
未生成ISO或整盘副本，未自行启动模拟器，未刷新字体、TOC或可玩入口；离线成功不是游戏验收。
下一批先补05_112_0/120_0/131_0/136_0/209_0/218_0任务100字段与E05邮件16字段，再按实际场景接续第六章。
