# 第十一批：柯塔马雷会面、扣留与火之KAN

日期：2026-10-19。新增INT213条draft，累计2,102条；154项candidate术语。
另新增盘1 csm03-40独立字幕9cue，字幕累计66/315cue，剩余249cue。

## 范围与上下文

- CSMB03_50/60/70三场共172条：村口会面、族长质问、扣留及前往救援的约定。
- Ch02_Abazet索引202–221实际新增18条；两条纯连字符保留，不计已译。累计220条draft，遍历至索引221，尚未完成整城。
- Ch02_253_0火之KAN任务19条，含接受/拒绝/进行/完成、说明、进度和目标字段。
- 塞蕾丝汀、凯汀、海底洞窟、连环力增幅共4条关联名称/技能字段。
- 分类205 dialogue、5 name、各1条quest_description、quest_progress、quest_objective。

新增候选：塞蕾丝汀、凯汀、青月特雷瓦、黑角特雷瓦、麻痹香、连环力增幅、海底洞窟、贝尔福特。
沿用阿尔戈、梅莉莎、蕾洁菲尔妲等词条；角色指控、传闻和族群偏见保持说话立场，不改成旁白已证实事实。
原文年龄、称呼和人物间关系不改；60/200/12/10数值逐条保留，不添加未明说的身份或情节。

## 格式与不计数项

城镇02_2263_00及02_2269_00为纯连字符标记，保持原值并登记ID/hash，不照抄计作翻译。
Ch02_Abazet的02_2271_00出现两次，两条各有稳定ID/occurrence及不同译文，不能按key合并覆盖。
火之KAN说明保留同一区域、至少6个、普通攻击/固有技两种方式；DES保留2个功能换行。
`QUEST%s:`保留大小写和一个`%s`；Result、Goaldesc原key不改。
118条对白只按显式计数移除继承硬换行；既有任务、选项与未知反斜线布局不动。
字幕保留两处`<br>`、时间轴、class、BOM与清屏标记，不套用Coalesced译文。

## 重建与证据

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/kotamare-batch011/workspace
python -m tools.export_subtitle_catalogs --source-root . --profile locales/zh-Hans/subtitle-profile.json --output build/batch-011-verification/subtitle-catalogs
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python -m unittest discover -s tests -q
python tools/check_repository.py
```

输出路径须全新。workflow十一份不重叠INT计划，字幕profile七份独立计划；重新验证两盘完整ISO与44份字幕hash。
Verified / offline：双盘INT结果一致，旧1,889条逐ID不变，原18,176条中16,074条保持原文。
字幕旧57cue保持不变，9cue实际回填且时序等结构不变，独立回滚副本恢复原字幕；修改输出保留新译。
INT独立回滚副本恢复1,889条基线，主MODIFIED_FILE.int仍保留2,102条；两个未知反斜线和两条纯标记保留原值。
另验证干净源码单测、依赖hash按实际workflow核验，以及164文件重建一致性。
四份主证据和字幕专用差异/基线/回滚副本均位于本地build/batch-011-verification。

清理仅处理核实可再生成的验证缓存，保留原盘、配置、存档、runs、入口依赖及必要基线/回滚/研究。
本批未更新字库/TOC/可玩包，不生成ISO/整盘副本、不启动游戏；草稿与候选不等于人工审核或游戏验收。
推送核对后从CSMB03_71接续，补齐城镇后续、任务和相邻字幕。
