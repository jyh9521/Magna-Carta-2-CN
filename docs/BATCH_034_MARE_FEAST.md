# 第三十四批：马雷成人礼与第六章场地念白补齐

日期：2026-10-19。新增INT125条，累计5,068条draft；224项共享candidate及1项独立字幕candidate。
全部未人工定稿。字幕profile27份187/315cue保持。

## 范围与明确覆盖

- Compose/Chapter06_33–67共35条；现该section全部67字段有draft。
- NpcTalk/06_Abajet源序第81至120条：34条draft、6个删除标记保留。
- NpcTalk/06_kotamare与06_kotamare_feast：26/25共51条，不合并庆典前与庆典中状态。
- Quest/06_cerestin_0三字段；Skill/Renkai_Ougi/Juto_Zephie_Renkai与CharacterName/Kiloti各1字段。
- 分类24 narrative、93 dialogue、2 menu、2 system_message、1 quest_description、3 name。

Verified / source/offline：新增ID与前33批不重叠。城镇已检查前120条，107draft/13源删除标记保持。
本批新增2219/2461/221/241/2229/2235六条；后续从源序偏移120接续，不按已译107偏移。
NPC灾祸种传说、战争责难、难民偏见、灭族主张与疑问均按发言立场保留，不变为旁白认可或工程事实。
拜泽恩线索支线只译三个原字段，不补写找到人物或完成结果。

天风一击闪、基洛蒂、塞莉娅、成人礼新增4项candidate。技能习得两条系统提示与实际Skill名称一致。
塞莉娅称谓不补亲属关系；CharacterName未找到同名字段，未编造ID。基洛蒂有确切关联姓名字段。
24条括号念白保留ASCII括号；58条去源硬换行显式声明；庆典X/Y菜单保留样式和1个功能换行。
源3年、307_no/307_s0末尾空格等逐字段保持；两条系统习得提示遵循单句不加句末句号规则。

字幕profile、27份计划和一号独立候选逐字节保持旧HEAD。本批不重读完整ISO，不将旧字幕证明称为新增验证。
场景主线/字幕已覆盖仍非全章所有文字完成；其他地区NPC、剩余城镇、任务和邮件尚有缺口。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/mare-feast-batch034/workspace
python build/batch-034-verification/verify_resources.py baseline
python build/batch-034-verification/verify_resources.py modified
python build/batch-034-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

输出须全新。双盘INT原hash保持，125条新值回填一致；旧4,943条保留，13,108条仍为源值。
独立回滚恢复4,943条基线，主MODIFIED_FILE.int保持5,068条；错误hash输入拒绝且不变。
干净Git index源码测试、98项依赖锁、164文件重建一致性及推送后四组GitHub CI分别核对。
完整原文、资源与本机验证脚本只在build/batch-034-verification，不进入Git。

仅清理已核实可再生成且无入口依赖的验证缓存；保留原盘、配置、存档、runs、当前包及必要基线/回滚/研究证据。
未生成ISO或整盘副本，未自行启动模拟器，未刷新字体、TOC或可玩入口；离线成功不是游戏验收。
下一批从城镇源序偏移120与同阶段06_chinook/dunanfield/dunanhill/oldfox继续，结合对应任务补齐，再接第七章。
