# 第四十六批：研究所入口、尼克斯与动力装置任务

日期：2026-10-20。新增INT93条，累计6,163条draft；302项共享candidate，另保留1项历史字幕来源候选记录。
“一号”现已进入共享库，该历史字幕记录不是另一个已核定角色。字幕28份194/315cue与邮件114/235字段不变。

## 范围与语境

- CSMB08_02/03/04/05/10共55条；第八章当前主线前缀共239条，本批55/239有draft。
- Compose/Chapter08_01-10括号提示10条；Quest/08_899_0十三、08_899_1八，共21字段。
- CharacterName/nicks与nicks _heal两字段，FieldName/SentinelLab/CentelLab一字段，动力装置/保管箱钥匙及说明四Item字段。
- 分类68 dialogue、10 narrative、7 name、3 quest_progress、2 quest_description、2 item_description、1 quest_objective。

Verified / source/offline：新增ID与前45批无重叠。尼克斯可能看见被带走的公主，保留“可能”，不补后续身份或研究真相。
地下2层、研究所1层、第2/4研究室、钥匙和供能后传送的条件保留；地下不受灾祸种影响仍是局部场景对白。
源FieldName称“中央研究所”，对白称“中央研究室”，各按源词保留，不擅推同一行政范围。
没有08_前缀NpcTalk资源；本批研究员对白在主线里，不造NPC占位或假ID。nicks _heal源键中的空格保持。
两条DES保留6个功能换行及空段落；38条普通对白有显式去硬换行策略。get2与两物品名称尾随空格保持。

## 一号候选的真实资源接续

此前batch033只有独立字幕中퍼스트→一号候选，通用terms导入器拒绝未导出的Movies资源。
本批CSMB08_10首次提供实际Coalesced的퍼스트锚点，因此同译法可按现有schema纳入共享terms，
无需伪造Coalesced ID，也无需放宽资源校验。旧batch033测试的全局“共享库永不含一号”断言在本批失败；
修订为历史前33批无该锚点、若后续共享则必须有真实后续计划ID/相同候选译法/Coalesced资源的正向契约，原字幕校验保留。原batch033字幕候选记录及hash逐字节保持。
新增共享11项：一号、尼克斯、中央研究室/所、动力装置/传送装置空格变体、动力钥匙和保管箱/钥匙。
均candidate/unverified，未核定官方译名或人工定稿；历史字幕记录与共享词条是不同来源，不重复计为独立已核身份。

第八章独立字幕只含csm08-30/40，尚未到该场景，本批不重复导出完整ISO。
第45批Windows3.14单项曾与成功总流程状态不一致；本轮重读单项已completed/success，之前三组成功终态保留，四组通过。
列表API曾Server Error，不当作测试失败；跟踪证据追加在build/batch-045-verification/VERIFICATION.txt。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/lab-opening-batch046/current-workspace
python build/batch-046-verification/verify_resources.py baseline
python build/batch-046-verification/verify_resources.py modified
python build/batch-046-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

输出须全新；current-workspace为任务路线措辞修订后的最终输入锁，未削弱格式/源hash校验。
双盘INT原hash保持179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c。
新93条双盘回填一致，旧6,070条保留，12,013条仍为源值；独立回滚恢复6,070条，主修改产物保留6,163条。
全部历史held/未知格式/旧译/重复key occurrence保持；错误hash回滚拒绝且不变。
干净Git index源码测试（修订后fresh clean-source-final）、123项依赖锁、164文件重建一致性与四组CI分别核对；完整原文/资源/验证证据仅在build/batch-046-verification。

仅清理核实绝对路径下可再生且无入口依赖的验证pyc；保留原盘/配置/存档/runs/当前包及必要研究和回滚证据。
未生成ISO或整盘副本，未启动模拟器，未刷新字库/TOC/可玩入口；离线成功不代替游戏验收。
下一批从CSMB08_20接续实验室事件与相关营救任务，再按场景补独立字幕。
