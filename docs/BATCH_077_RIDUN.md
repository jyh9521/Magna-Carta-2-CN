# 第七十七批：重逢、利登旧宅与队伍引导

日期：2026-10-20。新增INT39条，累计8,591条draft；共享402项candidate及1项历史字幕来源记录保持。
独立字幕44计划315/315已提取cue、邮件122/235保持，均未人工定稿。

## 范围与语境

- CSMBQ07_20/30/40/45/48五段27，Q07_qube_1任务说明/标题2，PartyTalk五角色Ch07两个阶段10同步；37 dialogue、1 quest_description、1 name。
- 泽罗哈重逢/被包围、拜泽恩线索、利登旧宅/火焰机关/读信后回顾分别核读，不按目录号断言实际触发顺序。父亲曾在此及被带走为转述，去王城可能得到线索仍为可能，不补下落或生死结论。
- 旧Q07邮件三封六字段、利登家主的信名/描述、家族火球/充能器、Chapter07既有40字段及07_前缀150任务全部保持，仅作上下文不重复计数。Q07_qube_1不在数字07_前缀中，不能以150任务有draft泛称全章所有任务已译。
- PartyTalk分别保留五角色的营救目标与研究所入口引导：占领区/驻地按源词分开，露只说情报员，不擅自替换为泽罗哈；阿尔戈/克罗塞尔相同源提示完整复用同一译值。
- Q07_qube_1/no_0原为编辑器默认值字面串；PartyTalk_Zephi两处原为纯省略号。三条按ID/hash保持held，不译、不照抄计draft；省略号是沉默、占位还是功能用途未核，不断言运行不用。
- 复用泽罗哈、拜泽恩、利登家族、玛莉丝、火之连环术/师与哨兵研究所候选。402项terms及GLOSSARY逐字节保持，无新增术语或人工定稿。机关“谁都能开”为角色夸口，不当实测权限/机制结论。
- 任务两字段保留布局，DES保留2处功能换行；23条普通对白/队伍引导显式去硬换行，控制码/数值/按键与前后空白保持。
- CSMBQ07完整40/40有draft，Q06旧117/117保持；PartyTalk的Ch07为10draft/2held。不是整章、全文或游戏验收完成。后续接CSMBQ08研究记录/寻找计划26条及同阶段关联任务、引导；后期玛拉基亚支线另接。

## 验证与收尾

```powershell
python tools/prepare_translation_workspace.py --source-root . --workflow locales/zh-Hans/translation-workflow.json --output build/ridun-batch077/workspace
python build/batch-077-verification/verify_resources.py baseline
python build/batch-077-verification/verify_resources.py modified
python build/batch-077-verification/verify_resources.py rollback
python -m unittest discover -s tests -q
python tools/series_terms.py check --with-references
python tools/series_terms.py render --check
python tools/check_repository.py
```

双盘INT源hash179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c保持。
39条双盘回填一致，旧8,552条保留，9,585条其余原值未改；隔离回滚恢复8,552条，主产物保留8,591条。
基线1218、修改/干净index1224测试各skip1；201项依赖锁、164工作区文件重建一致、647份index文件复核及错误hash回滚拒绝分别验证。
历史held含11_trewa/911_2及当前3处、重复occurrence、44字幕计划/profile/315cue、历史字幕来源、README、terms与GLOSSARY冻结。
第76批CI run39318778199四组实际completed/success；当前提交状态另存，不预报通过。
仅清理核实绝对路径内可再生验证pyc；保留原盘、配置、存档、runs、当前包、基线/回滚与研究证据。
未生成ISO/整盘副本，未启动模拟器，未刷新字库/TOC/玩家入口；离线成功不代替游戏验收，不以本次提交作为项目结束。
