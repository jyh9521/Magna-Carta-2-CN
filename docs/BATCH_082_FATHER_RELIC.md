# 第八十二批：父女相见与母亲的遗物

日期：2026-10-20。新增INT26条，累计8,801条draft；共享candidate411项，另保留1项历史字幕来源记录。未人工定稿。

## 范围与语境

- CSMBQ10_40父女相见19条与Quest10_cerestin_2七字段同步：24 dialogue、1 quest_description、1 name。11条普通对白显式去硬换行，两个非对白字段保留布局；控制码、括号、键位、数值、前后空白保持。
- 灰烬的推测、风与看向那边、相见、有限时间、物品交付与嘱托按源表达，不补复活、灵魂显现或附身机制，不推断真实运行触发条件。
- 母亲세리틴暂译塞莉汀，与女儿세레스틴塞蕾丝汀、旧세리아塞莉娅分开。只在继承任务两条对白见源，未见独立CharacterName字段；新增1项candidate，旧410项保持，未核官方名或跨作身份。
- 武器원형暂译原形，不扩写为现代实验原型或已确认某Item奖励。拜泽恩希望女儿继承遗物保留推测语气；凯汀将修整成武器，不写成已经完成。
- 拜泽恩/银白的拜泽恩、遗物、凯汀复用旧候选。父名两CharacterName与bizen_token名/描述四字段、此前寻父/研究所/墓地旧译保持，不重复计数。bizen_token原文尾空格与历史译文差异只记录，未借本批更改旧值。
- 本次在现有INT范围按세리틴/바이젠有界检索，不把未见独立母亲字段当运行文字不存在的证明。任务DES的[拜泽恩的遗物]与既有名匹配，不声称特定武器奖励绑定已验。
- CSMBQ10本组完成后97/97 draft；这不是全部支线或全文完成。rue_cerestin七字段下一组接续，不混同Rue_1雷力核心任务。
- 邮件124/235、44独立字幕计划315/315已提取cue、全部历史held与重复occurrence保持；已提取字幕覆盖不等于全部游戏字幕或游戏内验收。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/father-relic-batch082/workspace
python build/batch-082-verification/verify_resources.py baseline
python build/batch-082-verification/verify_resources.py modified
python build/batch-082-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
双盘26条新译回填一致，旧8,775条保留，9,375条其余原值未改；独立副本回滚恢复8,775条，主产物保留8,801条。
基线1248、修改/干净index1254测试各skip1；211依赖锁、164工作区文件重建一致、667份index文件复核及错误hash回滚拒绝分别验证。
README与全部旧字幕候选冻结；GLOSSARY由411项结构化源渲染核对。仅清理已核实绝对路径内可再生验证pyc，保留原盘、配置、存档、runs、当前包和基线/回滚/研究证据。
未生成ISO/整盘副本，未启动模拟器，未刷新字库/TOC/玩家入口；离线成功不代替游戏验收。提交推送后核对远端和干净状态，当前CI以实际状态记录。
