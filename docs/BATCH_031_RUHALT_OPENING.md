# 第三十一批：鲁哈尔特作战准备与连携奥义

日期：2026-10-19。新增INT137条，累计4,717条draft；216项candidate、0项人工reviewed。
字幕profile22份154/315cue不变。

## 连续剧情与关联资源

- CSMB06_010/011/015/017/020/021：28/7/4/19/16/16，共90条。
- Quest/06_220_0雷电炸弹任务20条；NpcTalk/06_Abajet按源顺序前20/191条。
- CharacterName/firewine、FieldName/Ruhalt_basin与basin2、Item两类雷电炸弹名称/说明：共7字段。
- 分类124 dialogue、2 narrative、1 quest_description、6 name、1 quest_progress、1 quest_objective、2 item_description。

Verified / source/offline：新增ID与前30批无重叠；完整品和未完成品不混淆，两个盆地名称字段独立保留。
KAN地雷、雷电炸弹、法伊尔瓦因、鲁哈尔特盆地、连携奥义、雷之KAN新增6项candidate，
仅为本作候选译法/音译，未确认官方英文或跨作身份。旧210项不改，未作人工定稿。

教程中双手剑/扇子、两人各自积累5个KAN、力量KAN/风之KAN、连锁、方向键右与AI均保留。
游戏任务的2个雷之KAN、5个未完成品/5次尝试/额外5个保持，不增加源文未有步骤。
所有机制仅为游戏剧情/玩法。劳德怀疑情报泄露不变成调查结论；灾祸种历史与KAN耗尽说保留NPC转述/推测。
010末两条保留朱特内心与回忆视角。79条去硬换行有显式line_break_policy；任务DES保留3个功能换行。
QUEST%s和另两个%s、空格/冒号、NPC203_6与未完成品名称的尾随空格均保持。

旁支审计发现06_zepi_1/order_2含未知反斜线序列，该支线不属于当前作战准备范围。
原值、hash和未回填状态已核验，另列队列待查，不把它猜成换行或计作本批draft。
本批无相邻新字幕；csm06-35及后段四份字幕需随后续场景推进，旧22份154cue和profile逐字节不变。
不重读完整ISO，不把旧字幕证明称为新增验证。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/ruhault-opening-batch031/current-workspace
python build/batch-031-verification/verify_resources.py baseline
python build/batch-031-verification/verify_resources.py modified
python build/batch-031-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

输出须全新。双盘原hash保持，137条新值回填一致；旧4,580条保留，13,459条仍为源值。
独立回滚恢复4,580条基线，主MODIFIED_FILE.int保持4,717条；错误hash输入拒绝且不变。
干净Git index源码测试、87项依赖锁、164文件重建一致性及推送后四组GitHub CI分别核对。
完整原文、资源与本机验证脚本只在build/batch-031-verification，不进入Git。

仅清理已核实可再生成且无入口依赖的验证缓存；保留原盘、配置、存档、runs、当前包及必要基线/回滚/研究证据。
未生成ISO或整盘副本，未自行启动模拟器，未刷新字体、TOC或可玩入口；离线成功不是游戏验收。
下一批从CSMB06_030/031继续，衔接csm06-35与同阶段NPC/任务，不重复本批教程或较晚的王之试炼。
