# 第一百零一批：其余六风格与强化加成（181条）

日期：2026-10-20。新增181条INT draft，累计10,916；新增49项技能candidate至575项，旧526项不改。

## 完整功能组与语境

- 塞蕾丝汀两风格29/22、露26/25、克罗塞尔23/20，合计145技能字段；MC2Kamond/Kamond_EquipBonus完整36字段。旧技能字段不重复计数，属性拼接等全部历史held保持。
- 保留源数据39个加号、2个百分号、16处强化加成换行及并列属性空格；数字、属性顺序、逐行首尾空白不改。寒冷/炎热免疫按源，不扩大为冰/火伤害免疫。
- Water字段的冰属性、技能的水之KAN/水之力、冰之波动逐字段依源保留，不替引擎统一水冰术语。빠르기暂译速度，不因DEX字段名改写为另一源词민첩的敏捷。
- 复用精气吸收、连环反射、瞬杀、雷震波、连环爆发、古代之魂、马雷族及旧连携奥义译法。新外来技能名为意译/音译candidate，不视为官方中文或机制验证。
- 潜隐三技能的使用前提、瞬杀发动率提高、逐渐恢复HP、单体/周围/一定范围、异常状态与材料效果均按源；不补概率、持续秒数、伤害倍率或任务触发结论。
- 普通说明与战斗说明按独立ID保留功能换行，不覆盖同名key的其他occurrence；旧10,735条保持。

## 有限跨源核读

Verified / source：核读本地INT与JPN对应技能名及完整说明，不据此声称所有同key剧情都已对齐。

| 字段 | 本地JPN实际字形/差异 | 本批处理 |
|---|---|---|
| Rue_Style1/Rue_Skill00 | 飛燕 | 飞燕，candidate |
| Rue_Style1/Rue_Skill02/03/04 | 潛隱 / 隱影 / 刺閃 | 潜隐 / 隐影 / 刺闪，candidate |
| Rue_Style1/Rue_Skill05/07 | 爆龍 / 不動陣 | 爆龙 / 不动阵，candidate |
| Crocell_Style1/Crocell_Skill02/05 | 爆鎖陣 / 爆鎖極陣 | 爆锁阵 / 爆锁极阵，candidate |
| Crocell_Style1/Crocell_Skill04 | JPN末字槌，INT为퇴，说明为连续回旋踢 | 依INT及动作说明译镇炎螺旋腿，不套JPN槌 |
| Crocell_Style2/Crocell_Normal | 玉炎旋風 | 玉炎旋风，字形参考但仍为candidate |
| Rue_Style2/Rue_inherent | JPN雷陣波，INT뇌진파 | 复用既有雷震波，不暗改旧候选 |

JPN资源未改；字形、跨语差异与中文候选的置信度不混为一谈。完整源资源与离线对照证据保留在忽略的build目录，不提交游戏资产。

## 可复现验证与阶段收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/batch-101-verification/final-workspace
python build/batch-101-verification/verify_resources.py baseline
python build/batch-101-verification/verify_resources.py modified
python build/batch-101-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘源INT SHA256仍为179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c。
双盘回填一致、旧10,735条与7,260个其余源值保持；隔离回滚恢复10,735，主MODIFIED_FILE保留10,916。
基线1362测试；本批新增六项范围/旧译/held/加成符号/条件/候选/字幕锁回归。完整运行命令、字面结果与退出状态保存在本地VERIFICATION.txt。

按用户重申的持续推进约定，每阶段统一验证、检查差异/依赖与仓库卫生，清理可再生成且无入口依赖的临时输出，提交推送并核对远端，再进入下一阶段。
保留原盘、配置、存档、runs、当前测试包与必要基线/回滚/研究证据。不生成ISO或整盘副本；未刷新字库/TOC/可玩入口，不把离线成功当作游戏验收。
邮件128/235、44字幕315cue保持；剩余原值含工具/样本，并非确定玩家待译总量。下一阶段核读卡蒙德词典与属性/状态说明等完整功能组。
