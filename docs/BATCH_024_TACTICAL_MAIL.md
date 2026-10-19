# 第二十四批：第四阶段战术邮件与哨所任务提示

日期：2026-10-19。新增INT13条draft，累计3,847条；204项candidate，0项人工reviewed。

## 覆盖与上下文

- MC2QubeMail/B04_001–005：五封首领/战术邮件，共10个主题/正文字段。
- MC2QubeMail/Q04_QUBE_0：哨所任务邮件主题与正文2字段。
- MC2CharacterName/Default/zerglone：泽格隆姓名1字段。
- 分类6 mail_subject、6 mail_body、1 name；与前23批不重叠。

Verified / source/offline：B04对应第2哨所贝卡斯、利维坦柱子机制、杜南丘陵炸弹箱、
泽格隆火焰与出征准备，Q04提及阿巴泽特附近的北部军哨所，与当前第四阶段地点/任务有关。
这是源文语境对应，不是游戏内触发时机验收。Q04正文源值本身止于未完从句，
译文同样止于“这意味着”，不擅自补充奖励、目标或后续结论。

五封B04正文保守保留34个源硬换行、全部空段落位置；B04_004_Con末尾全角空格保持。
数字2/3、HP、方括号均保持字面/数量；五封战术提示没有对白去硬换行策略。
贝卡斯复用旧candidate；雷卡斯仍独立保留，未推断二者是同一Boss或拼写错误。
利维坦、泽格隆、地面效果、烧伤新增4项candidate，官方英文/跨作身份尚未确认。

当前MC2QubeMail共235字段，E04/B04/Q04合计70字段有draft，余165字段仍须审计。
不是全章或全部邮件完成。字幕profile及18份141cue计划逐字节保持旧HEAD；
本批不重复csm04两份14cue，不重读完整ISO，不将既有字幕证据称为新增验证。

## 重建与验证

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/tactical-mail-batch024/workspace
python build/batch-024-verification/verify_resources.py baseline
python build/batch-024-verification/verify_resources.py modified
python build/batch-024-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

输出须全新。双盘源hash保持，回填字节一致；旧3,834条保持，14,329条仍为源值。
独立副本回滚恢复3,834条基线，主MODIFIED_FILE.int保留3,847条；错误hash输入拒绝且不变。
干净Git index源码测试、69项依赖锁、164文件重建一致性及推送后四组GitHub CI分别核对。
完整证据存于build/batch-024-verification，不将原文、容器或生成资源提交Git。

仅清理已核实可再生成且无入口依赖的验证缓存；保留原盘、配置、存档、runs、当前测试包及必要基线/研究/回滚证据。
未生成ISO或整盘副本，未启动模拟器，未刷新字体、TOC或可玩入口；离线成功不是游戏验收。
下一批从CSMB05_001（10条）继续，随后05_020/030/031；按相邻场景补齐第五章独立字幕及NPC/任务关联，
不重复已译E04/B04/Q04或第四章主剧情。
