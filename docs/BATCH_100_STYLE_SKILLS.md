# 第一百批：朱特、阿尔戈、洁菲六风格技能（164条）

日期：2026-10-20。第99批清理推送并核对后直接接续；新增164条INT draft，累计10,735。新增51项技能候选，共526项；旧475项保持。

## 完整功能组

- MC2Skill：Common9、StatUP1、Juto_Style1/2各25、Argo_Style1/2为23/21、Zephie_Style1/2为35/25。名称、普通说明与战斗说明按独立ID分别回填；原有已译字段不重复计数。
- StatStrong的8种属性主语与2个增长后缀共10条拼接片段保持held。数值位置/百分比/中文拼接词序未验证，不只翻前后片段拼出未经确认的句子。
- 旧反击、重击、狮子吼、破甲、风之盾、疗愈术等复用。源응급처치译应急处理，与旧精华提取是不同字段，不能仅凭同角色风格强行改成相同技能。
- 单体/全体/周围的对象范围、3/4/5次、1名、KAN减少1与HP/SP按实际源保留；没有补倍率、概率或持续时间。
- 正常/战斗说明保留各自功能换行、逐行首尾空白，未机械复用一个带换行版本覆盖两个ID；连携奥义已有的风/雷字段与同key两occurrence保持。

## 汉字名的有限跨源依据

Verified / source：本地INT与JPN实际提取字段中，朱特两风格的命名/邻接技能说明逐项核读。
以下是候选字形依据，不是仅凭key声明全部多语对齐，更不是官方中文定稿；JPN本身未改。

| INT字段 | JPN实际字形 | 本批中文候选 |
|---|---|---|
| Juto_Style1/Juto_Normal | 空進斬 | 空进斩 |
| Juto_Style1/Juto_Skill02 | 空進連閃 | 空进连闪 |
| Juto_Style1/Juto_Skill03 | 鉄一影 | 铁一影 |
| Juto_Style1/Juto_Skill04 | 幻隠閃 | 幻隐闪 |
| Juto_Style1/Juto_Skill05 | 裂進連閃 | 裂进连闪 |
| Juto_Style1/Juto_Skill06 | 空破裂進閃 | 空破裂进闪 |
| Juto_Style1/Juto_Skill07 | 超絶破天舞 | 超绝破天舞 |
| Juto_Style2/Juto_Normal | 剛進斬 | 刚进斩 |
| Juto_Style2/Juto_Skill03 | 破鎖乱閃 | 破锁乱闪 |
| Juto_Style2/Juto_Skill06 | 空破無双刀 | 空破无双刀 |

其他外来技能名为意译/音译candidate，来源、锚点与未验证关系记录在terms.json；不把字形参考升级为实际招式效果或官方译名证明。

## 重建与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/batch-100-verification/verified-workspace
python build/batch-100-verification/verify_resources.py baseline
python build/batch-100-verification/verify_resources.py modified
python build/batch-100-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

Verified / offline：双盘源INT仍为179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c，回填双盘相同。
旧10,571条保持、7,441个其余原值保持；隔离回滚恢复10,571，主MODIFIED_FILE仍为10,735。基线1356测试，新增六项回归后1362测试；完整结果以本地VERIFICATION.txt为准。
新静态回归最初误将一处源前导空格写成两空格断言，已按真实源修正；实际回填逐行空白核对通过，不改原文来迁就测试。

全部历史held、邮件128/235与44字幕315cue保持；复用既有测试副本，无ISO/整盘副本、字库/TOC/入口刷新或游戏内验收。
清理仅移除隔离源码验证副本里可再生成且无依赖的pyc；原盘、配置、存档、runs、当前测试包、回滚/研究证据保留。
推送核对后继续余下三名角色风格及卡蒙德完整功能组。
