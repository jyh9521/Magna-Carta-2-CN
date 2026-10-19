# 第十四批：湿地防卫、失控争执与猫猫铃铛

日期：2026-10-19。新增INT123条draft，累计2,520条；168项candidate术语。
另新增csm03-140独立字幕2cue，累计113/315cue；当前三份csm03字幕16cue均有draft。

## 范围

- CSMB03_121/124/126/150四场62条：防卫路线、修亚伦交锋、灾祸种降下与战后争执。
- Ch03_KotaMare_01状态section全部40条；与初始27条分开，_02/_03仍未在本批翻译。
- Ch02_295_00猫猫铃铛任务19条，另有铃铛/钥匙2条关联物品名称。
- 分类115 dialogue、3 name、1 quest_description、2 quest_progress、2 quest_objective。

CSMB03_150原始key从01开始，没有00；不补造条目，不把文件编号连续性当作缺行证明。
KotaMare_01中03_313_00出现两次，保留不同stable ID/occurrence，不按key合并覆盖。

## 语义与格式

新候选为猫猫的铃铛、黑猫猫的钥匙、猫猫族特制的炸弹；均未作人工reviewed。
失控事件中各人的指控、解释和信任按原立场保留，不把对白推断写成已证实旁白。
“爱心合击”是角色玩笑，不将其扩张为已验证的新战斗机制，也不替换现有连锁系统用词。
猫猫喵尾音仅按对应原文角色保留，非猫猫NPC不添加。
铃铛任务保留先取钥匙、再开箱取铃铛的关系；DES保留2个功能换行。
两个`QUEST :`保留空格与大小写；goaldesc/get_item2等字段拼写不改。
71条对白按显式计数移除继承硬换行；旧功能换行和未知转义不动。
字幕两句不补写指代人物身份，保持时间轴、class、BOM和清屏标记，不借Coalesced key推断对应关系。

## 重建与验证

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/defense-batch014/workspace
python -m tools.export_subtitle_catalogs --source-root . --profile locales/zh-Hans/subtitle-profile.json --output build/batch-014-verification/subtitle-catalogs
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python -m unittest discover -s tests -q
python tools/check_repository.py
```

输出须全新。workflow十四份不重叠INT计划，字幕profile十四份计划；两盘完整ISO及44份字幕hash重新核验。
Verified / offline：双盘INT结果一致，旧2,397条逐ID不变，原18,176条中15,656条保持原文。
字幕旧111cue不变，两句回填且结构不变；独立副本回滚恢复原字幕，修改输出保留新译。
INT独立回滚恢复2,397条基线，MODIFIED_FILE.int仍保留2,520条；旧未知转义、纯标记及重复key保持。
另核对KotaMare_01 40条与重复key、csm03字幕16/16、干净源码测试、依赖hash和164文件重建一致性。
四份主证据及字幕差异/基线/回滚副本保存在本地build/batch-014-verification。

只清理核实可再生成的验证缓存，保留原盘、配置、存档、runs、入口依赖及必要基线/回滚/研究证据。
本批不启动游戏、不生成ISO/整盘副本、不更新字库/TOC/可玩包；草稿与候选不等于人工/游戏内验收。
推送核对后从CSMB03_160继续，接KotaMare_02状态NPC、后续任务和剩余字幕。
