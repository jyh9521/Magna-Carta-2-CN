# 第十九批：黑刃要塞、梅莉莎再会与战后余波

日期：2026-10-19。新增INT147条draft，累计3,287条；188项candidate术语。
同阶段csm04两份独立字幕14cue已在第十六批覆盖；字幕总计141/315cue，本批不重复修改。

## 范围与限定覆盖

- CSMB04_091/093/095/110/120/130/140七场84条，从丘陵行军接至要塞发现与阿尔戈的战后谈话。
- CSMB04_120末尾3条为内心独白，显式分类narrative；剧情台词与人物陈述不充当研究结论。
- Ch04_Abazet索引61–90共30条，包含256_0/256_1和04_2201_close原key；累计91/242条。
- 04_406_0生物学家10条、04_404_0古文书递送8条、04_405_0讨伐科洛瑟斯11条，共29条。
- 关联名称：生物学家、古文书、风息岛；另补古文书物品说明1条。
- 分类132 dialogue、3 narrative、6 name、3 quest_description、各1条quest_progress/quest_objective/item_description。

Verified / offline：04_401_0至04_406_0六个任务section共71条均有draft；这一范围不包括
04_42xx任务分支、Compose引导、邮件或游戏中的全部第四章文字，不能据此声称章节全覆盖。

## 上下文和格式

梅莉莎关于正义的主张、朱特的疑问、阿尔戈的自责及族群经历均按角色立场翻译，不补写动机解释。
马雷族寿命与命定之人的说法保留原文语气，不引入年龄或寿命数值；特雷瓦族、青月/黑角族群区分。
马伦、艾菲斯、科洛瑟斯、古文书、生物学家5项均为candidate；姓名音译未作官方/跨作身份确认。
风息岛和德普廷矿山复用既有词根/候选；古文书只译道具说明，不补造原文未给的药方。
源文대센티널拼写、section和key保持原hash；中文按同场既有部队称谓采用反哨兵部队。

404/405任务DES各保留1个功能换行，406说明无源硬换行。唯一进度条目保留`QUEST%s :`和
1个`%s`，不擅加计数模板。第2哨所、特别奖励须击败目标后返回领取的条件保持。
70条对白按显式计数策略去继承硬换行；其余控制码、键位、数值、旧译与未知格式保持。

## 可复现验证和收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/stronghold-batch019/workspace
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python -m unittest discover -s tests -q
python tools/check_repository.py
```

输出目录须全新。双盘INT原件hash保持，147条新值回填一致；旧3,140条不变，14,889条仍为源值。
独立副本回滚恢复3,140条基线，主MODIFIED_FILE.int保持3,287条；错误hash目标被拒绝且保持原字节。
Git index源码干净导出后运行完整测试，59项依赖锁逐一核对；两次工作区164个文件hash一致。
字幕profile及18份计划逐字节保持旧HEAD，本批未重读完整ISO，不将旧字幕证据称为新增验证。
本地四份主证据、测试日志与独立回滚副本在build/batch-019-verification；完整原文/资源不提交。
仅清理已确认无入口依赖的可再生验证缓存；原盘、配置、存档、runs、当前包及基线/回滚/研究证据保留。

本批不生成ISO/整盘副本、不自行启动模拟器、不刷新字库/TOC/可玩入口；离线成功不是游戏验收。
提交推送并核对远端/干净状态后，从CSMB04_150、Ch04_Abazet索引91（04_2202_00）继续，
再推进同阶段04_42xx任务分支与后续独立字幕；不重复早先章节或已译字幕。
