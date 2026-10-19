# 第十五批：结盟、拜泽恩身世与黑猫猫任务

日期：2026-10-19。新增INT122条draft，累计2,642条；172项candidate术语。
另补齐csm01-45/50独立字幕14cue，累计127/315cue，剩余188cue；四份csm01字幕24cue均有draft。

## 范围与状态

- CSMB03_160/161两场77条：结盟、塞蕾丝汀加入、父亲下落与海底洞窟开门说明。
- Ch03_KotaMare_02状态全部26条，与初始/_01分别保留；_03状态仍待下一批。
- Ch02_296_00实际新增15条，另有1条原始空白pay字段不计已译。
- 拜泽恩两份名称、遗物名及遗物说明4条关联字段，分别保留ID。
- 分类114 dialogue、4 name、1 item_description、1 quest_description、1 quest_progress、1 quest_objective。

## 语义与格式

新增拜泽恩、银白的拜泽恩、香水瓶、拜泽恩的遗物4项candidate。
15年前原数字、父亲生死未知、与银白称号是否同一人尚未确定的语气全部保留。
不将“下落不明”误写成已经死亡，也不擅自认定传闻中的佣兵与父亲同一身份。
Vizen/bizen为两份同源名称字段，译名统一但ID不合并；遗物说明按单句规则不添句号。
香水瓶的摆放/开门条件只依本场虚构剧情翻译，不添加未出现的颜色、材料或配方。
黑猫猫任务目标6只及`QUEST%s:`另两个`%s`保留；Goaldesc拼写不改。
任务DES原本没有换行，保持单行；70条对白按显式计数移除继承硬换行。
pay字段原始为空白，保留完整原值/hash，不填0、不猜奖励、不照抄计作完成。
字幕8/6cue按源hash/时间轴独立翻译，保留5处br、BOM、class、清屏及叙述视角。

## 重建与证据

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/alliance-batch015/workspace
python -m tools.export_subtitle_catalogs --source-root . --profile locales/zh-Hans/subtitle-profile.json --output build/batch-015-verification/subtitle-catalogs
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python -m unittest discover -s tests -q
python tools/check_repository.py
```

输出须全新。workflow十五份不重叠INT计划，字幕profile十六份计划；两盘完整ISO及44份字幕hash重新核验。
Verified / offline：双盘INT结果一致，旧2,520条逐ID不变，原18,176条中15,534条保持原文。
字幕旧113cue不变，14cue回填且结构不变；独立副本回滚恢复原两份字幕，修改输出保留新译。
INT独立回滚恢复2,520条基线，MODIFIED_FILE.int仍保留2,642条；旧未知转义、纯标记、重复key与新空白pay保持。
另核对拜泽恩双名称、csm01 24/24、干净源码测试、依赖hash与164文件重建一致性。
四份主证据及字幕差异/基线/回滚副本保存在本地build/batch-015-verification。

清理仅处理核实可再生成的验证缓存，保留原盘、配置、存档、runs、入口依赖及必要基线/回滚/研究证据。
本批不启动游戏、不生成ISO/整盘副本、不更新字库/TOC/可玩包；草稿与候选仍需人工/游戏内验收。
推送核对后从CSMB03_170接续，接KotaMare_03状态、Ch02_299_00等后续任务与剩余字幕。
