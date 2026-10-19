# 第三十五批：第六章城镇与地区NPC补齐

日期：2026-10-19。新增INT132条，累计5,200条draft；228项共享candidate及1项独立字幕candidate。
均未人工定稿。字幕profile27份187/315cue不变。

## 范围与明确覆盖

- NpcTalk/06_Abajet源序第121至191条：59条draft、12个源标记保持（11删除、1纯连字符）。
- 06_oldfox/chinook/dunanhill/dunanfield：7/24/18/21，共70条。
- CharacterName/Heingel、FieldName/LanoaraLake与RuinofReinpolt：3个关联字段。
- 分类129 dialogue、3 name。

Verified / source/offline：所有新增ID与前34批无重叠。城镇全部191字段已检查，166draft/25标记保持；
第六章NpcTalk/06_七组共312字段，287draft/24删除标记及1纯连字符保持。
2202_0、2244_0、2245_0各有正常对白和删除标记两个occurrence，分别处理；2254_0两条正常对白语境不同也不合并。
源纯连字符2254_1不翻成对白，不计draft。其他六组地区NPC共121条均有draft，不扩大为所有游戏NPC完成。

海因格尔、拉诺阿拉湖、雷恩波尔特及其废墟新增4项candidate，关联地点/姓名复用相同译法。
150年字面及方括号保持；77条普通对白去源硬换行有显式line_break_policy。
岛民对新生的期待、战争追悼、历史怪物兵器与变异猜测保留发言立场，不补真实医疗解释或将传闻升级为事实。
原分成相邻key的句子继续分开，不将相邻台词合并成新ID。

CSMB06主线201、Compose67与五份字幕33cue已draft，仍不是全章所有可见文字完成。
Quest/06_当前50/316字段有draft，余266字段（含王之试炼未知反斜线）与E06/Q06邮件尚待推进。
字幕profile、27份计划和一号独立候选逐字节保持旧HEAD，本批不重读完整ISO。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/sixth-regions-batch035/workspace
python build/batch-035-verification/verify_resources.py baseline
python build/batch-035-verification/verify_resources.py modified
python build/batch-035-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

输出须全新。双盘INT原hash保持，132条新值回填一致；旧5,068条保留，12,976条仍为源值。
独立回滚恢复5,068条基线，主MODIFIED_FILE.int保留5,200条；错误hash输入拒绝且不变。
干净Git index源码测试、100项依赖锁、164文件重建一致性及推送后四组GitHub CI分别核对。
完整原文、资源与本机验证脚本只在build/batch-035-verification，不进入Git。

仅清理已核实可再生成且无入口依赖的验证缓存；保留原盘、配置、存档、runs、当前包及必要基线/回滚/研究证据。
未生成ISO或整盘副本，未自行启动模拟器，未刷新字体、TOC或可玩入口；离线成功不是游戏验收。
下一批按地区关联接续06_601_0/602_0/603_0/603_1等任务及关联名称，再审计邮件/王之试炼，未知格式继续保留。
