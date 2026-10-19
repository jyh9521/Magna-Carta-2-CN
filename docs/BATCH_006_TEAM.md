# 第六批：小队战斗、狼人据点与营救/护送

日期：2026-10-19。新增272条draft，累计1,389条INT草稿；124项术语仍为candidate。

## 范围

- CSMB02_25/28/31/32/34/35/36共180条：小队教学、属性/环境KAN、王室血统、凯托遗物及任务归来。
- Ch02_Abazet连续索引84–121共38条，接上一批84条；本城现有122/276条draft。
- Ch02_214_0营救胡安18条、Ch02_223_0护送采掘场27条，共45条。
- 猫猫两份名称、猫猫族长/商人、胡安、治愈种子、疗愈叶、经验腰带及阿巴泽特草原，共9条关联名称。
- 分类：247 dialogue、9 narrative、11 name、2 quest_description、2 quest_progress、1 menu。

原有1,117条逐ID保持不变；原18,176条INT中其余16,787条不变。旧动画字幕49条及异常转义1条不变。
不把这批范围扩大为整个第二章、整城NPC或全游戏完成。

## 机制与格式

保留1名队长/2名队员、1.5倍连锁、2倍连锁超限、2人过热、15/20分及300SID。
分别使用连锁、连锁超限、连锁终结，保留技能触发、切换队长、过热恢复的先后条件，
不把切换角色的一般动作等同于成功触发连锁。AI、Y/RB/LB/A等键位顺序逐条核对。
环境KAN与属性KAN分别记录，不把可消散的场地KAN译成体内累积的力量KAN。

三条功能性换行保留：奖励说明2个、护送DES2个、X/Y选项1个。其他对白只用显式计数去继承硬换行。
任务Resque字段的原key拼写不改，值中的`QUEST :`和`QUEST:`前缀保留，不机械统一空格。
护送说明明确保护成员抵御怪物/盗匪，而不是改写成避免接触敌人的额外要求。
猫猫说话的喵尾音按原文保留，不给非猫猫角色统一添加。

卡尔塔等命中固定系列参考只作为候选，不据同词面认定血统/人物跨作同一性。
王室来历是本作对白内容，不将游戏内叙述扩张为外部事实或其他作品设定。

## 重建与验证

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/team-batch006/verified-workspace
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python -m unittest discover -s tests -v
python tools/check_repository.py
```

输出必须全新。workflow当前六个不重叠计划，按八个原容器真实hash导出80份目录；两盘共享译文而保留来源。
本地build/batch-006-verification保存1,117条基线、1,389条MODIFIED_FILE.int、272条DIFF_FILE.json，
以及hash守卫ROLLBACK.sh和VERIFICATION.txt；回滚只测独立副本，主修改文件保持新增译文。
干净源码单测、双盘重建、旧译保留、键位/数值及功能换行分别验证。

本轮未更新字库/TOC/可玩包，不启动游戏，不生成ISO/整盘副本；原盘、用户配置、存档、runs和原入口不变。
临时装配由工具清理，必要基线/回滚/研究保留。提交推送并核对远端后，按TRANSLATION_QUEUE.md直接继续。
