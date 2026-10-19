# 第十批：灾祸种、柯塔马雷与精华提取

日期：2026-10-19。新增INT113条draft，累计1,889条；术语146项candidate。
另补齐csm02-61与csm03-10独立字幕8cue，累计57/315cue；不混计进INT数量。

## 范围

- CSMB03_20新增62条，保留1条未知转义；CSMB03_21为6条，CSMB03_30为5条，共73条。
- Ch02_Abazet索引182–201共20条，城镇累计202/276条；承接前批克蕾尔传闻。
- Ch02_252_0精华提取20条，保留接受/拒绝/进行/完成及说明字段。
- 分类109 dialogue、各1条name、quest_description、quest_progress、quest_objective。
- 独立字幕分别3/5cue，盘1来源明确；原四份计划49cue逐条不变，剩余258cue待译。

## 格式与候选语义

灾祸种成因、死亡传言和停止方法均保留角色的不确定表述，不改写为已证实世界设定。
3/150年、10/40年、第二首都的原数字不变；马雷族世界观按原文翻译，不添加外部推断。
新增玛格纳卡尔塔、鲁哈尔特内战、梦魇魔女3项candidate。
玛格纳卡尔塔是剧情内存在/称号的暂定音译，与作品标题《真名法典2》区分，仍待统一校对。
沿用洁菲/蕾洁菲尔妲、露、斯特拉斯等已有词条；传闻保留“据说/是真的吗”语气。

新待查：CSMB03_20/voc_csmb_0320_50含未知反斜线序列。保持原值并记录held ID/hash，
不猜作换行、不翻译后删除标记、不计draft。早先Ch00未知条目也保持原值。
精华提取DES保留3个功能换行；濒死、概率及洁菲担任队长三个条件保留；`Quest:`大小写不变。
72条对白仅按显式source_count策略移除继承硬换行。

## 重建与验证

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/calamity-batch010/final-workspace
python -m tools.export_subtitle_catalogs --source-root . --profile locales/zh-Hans/subtitle-profile.json --output build/batch-010-verification/subtitle-catalogs
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python -m unittest discover -s tests -q
python tools/check_repository.py
```

输出路径须全新。workflow十个不重叠INT计划；Movies profile独立锁定六份字幕计划。
字幕导出重新核验两盘完整ISO hash、44份成员清单与逐文件hash，不复制ISO/视频/整盘。
Verified / offline：双盘INT输出一致，旧1,776条逐ID不变，原18,176条中16,287条保持原文。
字幕时序、class、BOM、清屏标记和其他未译cue不变；独立副本回滚恢复原两份字幕，修改输出保留8条新译。
字幕源锁定回归测试保留原四份49cue与依赖hash，允许新增不重叠cue，不再将总数永久锁死为49。
INT独立回滚恢复1,776条基线，MODIFIED_FILE.int仍保留1,889条；另验证干净源码与164文件重建一致性。
本地build/batch-010-verification保存四份主证据及SUBTITLE_DIFF.json和逐字幕基线/修改/回滚副本。

整理与清理只处理核实可再生成的验证缓存，保留原盘、配置、存档、runs、入口依赖及必要研究证据。
本批未更新字库/TOC/可玩包，不启动游戏；离线完成不代替游戏显示验收。推送核对后继续CSMB03_50及其字幕。
