# 第二十七批：离队请求、村长委托与风歌洞窟遗物

日期：2026-10-19。新增INT122条，累计4,235条draft；208项candidate，0项人工reviewed。
字幕profile19份149/315cue不变。

## 连续场景与同阶段补齐

- CSMB05_070/072/073/080共79条：070原40条中39条draft、1条保留，另三场32/3/5条。
- MC2NpcTalk/05_chinook_s战斗期NPC8条，与已译05_chinook解放后状态独立保留。
- MC2Quest/05_101_0遗物任务7条；MC2Item/Article与Article_D关联名称/说明2条。
- MC2Compose/Chapter05_50–75共26条，其中16条括号念白、74/75两条阶段编辑提示。
- 分类96 dialogue、18 narrative、1 quest_description、2 name、1 quest_progress、1 quest_objective、2 editor_note、1 item_description。

Verified / source/offline：新增ID不与前26批重叠。070最后两条为朱特第一人称内心独白；
洁菲对政治婚约、傀儡处境和保护梅莉莎的限制按其解释翻译，不将角色立场变成额外旁白事实。
村长不知洞窟内的具体遭遇，译文保留“恐怕”的推测，不补写其未曾目击的过程。
战斗期_s NPC仍讲述死亡弩炮/杰巴萨阻碍，不能因与解放后NPC同名key而合并或更新为战后立场。

CSMB05_070/voc_csmb_05070_27疑似“缺失台词”编辑占位备注，运行用途尚未确认。
其id/hash写入held_entries，保留原值，不补造公主或朱特对白，不计draft。
Compose74/75明确按editor_note归类；翻译其阶段提示不代表已证实玩家可见。
当前Compose/Chapter05全部75字段有draft，但第五章剧情、任务、邮件和其他文本仍未完整。

QUEST%s后空格/冒号及另外两个%s、ASCII进度括号保持；任务DES保留1个功能换行。
60条对白/念白去硬换行逐条记录line_break_policy，Article源尾随1个空格保持。
风歌洞窟复用既有候选，村民的遗物新增candidate，未人工定稿。
字幕profile与19份计划逐字节保持旧HEAD；本批不重读完整ISO，不将旧字幕验证说成新增证明。
后段csm05-82/85/90五条在下一阶段按实际相邻剧情核对，不机械替用Coalesced台词。

## 可复现验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/villager-relic-batch027/workspace
python build/batch-027-verification/verify_resources.py baseline
python build/batch-027-verification/verify_resources.py modified
python build/batch-027-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

输出须全新。双盘源hash保持，122条新值回填一致；旧4,113条保持，13,941条仍为源值（含本批待查占位）。
独立副本回滚恢复4,113条基线，主MODIFIED_FILE.int保留4,235条；错误hash输入拒绝且不变。
干净Git index源码测试、76项依赖锁、164文件重建一致性及推送后四组GitHub CI分别核对。
完整原文、资源与本机验证脚本只在build/batch-027-verification，不进入Git。

仅清理已核实可再生成且无入口依赖的验证缓存；保留原盘、配置、存档、runs、当前包及必要基线/回滚/研究证据。
未生成ISO或整盘副本，未自行启动模拟器，未刷新字体、TOC或可玩入口；离线成功不是游戏验收。
下一批从CSMB05_086（63条）起，核读后续场景与独立字幕、任务关联，不重复已译75条场地提示。
