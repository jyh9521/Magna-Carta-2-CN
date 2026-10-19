# 第三十八批：成人礼通知与水火王之试炼

日期：2026-10-19。新增INT69条，累计5,400条draft；246项共享candidate及1项独立字幕candidate。
字幕27份187/315cue不变，所有译文与术语仍未人工定稿。

## 上下文与范围

- Quest/06_Qube_1成人礼通知4字段。
- 06_zepi_0王之试炼引导19、06_zepi_1水之试炼18、06_zepi_2火之试炼21，共58字段。
- 水之试炼order_2含此前已记录的未知反斜线序列，保持原值；该段19字段中仅18有draft，不称整段完成。
- CharacterName水/火之魂2字段；UI/information四神殿与Navigation/KingsDoom共5字段。
- 分类52 dialogue、11 name、4 quest_description、2 quest_progress。

Verified / source/offline：新增ID与前37批无重叠；Quest/06_由163增至225/316，剩91字段。
王之试炼、王室神殿、四神殿、水火之魂、水之民、赞达利亚峡谷、暗影藏身处和蕾洁菲尔妲全名，
共12项candidate。格蕾娜/赞达利亚为暂定音译，不视为官方译名或跨作身份已核定。
全名复用蕾洁菲尔妲与贝尔利内特音译部分，不覆盖旧姓名/家族词条。
各族认可、初代王惠西斯的观点、卡尔塔与人类的历史仍按说话者转述；
两位王的后裔与另一位获认可者仍仅译现有对白，不擅补指代对象或幕后机制。
com_4/com_5的未完句衔接、各段王权与中庸论述保持独立ID，不拼接或添加史实。

4条DES功能换行共3个保持；49条普通对白通过显式line_break_policy去源硬换行。
QUEST标识、ASCII标题连字符与方括号保持。未知序列及历史held值/重复key occurrence均原样保留。
邮件96/235字段及字幕profile/27份计划/独立字幕候选逐字节不变。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/royal-trials-batch038/workspace
python build/batch-038-verification/verify_resources.py baseline
python build/batch-038-verification/verify_resources.py modified
python build/batch-038-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

输出须全新；双盘原始资源SHA256保持179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c。
新69条回填一致，旧5,331条保留，12,776条仍为源值；独立回滚恢复5,331条，主修改产物保留5,400条。
错误hash回滚拒绝且不变；干净Git index源码测试、106项依赖锁、164文件重建一致性及四组云端CI分别核查。
完整原文、容器、差异和验证脚本只在build/batch-038-verification，不进入Git。

仅清理核实绝对路径下可再生且无入口依赖的验证pyc；原盘/配置/存档/runs/当前包及必要研究和回滚证据保留。
未生成ISO或整盘副本，未启动模拟器，未刷新字库/TOC/可玩入口；离线验证不代替游戏验收。
下一批接续06_301_0/302_0/304_0/307_0/699_0关联任务；雷/风神殿任务实际章节前缀需另审计，不能按UI名称推定本批已覆盖。
